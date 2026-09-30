import unittest
from pathlib import Path

from refresh_corpus_after_ingestion import (
    END_MARKER,
    START_MARKER,
    PIPELINE_COMMANDS,
    replace_metrics_block,
    run_pipeline,
)


class RefreshCorpusAfterIngestionTests(unittest.TestCase):
    def test_metrics_block_replaces_only_the_marked_section(self):
        readme = f"before\n{START_MARKER}\nold table\n{END_MARKER}\nafter\n"
        updated = replace_metrics_block(readme, "| Texts | 31,198 |")
        self.assertEqual(
            updated,
            f"before\n{START_MARKER}\n| Texts | 31,198 |\n{END_MARKER}\nafter\n",
        )

    def test_metrics_block_requires_exactly_one_marker_pair(self):
        with self.assertRaises(ValueError):
            replace_metrics_block("no markers", "table")
        duplicate = f"{START_MARKER}\n{END_MARKER}\n{START_MARKER}\n{END_MARKER}"
        with self.assertRaises(ValueError):
            replace_metrics_block(duplicate, "table")

    def test_pipeline_is_ordered_and_stops_on_failure(self):
        calls = []

        def runner(command, *, cwd, check, env):
            calls.append((command, cwd, check))
            if len(calls) == 3:
                raise RuntimeError("stop")

        with self.assertRaisesRegex(RuntimeError, "stop"):
            run_pipeline(Path("/repo"), runner=runner)

        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[0][0][1].endswith("ingest_jambu_garhwali.py"))
        self.assertEqual(calls[0][0][2:], ["--offline"])
        self.assertTrue(calls[1][0][1].endswith("ingest_garhwali_language_library.py"))
        self.assertTrue(calls[2][0][1].endswith("verify_ingestion.py"))
        self.assertTrue(all(cwd == Path("/repo") and check for _, cwd, check in calls))
        self.assertEqual(PIPELINE_COMMANDS[-2][0], "build_hf_reference_index.py")
        self.assertEqual(PIPELINE_COMMANDS[-1][0], "generate_project_file_map.py")

    def test_pipeline_refreshes_cleaned_text_before_language_quality_tags(self):
        names = [script for script, _ in PIPELINE_COMMANDS]
        self.assertLess(names.index("ingest_jambu_garhwali.py"), names.index("verify_ingestion.py"))
        self.assertLess(names.index("ingest_garhwali_language_library.py"), names.index("verify_ingestion.py"))
        self.assertLess(names.index("clean_text_corpus.py"), names.index("deep_cleanup.py"))
        self.assertLess(names.index("deep_cleanup.py"), names.index("tag_language_quality.py"))
        self.assertLess(names.index("tag_language_quality.py"), names.index("segment_text_corpus.py"))
        public_build = next(
            arguments for script, arguments in PIPELINE_COMMANDS
            if script == "build_huggingface_dataset.py" and "public" in arguments
        )
        self.assertTrue(
            any("garhwali-language-lab-v2.0.0-staging" in arg for arg in public_build)
        )

    def test_pipeline_ingests_pinned_static_source_before_rebuilding_views(self):
        names = [script for script, _ in PIPELINE_COMMANDS]
        self.assertLess(names.index("ingest_garhwali_language_library.py"), names.index("verify_ingestion.py"))


if __name__ == "__main__":
    unittest.main()
