import unittest

import sweep_sravaani_decoding as m


class SraVaaniDecodingSweepTests(unittest.TestCase):
    def test_plan_has_six_unique_rnnt_and_ctc_configurations(self):
        plan = m.decoding_plan()
        self.assertEqual(len(plan), 6)
        self.assertEqual(len({row["config_id"] for row in plan}), 6)
        self.assertEqual({row["decoder"] for row in plan}, {"rnnt", "ctc"})
        self.assertEqual(
            [row.get("beam_size") for row in plan if row["strategy"] == "beam"],
            [2, 4, 8],
        )


if __name__ == "__main__":
    unittest.main()
