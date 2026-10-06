import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_hf_reference_index as indexer
import hf_source_registry as source_registry


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
    assert result["quality_status"] == "automated_quality_assessed_unreviewed"
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
    def test_packaged_quickstart_counts_follow_candidate_manifests(self):
        template = (
            Path(__file__).resolve().parents[1] / "docs/DEVELOPER_QUICKSTART.md"
        ).read_text(encoding="utf-8")
        updated = indexer.sync_quickstart_text(template, {
            "release_id": "garhwali-language-lab-v0.2.2",
            "public_profile_package_rows": 15,
            "content_config_counts": {"lexicon": 7, "text": 8, "text_expansion": 3},
            "tables": {
                "record_index": {"records": 3},
                "source_catalog": {"records": 4},
                "record_sources": {"records": 5},
            },
        })
        self.assertIn("This guide is bundled with `garhwali-language-lab-v0.2.2`", updated)
        self.assertIn("Hub cards link to the latest published revisions", updated)
        self.assertNotIn("7cae908", updated)
        self.assertNotIn("9da266e", updated)
        self.assertIn("| `lexicon` | 7 |", updated)
        self.assertIn("| `text_expansion` | 3 |", updated)
        self.assertIn('"text_expansion", split="train", streaming=True', updated)
        self.assertIn("| `source_catalog` | 4 |", updated)
        self.assertIn("**27 total view rows**", updated)
        self.assertIn("15 content/config rows plus 12 reference rows", updated)
        self.assertEqual(
            indexer.sync_quickstart_text(updated, {
                "release_id": "garhwali-language-lab-v0.2.2",
                "public_profile_package_rows": 15,
                "content_config_counts": {"lexicon": 7, "text": 8, "text_expansion": 3},
                "tables": {
                    "record_index": {"records": 3},
                    "source_catalog": {"records": 4},
                    "record_sources": {"records": 5},
                },
            }),
            updated,
        )

    def test_social_source_locator_requires_matching_file_record_id_and_line(self):
        locators = {
            ("social-garhwali:0001", 1): {
                "source_url": "https://www.reddit.com/r/example/comments/post",
                "source_title": "Example post",
            },
        }
        item = {
            "file": source_registry.SOCIAL_RECORDS_RELATIVE_PATH,
            "record_id": "social-garhwali:0001",
            "line": 1,
        }
        self.assertEqual(
            source_registry.source_record_locator(item, locators),
            locators[("social-garhwali:0001", 1)],
        )
        self.assertEqual(
            source_registry.source_record_locator({**item, "line": 2}, locators),
            {},
        )
        self.assertEqual(
            source_registry.source_record_locator({**item, "file": "other.jsonl"}, locators),
            {},
        )
        self.assertEqual(
            source_registry.source_record_locator(
                {"record_id": "social-garhwali:0001"}, locators
            ),
            locators[("social-garhwali:0001", 1)],
        )
        self.assertEqual(
            source_registry.source_record_locator(
                {"record_id": "unrelated:0001"}, locators
            ),
            {},
        )

    def test_source_objects_resolves_social_seed_item_url(self):
        with patch.object(indexer, "source_record_locator", return_value={
            "source_url": "https://www.reddit.com/r/example/comments/post",
            "source_title": "Example post",
            "source_kind": "social_media_reddit",
        }):
            refs = indexer.source_objects({"provenance": [{
                "source_id": "records",
                "file": "data/extracted/social_garhwali/records.jsonl",
                "line": 1,
                "record_id": "social-garhwali:0001",
            }]})
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["source_url"], "https://www.reddit.com/r/example/comments/post")
        self.assertEqual(refs[0]["source_kind"], "social_media_reddit")

    def test_source_references_keep_snapshot_hashes_and_verified_site_urls(self):
        snapshot = "a" * 64
        source_id = "itihaas-garhwali-capture"
        ref = indexer.source_objects({
            "provenance": [{
                "source_id": source_id,
                "source_snapshot_sha256": snapshot,
            }],
        })[0]
        self.assertEqual(ref["source_snapshot_sha256"], snapshot)
        self.assertEqual(
            ref["source_url"],
            "https://www.itihaas.ai/en/languages/garhwali-language",
        )

    def test_pdf_sidecar_enriches_bibliographic_pointer_without_changing_rights(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "book.json"
            path.write_text(json.dumps({
                "source_id": "sample-pdf",
                "title": "A Garhwali dictionary",
                "author": "Example Author",
                "landing_page": "https://catalog.example.org/book/1",
                "rights_status": "copyright_no_open_license_identified",
            }), encoding="utf-8")
            metadata = indexer.incoming_pdf_source_metadata(Path(directory))

        refs = indexer.source_objects({
            "sources": [{
                "source_id": "sample-pdf",
                "rights_status": "user_supplied_source_rights_unverified",
            }],
        }, incoming_metadata=metadata)
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]["source_title"], "A Garhwali dictionary")
        self.assertEqual(refs[0]["source_url"], "https://catalog.example.org/book/1")
        self.assertEqual(refs[0]["attribution"], "Example Author")
        self.assertEqual(refs[0]["rights_status"], "user_supplied_source_rights_unverified")
        self.assertNotIn("license_id", refs[0])

    def test_verified_lexicon_sources_gain_source_urls_without_license_inference(self):
        source_id = "uttarakhandiwords_animals"
        ref = indexer.source_objects({"sources": [{"source_id": source_id}]})[0]
        self.assertEqual(
            ref["source_url"],
            "https://uttarakhandiwords.blogspot.com/2011/09/blog-post.html",
        )
        self.assertNotIn("license_id", ref)

    def test_official_vaani_sources_are_both_linked_in_the_reference_index(self):
        for source_id in (
            "ARTPARK-IISc/Vaani",
            "ARTPARK-IISc/Vaani-transcription-part",
        ):
            refs = indexer.source_objects({"source": source_id})
            self.assertEqual(len(refs), 1)
            self.assertEqual(refs[0]["source_id"], source_id)
            self.assertEqual(
                refs[0]["source_url"],
                f"https://huggingface.co/datasets/{source_id}",
            )
            self.assertEqual(refs[0]["license_id"], "CC-BY-4.0")

    def test_vaani_test_remainder_reference_has_official_locator_and_rights_evidence(self):
        ref = indexer.source_objects({"provenance": [{
            "source_id": "vaani-official-test-remainder",
            "rights_status": "upstream_vaani_cc_by_4_0",
            "license_id": "CC-BY-4.0",
            "rights_evidence": "https://vaani.iisc.ac.in/dataset/Version1",
            "attribution": "Project VAANI, IISc/ARTPARK",
        }]})[0]

        self.assertEqual(
            ref["source_url"], "https://huggingface.co/datasets/ARTPARK-IISc/Vaani"
        )
        self.assertEqual(ref["rights_status"], "upstream_vaani_cc_by_4_0")
        self.assertEqual(
            ref["rights_evidence"], "https://vaani.iisc.ac.in/dataset/Version1"
        )

    def test_card_describes_complete_reference_layer_once(self):
        with tempfile.TemporaryDirectory() as directory:
            card = Path(directory) / "README.md"
            (Path(directory) / "manifest.json").write_text(
                json.dumps({"release_id": "garhwali-language-lab-v0.2.1"}),
                encoding="utf-8",
            )
            card.write_text(
                "---\nconfigs:\n- config_name: text\n---\n\n"
                "# Garhwali Language Lab\n\n"
                "Release: **garhwali-language-lab-v0.2.1**\n\n"
                "## Linked speech dataset\n",
                encoding="utf-8",
            )
            (Path(directory) / "DEVELOPER_QUICKSTART.md").write_text(
                (
                    Path(__file__).resolve().parents[1]
                    / "docs/DEVELOPER_QUICKSTART.md"
                ).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            report = {
                "release_id": "garhwali-language-lab-v2.2.0",
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
            self.assertIn("Release: **garhwali-language-lab-v0.2.1**", result)
            self.assertNotIn("Release: **garhwali-language-lab-v2.2.0**", result)
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
            quickstart = (Path(directory) / "DEVELOPER_QUICKSTART.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("This guide is bundled with `garhwali-language-lab-v0.2.1`", quickstart)
            self.assertIn("| `source_catalog` | 590 |", quickstart)
