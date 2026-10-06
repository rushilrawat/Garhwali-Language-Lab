import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.prepare_hf_additive_upload import (
    RELEASE_VERSION,
    preflight_candidate,
    prepare,
    validate_package,
    version_card,
)


class AdditiveHuggingFaceUploadTests(unittest.TestCase):
    def test_default_release_version_targets_next_additive_candidate(self):
        self.assertEqual(RELEASE_VERSION, "0.2.8")

    def make_package(self, root: Path) -> Path:
        package = root / "package"
        (package / "data/catalog").mkdir(parents=True)
        content = '{"text":"गढ़वाली"}\n'
        payload = (package / "data/catalog/train-00000.jsonl")
        payload.write_text(content, encoding="utf-8")
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        (package / "README.md").write_text(
            "---\nconfigs:\n- config_name: catalog\n  data_files:\n  - split: train\n    path: data/catalog/train-*.jsonl\n---\n"
            "[Reference index](reference_index_manifest.json)\n",
            encoding="utf-8",
        )
        for name in ("ATTRIBUTION.md", "LICENSE_POLICY.md", "REMOVAL_POLICY.md"):
            (package / name).write_text("policy\n", encoding="utf-8")
        (package / "DEVELOPER_QUICKSTART.md").write_text("quick start\n", encoding="utf-8")
        (package / "DATASET_SCHEMA.md").write_text("schema\n", encoding="utf-8")
        (package / "search_garhwali_lexicon.py").write_text("print('search')\n", encoding="utf-8")
        (package / "research").mkdir()
        (package / "research/text-rights-resolution-2026-09-30.md").write_text(
            "rights decisions\n", encoding="utf-8"
        )
        reference = package / "reference_index_manifest.json"
        reference.write_text(json.dumps({
            "profile": "metadata_only_complete_reference_index", "tables": {},
        }), encoding="utf-8")
        (package / "manifest.json").write_text(json.dumps({
            "profile": "public", "release_id": "garhwali-language-lab-v0.2.0",
            "record_schema_version": "1.0.0",
            "include_audio": False, "linked_audio_files": 0,
            "removed_audio_files": 0,
            "configs": {"catalog/train": {
                "records": 1,
                "files": ["train-00000.jsonl"],
                "file_sha256": {"train-00000.jsonl": digest},
            }},
        }), encoding="utf-8")
        return package

    def test_card_paths_move_under_version_prefix(self):
        card = (
            "path: data/text/train-*.jsonl\n"
            "[rights report](research/text-rights-resolution-2026-09-30.md)\n"
            "[reference index](reference_index_manifest.json)\n"
            "[developer guide](DEVELOPER_QUICKSTART.md)\n"
            "[schema](DATASET_SCHEMA.md)\n"
        )
        self.assertEqual(
            version_card(card, "releases/v0.2.0"),
            "path: releases/v0.2.0/data/text/train-*.jsonl\n"
            "[rights report](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/releases/v0.2.0/research/text-rights-resolution-2026-09-30.md)\n"
            "[reference index](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/releases/v0.2.0/reference_index_manifest.json)\n"
            "[developer guide](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/releases/v0.2.0/DEVELOPER_QUICKSTART.md)\n"
            "[schema](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/resolve/main/releases/v0.2.0/DATASET_SCHEMA.md)\n",
        )

    def test_validates_package_hashes_and_prepares_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.make_package(root)
            self.assertEqual(len(validate_package(package)), 11)
            output = root / "upload"
            preflight = {
                "run_id": "garhwali-hf-public-cloud-validation-v0.2.0",
                "status": "passed",
                "report_sha256": "a" * 64,
                "record_schema_version": "1.0.0",
                "config_count": 1,
            }
            with patch(
                "scripts.prepare_hf_additive_upload.preflight_candidate",
                return_value=preflight,
            ):
                plan = prepare(package, output, root / "plan.json")
            self.assertEqual(plan["file_count"], 12)
            self.assertEqual(plan["candidate_preflight"], preflight)
            self.assertEqual(plan["record_schema_version"], "1.0.0")
            self.assertEqual(len(plan["input_manifest_sha256"]), 64)
            self.assertIn("releases/v0.2.0/data/catalog/train-*.jsonl", (output / "README.md").read_text())
            self.assertIn(
                "resolve/main/releases/v0.2.0/reference_index_manifest.json",
                (output / "README.md").read_text(),
            )
            self.assertTrue((output / "releases/v0.2.0/data/catalog/train-00000.jsonl").exists())
            self.assertTrue((output / "releases/v0.2.0/DEVELOPER_QUICKSTART.md").exists())
            self.assertTrue((output / "releases/v0.2.0/search_garhwali_lexicon.py").exists())
            self.assertEqual((root / "plan.json").stat().st_size > 0, True)
            with self.assertRaises(FileExistsError):
                prepare(package, output, root / "plan.json")

    def test_full_preflight_rejects_package_that_passes_inventory_only(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            validate_package(package)

            with self.assertRaisesRegex(ValueError, "Candidate full preflight failed"):
                preflight_candidate(package)

    def test_preflight_rejects_report_for_a_different_manifest_release(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))

            def write_mismatched_report(command, **kwargs):
                report_path = Path(command[command.index("--output") + 1])
                report_path.write_text(json.dumps({
                    "run_id": "garhwali-hf-public-cloud-validation-v0.2.1",
                    "release_id": "garhwali-language-lab-v0.2.1",
                    "status": "passed",
                    "record_schema_version": "1.0.0",
                    "configs": {},
                }), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch(
                "scripts.prepare_hf_additive_upload.subprocess.run",
                side_effect=write_mismatched_report,
            ):
                with self.assertRaisesRegex(
                    ValueError, "preflight and manifest provenance disagree"
                ):
                    preflight_candidate(package)

    def test_failed_preflight_writes_no_upload_tree_or_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.make_package(root)
            output = root / "upload"
            plan_path = root / "plan.json"
            with patch(
                "scripts.prepare_hf_additive_upload.preflight_candidate",
                side_effect=ValueError("Candidate full preflight failed: fixture"),
            ):
                with self.assertRaisesRegex(ValueError, "Candidate full preflight failed"):
                    prepare(package, output, plan_path)

            self.assertFalse(output.exists())
            self.assertFalse(plan_path.exists())

    def test_accepts_the_v025_split_overlap_audit_support_files(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            (package / "research/huggingface-upstream-split-overlap-2026-10-05.json").write_text(
                "{}\n", encoding="utf-8"
            )
            (package / "research/huggingface-upstream-split-overlap-2026-10-05.md").write_text(
                "audit\n", encoding="utf-8"
            )

            self.assertEqual(len(validate_package(package)), 13)

    def test_rejects_non_public_or_audio_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            manifest_path = package / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["profile"] = "all-data"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "rights-filtered public"):
                validate_package(package)

    def test_rejects_unmanifested_payload_file(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(Path(directory))
            (package / "data/catalog/source.pdf").write_bytes(b"scan")
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                validate_package(package)

    def test_rejects_unsafe_release_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.make_package(root)
            with self.assertRaisesRegex(ValueError, "safe relative POSIX path"):
                prepare(package, root / "upload", root / "plan.json", "../outside")

    def test_rejects_release_prefix_that_disagrees_with_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.make_package(root)
            with self.assertRaisesRegex(ValueError, "must match manifest release_id"):
                prepare(
                    package, root / "upload", root / "plan.json",
                    "releases/v0.2.1",
                )

    def test_plan_commit_message_uses_the_manifest_release_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.make_package(root)
            manifest_path = package / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["release_id"] = "garhwali-language-lab-v0.2.1"
            manifest_path.write_text(json.dumps(manifest))

            with patch(
                "scripts.prepare_hf_additive_upload.preflight_candidate",
                return_value={
                    "run_id": "garhwali-hf-public-cloud-validation-v0.2.1",
                    "status": "passed",
                    "report_sha256": "b" * 64,
                    "record_schema_version": "1.0.0",
                    "config_count": 1,
                },
            ):
                plan = prepare(
                    package, root / "upload", root / "plan.json",
                    "releases/v0.2.1",
                )

            self.assertIn("Add Garhwali corpus v0.2.1", plan["command"])


if __name__ == "__main__":
    unittest.main()
