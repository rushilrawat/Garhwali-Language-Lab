import hashlib
import tempfile
import types
import unittest
from pathlib import Path

from garhwali_lab.hashing import sha256_bytes, sha256_file, sha256_text
from garhwali_lab.io import iter_jsonl, read_json, read_jsonl, write_json, write_jsonl
from garhwali_lab.paths import ROOT
from garhwali_lab.text import clean_text, content_key, leakage_key, match_key


class IoTests(unittest.TestCase):
    def test_jsonl_round_trip_skips_blank_lines_and_creates_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "rows.jsonl"
            write_jsonl(path, [{"b": 1, "a": "क़"}, {"z": None}])
            path.write_text(path.read_text(encoding="utf-8") + "\n  \n", encoding="utf-8")
            self.assertEqual(read_jsonl(path), [{"a": "क़", "b": 1}, {"z": None}])
            self.assertEqual(read_jsonl(str(path)), read_jsonl(path))
            stream = iter_jsonl(path)
            self.assertIsInstance(stream, types.GeneratorType)
            self.assertEqual(list(stream), read_jsonl(path))

    def test_write_jsonl_uses_canonical_sorted_unescaped_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            write_jsonl(path, [{"b": 1, "a": "क़"}])
            self.assertEqual(path.read_text(encoding="utf-8"), '{"a": "क़", "b": 1}\n')

    def test_json_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out" / "value.json"
            write_json(path, {"b": [1], "a": "x"}, sort_keys=True)
            self.assertTrue(path.read_text(encoding="utf-8").startswith('{\n  "a"'))
            self.assertEqual(read_json(path), {"a": "x", "b": [1]})


class HashingTests(unittest.TestCase):
    def test_file_hash_matches_hashlib_across_chunk_boundary(self):
        payload = bytes(range(256)) * 5000
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blob.bin"
            path.write_bytes(payload)
            expected = hashlib.sha256(payload).hexdigest()
            self.assertEqual(sha256_file(path), expected)
            self.assertEqual(sha256_file(str(path)), expected)
        self.assertEqual(sha256_bytes(payload), expected)
        self.assertEqual(sha256_text("गढ़"), hashlib.sha256("गढ़".encode()).hexdigest())


class TextPolicyTests(unittest.TestCase):
    def test_clean_text_keeps_compatibility_characters(self):
        self.assertEqual(clean_text("  ﬁ\tＡ  "), "ﬁ Ａ")

    def test_match_key_folds_compatibility_case_and_space(self):
        self.assertEqual(match_key("  ﬁ\tＡ  "), match_key("fi a"))

    def test_content_key_keeps_devanagari_vowel_signs(self):
        self.assertNotEqual(content_key("काम"), content_key("कम"))
        self.assertEqual(content_key("काम!"), content_key("  काम "))

    def test_leakage_key_is_deliberately_looser_than_content_key(self):
        self.assertEqual(leakage_key("काम"), leakage_key("कम"))
        pairs = [("काम", "  काम!"), ("Garhwali 2026", "garhwali-2026"), ("ﬁ", "FI")]
        for left, right in pairs:
            self.assertEqual(content_key(left), content_key(right))
            self.assertEqual(leakage_key(left), leakage_key(right))

    def test_keys_accept_missing_values(self):
        for key in (content_key, leakage_key):
            self.assertEqual(key(None), "")


class PathTests(unittest.TestCase):
    def test_root_is_repository_root(self):
        self.assertTrue((ROOT / "scripts" / "garhwali_lab").is_dir())


if __name__ == "__main__":
    unittest.main()


class VersionTests(unittest.TestCase):
    def test_default_corpus_version_is_unpublished(self):
        from garhwali_lab import version

        self.assertFalse(version.is_published_corpus_version(version.corpus_default_version()))

    def test_guard_refuses_published_and_retired_versions(self):
        import os
        from unittest import mock

        from garhwali_lab import version

        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(version.ALLOW_REBUILD_ENV, None)
            for published in ("0.2.8", "v0.2.0", "2.2.0"):
                with self.assertRaises(version.PublishedVersionError):
                    version.ensure_unpublished_corpus_version(published)
            version.ensure_unpublished_corpus_version(version.corpus_default_version())
        with mock.patch.dict(os.environ, {version.ALLOW_REBUILD_ENV: "1"}):
            version.ensure_unpublished_corpus_version("0.2.8")

    def test_environment_override_applies_to_both_lines(self):
        import os
        from unittest import mock

        from garhwali_lab import version

        with mock.patch.dict(os.environ, {version.ENV_VAR: "v3.1.4"}):
            self.assertEqual(version.corpus_release_version(), "3.1.4")
            self.assertEqual(version.bundle_release_version(), "3.1.4")


class WriteJsonlReturnTests(unittest.TestCase):
    def test_write_jsonl_returns_the_sha256_of_the_file_it_wrote(self):
        import tempfile
        from pathlib import Path

        from garhwali_lab.hashing import sha256_file
        from garhwali_lab.io import write_jsonl
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'nested' / 'rows.jsonl'
            digest = write_jsonl(path, [{'b': 1, 'a': 'गढ़'}])
            self.assertEqual(digest, sha256_file(path))

