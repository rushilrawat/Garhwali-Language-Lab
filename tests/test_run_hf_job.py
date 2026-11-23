import io
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

import run_hf_job

ROOT = Path(__file__).resolve().parents[1]
LEGACY = json.loads((ROOT / "tests/fixtures/hf_jobs_legacy_commands.json").read_text(encoding="utf-8"))


def as_legacy(env, argv):
    return [f"{key}={value}" for key, value in env.items()] + argv


class RunHfJobTests(unittest.TestCase):
    def test_every_legacy_script_maps_to_one_job(self):
        self.assertEqual(sorted(LEGACY), sorted(run_hf_job.LEGACY_NAMES))
        self.assertEqual(len(run_hf_job.JOBS), 27)

    def test_each_job_runs_exactly_what_its_shell_script_ran(self):
        for legacy, commands in LEGACY.items():
            name = run_hf_job.LEGACY_NAMES[legacy]
            with self.subTest(job=name):
                steps = [as_legacy(env, argv) for env, argv in run_hf_job.JOBS[name].steps()]
                self.assertEqual(steps, commands)

    def test_task_scripts_exist_in_the_repo(self):
        for name, spec in run_hf_job.JOBS.items():
            with self.subTest(job=name):
                self.assertTrue((ROOT / "scripts" / spec.script).is_file(), spec.script)

    def test_legacy_file_name_and_path_resolve(self):
        self.assertEqual(run_hf_job.resolve("run_mt0_hf_job.sh"), "mt0")
        self.assertEqual(run_hf_job.resolve("/workspace/scripts/run_sravaani_hf_job.sh"), "sravaani")
        with self.assertRaises(SystemExit):
            run_hf_job.resolve("nope")

    def test_dry_run_prints_without_running(self):
        calls = []
        out = io.StringIO()
        code = run_hf_job.run_job("whisper_agreement", dry_run=True, runner=calls.append, out=out)
        self.assertEqual(code, 0)
        self.assertEqual(calls, [])
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[2].startswith("+ PYTHONPATH=/workspace/scripts python "))
        self.assertIn("'huggingface_hub[cli]'", lines[0])

    def test_stops_at_first_failing_step(self):
        calls = []

        def runner(argv, env, check):
            calls.append((argv, env))
            return SimpleNamespace(returncode=3 if len(calls) == 2 else 0)

        code = run_hf_job.run_job("mt0_selected_test", runner=runner, out=io.StringIO())
        self.assertEqual(code, 3)
        self.assertEqual(len(calls), 2)
        self.assertIsNone(calls[0][1])

    def test_pythonpath_only_on_task_step(self):
        calls = []

        def runner(argv, env, check):
            calls.append(env)
            return SimpleNamespace(returncode=0)

        run_hf_job.run_job("mt0_generation_analysis", runner=runner, out=io.StringIO())
        self.assertIsNone(calls[0])
        self.assertIsNone(calls[1])
        self.assertEqual(calls[2]["PYTHONPATH"], "/workspace/scripts")

    def test_cli_list_and_dry_run(self):
        out = io.StringIO()
        import contextlib
        with contextlib.redirect_stdout(out):
            self.assertEqual(run_hf_job.main(["--list"]), 0)
            self.assertEqual(run_hf_job.main(["sravaani_sweep", "--dry-run"]), 0)
        text = out.getvalue()
        self.assertIn("mt0_32768_seed43", text)
        self.assertIn("--max-runtime-seconds 20700", text)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            run_hf_job.main([])


if __name__ == "__main__":
    unittest.main()
