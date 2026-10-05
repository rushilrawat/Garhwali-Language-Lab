from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit_archive_media_first_pass import build_media_report, scan_transcript_sidecars


class ArchiveMediaFirstPassTests(unittest.TestCase):
    def fixture(self, root: Path, names: dict[str, bytes]):
        candidates = []
        quality_files = []
        for index, (name, payload) in enumerate(names.items()):
            path = root / "data" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            audio_only = name.endswith(".mp3")
            streams = (
                [{"codec_type": "audio", "codec_name": "mp3", "sample_rate": "44100", "channels": 2}]
                if audio_only
                else [
                    {"codec_type": "video", "codec_name": "h264", "width": 640, "height": 480},
                    {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2},
                ]
            )
            duration = float(index + 1)
            digest = hashlib.sha256(payload).hexdigest()
            candidates.append({
                "archive_identifier": f"item-{index}",
                "title": f"Title {index}",
                "media_path": path.relative_to(root).as_posix(),
                "media_sha256": digest,
                "bytes": len(payload),
                "duration_seconds": duration,
                "streams": streams,
                "license_claim": None,
                "license_claim_class": "no_reuse_license_claim_recorded",
                "rights_evidence_decision": "claim_not_verified",
                "publication_and_training_decision": "not_cleared",
                "transcript_status": "not_transcribed_in_this_workstream",
                "content_review_status": "not_reviewed_for_language_or_content",
                "source_url": f"https://archive.org/details/item-{index}",
            })
            quality_files.append({
                "path": str(path),
                "size_bytes": len(payload),
                "duration_seconds": duration,
                "streams": streams,
            })
        return candidates, {
            "media": {
                "files_found": len(names),
                "files_probed": len(names),
                "probe_failures": [],
                "files": quality_files,
            }
        }

    def test_build_media_report_verifies_and_aggregates_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidates, quality = self.fixture(root, {"lesson.mp3": b"audio", "field.mp4": b"video"})

            report = build_media_report(candidates, quality, root)

        self.assertEqual(report["summary"]["asset_count"], 2)
        self.assertEqual(report["summary"]["media_type_counts"], {"audio-only": 1, "audio+video": 1})
        self.assertEqual(report["summary"]["total_playback_seconds"], 3.0)
        self.assertEqual(report["summary"]["exact_duplicate_hash_groups"], 0)
        self.assertEqual(report["validation"]["errors"], [])
        self.assertEqual(report["assets"][0]["media_path"], "data/lesson.mp3")
        self.assertNotIn("text", report["assets"][0])

    def test_build_media_report_flags_hash_and_probe_mismatches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidates, quality = self.fixture(root, {"lesson.mp3": b"audio"})
            candidates[0]["media_sha256"] = "0" * 64
            quality["media"]["files"][0]["duration_seconds"] = 99.0

            report = build_media_report(candidates, quality, root)

        codes = {error["code"] for error in report["validation"]["errors"]}
        self.assertIn("sha256_mismatch", codes)
        self.assertIn("duration_mismatch", codes)

    def test_build_media_report_blocks_paths_outside_project_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            outside = Path(temporary) / "private.mp3"
            root.mkdir()
            outside.write_bytes(b"audio")
            candidates, quality = self.fixture(root, {"placeholder.mp3": b"audio"})
            candidates[0]["media_path"] = "../private.mp3"

            report = build_media_report(candidates, quality, root)

        self.assertIn(
            "media_path_outside_project_root",
            {error["code"] for error in report["validation"]["errors"]},
        )

    def test_scan_transcript_sidecars_matches_archive_listing_and_local_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            item_dir = root / "archive" / "item-a"
            item_dir.mkdir(parents=True)
            (item_dir / "audio.mp3").write_bytes(b"audio")
            (item_dir / "captions.en.vtt").write_text("WEBVTT\n", encoding="utf-8")
            (item_dir / "archive_metadata.json").write_text(
                '{"files": [{"name": "audio.mp3", "format": "VBR MP3"}, '
                '{"name": "captions.en.vtt", "format": "WebVTT"}]}',
                encoding="utf-8",
            )
            candidates = [{"archive_identifier": "item-a", "media_path": "archive/item-a/audio.mp3"}]

            result = scan_transcript_sidecars(candidates, root)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["listed_file_entries"], 2)
        self.assertEqual(len(result["archive_caption_or_transcript_candidates"]), 1)
        self.assertEqual(len(result["local_caption_or_transcript_files"]), 1)

    def test_scan_transcript_sidecars_marks_missing_item_metadata(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            item_dir = root / "archive" / "item-a"
            item_dir.mkdir(parents=True)
            candidates = [{"archive_identifier": "item-a", "media_path": "archive/item-a/audio.mp3"}]

            result = scan_transcript_sidecars(candidates, root)

        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["items_missing_metadata"], ["item-a"])

    def test_build_media_report_tracks_local_machine_draft_separately(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidates, quality = self.fixture(root, {"lesson.mp3": b"audio"})
            pilot_dir = root / "data" / "extracted" / "research"
            pilot_dir.mkdir(parents=True)
            (pilot_dir / "internet_archive_asr_pilot_2026-10-04.json").write_text(
                json.dumps({
                    "archive_identifier": "item-0",
                    "media_sha256": candidates[0]["media_sha256"],
                    "review_status": "machine_draft_unreviewed",
                    "training_eligible": False,
                    "public_redistribution_eligible": False,
                }),
                encoding="utf-8",
            )

            report = build_media_report(candidates, quality, root)

        self.assertEqual(report["summary"]["local_machine_draft_output_count"], 1)
        self.assertEqual(report["summary"]["local_machine_draft_matched_assets"], 1)
        self.assertEqual(report["assets"][0]["source_transcript_status"], "not_transcribed_in_this_workstream")
        self.assertEqual(report["assets"][0]["local_machine_draft_status"], "present_unreviewed")
        self.assertFalse(report["assets"][0]["local_machine_draft_outputs"][0]["training_eligible"])
        self.assertFalse(report["assets"][0]["local_machine_draft_outputs"][0]["public_redistribution_eligible"])


if __name__ == "__main__":
    unittest.main()
