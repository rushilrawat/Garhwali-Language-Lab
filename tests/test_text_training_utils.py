import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from text_training_utils import (
    deterministic_train_dev_split,
    is_recommended_training_row,
)


class DeterministicTrainDevSplitTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"id": f"row-{index}", "text": str(index)} for index in range(20)]

    def test_split_is_stable_when_input_order_changes(self):
        train, development = deterministic_train_dev_split(self.rows, seed=17)
        reversed_train, reversed_development = deterministic_train_dev_split(
            list(reversed(self.rows)), seed=17
        )

        self.assertEqual({row["id"] for row in train}, {row["id"] for row in reversed_train})
        self.assertEqual(
            {row["id"] for row in development},
            {row["id"] for row in reversed_development},
        )

    def test_split_has_disjoint_rows_and_keeps_a_development_slice(self):
        train, development = deterministic_train_dev_split(self.rows, seed=17)
        train_ids = {row["id"] for row in train}
        development_ids = {row["id"] for row in development}

        self.assertFalse(train_ids & development_ids)
        self.assertEqual(train_ids | development_ids, {row["id"] for row in self.rows})
        self.assertEqual(len(development), 2)

    def test_split_rejects_duplicate_or_missing_ids(self):
        with self.assertRaisesRegex(ValueError, "unique non-empty id"):
            deterministic_train_dev_split([{"id": "same"}, {"id": "same"}])
        with self.assertRaisesRegex(ValueError, "unique non-empty id"):
            deterministic_train_dev_split([{"text": "missing id"}, {"id": "ok"}])

    def test_split_rejects_too_few_rows(self):
        with self.assertRaisesRegex(ValueError, "at least two rows"):
            deterministic_train_dev_split([{"id": "only-row"}])

    def test_training_flag_accepts_boolean_and_csv_string_values(self):
        self.assertTrue(is_recommended_training_row({"recommended_for_training": True}))
        self.assertTrue(is_recommended_training_row({"recommended_for_training": "True"}))
        self.assertFalse(is_recommended_training_row({"recommended_for_training": "False"}))
        self.assertFalse(is_recommended_training_row({"recommended_for_training": None}))


if __name__ == "__main__":
    unittest.main()
