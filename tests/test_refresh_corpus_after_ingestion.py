import os
import unittest
from pathlib import Path

from refresh_corpus_after_ingestion import (
    END_MARKER,
    START_MARKER,
    PIPELINE_COMMANDS,
    build_pipeline_plan,
    configure_environment,
    replace_metrics_block,
    render_metrics_table,
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

    def test_local_metrics_table_is_compact_and_distinguishes_overlapping_views(self):
        metrics = {
            "release_id": "garhwali-language-lab-v0.2.6",
            "source_records": 43014,
            "source_files": 75,
            "exact_unique_parent_texts": 36105,
            "text_characters": 21990238,
            "whitespace_tokens": 4023979,
            "source_segments": 220034,
            "exact_unique_segments": 200548,
            "public_catalog_text_records": 12657,
            "public_catalog_metadata_only_records": 23448,
            "public_text_config_rows": 18598,
            "public_profile_package_rows_overlapping_views": 168388,
            "reference_index_rows": 355537,
        }

        table = render_metrics_table(metrics)

        self.assertIn("garhwali-language-lab-v0.2.6 local candidate", table)
        self.assertIn("12,657 full-text / 23,448 metadata-only", table)
        self.assertIn("overlapping content-view rows", table)
        self.assertEqual(table.count("\n|"), 9)

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

    def test_pipeline_builds_versioned_package_paths(self):
        calls = []

        def runner(command, *, cwd, check, env):
            calls.append((command, env.copy()))

        environment = dict(os.environ, GARHWALI_RELEASE_VERSION="0.2.1")
        run_pipeline(Path("/repo"), runner=runner, environment=environment)
        builders = [
            command for command, _ in calls
            if command[1].endswith("build_huggingface_dataset.py")
        ]
        self.assertEqual(len(builders), 2)
        self.assertIn("data/huggingface/garhwali-language-lab-all-data-v0.2.1-local", builders[0])
        self.assertIn("data/huggingface/garhwali-language-lab-v0.2.1-staging", builders[1])
        self.assertEqual(
            calls[-2][1]["GARHWALI_HF_PUBLIC_OUTPUT"],
            "data/huggingface/garhwali-language-lab-v0.2.1-staging",
        )

    def test_dry_run_lists_exact_commands_without_running_them(self):
        plan = build_pipeline_plan(Path(__file__).resolve().parents[1])

        self.assertEqual(plan["mode"], "dry-run")
        self.assertFalse(plan["mutates_workspace"])
        self.assertTrue(plan["ready"])
        self.assertEqual(plan["script_count"], len(PIPELINE_COMMANDS))
        self.assertEqual(plan["release_version"], "0.2.6")
        self.assertEqual(
            plan["public_output"],
            "data/huggingface/garhwali-language-lab-v0.2.6-staging",
        )
        public_build = next(
            step for step in plan["steps"]
            if step["script"] == "build_huggingface_dataset.py"
            and "public" in step["arguments"]
        )
        self.assertEqual(
            public_build["command"][-2:],
            ["--output", "data/huggingface/garhwali-language-lab-v0.2.6-staging"],
        )

    def test_default_pipeline_version_matches_current_schema_release(self):
        environment = configure_environment({})
        self.assertEqual(environment['GARHWALI_RELEASE_VERSION'], '0.2.6')
        self.assertEqual(
            environment['GARHWALI_HF_PUBLIC_OUTPUT'],
            'data/huggingface/garhwali-language-lab-v0.2.6-staging',
        )
        self.assertEqual(
            environment['GARHWALI_HF_ALL_DATA_OUTPUT'],
            'data/huggingface/garhwali-language-lab-all-data-v0.2.6-local',
        )

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
        self.assertEqual(public_build, ("--profile", "public"))

    def test_pipeline_ingests_pinned_static_source_before_rebuilding_views(self):
        names = [script for script, _ in PIPELINE_COMMANDS]
        self.assertLess(names.index("ingest_garhwali_language_library.py"), names.index("verify_ingestion.py"))


if __name__ == "__main__":
    unittest.main()
