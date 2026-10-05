import unittest

from audit_vaani_official_split_lineage import (
    build_official_test_remainder,
    build_report,
)


class OfficialSplitLineageTests(unittest.TestCase):
    @staticmethod
    def row(audio_hash, official_split, speaker_id):
        return {
            "audio_sha256": audio_hash,
            "transcription_split": official_split,
            "speaker_id": speaker_id,
            "duration_seconds": 2.0,
        }

    def test_maps_local_views_to_official_splits_and_flags_exposure(self):
        source = [
            self.row("a", "train", "s1"),
            self.row("b", "validation", "s2"),
            self.row("c", "test", "s1"),
            self.row("d", "test", "s1"),
        ]
        project_splits = {
            "asr_train": [self.row("a", "train", "s1")],
            "asr_validation": [self.row("b", "validation", "s2")],
            "asr_test": [self.row("c", "test", "s1")],
        }
        training_views = {
            "strict_asr_train": [self.row("a", "train", "s1")],
            "expanded_human_train": [
                self.row("a", "train", "s1"),
                self.row("d", "test", "s1"),
            ],
            "whisper_curriculum_train": [self.row("a", "train", "s1")],
        }

        report = build_report(source, project_splits, training_views)

        self.assertEqual(
            report["official_split_counts"],
            {"train": 1, "validation": 1, "test": 2},
        )
        self.assertEqual(
            report["project_split_coverage"]["asr_test"]["official_split_counts"],
            {"train": 0, "validation": 0, "test": 1},
        )
        self.assertEqual(report["official_test_remainder"]["records"], 1)
        self.assertEqual(
            report["official_test_remainder"]["training_view_overlap"][
                "whisper_curriculum_train"
            ]["audio_hash_rows"],
            0,
        )
        self.assertEqual(
            report["official_test_remainder"]["training_view_overlap"][
                "whisper_curriculum_train"
            ]["speaker_rows"],
            1,
        )
        self.assertEqual(
            report["official_test_remainder"]["training_view_overlap"][
                "expanded_human_train"
            ]["audio_hash_rows"],
            1,
        )

    def test_rejects_missing_hash_or_unknown_official_split(self):
        with self.assertRaisesRegex(ValueError, "audio_sha256"):
            build_report(
                [{"transcription_split": "test", "speaker_id": "s1"}],
                {"asr_test": []},
                {"strict_asr_train": []},
            )
        with self.assertRaisesRegex(ValueError, "unsupported transcription_split"):
            build_report(
                [self.row("a", "dev", "s1")],
                {"asr_test": []},
                {"strict_asr_train": []},
            )

    def test_remainder_keeps_only_official_test_rows_outside_fixed_test(self):
        source = [
            self.row("train-a", "train", "s1"),
            self.row("fixed", "test", "s2"),
            self.row("remainder", "test", "s3"),
        ]
        remainder = build_official_test_remainder(
            source, [self.row("fixed", "test", "s2")]
        )

        self.assertEqual([row["audio_sha256"] for row in remainder], ["remainder"])


if __name__ == "__main__":
    unittest.main()
