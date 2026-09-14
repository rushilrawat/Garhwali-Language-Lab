import tempfile
import unittest
from pathlib import Path

import train_sravaani_garhwali as m


class TrainSraVaaniGarhwaliTests(unittest.TestCase):
    def test_computes_optimizer_steps_with_partial_batches(self):
        self.assertEqual(
            m.compute_optimizer_steps(
                records=1621,
                batch_size=4,
                accumulate_grad_batches=8,
                epochs=2,
            ),
            102,
        )

    def test_builds_decoder_only_plan_without_using_test_split(self):
        package = {
            'run_id': 'package-test',
            'package_status': 'ready_for_nemo_cuda_training',
            'splits': {
                'train': {'records': 1621, 'duration_seconds': 10333.4},
                'validation': {'records': 269, 'duration_seconds': 1696.3},
                'test': {'records': 112, 'duration_seconds': 794.9},
            },
            'leakage': {
                'audio_hash_cross_split': 0,
                'identified_speaker_cross_split': 0,
            },
            'test_split_held_out_from_training': True,
        }
        plan = m.build_training_plan(package)
        self.assertEqual(plan['optimizer_steps'], 102)
        self.assertEqual(plan['effective_batch_size'], 32)
        self.assertEqual(plan['adaptation_scope'], 'decoder_and_joint_only_encoder_frozen')
        self.assertEqual(plan['training_records'], 1621)
        self.assertEqual(plan['validation_records'], 269)
        self.assertEqual(plan['held_out_test_records'], 112)

    def test_external_dependency_audit_names_missing_checkpoint_and_cuda(self):
        with tempfile.TemporaryDirectory() as directory:
            status = m.external_dependency_status(
                Path(directory) / 'missing.nemo',
                cuda_available=False,
            )
        self.assertEqual(status['status'], 'blocked_external_dependencies')
        self.assertEqual(
            status['missing'],
            ['sravaani_nemo_checkpoint', 'cuda_capable_nvidia_gpu'],
        )

    def test_external_dependency_audit_accepts_present_checkpoint_and_cuda(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / 'model.nemo'
            checkpoint.write_bytes(b'checkpoint')
            status = m.external_dependency_status(checkpoint, cuda_available=True)
        self.assertEqual(status, {'status': 'ready', 'missing': []})


if __name__ == '__main__':
    unittest.main()
