#!/usr/bin/env python3
"""Fine-tune Whisper on the strict speaker-safe Garhwali ASR split."""

import argparse
import json
import os
import random
from collections import Counter
from pathlib import Path

from asr_metrics import normalize
from run_whisper_comparison import make_prediction_row, model_weight_sha256, sha256_file


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


def training_tier(row):
    return (
        row.get('curriculum_tier')
        or row.get('target_type')
        or row.get('transcript_review_status')
        or 'strict_human_reference'
    )


def validate_split_isolation(train_rows, evaluation_rows):
    """Reject unsafe or overlapping training/evaluation manifests."""
    unsafe_training = sum(row.get('split_safe_for_training') is False for row in train_rows)
    unsafe_evaluation = sum(row.get('split_safe_for_evaluation') is False for row in evaluation_rows)
    if unsafe_training:
        raise ValueError(f'{unsafe_training} training rows are not marked safe for training')
    if unsafe_evaluation:
        raise ValueError(f'{unsafe_evaluation} evaluation rows are not marked safe for evaluation')

    train_audio = {row.get('audio_sha256') for row in train_rows if row.get('audio_sha256')}
    evaluation_audio = {row.get('audio_sha256') for row in evaluation_rows if row.get('audio_sha256')}
    audio_overlap = train_audio & evaluation_audio
    if audio_overlap:
        raise ValueError(f'train/evaluation audio hash overlap: {len(audio_overlap)}')

    train_text = {normalize(training_target(row)) for row in train_rows if normalize(training_target(row))}
    evaluation_text = {
        normalize(training_target(row)) for row in evaluation_rows
        if normalize(training_target(row))
    }
    text_overlap = train_text & evaluation_text
    if text_overlap:
        raise ValueError(f'train/evaluation normalized transcript overlap: {len(text_overlap)}')

    def known_speakers(rows):
        return {
            str(row['speaker_id']).strip()
            for row in rows
            if row.get('speaker_id') is not None
            and str(row['speaker_id']).strip().casefold() not in {'', 'na', 'unknown', 'null', 'none'}
        }

    speaker_overlap = known_speakers(train_rows) & known_speakers(evaluation_rows)
    if speaker_overlap:
        raise ValueError(f'train/evaluation known speaker overlap: {len(speaker_overlap)}')
    return {
        'audio_hash_overlap_groups': 0,
        'normalized_text_overlap_groups': 0,
        'speaker_overlap_ids': 0,
        'unsafe_training_rows': 0,
        'unsafe_evaluation_rows': 0,
    }


def seed_training(seed, torch_module):
    random.seed(seed)
    torch_module.manual_seed(seed)


def resolve_manifest_paths(split_dir, eval_split, train_manifest=None, eval_manifest=None):
    train_path = Path(train_manifest) if train_manifest else Path(split_dir) / 'train.jsonl'
    eval_path = Path(eval_manifest) if eval_manifest else Path(split_dir) / f'{eval_split}.jsonl'
    return train_path, eval_path


def evaluation_prediction_row(row, hypothesis, metrics):
    """Retain stable input identity and source metadata beside each score."""
    result = make_prediction_row(row, hypothesis, metrics)
    result['prediction'] = result.pop('hypothesis')
    return result


def training_weight(row):
    weight = float(row.get('sample_weight', 1.0))
    if weight <= 0:
        raise ValueError('Training sample weights must be positive')
    return weight


def weighted_training_loss(loss, row):
    return loss * training_weight(row)


def normalized_batch_weights(rows):
    weights = [training_weight(row) for row in rows]
    total = sum(weights)
    return [weight / total for weight in weights]


def weighted_batch_loss(losses, rows):
    return sum(
        loss * weight
        for loss, weight in zip(losses, normalized_batch_weights(rows))
    )


