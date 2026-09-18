import unittest

import audit_semantic_duplicates as m


class SemanticDuplicateAuditTests(unittest.TestCase):
    def test_source_ids_normalizes_missing_values(self):
        row = {"parents": [{"provenance": [{"source_id": None}, {}]}]}
        self.assertEqual(m.source_ids(row), ["unknown"])

    def test_collect_pairs_deduplicates_neighbors_and_marks_cross_split(self):
        rows = [
            {"segment_sha256": "a", "split": "train", "text": "one", "parents": []},
            {"segment_sha256": "b", "split": "validation", "text": "two", "parents": []},
            {"segment_sha256": "c", "split": "train", "text": "three", "parents": []},
        ]
        pairs = m.collect_pairs(
            rows,
            [[0, 1, 2], [1, 0, 2], [2, 0, 1]],
            [[1.0, .97, .4], [1.0, .97, .3], [1.0, .4, .3]],
            threshold=.9,
        )
        self.assertEqual(len(pairs), 1)
        self.assertTrue(pairs[0]["cross_split"])
        self.assertEqual(pairs[0]["cosine_similarity"], .97)


if __name__ == "__main__":
    unittest.main()
