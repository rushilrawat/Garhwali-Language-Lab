"""Write consistent, hash-linked artifacts for a completed evaluation run."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def config_sha256(config):
    return hashlib.sha256(_canonical_json(config).encode('utf-8')).hexdigest()


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _git_state(git_root):
    if git_root is None:
        return {'commit': None, 'worktree_dirty': None}
    root = Path(git_root)
    commit = subprocess.run(
        ['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, check=False,
    )
    status = subprocess.run(
        ['git', 'status', '--porcelain'], cwd=root, capture_output=True, text=True, check=False,
    )
    return {
        'commit': commit.stdout.strip() if commit.returncode == 0 else None,
        'worktree_dirty': bool(status.stdout.strip()) if status.returncode == 0 else None,
    }


def _json_bytes(value, *, indent=None):
    return (json.dumps(value, ensure_ascii=False, indent=indent, sort_keys=True) + '\n').encode('utf-8')


def write_run_artifacts(
    output_dir,
    predictions,
    report,
    *,
    config,
    model=None,
    runtime=None,
    device=None,
    seed=None,
    code_paths=(),
    git_root=None,
    started_at_utc=None,
):
    """Write predictions, aggregate report, and their provenance manifest."""
    predictions = list(predictions)
    expected_count = report.get('evaluation_records')
    if expected_count is not None and expected_count != len(predictions):
        raise ValueError('prediction count does not match report evaluation_records')

    prediction_ids = [row.get('record_id') for row in predictions]
    selected_ids = report.get('selected_record_ids')
    checked_ids = selected_ids if selected_ids is not None else prediction_ids
    if len(checked_ids) != len(set(checked_ids)):
        raise ValueError('duplicate record_id values in evaluation predictions')
    if selected_ids is not None and selected_ids != prediction_ids:
        raise ValueError('prediction record IDs do not match report selected_record_ids')

    prediction_bytes = b''.join(_json_bytes(row) for row in predictions)
    report_bytes = _json_bytes(report, indent=2)
    code_hashes = {
        Path(path).name: _sha256_bytes(Path(path).read_bytes())
        for path in code_paths
    }
    completed_at_utc = utc_now()
    manifest = {
        'schema_version': 1,
        'run_id': report.get('run_id'),
        'status': 'complete',
        'timestamps_utc': {
            'started': started_at_utc or completed_at_utc,
            'completed': completed_at_utc,
        },
        'evaluation_split': report.get('evaluation_split'),
        'benchmark_input_sha256': report.get('input_sha256'),
        'selected_rows_sha256': report.get('selected_rows_sha256'),
        'selected_record_count': len(predictions),
        'selected_record_ids': prediction_ids,
        'config': config,
        'config_sha256': config_sha256(config),
        'model': model,
        'runtime': runtime or {},
        'device': device,
        'seed': seed,
        'code': {
            **_git_state(git_root),
            'files_sha256': code_hashes,
        },
        'outputs': {
            'predictions.jsonl': _sha256_bytes(prediction_bytes),
            'report.json': _sha256_bytes(report_bytes),
        },
    }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'predictions.jsonl').write_bytes(prediction_bytes)
    (output_dir / 'report.json').write_bytes(report_bytes)
    (output_dir / 'run_manifest.json').write_bytes(_json_bytes(manifest, indent=2))
    return manifest