def build_stratified_weighted_batches(rows):
    human = sorted(
        (row for row in rows if row.get('target_type') == 'human_reference'),
        key=lambda row: row['audio_sha256'],
    )
    machine = sorted(
        (row for row in rows if row.get('target_type') == 'machine_pseudo_label'),
        key=lambda row: row['audio_sha256'],
    )
    if len(human) + len(machine) != len(rows):
        raise ValueError('Weighted batches found an unsupported target type')
    if not human or not machine:
        raise ValueError('Weighted batches require both human and machine records')
    batches = [[row] for row in human]
    for index, row in enumerate(machine):
        batches[index % len(batches)].append(row)
    return batches


def summarize_weighted_batches(batches, epochs):
    rows = [row for batch in batches for row in batch]
    sizes = [len(batch) for batch in batches]
    return {
        'batches_per_epoch': len(batches),
        'projected_optimizer_steps': len(batches) * epochs,
        'records_per_batch': {'minimum': min(sizes), 'maximum': max(sizes)},
        'human_records': sum(
            row.get('target_type') == 'human_reference' for row in rows
        ),
        'machine_records': sum(
            row.get('target_type') == 'machine_pseudo_label' for row in rows
        ),
        'human_weight_mass': sum(
            training_weight(row)
            for row in rows
            if row.get('target_type') == 'human_reference'
        ),
        'machine_weight_mass': sum(
            training_weight(row)
            for row in rows
            if row.get('target_type') == 'machine_pseudo_label'
        ),
    }


def resolve_evaluation_split(requested, curriculum_stage):
    if requested:
        return requested
    return 'validation' if curriculum_stage is not None else 'test'


def select_pilot_rows(rows, human_records, machine_records):
    human = sorted(
        (row for row in rows if row.get('target_type') == 'human_reference'),
        key=lambda row: row['audio_sha256'],
    )
    machine = sorted(
        (row for row in rows if row.get('target_type') == 'machine_pseudo_label'),
        key=lambda row: row['audio_sha256'],
    )
    if len(human) < human_records:
        raise ValueError(f'Pilot requested {human_records} human rows but only {len(human)} exist')
    if len(machine) < machine_records:
        raise ValueError(
            f'Pilot requested {machine_records} machine rows but only {len(machine)} exist'
        )
    return sorted(
        human[:human_records] + machine[:machine_records],
        key=lambda row: row['audio_sha256'],
    )


def is_complete_stage_run(curriculum_stage, max_train, pilot_human, pilot_machine):
    if curriculum_stage is None:
        return True
    return not max_train and not pilot_human and not pilot_machine


def generation_kwargs():
    return {'language': 'hi', 'task': 'transcribe', 'max_length': 128}


