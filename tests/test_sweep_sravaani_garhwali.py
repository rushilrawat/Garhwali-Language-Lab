import unittest

import sweep_sravaani_garhwali as m


class SraVaaniSweepTests(unittest.TestCase):
    def test_trial_plan_starts_with_broad_validation_first_comparison(self):
        trials = m.build_trial_plan()
        self.assertEqual(len(trials), 61)
        self.assertEqual(len({trial.trial_id for trial in trials}), 61)
        self.assertEqual({trial.scope for trial in trials[:6]}, {"decoder_joint", "full"})
        self.assertEqual({trial.seed for trial in trials[:10]}, {17})
        self.assertTrue(all(trial.epochs >= 1 for trial in trials))
        self.assertTrue(all(trial.learning_rate <= 1e-4 for trial in trials))

    def test_optimizer_steps_respect_effective_batch(self):
        decoder = m.build_trial_plan()[0]
        full = m.build_trial_plan()[3]
        self.assertEqual(decoder.batch_size * decoder.accumulate_grad_batches, 32)
        self.assertEqual(full.batch_size * full.accumulate_grad_batches, 32)
        self.assertEqual(m.optimizer_steps(1621, decoder), 51)
        self.assertEqual(m.optimizer_steps(1621, full), 51)

    def test_six_hour_cap_uses_nearly_all_five_dollar_balance(self):
        prior = m.conservative_prior_cost_usd([487.503, 164.042])
        self.assertAlmostEqual(prior, 0.144788, places=6)
        self.assertAlmostEqual(m.max_combined_cost_usd(prior), 4.944788, places=6)
        self.assertLess(m.max_combined_cost_usd(prior), 5.0)

    def test_first_six_trials_balance_decoder_and_full_model_scope(self):
        trials = m.build_trial_plan()[:6]
        self.assertEqual(sum(row.scope == "decoder_joint" for row in trials), 3)
        self.assertEqual(sum(row.scope == "full" for row in trials), 3)

    def test_refined_plan_has_61_decoder_only_trials(self):
        trials = m.build_refined_decoder_plan()
        self.assertEqual(len(trials), 61)
        self.assertEqual(len({row.trial_id for row in trials}), 61)
        self.assertTrue(all(row.scope == "decoder_joint" for row in trials))
        self.assertEqual({row.seed for row in trials}, {17, 29, 41, 53, 71})
        self.assertIn(3e-5, {row.learning_rate for row in trials})

    def test_builds_single_validation_selected_expanded_human_trial(self):
        trials = m.build_expanded_human_plan()
        self.assertEqual(len(trials), 1)
        trial = trials[0]
        self.assertEqual(trial.scope, "decoder_joint")
        self.assertEqual(trial.learning_rate, 5e-5)
        self.assertEqual(trial.epochs, 2)
        self.assertEqual(trial.seed, 17)


if __name__ == "__main__":
    unittest.main()
