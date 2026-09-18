import unittest

import validate_ocr_corrections as m


class OcrCorrectionValidationTests(unittest.TestCase):
    def test_proposed_text_applies_each_candidate_once(self):
        text, changes = m.proposed_text({
            "text_original": "घरवळि घरवळि",
            "spelling_candidates": [{"observed": "घरवळि", "candidate": "गढ़वळि"}],
        })
        self.assertEqual(text, "गढ़वळि घरवळि")
        self.assertEqual(len(changes), 1)

    def test_classify_requires_seed_majority(self):
        self.assertEqual(m.classify([-1.0, -0.8, 0.1]), ("model_supported_proposal", "medium"))
        self.assertEqual(m.classify([0.7, 0.8, 1.0]), ("model_rejects_proposal", "high"))
        self.assertEqual(m.classify([-0.8, 0.8, 0.0]), ("inconclusive", "low"))


if __name__ == "__main__":
    unittest.main()
