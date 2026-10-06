import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_quality_text_release import build_quality_text_release


def meta_candidate(record_id="meta-1", text="गढ़वाली भाषा का एक वाक्य।"):
    source = {
        "source_id": "meta_omni",
        "source_url": "https://huggingface.co/datasets/facebook/omnilingual-asr-corpus",
        "record_id": record_id,
        "rights_status": "upstream_meta_cc_by_4_0",
        "rights_evidence": "sources/online/meta_omni/card.md.metadata.json",
        "license_id": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": "Meta Omnilingual ASR Corpus contributors",
        "training_eligible": False,
        "quality_flags": [],
    }
    return {
        "id": record_id,
        "text": text,
        "language": "gbm",
        "script": "Deva",
        "source_languages": ["gbm"],
        "language_buckets": ["garhwali_candidate"],
        "quality_tiers": ["strict_gold_candidate"],
        "quality_status": "automated_quality_assessed_unreviewed",
        "quality_flags": [],
        "record_quality_flags": [],
        "split": "train",
        "source_split_overlap_status": "no_upstream_eval_match_detected",
        "recommended_for_training": False,
        "provenance": [source],
        "public_rights_basis": [source],
    }


def base_hf_card():
    return """---
dataset_info: []
---
Release: **garhwali-language-lab-v0.2.7**

The live Hub repository displays **961,533 rows** and **7.56 GB** of files.
This is not a count of unique language examples: **778,157 rows (80.9%)** are
source/reference tables, and the remaining **183,376** are overlapping config
views. Across `text`, `text_expansion`
(1,737 rows), and `text_resources` (475 rows), **zero rows are currently marked
recommended for general text-model training**. The 14,988 `paharili_gbm` rows
remain experimental.

## Configurations and current row counts

| Configuration | Rows | Use |
| --- | ---: | --- |
| `record_sources` | 412,740 | record-to-source join table |
| `source_catalog` | 9,571 | deduplicated source and rights references |

[Developer quick start](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/releases/v0.2.7/DEVELOPER_QUICKSTART.md)
[Dataset schema](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/releases/v0.2.7/DATASET_SCHEMA.md)
[Lexicon script](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/releases/v0.2.7/search_garhwali_lexicon.py)

The current public package has **183,376 rows** across its content configurations;

The content views contain **183,376 overlapping rows** across 15 named content
configurations and 26 content config/split views. With three reference
configurations, the full dataset has 18 named configurations and 29
config/split views. Reuse terms vary by row and configuration.

The figures below describe the current v0.2.7 package, not a cumulative sum of
overlapping views.

This public-profile package contains **183,376 overlapping content-view rows**
across 15 content configs. The three reference-table configs add 778,157
overlapping-view rows, for 18 named configs and 29 config/split views total.

## Developer quick start
"""


