import tempfile
import unittest
from pathlib import Path

from generate_project_file_map import collect_project_files, render_file_map


class ProjectFileMapTests(unittest.TestCase):
    def test_render_groups_every_file_and_counts_unique_paths(self):
        result = render_file_map([
            "README.md",
            "scripts/ingest_jambu_garhwali.py",
            "tests/test_ingest_jambu_garhwali.py",
            "README.md",
        ])

        self.assertIn("Files indexed: **3**.", result)
        self.assertIn("- `README.md`", result)
        self.assertIn("- `scripts/ingest_jambu_garhwali.py`", result)
        self.assertIn("- `tests/test_ingest_jambu_garhwali.py`", result)

    def test_map_explains_that_ignored_data_is_indexed_by_manifests(self):
        result = render_file_map([])

        self.assertIn("Ignored raw downloads, caches", result)
        self.assertIn("Hugging Face manifests", result)
        self.assertIn("Files indexed: **0**.", result)

    def test_lists_only_tracked_files(self):
        calls = []

        class Result:
            stdout = b"README.md\0scripts/a.py\0"

        def runner(command, **kwargs):
            calls.append(command)
            return Result()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "README.md").write_text("x")
            (root / "scripts/a.py").write_text("x")
            self.assertEqual(collect_project_files(root, runner=runner), ["README.md", "scripts/a.py"])
        self.assertEqual(calls, [["git", "ls-files", "--cached", "-z"]])


if __name__ == "__main__":
    unittest.main()
