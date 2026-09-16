import tempfile
import tarfile
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
        self.assertEqual(plan['base_checkpoint']['bytes'], 1796208640)
        self.assertEqual(plan['base_checkpoint']['availability'], 'official_direct_download')
        self.assertEqual(plan['cloud_job']['hardware'], 'l4x1')
        self.assertEqual(plan['cloud_job']['timeout_hours'], 6)
        self.assertEqual(plan['cloud_job']['maximum_compute_cost_usd'], 4.8)

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

    def test_checkpoint_validation_requires_exact_size_and_tar_structure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / 'weights.bin'
            payload.write_bytes(b'weights')
            checkpoint = root / 'model.nemo'
            with tarfile.open(checkpoint, 'w') as archive:
                archive.add(payload, arcname='model_weights.ckpt')
            result = m.validate_checkpoint_file(
                checkpoint, expected_bytes=checkpoint.stat().st_size
            )
            self.assertEqual(result['bytes'], checkpoint.stat().st_size)
            self.assertTrue(result['tar_valid'])
            with self.assertRaises(ValueError):
                m.validate_checkpoint_file(
                    checkpoint, expected_bytes=checkpoint.stat().st_size + 1
                )


if __name__ == '__main__':
    unittest.main()