def validate_previous_stage(output, current_stage):
    output = Path(output)
    sidecar = output / 'curriculum_stage_report.json'
    report_path = sidecar if sidecar.exists() else output / 'report.json'
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
    records_by_tier = Counter(training_tier(row) for row in train_rows)
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
    parser.add_argument('--train-manifest', type=Path)
    parser.add_argument('--eval-manifest', type=Path)
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--learning-rate', type=float, default=1e-5)
    parser.add_argument('--max-train', type=int, default=0)
    parser.add_argument('--max-eval', type=int, default=0)
    parser.add_argument('--save-every', type=int, default=100)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    parser.add_argument('--local-files-only', action='store_true')
    parser.add_argument('--curriculum-stage', type=int, choices=range(5))
    parser.add_argument('--eval-split', choices=('validation', 'test'))
    parser.add_argument('--resume-from', type=Path)
    parser.add_argument('--pilot-human', type=int, default=0)
    parser.add_argument('--pilot-machine', type=int, default=0)
    parser.add_argument('--weighted-batches', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--dry-run-report', type=Path, default=DRY_RUN_REPORT)
    args = parser.parse_args()

    os.environ.setdefault('HF_HOME', str(ROOT / '.cache/huggingface'))
    os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    if (args.train_manifest or args.eval_manifest) and args.curriculum_stage is not None:
        parser.error('custom manifests cannot be combined with --curriculum-stage')
    split_dir = CURRICULUM_SPLITS if args.curriculum_stage is not None else SPLITS
    eval_split = (
        'custom' if args.eval_manifest and args.eval_split is None
        else resolve_evaluation_split(args.eval_split, args.curriculum_stage)
    )
    train_manifest_path, eval_manifest_path = resolve_manifest_paths(
        split_dir, eval_split, args.train_manifest, args.eval_manifest
    )
    all_train_rows = load_rows(train_manifest_path, max_stage=args.curriculum_stage)
    pilot_requested = bool(args.pilot_human or args.pilot_machine)
    if pilot_requested:
        if args.curriculum_stage != 1:
            parser.error('pilot selection currently requires --curriculum-stage 1')
        if not args.pilot_human or not args.pilot_machine:
            parser.error('--pilot-human and --pilot-machine must both be positive')
        if args.max_train:
            parser.error('--max-train cannot be combined with pilot selection')
        train_rows = select_pilot_rows(
            all_train_rows, args.pilot_human, args.pilot_machine
        )
    else:
        train_rows = all_train_rows[:args.max_train] if args.max_train else all_train_rows
    if args.weighted_batches:
        if args.curriculum_stage is None or args.curriculum_stage < 1:
            parser.error('--weighted-batches requires curriculum stage 1 or later')
        try:
            training_batches = build_stratified_weighted_batches(train_rows)
        except ValueError as error:
            parser.error(str(error))
    else:
        training_batches = [[row] for row in train_rows]
    eval_rows = load_rows(eval_manifest_path, args.max_eval)
    split_isolation = validate_split_isolation(train_rows, eval_rows)
    output = args.output
    if output == DEFAULT_OUTPUT and args.curriculum_stage is not None:
        suffix = f'curriculum-stage-{args.curriculum_stage}'
        if pilot_requested:
            suffix += f'-pilot-h{args.pilot_human}-m{args.pilot_machine}'
        if args.weighted_batches:
            suffix += '-weighted-batches'
        output = ROOT / f'models/whisper-tiny-garhwali-{suffix}'
    complete_stage = is_complete_stage_run(
        args.curriculum_stage,
        args.max_train,
        args.pilot_human,
        args.pilot_machine,
    )
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
        if args.weighted_batches:
            batch_plan = summarize_weighted_batches(training_batches, args.epochs)
            plan['projected_training_steps'] = batch_plan['projected_optimizer_steps']
            plan['weighted_batch_plan'] = batch_plan
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
            'run_id': f'garhwali-whisper-training-dry-run-seed-{args.seed}',
            'curriculum_stage': args.curriculum_stage,
            'seed': args.seed,
            'evaluation_split': eval_split,
            'training_manifest': str(train_manifest_path),
            'training_manifest_sha256': sha256_file(train_manifest_path),
            'evaluation_manifest': str(eval_manifest_path),
            'evaluation_manifest_sha256': sha256_file(eval_manifest_path),
            'initial_model_weight_sha256': model_weight_sha256(model_source),
            'split_isolation': split_isolation,
            'full_stage_train_records': len(all_train_rows),
            'pilot_human_records': args.pilot_human,
            'pilot_machine_records': args.pilot_machine,
            'batching_strategy': (
                'stratified_normalized_weighted_gradient_accumulation'
                if args.weighted_batches else 'one_record_per_optimizer_step'
            ),
            'training_complete': complete_stage,
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
    seed_training(args.seed, torch)
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
    initial_model_weight_sha256 = model_weight_sha256(model_source)
    model.config.use_cache = False
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    raw_losses = []
    objective_losses = []
    step = 0
    examples_seen = 0
    model.train()
    for epoch in range(args.epochs):
        for batch in training_batches:
            optimizer.zero_grad(set_to_none=True)
            factors = (
                normalized_batch_weights(batch)
                if args.weighted_batches
                else [training_weight(batch[0])]
            )
            batch_objective = 0.0
            for row, factor in zip(batch, factors):
                audio = read_audio(ROOT / row['local_audio_path'])
                features = processor(
                    audio, sampling_rate=16000, return_tensors='pt'
                ).input_features.to(device)
                labels = processor.tokenizer(
                    training_target(row), return_tensors='pt'
                ).input_ids.to(device)
                raw_loss = model(input_features=features, labels=labels).loss
                objective_loss = raw_loss * factor
                objective_loss.backward()
                raw_losses.append(float(raw_loss.detach().cpu()))
                batch_objective += float(objective_loss.detach().cpu())
                examples_seen += 1
            optimizer.step()
            step += 1
            objective_losses.append(batch_objective)
            state = {
                'epoch': epoch + 1,
                'step': step,
                'examples_seen': examples_seen,
                'last_audio_sha256': batch[-1]['audio_sha256'],
                'batch_records': len(batch),
                'batch_weight_mass': sum(training_weight(row) for row in batch),
                'device': device,
                'curriculum_stage': args.curriculum_stage,
                'batching_strategy': (
                    'stratified_normalized_weighted_gradient_accumulation'
                    if args.weighted_batches else 'one_record_per_optimizer_step'
                ),
            }
            (output / 'trainer_state.json').write_text(
                json.dumps(state, indent=2) + '\n', encoding='utf-8'
            )
            if step == 1 or step % 25 == 0:
                print(
                    f"step={step}/{len(training_batches) * args.epochs} "
                    f"examples={examples_seen} batch_records={len(batch)} "
                    f"objective_loss={objective_losses[-1]:.4f}",
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
            generated = model.generate(features, **generation_kwargs())
            prediction = processor.batch_decode(
                generated,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0].strip()
            reference = training_target(row)
            metrics = score(reference, prediction)
            scores.append(metrics)
            predictions.append(evaluation_prediction_row(row, prediction, metrics))
    evaluation = summarize_scores(scores)
    (output / 'evaluation_predictions.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in predictions), encoding='utf-8'
    )
    report = {
        'base_model': args.model,
        'model_source': model_source,
        'initial_model_weight_sha256': initial_model_weight_sha256,
        'trained_model_weight_sha256': model_weight_sha256(output),
        'device': device,
        'seed': args.seed,
        'epochs': args.epochs,
        'curriculum_stage': args.curriculum_stage,
        'full_stage_train_records': len(all_train_rows),
        'pilot_human_records': args.pilot_human,
        'pilot_machine_records': args.pilot_machine,
        'resumed_from_stage': (
            previous_stage_report['curriculum_stage'] if previous_stage_report else None
        ),
        'train_records': len(train_rows),
        'training_manifest': str(train_manifest_path),
        'training_manifest_sha256': sha256_file(train_manifest_path),
        'training_steps': step,
        'training_examples': examples_seen,
        'batching_strategy': (
            'stratified_normalized_weighted_gradient_accumulation'
            if args.weighted_batches else 'one_record_per_optimizer_step'
        ),
        'records_per_batch': {
            'minimum': min(len(batch) for batch in training_batches),
            'maximum': max(len(batch) for batch in training_batches),
        },
        'effective_weight_mass': round(
            sum(training_weight(row) for row in train_rows), 6
        ),
        'mean_training_loss': sum(objective_losses) / max(1, len(objective_losses)),
        'mean_raw_training_loss': sum(raw_losses) / max(1, len(raw_losses)),
        'evaluation_records': len(eval_rows),
        'evaluation_split': eval_split,
        'evaluation_manifest': str(eval_manifest_path),
        'evaluation_manifest_sha256': sha256_file(eval_manifest_path),
        'split_isolation': split_isolation,
        'training_complete': complete_stage,
        **evaluation,
    }
    (output / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
