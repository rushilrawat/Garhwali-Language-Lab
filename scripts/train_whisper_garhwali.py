#!/usr/bin/env python3
"""Fine-tune Whisper on the strict speaker-safe Garhwali ASR split."""

import argparse
import json
import os
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / 'data/processed/model_ready/splits/asr'
CURRICULUM_SPLITS = ROOT / 'data/processed/model_ready/asr_curriculum'
DEFAULT_OUTPUT = ROOT / 'models/whisper-tiny-garhwali-v0.1'
DRY_RUN_REPORT = CURRICULUM_SPLITS / 'trainer_dry_run_report.json'


def load_rows(path, limit=0, max_stage=None):
    with path.open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if max_stage is not None:
        rows = [row for row in rows if row['introduced_stage'] <= max_stage]
    rows.sort(key=lambda row: row['audio_sha256'])
    return rows[:limit] if limit else rows


def training_target(row):
    return row.get('target_text', row.get('asr_target_clean', ''))


def training_weight(row):
    weight = float(row.get('sample_weight', 1.0))
    if weight <= 0:
        raise ValueError('Training sample weights must be positive')
    return weight


def weighted_training_loss(loss, row):
    return loss * training_weight(row)


def resolve_evaluation_split(requested, curriculum_stage):
    if requested:
        return requested
    return 'validation' if curriculum_stage is not None else 'test'


def validate_previous_stage(output, current_stage):
    output = Path(output)
    report_path = output / 'report.json'
    if not report_path.exists():
        raise ValueError(f'Previous-stage report is missing: {report_path}')
    report = json.loads(report_path.read_text(encoding='utf-8'))
    expected = current_stage - 1
    if not report.get('training_complete') or report.get('curriculum_stage') != expected:
        raise ValueError(
            f'Curriculum stage {current_stage} requires a completed stage {expected} checkpoint'
        )
    required = ('config.json', 'processor_config.json', 'tokenizer.json')
    has_weights = any(
        (output / name).is_file() for name in ('model.safetensors', 'pytorch_model.bin')
    )
    if not has_weights or any(not (output / name).is_file() for name in required):
        raise ValueError(f'Previous-stage model checkpoint is incomplete: {output}')
    return report


def build_dry_run_plan(train_rows, eval_rows, epochs, root=ROOT):
    targets = [training_target(row) for row in train_rows]
    eval_targets = [training_target(row) for row in eval_rows]
    weights = [training_weight(row) for row in train_rows]
    hashes = [row['audio_sha256'] for row in train_rows]
    records_by_tier = Counter(
        row.get('curriculum_tier', 'strict_human_reference') for row in train_rows
    )
    missing_audio = sum(
        not (Path(root) / row['local_audio_path']).is_file() for row in train_rows + eval_rows
    )
    return {
        'train_records': len(train_rows),
        'evaluation_records': len(eval_rows),
        'projected_training_steps': len(train_rows) * epochs,
        'records_by_tier': dict(sorted(records_by_tier.items())),
        'effective_weight_mass': round(sum(weights), 6),
        'audio_hours': round(
            sum(float(row.get('duration_seconds') or 0) for row in train_rows) / 3600,
            6,
        ),
        'empty_targets': sum(not target.strip() for target in targets),
        'empty_evaluation_targets': sum(
            not target.strip() for target in eval_targets
        ),
        'duplicate_audio_hashes': len(hashes) - len(set(hashes)),
        'missing_audio_files': missing_audio,
    }


