#!/usr/bin/env python3
"""Build a three-checkpoint, audio-review queue for risky SraVaani drafts."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from asr_metrics import score
from calibrate_sravaani_recovery_confidence import character_agreement
from redecode_sravaani_recovery import candidate_flags, severity


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl'
WHISPER_V01 = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.1.jsonl'
CALIBRATION_MANIFEST = ROOT / 'data/processed/evaluation/asr/confidence_calibration/manifest.jsonl'
SRA_CALIBRATION = ROOT / 'data/processed/evaluation/asr/confidence_calibration/sravaani/predictions.jsonl'
WHISPER_V01_CALIBRATION = ROOT / 'models/whisper-tiny-garhwali-v0.1/evaluation_predictions.jsonl'
WHISPER_V02_CALIBRATION = ROOT / 'models/whisper-tiny-garhwali-v0.2/evaluation_predictions.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_adjudication.jsonl'
REVIEW = ROOT / 'data/processed/review/sravaani_recovery_adjudication.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_adjudication_report.json'

MODEL_RANK = {
    'ARTPARK-IISc/SraVaani-1.0': 0,
    'whisper-tiny-garhwali-v0.2': 1,
    'whisper-tiny-garhwali-v0.1': 2,
}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prediction(row):
    return row.get('hypothesis', row.get('prediction', ''))


def choose_candidate(candidates):
    """Prefer fewer structural faults, then the strongest held-out model."""
    return min(
        candidates,
        key=lambda item: (
            severity(item['flags']),
            MODEL_RANK[item['model']],
        ),
    )


def build_review_row(row, whisper_v01, whisper_v01_frequency=1):
    recovery = row['recovery_confidence']
    duration = row.get('duration_seconds') or 0
    candidates = [
        {
            'model': 'ARTPARK-IISc/SraVaani-1.0',
            'transcript': row.get('machine_transcript', ''),
            'flags': list((row.get('machine_transcript_quality') or {}).get('flags', [])),
        },
        {
            'model': 'whisper-tiny-garhwali-v0.2',
            'transcript': recovery.get('whisper_candidate', ''),
            'flags': list(recovery.get('whisper_candidate_flags', [])),
        },
        {
            'model': 'whisper-tiny-garhwali-v0.1',
            'transcript': whisper_v01.get('machine_transcript', ''),
            'flags': candidate_flags(
                whisper_v01.get('machine_transcript', ''),
                duration,
                whisper_v01_frequency,
            ),
        },
    ]
    selected = choose_candidate(candidates)
    v01 = candidates[2]['transcript']
    v02 = candidates[1]['transcript']
    sra = candidates[0]['transcript']
    whisper_agreement = character_agreement(v01, v02)
    selected_clean = not selected['flags']
    if selected_clean and selected['model'].startswith('whisper') and whisper_agreement >= 0.75:
        evidence_status = 'related_checkpoint_consensus_clean'
    elif selected_clean:
        evidence_status = 'clean_candidate_low_consensus'
    else:
        evidence_status = 'unresolved_structural_risk'
    priority = 100 * (
        0.55 * (1 - whisper_agreement)
        + 0.30 * min(1.0, severity(selected['flags']) / 80)
        + 0.15 * (1 - float(whisper_v01.get('token_confidence_uncalibrated', 0)))
    )
    return {
        'audio_sha256': row['audio_sha256'],
        'audio_path': row.get('audio_path'),
        'local_audio_path': row.get('local_audio_path'),
        'duration_seconds': row.get('duration_seconds'),
        'district': row.get('district'),
        'speaker_id': row.get('speaker_id'),
        'license': row.get('license'),
        'candidates': candidates,
        'pairwise_character_agreement': {
            'sravaani_to_whisper_v0.1': round(character_agreement(sra, v01), 6),
            'sravaani_to_whisper_v0.2': round(character_agreement(sra, v02), 6),
            'whisper_v0.1_to_v0.2': round(whisper_agreement, 6),
        },
        'whisper_v0.1_token_confidence_uncalibrated': whisper_v01.get(
            'token_confidence_uncalibrated'
        ),
        'proposed_machine_transcript': selected['transcript'],
        'proposed_machine_transcript_model': selected['model'],
        'proposed_machine_transcript_flags': selected['flags'],
        'proposal_basis': 'lowest_structural_severity_then_held_out_model_rank',
        'evidence_status': evidence_status,
        'review_priority': round(priority, 3),
        'human_review_status': 'pending_audio_review',
        'automatic_correction': False,
        'human_reference_available': False,
        'supervised_training_eligible': False,
        'recommended_for_machine_label_training': False,
        'original_transcript_preserved': True,
    }


def calibration_summary(manifest_rows, sra_rows, whisper_v01_rows, whisper_v02_rows):
    manifest = {row['audio_sha256']: row for row in manifest_rows}
    sra = {row['audio_sha256']: row for row in sra_rows}
    v01 = {row['audio_sha256']: row for row in whisper_v01_rows}
    v02 = {row['audio_sha256']: row for row in whisper_v02_rows}
    shared = sorted(set(manifest) & set(sra) & set(v01) & set(v02))
    wins = Counter()
    row_cer = Counter()
    flagged_sra = 0
    for audio_hash in shared:
        reference = sra[audio_hash]['reference']
        hypotheses = {
            'ARTPARK-IISc/SraVaani-1.0': prediction(sra[audio_hash]),
            'whisper-tiny-garhwali-v0.1': prediction(v01[audio_hash]),
            'whisper-tiny-garhwali-v0.2': prediction(v02[audio_hash]),
        }
        metrics = {model: score(reference, text)['cer'] for model, text in hypotheses.items()}
        best = min(metrics.values())
        for model, cer in metrics.items():
            row_cer[model] += cer
            if cer == best:
                wins[model] += 1
        duration = manifest[audio_hash].get('duration_seconds') or 0
        if candidate_flags(hypotheses['ARTPARK-IISc/SraVaani-1.0'], duration):
            flagged_sra += 1
    return {
        'shared_human_reference_records': len(shared),
        'row_mean_cer': {
            model: round(total / len(shared), 6) if shared else None
            for model, total in sorted(row_cer.items())
        },
        'lowest_row_cer_counts_including_ties': dict(sorted(wins.items())),
        'calibration_records_with_flagged_sravaani_output': flagged_sra,
        'failure_pattern_has_direct_calibration_support': bool(flagged_sra),
    }


def run(
    input_path=INPUT,
    whisper_v01_path=WHISPER_V01,
    output_path=OUTPUT,
    review_path=REVIEW,
    report_path=REPORT,
):
    rows = read_jsonl(input_path)
    targeted = {
        row['audio_sha256']: row
        for row in rows
        if row.get('recovery_confidence')
        and row.get('language_scope_status') != 'source_label_conflict'
    }
    v01_rows = read_jsonl(whisper_v01_path)
    v01 = {row['audio_sha256']: row for row in v01_rows}
    if len(v01) != len(v01_rows):
        raise ValueError('Whisper v0.1 recovery hashes are not unique')
    missing = set(targeted) - set(v01)
    if missing:
        raise ValueError(f'Whisper v0.1 recovery pass is incomplete: {len(missing)} missing')
    frequencies = Counter(row.get('machine_transcript', '') for row in v01_rows)
    adjudicated = [
        build_review_row(row, v01[audio_hash], frequencies[v01[audio_hash].get('machine_transcript', '')])
        for audio_hash, row in targeted.items()
    ]
    adjudicated.sort(key=lambda row: (-row['review_priority'], row['audio_sha256']))
    write_jsonl(output_path, sorted(adjudicated, key=lambda row: row['audio_sha256']))
    write_jsonl(review_path, adjudicated)
    calibration = calibration_summary(
        read_jsonl(CALIBRATION_MANIFEST),
        read_jsonl(SRA_CALIBRATION),
        read_jsonl(WHISPER_V01_CALIBRATION),
        read_jsonl(WHISPER_V02_CALIBRATION),
    )
    report = {
        'run_id': 'sravaani-risky-draft-three-checkpoint-review-v0.1',
        'records': len(adjudicated),
        'unique_audio_hashes': len({row['audio_sha256'] for row in adjudicated}),
        'source_label_conflicts_handled_separately': sum(
            row.get('language_scope_status') == 'source_label_conflict' for row in rows
        ),
        'evidence_status': dict(sorted(Counter(
            row['evidence_status'] for row in adjudicated
        ).items())),
        'proposed_models': dict(sorted(Counter(
            row['proposed_machine_transcript_model'] for row in adjudicated
        ).items())),
        'proposals_with_structural_flags': sum(
            bool(row['proposed_machine_transcript_flags']) for row in adjudicated
        ),
        'automatic_corrections': 0,
        'supervised_training_promotions': 0,
        'recommended_machine_label_training_records': 0,
        'all_originals_preserved': all(row['original_transcript_preserved'] for row in adjudicated),
        'calibration': calibration,
        'evidence_limit': (
            'The two Whisper checkpoints are related, no target record has a human '
            'reference, and the shared calibration set contains no SraVaani output '
            'with this failure pattern. Proposals improve reviewability, not proven accuracy.'
        ),
        'inputs': {
            'confidence_aware_drafts': {
                'path': str(Path(input_path).relative_to(ROOT)),
                'sha256': sha256_file(input_path),
            },
            'whisper_v0.1_recovery': {
                'path': str(Path(whisper_v01_path).relative_to(ROOT)),
                'sha256': sha256_file(whisper_v01_path),
            },
        },
        'output': str(Path(output_path).relative_to(ROOT)),
        'review_queue': str(Path(review_path).relative_to(ROOT)),
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
