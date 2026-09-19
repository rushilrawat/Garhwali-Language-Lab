#!/usr/bin/env python3
"""Independent full-package validation for the Hugging Face all-data export."""

import argparse
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def script_profile(text):
    counts = Counter()
    for char in str(text or ""):
        code = ord(char)
        if 0x0900 <= code <= 0x097F:
            counts["Deva"] += 1
        elif 0x0980 <= code <= 0x09FF:
            counts["Beng"] += 1
        elif char.isascii() and char.isalpha():
            counts["Latn"] += 1
        elif char.isalpha():
            counts[unicodedata.name(char, "OTHER").split()[0]] += 1
    return counts.most_common(1)[0][0] if counts else "none"


def identity(config, row):
    if config == "asr" or config == "sravaani_drafts":
        return row.get("audio_sha256")
    if config == "instructions":
        return row.get("instruction_sha256")
    return row.get("id") or row.get("text_sha256") or row.get("record_id")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((args.package / "manifest.json").read_text())
    errors = []
    configs = {}
    split_ids = defaultdict(lambda: defaultdict(set))
    global_stats = Counter()
    source_ids = Counter()
    instruction_prompts = defaultdict(lambda: defaultdict(set))
    file_hashes = []
    for key, expected in sorted(manifest["configs"].items()):
        config, split = key.split("/", 1)
        seen = set()
        stats = Counter()
        scripts = Counter()
        for filename in expected["files"]:
            path = args.package / "data" / config / filename
            if not path.exists():
                errors.append(f"missing_file:{config}/{filename}")
                continue
            file_hashes.append({"path": str(path.relative_to(args.package)), "sha256": sha256(path)})
            with path.open(encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, 1):
                    try:
                        row = json.loads(line)
                    except Exception as exc:
                        errors.append(f"invalid_json:{config}/{filename}:{line_number}:{exc}")
                        continue
                    stats["records"] += 1
                    rid = identity(config, row)
                    if not rid:
                        stats["missing_identity"] += 1
                    elif rid in seen:
                        stats["duplicate_identity"] += 1
                    else:
                        seen.add(rid)
                        split_ids[config][split].add(rid)
                    text = row.get("text") if "text" in row else row.get("transcript")
                    if text is not None:
                        stats["empty_content"] += int(not str(text).strip())
                        scripts[script_profile(text)] += 1
                    provenance = row.get("provenance") or row.get("sources") or []
                    stats["rows_with_provenance"] += int(bool(provenance))
                    stats["rows_with_quality_metadata"] += int(any(
                        key_name in row for key_name in (
                            "quality_flags", "machine_transcript_quality", "quality_v2",
                            "language_quality", "surface_quality"
                        )
                    ))
                    for item in provenance:
                        source = item.get("source_id")
                        if source:
                            source_ids[source] += 1
                    if config == 'text':
                        source_languages = set(row.get('source_languages') or [])
                        if row.get('language') == 'gbm' and source_languages & {'eng', 'hin', 'mul'}:
                            stats['unsupported_garhwali_label'] += 1
                        if any(
                            field not in row for field in (
                                'language_buckets', 'quality_tiers',
                                'recommended_for_training',
                            )
                        ):
                            stats['missing_admission_metadata'] += 1
                    elif config == 'instructions':
                        prompt = ' '.join(
                            str(row.get('instruction') or '').casefold().split()
                        )
                        instruction_prompts[config][split].add(prompt)
                        if not row.get('acceptable_responses'):
                            stats['missing_acceptable_responses'] += 1
        if stats["records"] != expected["records"]:
            errors.append(f"record_count:{key}:{stats['records']}!={expected['records']}")
        if stats["missing_identity"]:
            errors.append(f"missing_identity:{key}:{stats['missing_identity']}")
        if stats['duplicate_identity']:
            errors.append(f"duplicate_identity:{key}:{stats['duplicate_identity']}")
        for field in (
            'unsupported_garhwali_label', 'missing_admission_metadata',
            'missing_acceptable_responses',
        ):
            if stats[field]:
                errors.append(f'{field}:{key}:{stats[field]}')
        configs[key] = {**dict(stats), "scripts": dict(sorted(scripts.items()))}
        global_stats.update(stats)

    leakage = {}
    for config, splits in split_ids.items():
        names = sorted(splits)
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                count = len(splits[left] & splits[right])
                leakage[f"{config}:{left}:{right}"] = count
                if count:
                    errors.append(f"cross_split_identity:{config}:{left}:{right}:{count}")
    for config, splits in instruction_prompts.items():
        names = sorted(splits)
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                count = len(splits[left] & splits[right])
                leakage[f'{config}_prompt:{left}:{right}'] = count
                if count:
                    errors.append(
                        f'cross_split_instruction_prompt:{left}:{right}:{count}'
                    )

    expected_files = {
        'README.md', 'manifest.json', 'LICENSE_POLICY.md',
        'ATTRIBUTION.md', 'REMOVAL_POLICY.md',
    }
    for key, config in manifest['configs'].items():
        group, _ = key.split('/', 1)
        expected_files.update(
            f'data/{group}/{filename}' for filename in config.get('files', [])
        )
    actual_files = {
        path.relative_to(args.package).as_posix()
        for path in args.package.rglob('*') if path.is_file() or path.is_symlink()
    }
    for path in sorted(actual_files - expected_files):
        if not (manifest.get('include_audio') and path.startswith('audio/')):
            errors.append(f'unexpected_file:{path}')
    for path in sorted(path for path in args.package.rglob('*') if path.is_symlink()):
        errors.append(f'symlink:{path.relative_to(args.package).as_posix()}')

    report = {
        "run_id": "garhwali-hf-all-data-cloud-validation-v0.1",
        "release_id": manifest["release_id"],
        "status": "passed" if not errors else "failed",
        "manifest_profile": manifest["profile"],
        "configs": configs,
        "totals": dict(global_stats),
        "cross_split_identity_overlap": leakage,
        "distinct_provenance_sources": len(source_ids),
        "top_provenance_sources": source_ids.most_common(50),
        "file_hashes": file_hashes,
        "errors": errors,
        "records_deleted_or_mutated": 0,
    }
    output_path = (
        args.output if args.output.suffix == '.json' else args.output / 'report.json'
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