def summarize_scores(scores):
    totals = {
        key: sum(row[key] for row in scores)
        for key in ('word_errors', 'reference_words', 'character_errors', 'reference_characters')
    }
    totals['wer'] = totals['word_errors'] / max(1, totals['reference_words'])
    totals['cer'] = totals['character_errors'] / max(1, totals['reference_characters'])
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='openai/whisper-tiny')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--learning-rate', type=float, default=1e-5)
    parser.add_argument('--max-train', type=int, default=0)
    parser.add_argument('--max-eval', type=int, default=0)
    parser.add_argument('--save-every', type=int, default=100)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    parser.add_argument('--local-files-only', action='store_true')
    parser.add_argument('--curriculum-stage', type=int, choices=range(5))
    parser.add_argument('--eval-split', choices=('validation', 'test'))
    parser.add_argument('--resume-from', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--dry-run-report', type=Path, default=DRY_RUN_REPORT)
    args = parser.parse_args()

    os.environ.setdefault('HF_HOME', str(ROOT / '.cache/huggingface'))
    os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    split_dir = CURRICULUM_SPLITS if args.curriculum_stage is not None else SPLITS
    eval_split = resolve_evaluation_split(args.eval_split, args.curriculum_stage)
    train_rows = load_rows(
        split_dir / 'train.jsonl', args.max_train, max_stage=args.curriculum_stage
    )
    eval_rows = load_rows(split_dir / f'{eval_split}.jsonl', args.max_eval)
    output = args.output
    if output == DEFAULT_OUTPUT and args.curriculum_stage is not None:
        output = ROOT / f'models/whisper-tiny-garhwali-curriculum-stage-{args.curriculum_stage}'
    model_source = args.model
    previous_stage_report = None
    if args.resume_from:
        if args.curriculum_stage is None:
            parser.error('--resume-from requires --curriculum-stage')
        previous_stage_report = validate_previous_stage(
            args.resume_from, args.curriculum_stage
        )
        model_source = str(args.resume_from)
    elif args.curriculum_stage and not args.dry_run:
        parser.error('curriculum stages 1-4 require --resume-from for the preceding stage')

    if args.dry_run:
        plan = build_dry_run_plan(train_rows, eval_rows, args.epochs)
        failures = [
            name for name in (
                'empty_targets', 'empty_evaluation_targets',
                'duplicate_audio_hashes', 'missing_audio_files'
            ) if plan[name]
        ]
        if not plan['train_records']:
            failures.append('no_training_records')
        if not plan['evaluation_records']:
            failures.append('no_evaluation_records')
        plan.update({
            'run_id': 'garhwali-whisper-curriculum-dry-run-v0.1',
            'curriculum_stage': args.curriculum_stage,
            'evaluation_split': eval_split,
            'model_source': model_source,
            'resume_from': str(args.resume_from) if args.resume_from else None,
            'previous_stage': previous_stage_report,
            'failures': failures,
            'status': 'passed' if not failures else 'failed',
        })
        args.dry_run_report.parent.mkdir(parents=True, exist_ok=True)
        args.dry_run_report.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
            encoding='utf-8',
        )
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        if failures:
            raise SystemExit(1)
        return

    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from asr_metrics import score
    from run_asr_baseline import read_audio

    if args.device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    else:
        device = args.device
    output.mkdir(parents=True, exist_ok=True)

    processor = WhisperProcessor.from_pretrained(
        model_source,
        cache_dir=ROOT / '.cache/huggingface/hub',
        local_files_only=args.local_files_only or args.resume_from is not None,
    )
    model = WhisperForConditionalGeneration.from_pretrained(
        model_source,
        cache_dir=ROOT / '.cache/huggingface/hub',
        local_files_only=args.local_files_only or args.resume_from is not None,
    ).to(device)
    model.config.use_cache = False
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    raw_losses = []
    weighted_losses = []
    step = 0
    model.train()
    for epoch in range(args.epochs):
        for row in train_rows:
            audio = read_audio(ROOT / row['local_audio_path'])
            features = processor(audio, sampling_rate=16000, return_tensors='pt').input_features.to(device)
            labels = processor.tokenizer(training_target(row), return_tensors='pt').input_ids.to(device)
            optimizer.zero_grad(set_to_none=True)
            raw_loss = model(input_features=features, labels=labels).loss
            weight = training_weight(row)
            weighted_loss = weighted_training_loss(raw_loss, row)
            weighted_loss.backward()
            optimizer.step()
            step += 1
            raw_losses.append(float(raw_loss.detach().cpu()))
            weighted_losses.append(float(weighted_loss.detach().cpu()))
            state = {
                'epoch': epoch + 1,
                'step': step,
                'last_audio_sha256': row['audio_sha256'],
                'device': device,
                'curriculum_stage': args.curriculum_stage,
                'sample_weight': weight,
            }
            (output / 'trainer_state.json').write_text(
                json.dumps(state, indent=2) + '\n', encoding='utf-8'
            )
            if step == 1 or step % 25 == 0:
                print(
                    f"step={step}/{len(train_rows) * args.epochs} "
                    f"raw_loss={raw_losses[-1]:.4f} weighted_loss={weighted_losses[-1]:.4f}",
                    flush=True,
                )
            if args.save_every and step % args.save_every == 0:
                model.save_pretrained(output)
                processor.save_pretrained(output)

    model.save_pretrained(output)
    processor.save_pretrained(output)
    model.eval()
    predictions = []
    scores = []
    with torch.no_grad():
        for row in eval_rows:
            audio = read_audio(ROOT / row['local_audio_path'])
            features = processor(audio, sampling_rate=16000, return_tensors='pt').input_features.to(device)
            generated = model.generate(features, language='hi', task='transcribe', max_new_tokens=128)
            prediction = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
            reference = training_target(row)
            metrics = score(reference, prediction)
            scores.append(metrics)
            predictions.append({
                'audio_sha256': row['audio_sha256'],
                'reference': reference,
                'prediction': prediction,
                **metrics,
            })
    evaluation = summarize_scores(scores)
    (output / 'evaluation_predictions.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in predictions), encoding='utf-8'
    )
    report = {
        'base_model': args.model,
        'model_source': model_source,
        'device': device,
        'epochs': args.epochs,
        'curriculum_stage': args.curriculum_stage,
        'resumed_from_stage': (
            previous_stage_report['curriculum_stage'] if previous_stage_report else None
        ),
        'train_records': len(train_rows),
        'training_steps': step,
        'effective_weight_mass': round(
            sum(training_weight(row) for row in train_rows), 6
        ),
        'mean_training_loss': sum(weighted_losses) / max(1, len(weighted_losses)),
        'mean_raw_training_loss': sum(raw_losses) / max(1, len(raw_losses)),
        'evaluation_records': len(eval_rows),
        'evaluation_split': eval_split,
        'training_complete': True,
        **evaluation,
    }
    (output / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
