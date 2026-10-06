import os
import tempfile
import unittest
from pathlib import Path

from refresh_corpus_after_ingestion import (
    END_MARKER,
    START_MARKER,
    PIPELINE_COMMANDS,
    REQUIRED_SOURCE_MANIFESTS,
    build_source_input_provenance,
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
        self.assertEqual(plan["plan_schema_version"], 2)
        self.assertFalse(plan["mutates_workspace"])
        self.assertEqual(plan["script_count"], len(PIPELINE_COMMANDS))
        self.assertEqual(plan["release_version"], "0.2.8")
        self.assertEqual(
            plan["public_output"],
            "data/huggingface/garhwali-language-lab-v0.2.8-staging",
        )
        public_build = next(
            step for step in plan["steps"]
            if step["script"] == "build_huggingface_dataset.py"
            and "public" in step["arguments"]
        )
        self.assertEqual(
            public_build["command"][-2:],
            ["--output", "data/huggingface/garhwali-language-lab-v0.2.8-staging"],
        )
        code = plan["provenance"]["code"]
        source_inputs = plan["provenance"]["source_inputs"]
        self.assertEqual(len(code["git_revision"]), 40)
        self.assertTrue(any(
            item["path"] == "scripts/refresh_corpus_after_ingestion.py"
            and len(item["sha256"]) == 64
            for item in code["pipeline_scripts"]
        ))
        self.assertTrue({
            "scripts/validate_hf_package_cloud.py",
            "scripts/compare_hf_release_metrics.py",
        }.issubset({item["path"] for item in code["pipeline_scripts"]}))
        self.assertEqual(
            plan["ready"],
            all(step["script_exists"] for step in plan["steps"])
            and source_inputs["complete"],
        )
        self.assertEqual(
            source_inputs["complete"],
            not source_inputs["missing_required_manifests"],
        )
        self.assertEqual(source_inputs["capture_stage"], "pre_execution_dry_run")
        self.assertTrue(any(
            item["path"] == "corpus/jambu_garhwali_manifest.json"
            for item in source_inputs["files"]
        ))
        self.assertEqual(len(source_inputs["inventory_sha256"]), 64)

    def test_source_input_inventory_hashes_text_manifests_and_snapshot_pointers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in REQUIRED_SOURCE_MANIFESTS:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('{"pinned":true}\n', encoding="utf-8")
            text_input = root / "experimental" / "new_source.jsonl"
            text_input.parent.mkdir(parents=True)
            text_input.write_text('{"text":"गढ़वाळि"}\n', encoding="utf-8")
            pointer = root / "sources/online/test/source.metadata.json"
            pointer.parent.mkdir(parents=True)
            pointer.write_text('{"sha256":"source-snapshot"}\n', encoding="utf-8")

            inventory = build_source_input_provenance(root, "test")

            self.assertTrue(inventory["complete"])
            self.assertEqual(inventory["text_record_jsonl_count"], 1)
            self.assertEqual(inventory["capture_stage"], "test")
            kinds = {item["path"]: item["kind"] for item in inventory["files"]}
            self.assertEqual(kinds["experimental/new_source.jsonl"], "text_record_jsonl")
            self.assertEqual(kinds["sources/online/test/source.metadata.json"], "source_snapshot_pointer")
            self.assertEqual(len(inventory["inventory_sha256"]), 64)

    def test_run_pipeline_captures_source_inputs_after_pinned_ingestors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            def runner(command, *, cwd, check, env):
                calls.append(command)
                if len(calls) == 2:
                    source = root / "corpus/new_source.jsonl"
                    source.parent.mkdir(parents=True, exist_ok=True)
                    source.write_text('{"text":"गढ़वाली"}\n', encoding="utf-8")

            provenance = run_pipeline(root, runner=runner)

            self.assertEqual(len(calls), len(PIPELINE_COMMANDS))
            self.assertEqual(
                provenance["source_inputs"]["capture_stage"],
                "after_source_ingestion_before_derivation",
            )
            self.assertTrue(any(
                item["path"] == "corpus/new_source.jsonl"
                for item in provenance["source_inputs"]["files"]
            ))

    def test_default_pipeline_version_matches_current_schema_release(self):
        environment = configure_environment({})
        self.assertEqual(environment['GARHWALI_RELEASE_VERSION'], '0.2.8')
        self.assertEqual(
            environment['GARHWALI_HF_PUBLIC_OUTPUT'],
            'data/huggingface/garhwali-language-lab-v0.2.8-staging',
        )
        self.assertEqual(
            environment['GARHWALI_HF_ALL_DATA_OUTPUT'],
            'data/huggingface/garhwali-language-lab-all-data-v0.2.8-local',
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
