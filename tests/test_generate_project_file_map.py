import unittest

from generate_project_file_map import append_disk_inventory, render_file_map


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

    def test_map_summarizes_ignored_payloads_without_losing_total_file_counts(self):
        result = append_disk_inventory(render_file_map([]), {
            "total_files": 10,
            "total_bytes": 2048,
            "listed_files": 4,
            "unlisted_files": 6,
            "unlisted_bytes": 1024,
            "groups": {"data/audio/…/": [5, 900], "data/cache/": [1, 124]},
        })

        self.assertIn("Workspace files counted: **10**", result)
        self.assertIn("Ignored or otherwise unlisted payload files: **6** (1,024 bytes)", result)
        self.assertIn("`data/audio/…/` | 5 | 900", result)


if __name__ == "__main__":
    unittest.main()
