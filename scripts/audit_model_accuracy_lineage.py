"""Audit frozen model-evaluation data lineage without changing corpus rows."""

from __future__ import annotations

import json
import argparse
import hashlib
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Iterable


def read_jsonl(path: str | Path) -> list[dict]:
    """Read JSON objects from JSONL and identify malformed input precisely."""
    path = Path(path)
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"{path}:{line_number}: malformed JSON: {error.msg}"
                ) from error
            if not isinstance(row, dict):
                raise ValueError(
                    f"{path}:{line_number}: expected a JSON object, "
                    f"got {type(row).__name__}"
                )
            rows.append(row)
    return rows


def _row_id(row: dict) -> object:
    for field in (
        "id",
        "row_id",
        "example_id",
        "record_id",
        "utterance_id",
        "row_idx",
        "audio_path",
        "audio",
    ):
        value = row.get(field)
        if value is not None and value != "":
            return value
    return None


def hash_overlap(
    named_rows: dict[str, Iterable[dict]], field: str
) -> list[dict]:
    """Return repeated hash groups in deterministic order without dropping rows.

    Hash strings are trimmed and lowercased. IDs and split labels are retained
    as supplied. Repeats within one split are included as well as cross-split
    repeats so duplicate rows remain visible to the audit.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for split, rows in named_rows.items():
        for row in rows:
            value = row.get(field)
            if not isinstance(value, str):
                continue
            normalized = value.strip().lower()
            if not normalized:
                continue
            grouped[normalized].append({"row_id": _row_id(row), "split": split})

    duplicates = []
    for value, rows in sorted(grouped.items()):
        if len(rows) < 2:
            continue
        rows = sorted(
            rows,
            key=lambda row: (
                str(row["split"]),
                "" if row["row_id"] is None else str(row["row_id"]),
            ),
        )
        duplicates.append(
            {
                "hash": value,
                "rows": rows,
                "splits": sorted({row["split"] for row in rows}),
            }
        )
    return duplicates


SPLIT_MANIFESTS = {
    "asr": {
        split: f"data/processed/model_ready/splits/asr/{split}.jsonl"
        for split in ("train", "validation", "test")
    },
    "asr_expanded_human": {
        split: f"data/processed/model_ready/splits/asr_expanded_human/{split}.jsonl"
        for split in ("train", "validation", "test")
    },
    "asr_experimental": {
        split: f"data/processed/model_ready/splits/asr_experimental/{split}.jsonl"
        for split in ("train", "validation", "test")
    },
    "text_recommended": {
        split: f"data/processed/model_ready/splits/text_recommended/{split}.jsonl"
        for split in ("train", "validation", "test")
    },
    "instructions_v0.2": {
        split: f"data/processed/model_ready/instructions_v0.2/{split}.jsonl"
        for split in ("train", "validation", "test")
    },
    "tts": {
        split: f"data/processed/model_ready/splits/tts/{split}.jsonl"
        for split in ("train", "validation", "test")
    },
    "tts_language_resources": {
        split: f"data/processed/model_ready/language_resources/tts/{split}.jsonl"
        for split in ("train", "validation", "test")
    },
}

SINGLE_MANIFESTS = {
    "meta_omnilingual": {
        "path": "data/huggingface/garhwali-language-lab-speech-2026-09-23/meta_omnilingual-manifest.jsonl",
        "split_field": "split",
        "required_splits": ("train", "validation", "test"),
    },
}

BENCHMARKS = {
    "flores": "benchmarks/indicgenbench_flores.jsonl",
    "xorqa": "benchmarks/indicgenbench_xorqa.jsonl",
    "crosssum": "benchmarks/indicgenbench_crosssum.jsonl",
}

BENCHMARK_SPLITS = {
    "flores": ("dev", "test"),
    "xorqa": ("train", "dev", "test"),
    "crosssum": ("train", "dev", "test"),
}

HASH_FIELDS = (
    "audio_sha256",
    "text_sha256",
    "transcript_sha256",
    "selected_transcript_sha256",
    "asr_target_sha256",
    "instruction_sha256",
    "parent_text_sha256",
    "derived_text_sha256",
)
MANIFEST_HASH_FIELDS = tuple(
    field for field in HASH_FIELDS if field != "derived_text_sha256"
)
TEXT_HASH_FIELDS = (
    "text_sha256",
    "transcript_sha256",
    "selected_transcript_sha256",
    "asr_target_sha256",
    "instruction_sha256",
    "parent_text_sha256",
)
TEXT_FIELDS = (
    "text",
    "asr_target_clean",
    "selected_transcript",
    "asr_target",
    "transcript",
    "canonical_transcript",
    "instruction",
)
UNKNOWN_SPEAKER_IDS = {"", "na", "n/a", "unknown", "none", "null", "unidentified"}
MODEL_LINEAGE_EVIDENCE = {
    "sravaani_1_0": {
        "sources": [
            "https://huggingface.co/ARTPARK-IISc/SraVaani-1.0",
            "https://arxiv.org/abs/2608.08235",
        ],
        "reported_training_data": (
            "The model card reports 31,255 hours of VAANI pretraining and about "
            "31,270 hours of labelled fine-tuning from VAANI plus open-source "
            "speech datasets; its dataset links include Vaani and "
            "Vaani-transcription-part. The paper describes 24 public datasets "
            "for labelled fine-tuning. Neither source provides Garhwali row IDs "
            "or confirms exclusion of this project's fixed splits."
        ),
        "implication": (
            "Exact VAANI test exposure is unknown; absence of a named Meta "
            "Omnilingual source does not prove it was excluded from every "
            "upstream dataset."
        ),
    }
}
ID_FIELDS = ("record_id", "example_id", "row_id", "id")
PATH_FIELDS = ("audio_path", "local_audio_path", "audio_filepath", "audio")
EVALUATION_ROOTS = (
    "data/processed/evaluation/asr",
    "data/processed/evaluation/translation",
    "data/processed/evaluation/retrieval",
    "data/processed/evaluation/controlled_modeling",
)
METADATA_FIELDS = (
    "run_id",
    "model",
    "model_name",
    "model_id",
    "model_path",
    "model_revision",
    "revision",
    "checkpoint",
    "checkpoint_path",
    "checkpoint_sha256",
    "base_checkpoint_sha256",
    "best_checkpoint_sha256",
    "training_manifest_sha256",
    "training_manifest_hashes",
    "train_sha256",
    "validation_sha256",
    "test_sha256",
    "train_records",
    "validation_records",
    "test_records",
    "test_opened_once",
    "test_opened_after_training_and_selection",
    "selection",
    "further_selection_on_test_prohibited",
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _required_rows(root: Path, family: str, split: str, relative_path: str) -> list[dict]:
    path = root / relative_path
    if not path.is_file():
        raise FileNotFoundError(
            f"required manifest missing for {family}/{split}: {relative_path}"
        )
    return read_jsonl(path)


def _path_key(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1].casefold()


def _manifest_record(family: str, split: str, row: dict) -> dict:
    hashes = {
        key: row[key]
        for key in HASH_FIELDS
        if key != "derived_text_sha256"
        and isinstance(row.get(key), str)
        and row[key].strip()
    }
    if not any(key in hashes for key in TEXT_HASH_FIELDS):
        for field in TEXT_FIELDS:
            value = row.get(field)
            if isinstance(value, str) and value.strip():
                normalized = unicodedata.normalize("NFC", value.strip())
                hashes["derived_text_sha256"] = hashlib.sha256(
                    normalized.encode("utf-8")
                ).hexdigest()
                break
    return {
        "family": family,
        "split": split,
        "row_id": _row_id(row),
        "ids": {key: row[key] for key in ID_FIELDS if row.get(key) is not None},
        "hashes": hashes,
        "paths": {
            key: row[key]
            for key in PATH_FIELDS
            if isinstance(row.get(key), str) and row[key].strip()
        },
        "speaker_id": row.get("speaker_id"),
        "split_safe_for_evaluation": row.get("split_safe_for_evaluation"),
        "split_safe_for_training": row.get("split_safe_for_training"),
        "cross_split_audio_overlap": row.get("cross_split_audio_overlap"),
        "transcript_conflict_for_audio": row.get("transcript_conflict_for_audio"),
    }


def _overlap_summary(named_rows: dict[str, list[dict]]) -> dict:
    audited_rows = {}
    for split, rows in named_rows.items():
        split_rows = []
        for row in rows:
            audited = row.copy()
            has_text_hash = any(
                isinstance(audited.get(field), str) and audited[field].strip()
                for field in TEXT_HASH_FIELDS
            )
            if not has_text_hash:
                for field in TEXT_FIELDS:
                    text = audited.get(field)
                    if isinstance(text, str) and text.strip():
                        normalized = unicodedata.normalize("NFC", text.strip())
                        audited["derived_text_sha256"] = hashlib.sha256(
                            normalized.encode("utf-8")
                        ).hexdigest()
                        break
            split_rows.append(audited)
        audited_rows[split] = split_rows
    named_rows = audited_rows
    result = {}
    for field in HASH_FIELDS:
        if not any(field in row for rows in named_rows.values() for row in rows):
            continue
        groups = hash_overlap(named_rows, field)
        cross_split = [group for group in groups if len(group["splits"]) > 1]
        result[field] = {
            "repeated_hash_group_count": len(groups),
            "cross_split_group_count": len(cross_split),
            "cross_split_row_count": sum(len(group["rows"]) for group in cross_split),
            "cross_split_groups": cross_split,
        }

    speakers: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    speaker_display = {}
    unidentified_speakers: dict[str, int] = defaultdict(int)
    for split, rows in named_rows.items():
        for row in rows:
            value = row.get("speaker_id")
            if "speaker_id" not in row:
                continue
            if isinstance(value, str) and value.strip():
                normalized = value.strip().casefold()
                if normalized in UNKNOWN_SPEAKER_IDS:
                    unidentified_speakers[split] += 1
                    continue
                speakers[normalized][split] += 1
                speaker_display.setdefault(normalized, value.strip())
            else:
                unidentified_speakers[split] += 1
    shared_speakers = [
        {"speaker_id": speaker_display[speaker], "rows_by_split": dict(sorted(counts.items()))}
        for speaker, counts in sorted(speakers.items())
        if len(counts) > 1
    ]
    result["speaker_id"] = {
        "cross_split_speaker_count": len(shared_speakers),
        "cross_split_speakers": shared_speakers,
        "unidentified_speaker_rows_by_split": dict(sorted(unidentified_speakers.items())),
    }

    conflicts = {}
    audio_rows: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for split, rows in named_rows.items():
        for row in rows:
            audio_hash = row.get("audio_sha256")
            if isinstance(audio_hash, str) and audio_hash.strip():
                audio_rows[audio_hash.strip().lower()].append((split, row))
    for text_field in (
        "selected_transcript_sha256",
        "asr_target_sha256",
        "transcript_sha256",
        "text_sha256",
        "derived_text_sha256",
    ):
        groups = []
        for audio_hash, rows in sorted(audio_rows.items()):
            text_hashes = {
                row.get(text_field).strip().lower()
                for _, row in rows
                if isinstance(row.get(text_field), str) and row[text_field].strip()
            }
            if len(text_hashes) > 1:
                groups.append(
                    {
                        "audio_sha256": audio_hash,
                        "rows": sorted(
                            [
                                {
                                    "row_id": _row_id(row),
                                    "split": split,
                                    "transcript_sha256": row[text_field],
                                }
                                for split, row in rows
                                if isinstance(row.get(text_field), str)
                            ],
                            key=lambda item: (item["split"], str(item["row_id"])),
                        ),
                    }
                )
        if groups:
            conflicts[text_field] = groups
    result["audio_transcript_conflicts"] = conflicts
    return result


def _file_summary(
    path: Path, rows: list[dict], relative_path: str, split: str | None = None
) -> dict:
    summary = {
        "path": relative_path,
        "sha256": _sha256_file(path),
        "rows": len(rows),
        "missing_hash_counts": {
            field: sum(
                not isinstance(row.get(field), str) or not row[field].strip()
                for row in rows
            )
            for field in MANIFEST_HASH_FIELDS
        },
        "missing_any_text_hash_count": sum(
            not any(
                isinstance(row.get(field), str) and row[field].strip()
                for field in TEXT_HASH_FIELDS
            )
            and not any(
                isinstance(row.get(field), str) and row[field].strip()
                for field in TEXT_FIELDS
            )
            for row in rows
        ),
        "unidentified_speaker_rows": sum(
            "speaker_id" in row
            and (
                not isinstance(row.get("speaker_id"), str)
                or row["speaker_id"].strip().casefold() in UNKNOWN_SPEAKER_IDS
            )
            for row in rows
        ),
    }
    if split is not None:
        summary["split"] = split
    return summary


def _flag_consistency(rows_by_split: dict[str, list[dict]]) -> dict:
    expected = {
        "cross_split_audio_overlap": set(),
        "cross_split_text_overlap": set(),
        "transcript_conflict_for_audio": set(),
    }
    for field, flag in (
        ("audio_sha256", "cross_split_audio_overlap"),
        ("text_sha256", "cross_split_text_overlap"),
        ("derived_text_sha256", "cross_split_text_overlap"),
    ):
        for group in hash_overlap(rows_by_split, field):
            if len(group["splits"]) > 1:
                expected[flag].update(
                    (row["split"], str(row["row_id"])) for row in group["rows"]
                )
    conflict_groups = _overlap_summary(rows_by_split)["audio_transcript_conflicts"]
    for groups in conflict_groups.values():
        for group in groups:
            expected["transcript_conflict_for_audio"].update(
                (row["split"], str(row["row_id"])) for row in group["rows"]
            )

    result = {}
    for flag, computed in expected.items():
        declared_true = 0
        present = 0
        mismatches = []
        for split, rows in rows_by_split.items():
            for row in rows:
                identity = (split, str(_row_id(row)))
                computed_value = identity in computed
                if flag not in row or not isinstance(row[flag], bool):
                    continue
                present += 1
                declared_true += row[flag] is True
                if row[flag] != computed_value:
                    mismatches.append(
                        {
                            "row_id": _row_id(row),
                            "split": split,
                            "declared": row[flag],
                            "computed": computed_value,
                        }
                    )
        result[flag] = {
            "computed_true_rows": len(computed),
            "declared_true_rows": declared_true,
            "rows_with_declared_flag": present,
            "mismatch_count": len(mismatches),
            "mismatches": sorted(
                mismatches, key=lambda item: (item["split"], str(item["row_id"]))
            ),
        }
    return result


def _load_families(root: Path) -> tuple[dict, list[dict]]:
    family_reports = {}
    index_records = []

    for family, split_paths in SPLIT_MANIFESTS.items():
        rows_by_split = {}
        files = []
        for split, relative_path in split_paths.items():
            path = root / relative_path
            rows = _required_rows(root, family, split, relative_path)
            rows_by_split[split] = rows
            files.append(_file_summary(path, rows, relative_path, split))
            index_records.extend(
                _manifest_record(family, split, row) for row in rows
            )
        family_reports[family] = {
            "manifests": files,
            "row_counts": {split: len(rows) for split, rows in rows_by_split.items()},
            "overlaps": _overlap_summary(rows_by_split),
        }

    for family, config in SINGLE_MANIFESTS.items():
        relative_path = config["path"]
        path = root / relative_path
        all_rows = _required_rows(root, family, "all", relative_path)
        rows_by_split = defaultdict(list)
        for row in all_rows:
            split = row.get(config["split_field"])
            if isinstance(split, str) and split:
                rows_by_split[split].append(row)
        for split in config["required_splits"]:
            if split not in rows_by_split:
                raise ValueError(
                    f"required split missing for {family}/{split} in {relative_path}"
                )
        report_rows = {split: rows_by_split[split] for split in sorted(rows_by_split)}
        family_reports[family] = {
            "manifests": [_file_summary(path, all_rows, relative_path)],
            "row_counts": {split: len(rows) for split, rows in report_rows.items()},
            "overlaps": _overlap_summary(report_rows),
            "flag_consistency": _flag_consistency(report_rows),
            "split_safe_counts": {
                split: {
                    field: {
                        "true": sum(row.get(field) is True for row in rows),
                        "false": sum(row.get(field) is False for row in rows),
                        "missing_or_invalid": sum(
                            not isinstance(row.get(field), bool) for row in rows
                        ),
                    }
                    for field in (
                        "split_safe_for_evaluation",
                        "split_safe_for_training",
                    )
                }
                for split, rows in report_rows.items()
            },
            "duplicate_flag_counts": {
                split: {
                    "cross_split_audio_overlap": sum(
                        row.get("cross_split_audio_overlap") is True for row in rows
                    ),
                    "transcript_conflict_for_audio": sum(
                        row.get("transcript_conflict_for_audio") is True for row in rows
                    ),
                    "cross_split_text_overlap": sum(
                        row.get("cross_split_text_overlap") is True for row in rows
                    ),
                }
                for split, rows in report_rows.items()
            },
        }
        for split, rows in report_rows.items():
            index_records.extend(
                _manifest_record(family, split, row) for row in rows
            )

    for name, relative_path in BENCHMARKS.items():
        path = root / relative_path
        rows = _required_rows(root, name, "benchmark", relative_path)
        rows_by_split = defaultdict(list)
        for row in rows:
            split = row.get("split")
            if isinstance(split, str) and split:
                rows_by_split[split].append(row)
        for split in BENCHMARK_SPLITS[name]:
            if split not in rows_by_split:
                raise ValueError(
                    f"required split missing for benchmark {name}/{split} in {relative_path}"
                )
        report_rows = {split: rows_by_split[split] for split in sorted(rows_by_split)}
        family = f"benchmark_{name}"
        family_reports[family] = {
            "manifests": [_file_summary(path, rows, relative_path)],
            "row_counts": {split: len(items) for split, items in report_rows.items()},
            "overlaps": _overlap_summary(report_rows),
        }
        for split, split_rows in report_rows.items():
            index_records.extend(
                _manifest_record(family, split, row) for row in split_rows
            )

    return family_reports, index_records


def _index_records(records: list[dict]) -> tuple[dict, dict, dict]:
    id_index: dict[tuple[str, str], set[int]] = defaultdict(set)
    hash_index: dict[tuple[str, str], set[int]] = defaultdict(set)
    path_index: dict[tuple[str, str], set[int]] = defaultdict(set)
    for index, record in enumerate(records):
        for field, value in record["ids"].items():
            id_index[(field, str(value))].add(index)
        for field, value in record["hashes"].items():
            hash_index[(field, value.strip().lower())].add(index)
        for field, value in record["paths"].items():
            path_key = _path_key(value)
            if path_key:
                path_index[(field, path_key)].add(index)
                path_index[("basename", path_key)].add(index)
                path_stem = path_key.rsplit(".", 1)[0]
                path_index[("audio_hash_stem", path_stem)].add(index)
        audio_hash = record["hashes"].get("audio_sha256")
        if isinstance(audio_hash, str) and audio_hash.strip():
            path_index[("audio_hash_stem", audio_hash.strip().lower())].add(index)
    return id_index, hash_index, path_index


def _cross_role_overlaps(records: list[dict]) -> dict:
    identity_groups = {
        "audio_sha256": ("audio_sha256",),
        "text_sha256": (
            "text_sha256",
            "transcript_sha256",
            "selected_transcript_sha256",
            "asr_target_sha256",
            "parent_text_sha256",
            "derived_text_sha256",
        ),
    }
    result = {}
    for group_name, fields in identity_groups.items():
        grouped: dict[str, dict[str, dict[tuple, set[str]]]] = defaultdict(
            lambda: {"training": defaultdict(set), "evaluation": defaultdict(set)}
        )
        for record in records:
            split = record["split"]
            role = "training" if split == "train" else "evaluation"
            for field in fields:
                value = record["hashes"].get(field)
                if isinstance(value, str) and value.strip():
                    key = (record["family"], split, str(record["row_id"]))
                    grouped[value.strip().lower()][role][key].add(field)
        groups = []
        family_pairs: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        for value, roles in sorted(grouped.items()):
            if not roles["training"] or not roles["evaluation"]:
                continue
            def rows_for(role):
                return [
                    {
                        "family": family,
                        "split": split,
                        "row_id": row_id,
                        "fields": sorted(found_fields),
                    }
                    for (family, split, row_id), found_fields in sorted(
                        roles[role].items()
                    )
                ]

            groups.append(
                {
                    "hash": value,
                    "training_rows": rows_for("training"),
                    "evaluation_rows": rows_for("evaluation"),
                }
            )
            for training in roles["training"]:
                for evaluation in roles["evaluation"]:
                    family_pairs[(training[0], evaluation[0], evaluation[1])].add(value)
        result[group_name] = {
            "group_count": len(groups),
            "groups": groups,
            "family_pairs": [
                {
                    "training_family": train_family,
                    "evaluation_family": eval_family,
                    "evaluation_split": eval_split,
                    "group_count": len(values),
                }
                for (train_family, eval_family, eval_split), values in sorted(
                    family_pairs.items()
                )
            ],
        }

    speakers: dict[str, dict[str, dict[tuple[str, str], int]]] = defaultdict(
        lambda: {"training": defaultdict(int), "evaluation": defaultdict(int)}
    )
    speaker_names = {}
    for record in records:
        value = record["speaker_id"]
        if not isinstance(value, str) or value.strip().casefold() in UNKNOWN_SPEAKER_IDS:
            continue
        normalized = value.strip().casefold()
        role = "training" if record["split"] == "train" else "evaluation"
        speakers[normalized][role][(record["family"], record["split"])] += 1
        speaker_names.setdefault(normalized, value.strip())
    shared = []
    speaker_pairs: dict[tuple[str, str, str], int] = defaultdict(int)
    for speaker, roles in sorted(speakers.items()):
        if not roles["training"] or not roles["evaluation"]:
            continue
        shared.append(
            {
                "speaker_id": speaker_names[speaker],
                "training_rows_by_family_split": {
                    f"{family}/{split}": count
                    for (family, split), count in sorted(roles["training"].items())
                },
                "evaluation_rows_by_family_split": {
                    f"{family}/{split}": count
                    for (family, split), count in sorted(roles["evaluation"].items())
                },
            }
        )
        for training_family, _ in roles["training"]:
            for evaluation_family, evaluation_split in roles["evaluation"]:
                speaker_pairs[(training_family, evaluation_family, evaluation_split)] += 1
    result["speaker_id"] = {
        "group_count": len(shared),
        "groups": shared,
        "family_pairs": [
            {
                "training_family": train_family,
                "evaluation_family": eval_family,
                "evaluation_split": eval_split,
                "group_count": count,
            }
            for (train_family, eval_family, eval_split), count in sorted(
                speaker_pairs.items()
            )
        ],
    }
    return result


def _prediction_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: malformed JSON: {error.msg}") from error
    if isinstance(value, list) and all(isinstance(row, dict) for row in value):
        return value
    if isinstance(value, dict):
        for key in ("predictions", "rows", "results", "examples"):
            if isinstance(value.get(key), list):
                if not all(isinstance(row, dict) for row in value[key]):
                    raise ValueError(f"{path}: {key} must contain JSON objects")
                return value[key]
        return [value]
    raise ValueError(f"{path}: expected a JSON object or array of objects")


def _metadata_values(value: object) -> dict:
    found = {}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in METADATA_FIELDS and item is not None:
                found[key] = item
            elif isinstance(item, (dict, list)):
                child = _metadata_values(item)
                for child_key, child_value in child.items():
                    found.setdefault(child_key, child_value)
    elif isinstance(value, list):
        for item in value:
            for key, child_value in _metadata_values(item).items():
                found.setdefault(key, child_value)
    return found


def _prediction_files(root: Path) -> list[Path]:
    paths = []
    for relative_root in EVALUATION_ROOTS:
        directory = root / relative_root
        if not directory.exists():
            continue
        paths.extend(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and "prediction" in path.name.casefold()
            and path.suffix.casefold() in {".json", ".jsonl"}
        )
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def _match_prediction_row(
    row: dict, records: list[dict], indexes: tuple[dict, dict, dict]
) -> tuple[set[int], set[int]]:
    id_index, hash_index, path_index = indexes
    strong_matches = set()
    for field in ID_FIELDS:
        value = row.get(field)
        if value is not None:
            strong_matches.update(id_index.get((field, str(value)), ()))
    if strong_matches:
        return strong_matches, set()

    audio_hash = row.get("audio_sha256")
    if isinstance(audio_hash, str) and audio_hash.strip():
        strong_matches.update(
            hash_index.get(("audio_sha256", audio_hash.strip().lower()), ())
        )
    if strong_matches:
        return strong_matches, set()

    for field in PATH_FIELDS:
        path_key = _path_key(row.get(field))
        if path_key:
            strong_matches.update(path_index.get((field, path_key), ()))
            strong_matches.update(path_index.get(("basename", path_key), ()))
            strong_matches.update(
                path_index.get(("audio_hash_stem", path_key.rsplit(".", 1)[0]), ())
            )
    if strong_matches:
        return strong_matches, set()

    content_matches = set()
    for field in HASH_FIELDS:
        if field == "audio_sha256":
            continue
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            content_matches.update(
                hash_index.get((field, value.strip().lower()), ())
            )
    if len(content_matches) <= 1:
        return content_matches, set()
    return set(), content_matches


def _compact_record(record: dict) -> dict:
    compact = {
        "row_id": record["row_id"],
        "family": record["family"],
        "split": record["split"],
    }
    if record["ids"]:
        compact["ids"] = record["ids"]
    if record["hashes"]:
        compact["hashes"] = record["hashes"]
    if record["speaker_id"] is not None:
        compact["speaker_id"] = record["speaker_id"]
    for field in (
        "split_safe_for_evaluation",
        "split_safe_for_training",
        "cross_split_audio_overlap",
        "transcript_conflict_for_audio",
    ):
        if record[field] is not None:
            compact[field] = record[field]
    return compact


def _count_candidate_splits(records: list[dict]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for record in records:
        counts[record["family"]][record["split"]] += 1
    return counts


def _row_set_sha256(rows: list[dict]) -> str:
    identities = [
        {
            "family": row.get("family"),
            "split": row.get("split"),
            "row_id": str(row.get("row_id")),
            "hashes": row.get("hashes", {}),
        }
        for row in rows
    ]
    identities.sort(key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    payload = json.dumps(
        identities, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _evaluation_decisions(
    families: dict, records: list[dict], previously_scored: dict
) -> dict:
    """Attach explicit use limits and row-set fingerprints to key evaluations."""
    specs = {
        "vaani_asr_validation": (
            "asr", "validation", False, "development_only",
            "Selection and error analysis only. All 269 rows already have saved predictions; this is not fresh confirmation.",
        ),
        "vaani_asr_test": (
            "asr", "test", False, "development_only",
            "No further tuning or blind-test claim. All 112 rows have saved predictions, and SraVaani's exact VAANI exposure is unspecified upstream.",
        ),
        "meta_omnilingual_validation": (
            "meta_omnilingual", "validation", True, "development_only",
            "Use the internally safe rows for development selection/error analysis only. Upstream checkpoint exposure is unknown, so results cannot establish independent generalization.",
        ),
        "meta_omnilingual_test": (
            "meta_omnilingual", "test", True, "unresolved",
            "Do not use as a final held-out claim until upstream checkpoint pretraining/fine-tuning overlap is resolved. The internal safety flags only address duplicates within this Meta manifest.",
        ),
        "instructions_test": (
            "instructions_v0.2", "test", False, "development_only",
            "134 of 260 current rows match saved test predictions. Another 126 lack a match, which is not proof they were unseen; an older mT0 test sidecar has a different split membership.",
        ),
        "flores_test": (
            "benchmark_flores", "test", False, "development_only",
            "All 1,012 rows have saved translation predictions; this set is already examined.",
        ),
        "xorqa_dev": (
            "benchmark_xorqa", "dev", False, "development_only",
            "All 500 rows have saved retrieval predictions; use only as historical development evidence.",
        ),
        "xorqa_test": (
            "benchmark_xorqa", "test", False, "development_only",
            "All 539 rows have saved retrieval predictions; this set is already examined.",
        ),
        "crosssum_test": (
            "benchmark_crosssum", "test", False, "unresolved",
            "No local prediction match was found, but upstream model pretraining overlap has not been established; do not call it blind.",
        ),
        "text_recommended_test": (
            "text_recommended", "test", False, "unresolved",
            "No local prediction match was found, but base-checkpoint pretraining exposure is unknown. Cross-view exact-text overlaps also require the workstream to use this family in isolation.",
        ),
    }
    result = {}
    for name, (family, split, require_safe_flag, status, reason) in specs.items():
        family_rows = [
            row for row in records
            if row["family"] == family and row["split"] == split
        ]
        selected = [
            row for row in family_rows
            if not require_safe_flag or row["split_safe_for_evaluation"] is True
        ]
        seen = previously_scored.get(family, {}).get(split, [])
        manifests = families[family]["manifests"]
        manifest = next(
            (item for item in manifests if item.get("split") == split),
            manifests[0],
        )
        result[name] = {
            "family": family,
            "split": split,
            "status": status,
            "permitted_use": (
                "development_selection_and_error_analysis_only"
                if split in {"validation", "dev"}
                else "historical_or_unresolved_only; no blind-test claim"
            ),
            "manifest_sha256": manifest["sha256"],
            "manifest_row_count": len(family_rows),
            "selected_row_count": len(selected),
            "excluded_by_internal_evaluation_safety_flag": len(family_rows) - len(selected),
            "row_set_sha256": _row_set_sha256(selected),
            "previously_scored_row_count": len(seen),
            "previously_scored_row_set_sha256": _row_set_sha256(seen),
            "eligible_for_heldout_claim": False,
            "reason": reason,
        }
    return result


def _prediction_report(root: Path, path: Path, records: list[dict], indexes: tuple) -> dict:
    rows = _prediction_rows(path)
    matched = set()
    matched_prediction_rows = 0
    unmatched = []
    ambiguous_prediction_rows = 0
    ambiguous_examples = []
    matched_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    matched_eval_rows: dict[int, dict] = {}
    for row_number, row in enumerate(rows, start=1):
        matches, ambiguous = _match_prediction_row(row, records, indexes)
        if not matches:
            identity = next(
                (row.get(field) for field in (*ID_FIELDS, *HASH_FIELDS, *PATH_FIELDS) if row.get(field) is not None),
                None,
            )
            if ambiguous:
                ambiguous_prediction_rows += 1
                if len(ambiguous_examples) < 10:
                    candidates = [records[index] for index in sorted(ambiguous)]
                    ambiguous_examples.append(
                        {
                            "row_number": row_number,
                            "identity": identity,
                            "candidate_row_count": len(candidates),
                            "candidate_splits": {
                                family: dict(sorted(counts.items()))
                                for family, counts in sorted(
                                    _count_candidate_splits(candidates).items()
                                )
                            },
                        }
                    )
            elif len(unmatched) < 10:
                unmatched.append({"row_number": row_number, "identity": identity})
            continue
        matched_prediction_rows += 1
        for index in sorted(matches):
            record = records[index]
            matched.add(index)
            if record["split"] in {"validation", "dev", "test"}:
                matched_eval_rows[index] = _compact_record(record)

    for index in sorted(matched):
        record = records[index]
        matched_counts[record["family"]][record["split"]] += 1

    metadata = {}
    for candidate in (path.parent / "report.json", path.parent.parent / "report.json"):
        if candidate.is_file():
            try:
                metadata.update(_metadata_values(json.loads(candidate.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, OSError):
                metadata["report_sidecar_read_error"] = candidate.relative_to(root).as_posix()
    for row in rows:
        metadata.update({k: v for k, v in _metadata_values(row).items() if k not in metadata})

    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": _sha256_file(path),
        "rows": len(rows),
        "model_metadata": metadata,
        "training_data_lineage": "unknown",
        "upstream_pretraining_overlap": "unknown",
        "matched_split_counts": {
            family: dict(sorted(splits.items()))
            for family, splits in sorted(matched_counts.items())
        },
        "matched_evaluation_row_count": len(matched_eval_rows),
        "matched_test_rows": {
            family: [
                record
                for index, record in sorted(matched_eval_rows.items())
                if records[index]["family"] == family and records[index]["split"] == "test"
            ]
            for family in sorted(
                {
                    records[index]["family"]
                    for index in matched_eval_rows
                    if records[index]["split"] == "test"
                }
            )
        },
        "matched_validation_or_dev_rows": {
            family: [
                record
                for index, record in sorted(matched_eval_rows.items())
                if records[index]["family"] == family
                and records[index]["split"] in {"validation", "dev"}
            ]
            for family in sorted(
                {
                    records[index]["family"]
                    for index in matched_eval_rows
                    if records[index]["split"] in {"validation", "dev"}
                }
            )
        },
        "matched_prediction_row_count": matched_prediction_rows,
        "ambiguous_prediction_row_count": ambiguous_prediction_rows,
        "ambiguous_examples": ambiguous_examples,
        "unmatched_prediction_row_count": len(rows)
        - matched_prediction_rows
        - ambiguous_prediction_rows,
        "unmatched_examples": unmatched,
    }


def build_report(project_root: str | Path) -> dict:
    """Build the deterministic split and prior-evaluation lineage inventory."""
    root = Path(project_root).resolve()
    families, records = _load_families(root)
    indexes = _index_records(records)
    predictions = [
        _prediction_report(root, path, records, indexes)
        for path in _prediction_files(root)
    ]
    previously_scored = defaultdict(lambda: defaultdict(dict))
    for prediction in predictions:
        for groups in (
            prediction["matched_test_rows"],
            prediction["matched_validation_or_dev_rows"],
        ):
            for family, rows in groups.items():
                for row in rows:
                    split = row["split"]
                    row_key = json.dumps(row, sort_keys=True, ensure_ascii=False)
                    previously_scored[family][split][row_key] = row
    previously_scored_rows = {
        family: {
            split: [rows[row_key] for row_key in sorted(rows)]
            for split, rows in sorted(splits.items())
        }
        for family, splits in sorted(previously_scored.items())
    }
    return {
        "schema_version": 1,
        "audit": "model accuracy split and evaluation lineage",
        "manifest_families": families,
        "cross_role_overlaps": _cross_role_overlaps(records),
        "predictions": predictions,
        "previously_scored_rows": previously_scored_rows,
        "evaluation_decisions": _evaluation_decisions(
            families, records, previously_scored_rows
        ),
        "model_lineage_evidence": MODEL_LINEAGE_EVIDENCE,
        "lineage_limits": {
            "training_data_lineage": "unknown unless recorded in a saved artifact sidecar",
            "upstream_pretraining_overlap": "unknown unless independently verified",
            "test_policy": "Any test rows found in saved predictions are previously inspected; do not call them blind.",
        },
    }


def render_json(report: dict) -> str:
    return json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def render_markdown(report: dict) -> str:
    lines = [
        "# Model accuracy split and evaluation lineage audit",
        "",
        "This deterministic audit inventories frozen input manifests and saved prediction files. It does not modify corpus rows or model artifacts.",
        "",
        "Model training lineage and upstream pretraining overlap are recorded as unknown unless an artifact records them. Any matched validation, development, or test rows have prior evaluation evidence; test rows must not be described as blind.",
        "",
        "## Frozen manifests",
        "",
        "| Family | Split | Rows | Manifest SHA-256 | Missing audio hashes | Missing text hashes |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for family, summary in sorted(report["manifest_families"].items()):
        for manifest in summary["manifests"]:
            split = manifest.get("split")
            if split is None:
                split = ", ".join(
                    f"{name}={count}"
                    for name, count in sorted(summary["row_counts"].items())
                )
            lines.append(
                f"| {family} | {split} | {manifest['rows']} | `{manifest['sha256']}` | "
                f"{manifest['missing_hash_counts'].get('audio_sha256', 0)} | "
                f"{manifest['missing_any_text_hash_count']} |"
            )
    lines.extend(["", "## Split overlap findings", ""])
    for family, summary in sorted(report["manifest_families"].items()):
        overlaps = summary["overlaps"]
        cross = {
            field: detail["cross_split_group_count"]
            for field, detail in overlaps.items()
            if isinstance(detail, dict) and "cross_split_group_count" in detail
        }
        unidentified = sum(
            overlaps.get("speaker_id", {})
            .get("unidentified_speaker_rows_by_split", {})
            .values()
        )
        if (
            any(cross.values())
            or overlaps.get("speaker_id", {}).get("cross_split_speaker_count", 0)
            or unidentified
        ):
            lines.append(f"### {family}")
            lines.append("")
            for field, count in cross.items():
                if count:
                    lines.append(f"- `{field}`: {count} cross-split duplicate groups")
            speaker_count = overlaps.get("speaker_id", {}).get("cross_split_speaker_count", 0)
            if speaker_count:
                lines.append(f"- `speaker_id`: {speaker_count} speakers appear in multiple splits")
            if unidentified:
                lines.append(f"- `speaker_id`: {unidentified} rows have no usable speaker ID")
            conflicts = overlaps.get("audio_transcript_conflicts", {})
            if conflicts:
                lines.append(
                    "- Same-audio conflicting transcript hashes: "
                    + ", ".join(f"{field}={len(groups)}" for field, groups in sorted(conflicts.items()))
                )
            lines.append("")
    if not any(
        summary["overlaps"].get("speaker_id", {}).get("cross_split_speaker_count", 0)
        or any(summary["overlaps"].get("audio_transcript_conflicts", {}).values())
        or any(
            value.get("cross_split_group_count", 0)
            for value in summary["overlaps"].values()
            if isinstance(value, dict)
        )
        for summary in report["manifest_families"].values()
    ):
        lines.extend(["No cross-split hash or speaker overlaps were detected.", ""])
    lines.extend(
        [
            "## Training-to-evaluation overlap between views",
            "",
            "| Training view | Evaluation view | Audio hashes | Exact text hashes | Speakers |",
            "|---|---|---:|---:|---:|",
        ]
    )
    pair_counts = defaultdict(dict)
    for field, summary in report.get("cross_role_overlaps", {}).items():
        for pair in summary.get("family_pairs", []):
            key = (
                pair["training_family"],
                pair["evaluation_family"],
                pair["evaluation_split"],
            )
            pair_counts[key][field] = pair["group_count"]
    for (train_family, eval_family, split), counts in sorted(pair_counts.items()):
        lines.append(
            f"| {train_family} | {eval_family}/{split} | "
            f"{counts.get('audio_sha256', 0)} | {counts.get('text_sha256', 0)} | "
            f"{counts.get('speaker_id', 0)} |"
        )
    if not pair_counts:
        lines.append("| None detected | — | 0 | 0 | 0 |")
    lines.extend([
        "Exact row references and hashes are in the local-only JSON ledger, which contains VAANI speaker identifiers and is excluded from Git and public packages.",
        "",
    ])
    lines.extend(
        [
            "## Evaluation use decisions",
            "",
            "No current split is approved as an independent held-out confirmation. A row-set fingerprint identifies each exact subset; its manifest SHA-256 and any previously scored row IDs/hashes are in the local-only JSON ledger, which contains VAANI speaker identifiers and is excluded from Git and public packages.",
            "",
            "| Evaluation | Status | Selected rows | Previously scored | Permitted use |",
            "|---|---|---:|---:|---|",
        ]
    )
    for name, decision in sorted(report.get("evaluation_decisions", {}).items()):
        lines.append(
            f"| {name} | {decision['status']} | {decision['selected_row_count']} / "
            f"{decision['manifest_row_count']} | {decision['previously_scored_row_count']} | "
            f"{decision['permitted_use']} |"
        )
        lines.append(f"\n- **{name}:** {decision['reason']}")
    lines.append("")
    for name, evidence in sorted(report.get("model_lineage_evidence", {}).items()):
        lines.extend(
            [
                f"### Upstream evidence: {name}",
                "",
                evidence["reported_training_data"],
                "",
                evidence["implication"],
                "",
                "Sources: " + ", ".join(f"[{url}]({url})" for url in evidence["sources"]),
                "",
            ]
        )
    meta = report["manifest_families"].get("meta_omnilingual")
    if meta:
        lines.extend(
            [
                "## Meta split-safety flags",
                "",
                "| Split | Safety flag | True | False | Missing/invalid |",
                "|---|---|---:|---:|---:|",
            ]
        )
        for split, flags in sorted(meta["split_safe_counts"].items()):
            for field, counts in sorted(flags.items()):
                lines.append(
                    f"| {split} | `{field}` | {counts['true']} | {counts['false']} | "
                    f"{counts['missing_or_invalid']} |"
                )
        lines.extend(
            [
                "",
                "| Duplicate flag | Computed rows | Declared true rows | Mismatches |",
                "|---|---:|---:|---:|",
            ]
        )
        for flag, check in sorted(meta["flag_consistency"].items()):
            lines.append(
                f"| `{flag}` | {check['computed_true_rows']} | "
                f"{check['declared_true_rows']} | {check['mismatch_count']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Previously saved prediction outputs",
            "",
            "| File | Rows | SHA-256 | Matched split rows | Matched validation/dev rows | Matched test rows | Ambiguous rows | Unmatched rows |",
            "|---|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for item in report["predictions"]:
        split_counts = "; ".join(
            f"{family}:" + ", ".join(f"{split}={count}" for split, count in splits.items())
            for family, splits in item["matched_split_counts"].items()
        ) or "unmatched"
        test_rows = sum(len(rows) for rows in item["matched_test_rows"].values())
        lines.append(
            f"| `{item['path']}` | {item['rows']} | `{item['sha256']}` | {split_counts} | "
            f"{item['matched_evaluation_row_count'] - test_rows} | {test_rows} | "
            f"{item['ambiguous_prediction_row_count']} | "
            f"{item['unmatched_prediction_row_count']} |"
        )
    lines.extend(["", "## Exact previously scored rows", ""])
    for family, splits in sorted(report["previously_scored_rows"].items()):
        counts = ", ".join(f"{split}={len(rows)}" for split, rows in sorted(splits.items()))
        lines.append(f"- **{family}:** {counts}. Exact row IDs and hashes are in the local-only JSON ledger.")
    if not report["previously_scored_rows"]:
        lines.append("- No prediction rows matched the configured manifests.")
    lines.extend(
        [
            "",
            "## Provenance limits",
            "",
            "Prediction files and manifests include local SHA-256 digests. Content-hash matches that identify multiple manifest rows are marked ambiguous and do not assign a split. Unmatched rows may come from corpus candidates or inputs outside the configured fixed splits; they are not automatically leakage. Model training data lineage and upstream pretraining overlap remain unknown unless recorded in a saved artifact. Exact matches establish that a row was evaluated before; an absent match is not proof that a test row was never viewed or used elsewhere.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("research/model-accuracy-lineage-2026-09-24"),
    )
    args = parser.parse_args()
    report = build_report(args.project_root)
    prefix = args.output_prefix
    if not prefix.is_absolute():
        prefix = args.project_root / prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix(".json").write_text(render_json(report), encoding="utf-8")
    prefix.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote {prefix.with_suffix('.json')}")
    print(f"Wrote {prefix.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
