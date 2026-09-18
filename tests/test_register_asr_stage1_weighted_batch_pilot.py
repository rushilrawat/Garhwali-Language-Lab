import unittest

import register_asr_stage1_weighted_batch_pilot as m


class RegisterAsrStage1WeightedBatchPilotTests(unittest.TestCase):
    def test_validates_exact_weighted_batch_pilot_shape(self):
        report = {
            'curriculum_stage': 1,
            'training_complete': False,
            'batching_strategy': 'stratified_normalized_weighted_gradient_accumulation',
            'pilot_human_records': 32,
            'pilot_machine_records': 2048,
            'training_examples': 2080,
            'training_steps': 32,
            'records_per_batch': {'minimum': 65, 'maximum': 65},
        }
        self.assertTrue(m.validate_training_report(report))

    def test_rejects_unbalanced_or_completed_training_report(self):
        report = {
            'curriculum_stage': 1,
            'training_complete': True,
            'batching_strategy': 'one_record_per_optimizer_step',
            'pilot_human_records': 32,
            'pilot_machine_records': 2048,
            'training_examples': 2080,
            'training_steps': 2080,
            'records_per_batch': {'minimum': 1, 'maximum': 1},
        }
        with self.assertRaisesRegex(ValueError, 'weighted-batch'):
            m.validate_training_report(report)


if __name__ == '__main__':
    unittest.main()
