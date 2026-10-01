import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_hf_additive_upload import prepare, validate_package, version_card


class AdditiveHuggingFaceUploadTests(unittest.TestCase):
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
            "include_audio": False, "linked_audio_files": 0,
            "removed_audio_files": 0,
            "configs": {"catalog/train": {
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
            plan = prepare(package, output, root / "plan.json")
            self.assertEqual(plan["file_count"], 12)
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

    def test_plan_commit_message_uses_the_manifest_release_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self.make_package(root)
            manifest_path = package / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["release_id"] = "garhwali-language-lab-v0.2.1"
            manifest_path.write_text(json.dumps(manifest))

            plan = prepare(
                package, root / "upload", root / "plan.json",
                "releases/v0.2.1",
            )

            self.assertIn("Add Garhwali corpus v0.2.1", plan["command"])


if __name__ == "__main__":
    unittest.main()