class BuildQualityTextReleaseTests(unittest.TestCase):
    def test_builds_matching_nonempty_huggingface_and_kaggle_views(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "data/text").mkdir(parents=True)
            (source / "data/text_expansion").mkdir(parents=True)
            (source / "manifest.json").write_text(
                json.dumps({"release_id": "garhwali-language-lab-v0.2.7"}),
                encoding="utf-8",
            )
            (source / "data/text/train-00000.jsonl").write_text(
                json.dumps(meta_candidate(), ensure_ascii=False) + "\n"
                + json.dumps(meta_candidate("blank", "  "), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            (source / "data/text_expansion/train-00000.jsonl").write_text("", encoding="utf-8")
            hf_output = root / "hf-upload"
            kaggle_output = root / "kaggle"
            base_card_path = root / "base-card.md"
            base_card_path.write_text(base_hf_card(), encoding="utf-8")

            manifest = build_quality_text_release(
                source, hf_output, kaggle_output, base_card_path
            )

            self.assertEqual(manifest["selected_records"], 1)
            self.assertEqual(manifest["training_records"], 1)
            self.assertEqual(manifest["blank_excluded"], 1)
            hf_data = hf_output / "releases/v0.2.8/data/screened_meta_gbm/train-00000.jsonl"
            records = [json.loads(line) for line in hf_data.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0]["recommended_for_training"])
            self.assertFalse(records[0]["native_reviewed"])
            self.assertEqual(records[0]["text"], "गढ़वाली भाषा का एक वाक्य।")
            with (kaggle_output / "train.csv").open(encoding="utf-8", newline="") as stream:
                csv_rows = list(csv.DictReader(stream))
            self.assertEqual(len(csv_rows), 1)
            self.assertEqual(csv_rows[0]["text"], records[0]["text"])
            self.assertEqual(csv_rows[0]["source_record_ids"], '["meta-1"]')
            card = (hf_output / "README.md").read_text(encoding="utf-8")
            self.assertIn("**961,534 rows** and **7.57 GB**", card)
            self.assertIn("| `screened_meta_gbm` | 1 |", card)
            self.assertIn("| `short_utterances_meta_gbm` | 0 |", card)
            self.assertIn("The separate v0.2.8 `screened_meta_gbm` config adds", card)
            self.assertIn("All 1,951 selected text values were found verbatim", card)
            self.assertIn("v0.2.8 adds 1 quality-screened text rows", card)
            self.assertIn("20 named configurations and 31 config/split views", card)
            self.assertIn("releases/v0.2.8/DEVELOPER_QUICKSTART.md", card)
            self.assertNotIn("releases/v0.2.7/DEVELOPER_QUICKSTART.md", card)
            self.assertIn("current v0.2.8 package", card)
            self.assertNotIn("current v0.2.7 package", card)
            self.assertIn("183,377 overlapping content-view rows", card)
            kaggle_metadata = json.loads(
                (kaggle_output / "dataset-metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                kaggle_metadata["id"], "rushilrawat1/garhwali-screened-text-candidates"
            )

    def test_deduplicates_candidate_text_and_documents_exclusion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "data/text").mkdir(parents=True)
            (source / "data/text_expansion").mkdir(parents=True)
            (source / "manifest.json").write_text(
                json.dumps({"release_id": "garhwali-language-lab-v0.2.7"}),
                encoding="utf-8",
            )
            rows = [
                meta_candidate("one"),
                meta_candidate("two", "  गढ़वाली   भाषा का एक वाक्य। "),
            ]
            (source / "data/text/train-00000.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            (source / "data/text_expansion/train-00000.jsonl").write_text("", encoding="utf-8")

            manifest = build_quality_text_release(source, root / "hf", root / "kaggle")
            self.assertEqual(manifest["selected_records"], 1)
            self.assertEqual(manifest["normalized_duplicate_excluded"], 1)
            exclusions = json.loads(
                (hf_output := root / "hf" / "releases/v0.2.8/quality-screened-exclusions.json").read_text(encoding="utf-8")
            )
            self.assertEqual(exclusions["duplicate_text"][0]["excluded_id"], "two")

    def test_short_nonblank_utterance_is_preserved_outside_lm_training_view(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "data/text").mkdir(parents=True)
            (source / "data/text_expansion").mkdir(parents=True)
            (source / "manifest.json").write_text(
                json.dumps({"release_id": "garhwali-language-lab-v0.2.7"}),
                encoding="utf-8",
            )
            rows = [meta_candidate("full"), meta_candidate("short", "अनुभव।")]
            (source / "data/text/train-00000.jsonl").write_text(
                "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                encoding="utf-8",
            )
            (source / "data/text_expansion/train-00000.jsonl").write_text("", encoding="utf-8")
            hf_output, kaggle_output = root / "hf", root / "kaggle"

            manifest = build_quality_text_release(source, hf_output, kaggle_output)

            self.assertEqual(manifest["training_records"], 1)
            self.assertEqual(manifest["short_utterance_records"], 1)
            short_path = hf_output / "releases/v0.2.8/data/short_utterances_meta_gbm/train-00000.jsonl"
            short = json.loads(short_path.read_text(encoding="utf-8"))
            self.assertEqual(short["text"], "अनुभव।")
            self.assertFalse(short["recommended_for_training"])
            with (kaggle_output / "short_utterances.csv").open(encoding="utf-8", newline="") as stream:
                short_csv = list(csv.DictReader(stream))
            self.assertEqual(len(short_csv), 1)
            self.assertEqual(short_csv[0]["recommended_for_training"], "False")


if __name__ == "__main__":
    unittest.main()
