import unittest

from audit_archive_corpus_overlap import audit_overlap


class ArchiveCorpusOverlapTests(unittest.TestCase):
    def test_exact_normalized_matches_are_reported_without_text(self):
        archive = [{
            "record_id": "ia:page:1",
            "source_id": "ia-book",
            "text": "गढ़वाली भाषा और लोकगीत",
        }]
        corpus = [{"text_clean": "गढ़वाली भाषा और लोकगीत", "split": "train"}]

        report = audit_overlap(archive, corpus, min_chars=3, ngram_size=2)

        self.assertEqual(report["exact"]["normalized_match_rows"], 1)
        self.assertEqual(report["exact"]["archive_rows_with_match"], 1)
        self.assertNotIn("text", report["exact"]["matches"][0]["archive"])
        self.assertNotIn("text", report["exact"]["matches"][0]["corpus"])

    def test_near_match_is_reported_as_unadjudicated_candidate(self):
        text = "garhwali language folk music archive reference page"
        archive = [{"record_id": "ia:page:2", "source_id": "ia-book", "text": text}]
        corpus = [{"text_clean": text + " corrected", "split": "train"}]

        report = audit_overlap(
            archive, corpus, ngram_size=3, min_chars=10, min_jaccard=0.5,
        )

        self.assertEqual(report["near_duplicate"]["threshold_pairs"], 1)
        self.assertEqual(
            report["near_duplicate"]["matches"][0]["review_state"],
            "candidate_only_unadjudicated",
        )

    def test_short_text_is_exact_checked_but_not_near_checked(self):
        archive = [{"record_id": "ia:page:3", "source_id": "ia-book", "text": "राम"}]
        corpus = [{"text_clean": "राम", "split": "train"}]

        report = audit_overlap(archive, corpus)

        self.assertEqual(report["exact"]["normalized_match_rows"], 1)
        self.assertEqual(report["near_duplicate"]["candidate_pairs_scored"], 0)
        self.assertEqual(report["near_duplicate"]["threshold_pairs"], 0)


if __name__ == "__main__":
    unittest.main()
