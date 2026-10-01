import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_hf_reference_index as indexer


def test_index_row_references_source_and_excludes_record_payloads():
    row = {
        "text": "PRIVATE_CORPUS_TEXT",
        "text_sha256": "PRIVATE_TEXT_HASH",
        "transcript": "PRIVATE_TRANSCRIPT",
        "audio_sha256": "PRIVATE_AUDIO_HASH",
        "speaker_id": "PRIVATE_SPEAKER_ID",
        "language": "gbm",
        "provenance": [{
            "source_id": "sample-source",
            "source_url": "https://example.org/item",
            "license_id": "CC-BY-4.0",
            "rights_status": "rights_pending",
            "file": "restricted/local.jsonl",
        }],
        "quality_flags": ["needs_review"],
    }

    source_ref = indexer.source_objects(row)[0]
    source_id = indexer.source_reference_id(source_ref)
    result = indexer.make_record_row("text", "train", "train-00000", 1, row, {}, [source_id])
    serialized = json.dumps(result)

    assert result["record_family"] == "text"
    assert result["record_rights_status"] == "not_recorded"
    assert result["rights_status"] == "resolve_via_record_and_source_join"
    assert result["quality_status"] == "automated_flags_present; not linguistically reviewed"
    assert isinstance(result["license_labels"], list)
    assert source_id in result["source_ref_ids_json"]
    assert "https://example.org/item" not in serialized
    assert "PRIVATE_" not in serialized
    assert "restricted/local.jsonl" not in serialized
    assert not indexer.FORBIDDEN_OUTPUT_KEYS.intersection(result)


def test_catalog_public_availability_respects_redaction_flag():
    row = {"id": "stable-key", "text": "not copied", "language_bucket": "gbm"}

    included = indexer.make_record_row(
        "catalog", "train", "train-00000", 1, row,
        {"catalog": {"stable-key": True}}, [],
    )
    redacted = indexer.make_record_row(
        "catalog", "train", "train-00000", 2, row,
        {"catalog": {"stable-key": False}}, [],
    )

    assert included["public_profile_content_available"] is True
    assert redacted["public_profile_content_available"] is False
    assert "not copied" not in json.dumps(included)


class ReferenceIndexCardTests(unittest.TestCase):
    def test_card_describes_complete_reference_layer_once(self):
        with tempfile.TemporaryDirectory() as directory:
            card = Path(directory) / "README.md"
            card.write_text(
                "---\nconfigs:\n- config_name: text\n---\n\n"
                "# Garhwali Language Lab\n\nRelease: **test**\n\n"
                "## Linked speech dataset\n",
                encoding="utf-8",
            )
            report = {
                "release_id": "test",
                "records": 257807,
                "source_catalog_records": 590,
                "record_source_links": 277637,
                "public_profile_package_rows": 146684,
                "records_with_content_in_public_profile": 122118,
                "record_rights_status_counts": {"not_recorded": 228836},
                "content_config_counts": {"text": 120, "lexicon": 7},
                "public_content_config_count": 6,
                "public_content_config_split_views": 12,
                "tables": {
                    "record_index": {"records": 257807},
                    "source_catalog": {"records": 590},
                    "record_sources": {"records": 277637},
                },
            }
            with patch.object(indexer, "PUBLIC_DATA", Path(directory)):
                indexer.update_dataset_card(report)
                indexer.update_dataset_card(report)

            result = card.read_text(encoding="utf-8")
            self.assertEqual(result.count("## What this repository provides"), 1)
            self.assertIn("257,807 rows", result)
            self.assertIn("590 deduplicated source records", result)
            self.assertIn("277,637 record-to-source links", result)
            self.assertIn("not_recorded` for **228,836 rows**", result)
            self.assertIn("## Developer quick start", result)
            self.assertEqual(result.count("## Developer quick start"), 1)
            self.assertIn("`text` | 120", result)
            self.assertIn("`record_index` | 257,807", result)
            self.assertIn("speaker identifiers, local paths, or content hashes", result)
