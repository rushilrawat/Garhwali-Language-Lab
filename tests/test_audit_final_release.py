import json
import hashlib
import tempfile
import unittest
from pathlib import Path

import audit_final_release as m


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8'
    )


class FinalReleaseAuditTests(unittest.TestCase):
    def benchmark_fixture(self, root):
        text_eval = [{'text': 'गढ़वाली वाक्य', 'id': 'eval-text'}]
        asr_eval = [{'audio_sha256': 'held-out-audio', 'speaker_id': 'held-out-speaker'}]
        text_train = [{'text': 'प्रशिक्षण वाक्य'}]
        asr_train = [{'audio_sha256': 'train-audio', 'speaker_id': 'train-speaker'}]
        asr_validation = [{'audio_sha256': 'validation-audio', 'speaker_id': 'validation-speaker'}]
        artifacts = {
            'data/processed/evaluation/garhwali_bench/internal_text.jsonl': text_eval,
            'data/processed/model_ready/splits/evaluation/asr_candidate.jsonl': asr_eval,
            'data/processed/model_ready/splits/text/train.jsonl': text_train,
            'data/processed/model_ready/splits/asr/train.jsonl': asr_train,
            'data/processed/model_ready/splits/asr/validation.jsonl': asr_validation,
            'data/processed/evaluation/garhwali_bench/benchmarks/flores.jsonl': [{'source': 'hello'}],
            'data/processed/evaluation/garhwali_bench/benchmarks/crosssum.jsonl': [{'source': 'story'}],
            'data/processed/evaluation/garhwali_bench/benchmarks/xorqa.jsonl': [{'question': 'what?'}],
        }
        expected = {}
        for relative, rows in artifacts.items():
            path = root / relative
            write_jsonl(path, rows)
            expected[relative] = {
                'path': relative,
                'records': len(rows),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        manifest = {
            'records': {'text_evaluation': 1, 'asr_evaluation': 1},
            'internal_evaluation': {
                'text': expected['data/processed/evaluation/garhwali_bench/internal_text.jsonl'],
                'asr': expected['data/processed/model_ready/splits/evaluation/asr_candidate.jsonl'],
            },
            'tasks': {
                'flores': {**expected['data/processed/evaluation/garhwali_bench/benchmarks/flores.jsonl'], 'usage': 'evaluation_only', 'schema_errors': 0},
                'crosssum': {**expected['data/processed/evaluation/garhwali_bench/benchmarks/crosssum.jsonl'], 'usage': 'evaluation_only', 'schema_errors': 0},
                'xorqa': {**expected['data/processed/evaluation/garhwali_bench/benchmarks/xorqa.jsonl'], 'usage': 'evaluation_only', 'schema_errors': 0},
            },
        }
        path = root / 'data/processed/evaluation/garhwali_bench/manifest.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest), encoding='utf-8')
        return root

    def test_benchmark_audit_recomputes_hashes_counts_and_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.benchmark_fixture(Path(directory))
            report = m.audit_benchmark(root)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['artifact_failures'], 0)
        self.assertEqual(report['leakage']['internal_text_exact_train_text'], 0)
        self.assertEqual(report['leakage']['asr_audio_train_or_validation_overlap'], 0)
        self.assertEqual(report['leakage']['asr_speaker_train_or_validation_overlap'], 0)

    def test_benchmark_audit_rejects_changed_artifact_and_recomputes_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.benchmark_fixture(Path(directory))
            text_train = root / 'data/processed/model_ready/splits/text/train.jsonl'
            write_jsonl(text_train, [{'text': 'गढ़वाली वाक्य'}])
            changed = root / 'data/processed/evaluation/garhwali_bench/internal_text.jsonl'
            write_jsonl(changed, [{'text': 'गढ़वाली वाक्य'}])
            asr_train = root / 'data/processed/model_ready/splits/asr/train.jsonl'
            write_jsonl(asr_train, [{'audio_sha256': 'held-out-audio', 'speaker_id': 'held-out-speaker'}])
            report = m.audit_benchmark(root)
        self.assertEqual(report['status'], 'failed')
        self.assertGreaterEqual(report['artifact_failures'], 1)
        self.assertEqual(report['leakage']['internal_text_exact_train_text'], 1)
        self.assertEqual(report['leakage']['asr_audio_train_or_validation_overlap'], 1)
        self.assertEqual(report['leakage']['asr_speaker_train_or_validation_overlap'], 1)

    def fixture(self, root):
        configs = {}
        provenance = [{
            'source_url': 'https://example.org/source',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'license_id': 'CC-BY-4.0',
            'attribution': 'Test source',
            'iso_639_3': 'gbm',
            'source_id': 'test-source',
        }]
        knowledge = lambda record_id, family: {
            'id': record_id,
            'knowledge_family': family,
            'provenance': provenance,
            'public_rights_basis': provenance,
            'quality_metadata': {
                'review_status': 'source_verified', 'native_reviewed': True,
            },
            'rights_status': 'CC-BY-4.0',
        }
        text_ids = {
            text: hashlib.sha256(text.encode('utf-8')).hexdigest()
            for text in ('अ', 'ब', 'क')
        }
        rows = {
            'text/train': [{'id': text_ids['अ'], 'text': 'अ', 'language': 'gbm', 'source_languages': ['gbm'], 'provenance': provenance, 'language_buckets': ['garhwali_candidate'], 'quality_tiers': ['strict_gold_candidate'], 'quality_flags': [], 'public_rights_basis': provenance, 'recommended_for_training': True}],
            'text/validation': [{'id': text_ids['ब'], 'text': 'ब', 'language': 'gbm', 'source_languages': ['gbm'], 'provenance': provenance, 'language_buckets': ['garhwali_candidate'], 'quality_tiers': ['strict_gold_candidate'], 'quality_flags': [], 'public_rights_basis': provenance, 'recommended_for_training': True}],
            'text/test': [{'id': text_ids['क'], 'text': 'क', 'language': 'gbm', 'source_languages': ['gbm'], 'provenance': provenance, 'language_buckets': ['garhwali_candidate'], 'quality_tiers': ['strict_gold_candidate'], 'quality_flags': [], 'public_rights_basis': provenance, 'recommended_for_training': True}],
            'asr/train': [{'audio': 'audio/audio-a.wav', 'audio_sha256': 'audio-a', 'speaker_id': 'speaker-a', 'transcript': 'अ', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'asr/validation': [{'audio': 'audio/audio-b.wav', 'audio_sha256': 'audio-b', 'speaker_id': 'speaker-b', 'transcript': 'ब', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'asr/test': [{'audio': 'audio/audio-c.wav', 'audio_sha256': 'audio-c', 'speaker_id': 'speaker-c', 'transcript': 'क', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'sravaani_drafts/train': [{'audio': 'audio/draft-a.wav', 'audio_sha256': 'draft-a', 'transcript': '', 'training_eligible': False, 'experimental_training_eligible': True, 'machine_transcript_quality': {'level': 'high_risk'}}],
            'lexicon/train': [{
                'form': 'अ', 'provenance': provenance,
                'form_sha256': hashlib.sha256('अ'.encode()).hexdigest(),
            }],
            'instructions/train': [{'instruction': 'a', 'response': 'b', 'acceptable_responses': ['b'], 'provenance': provenance}],
            'instructions/validation': [{'instruction': 'c', 'response': 'd', 'acceptable_responses': ['d'], 'provenance': provenance}],
            'instructions/test': [{'instruction': 'e', 'response': 'f', 'acceptable_responses': ['f'], 'provenance': provenance}],
            'catalog/train': [
                {'id': text_ids['अ'], 'text_sha256': text_ids['अ'], 'text': 'अ', 'sources': provenance,
                 'release_text_sha256': text_ids['अ']},
                {'id': text_ids['ब'], 'text_sha256': text_ids['ब'], 'text': None, 'redaction_reason': 'rights_pending', 'sources': provenance},
                {'id': text_ids['क'], 'text_sha256': text_ids['क'], 'text': 'क', 'sources': provenance,
                 'release_text_sha256': text_ids['क']},
            ],
            'geography/train': [knowledge('place-a', 'geography')],
            'historical_terms/train': [knowledge('term-a', 'historical_terms')],
            'literary_people/train': [knowledge('person-a', 'literary_people')],
            'literary_works/train': [knowledge('work-a', 'literary_works')],
            'popular_songs/train': [knowledge('song-a', 'popular_songs')],
            'university_research/train': [knowledge('research-a', 'university_research')],
        }
        for key, content in rows.items():
            config, split = key.split('/')
            name = f'{split}-00000.jsonl'
            shard_path = root / 'data' / config / name
            write_jsonl(shard_path, content)
            configs[key] = {
                'files': [name], 'records': len(content), 'shards': 1,
                'file_sha256': {name: hashlib.sha256(shard_path.read_bytes()).hexdigest()},
            }
        manifest = {
            'release_id': 'candidate',
            'profile': 'public',
            'configs': configs,
            'draft_queue_records': 1,
            'draft_records': 1,
            'draft_unique_audio': 1,
            'draft_inherited_duplicate_rows': 0,
            'draft_source_label_conflicts': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_third_checkpoint_records': 0,
            'draft_audio_grounded_review_records': 0,
            'drafts_complete': True,
            'include_audio': False,
        }
        (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        index = {
            'release_id': 'candidate',
            'status': 'integrated_experimental_release',
            'text': {'total': 3, 'splits': {'train': 1, 'validation': 1, 'test': 1}},
            'speech': {
                'total': 3,
                'splits': {'train': 1, 'validation': 1, 'test': 1},
                'strict_comparison_rows': 3,
            },
            'leakage': {'text_hash_cross_split': 0, 'identified_speaker_cross_split': 0},
            'speech_baseline_comparison': {
                'sravaani_draft_rows': 1,
                'sravaani_draft_unique_audio': 1,
                'sravaani_draft_inherited_duplicate_rows': 0,
            },
        }
        return index

    def test_accepts_complete_package_and_reports_draft_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = m.audit(self.fixture(root), root)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['drafts']['empty_transcripts'], 1)
        self.assertIn('audio_not_included', report['warnings'])

    def test_public_audit_allows_structured_configs_to_be_filtered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            for family in m.KNOWLEDGE_GROUPS:
                (root / 'data' / family / 'train-00000.jsonl').unlink()
                manifest['configs'].pop(f'{family}/train')
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['structured_knowledge']['records'], 0)
        self.assertEqual(report['structured_knowledge']['configs'], [])

    def test_accepts_explicit_open_basis_with_blocked_mirror_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/text/train-00000.jsonl'
            row = json.loads(path.read_text())
            open_source = row['provenance'][0]
            row['provenance'].append({
                'license_id': 'CC-BY-4.0',
                'iso_639_3': 'gbm',
                'rights_status': 'component_rights_review_required',
            })
            row['public_rights_basis'] = [open_source]
            write_jsonl(path, [row])
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['configs']['text/train']['file_sha256']['train-00000.jsonl'] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['provenance']['public_rights_failures'], 0)
        self.assertEqual(report['provenance']['text_language_scope_failures'], 0)

    def test_rejects_shard_mismatch_and_split_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/text/test-00000.jsonl'
            write_jsonl(path, [{'id': hashlib.sha256('अ'.encode()).hexdigest(), 'text': 'अ', 'language': 'gbm'}])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('text IDs overlap across train and test', report['errors'])
        self.assertIn('text/test has 1 rows without provenance', report['errors'])
        self.assertTrue(any('shard hash mismatch' in error for error in report['errors']))

    def test_rejects_forged_shard_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['configs']['text/train']['file_sha256']['train-00000.jsonl'] = '0' * 64
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            report = m.audit(index, root)
        self.assertIn('text/train shard hash mismatch: train-00000.jsonl', report['errors'])

    def test_recomputes_text_id_from_exported_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/text/train-00000.jsonl'
            row = json.loads(path.read_text())
            row['id'] = '0' * 64
            write_jsonl(path, [row])
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['configs']['text/train']['file_sha256']['train-00000.jsonl'] = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            report = m.audit(index, root)
        self.assertIn(
            'text/train has 1 text IDs that do not match SHA-256 of exported text',
            report['errors'],
        )

    def test_rejects_duplicate_knowledge_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/geography/train-00000.jsonl'
            write_jsonl(path, [
                {'id': 'place-a', 'knowledge_family': 'geography'},
                {'id': 'place-a', 'knowledge_family': 'geography'},
            ])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('geography contains a missing or duplicate stable ID', report['errors'])

    def test_rejects_knowledge_without_quality_or_public_rights_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/geography/train-00000.jsonl'
            row = json.loads(path.read_text())
            row.pop('quality_metadata')
            row.pop('public_rights_basis')
            write_jsonl(path, [row])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('geography/train has 1 rows without quality metadata', report['errors'])
        self.assertIn('geography/train has 1 rows without compatible public rights', report['errors'])
        self.assertEqual(report['provenance']['knowledge_public_rights_failures'], 1)
        self.assertEqual(report['provenance']['public_rights_failures'], 0)

    def test_rejects_knowledge_provenance_with_only_an_internal_source_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/geography/train-00000.jsonl'
            row = json.loads(path.read_text())
            row['provenance'] = [{'source_id': 'unmapped-source'}]
            write_jsonl(path, [row])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            'geography/train has 1 rows with source IDs but no source URL or captured-source locator',
            report['errors'],
        )
        self.assertEqual(report['provenance']['knowledge_source_untraceable_rows'], 1)

    def test_rejects_unhandled_public_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['configs']['unknown/train'] = {
                'files': ['train-00000.jsonl'], 'records': 1, 'shards': 1,
            }
            manifest_path.write_text(json.dumps(manifest))
            write_jsonl(root / 'data/unknown/train-00000.jsonl', [{'id': 'x'}])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('unexpected configs: unknown/train', report['errors'])

    def test_rejects_instruction_prompt_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/instructions/test-00000.jsonl'
            write_jsonl(path, [{
                'instruction': '  A  ', 'response': 'z',
                'acceptable_responses': ['z'],
                'provenance': [{
                    'license_url': 'https://creativecommons.org/licenses/by/4.0/',
                    'license_id': 'CC-BY-4.0',
                    'attribution': 'Test source',
                    'iso_639_3': 'gbm',
                }],
            }])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            'instruction prompts overlap across train and test', report['errors']
        )

    def test_rejects_text_without_quality_admission_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/text/train-00000.jsonl'
            row = json.loads(path.read_text())
            row.pop('recommended_for_training')
            write_jsonl(path, [row])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            'text/train has 1 rows without language/quality admission metadata',
            report['errors'],
        )

    def test_rejects_training_recommendation_for_non_garhwali_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/text/train-00000.jsonl'
            row = json.loads(path.read_text())
            row['language'] = 'mul'
            write_jsonl(path, [row])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            'text/train has 1 training recommendation flags that disagree with Garhwali, quality, and public-rights evidence',
            report['errors'],
        )

    def test_rejects_eligible_row_incorrectly_marked_ineligible(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/text/train-00000.jsonl'
            row = json.loads(path.read_text())
            row['recommended_for_training'] = False
            write_jsonl(path, [row])
            report = m.audit(index, root)
        self.assertIn(
            'text/train has 1 training recommendation flags that disagree with Garhwali, quality, and public-rights evidence',
            report['errors'],
        )

    def test_requires_every_audio_file_when_audio_is_included(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['include_audio'] = True
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('4 referenced audio files are missing', report['errors'])

    def test_rejects_source_conflict_as_garhwali_training_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            write_jsonl(path, [{
                'audio_sha256': 'draft-a',
                'transcript': 'বাংলা পাঠ',
                'training_eligible': False,
                'experimental_training_eligible': True,
                'machine_transcript_quality': {'level': 'high_risk'},
                'language_scope_status': 'source_label_conflict',
                'active_for_source_error_analysis': True,
            }])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 source-label conflict drafts are marked as Garhwali training data',
            report['errors'],
        )

    def test_rejects_unsupported_recovery_accuracy_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]['recovery_adjudication'] = {
                'automatic_correction': True,
                'human_reference_available': False,
                'supervised_training_eligible': False,
                'recommended_for_machine_label_training': False,
                'original_transcript_preserved': True,
            }
            write_jsonl(path, rows)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['draft_three_checkpoint_review_records'] = 1
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 recovery adjudications make an unsupported training or accuracy claim',
            report['errors'],
        )

    def test_rejects_calibrated_claim_for_third_checkpoint_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]['recovery_third_checkpoint'] = {
                'transcript': 'गढ़वळि पाठ',
                'confidence_is_calibrated': True,
                'human_reference_available': False,
            }
            write_jsonl(path, rows)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['draft_third_checkpoint_records'] = 1
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 third-checkpoint records make an unsupported confidence or reference claim',
            report['errors'],
        )

    def test_audio_grounded_review_must_remain_pending_human_listening(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]['audio_grounded_review'] = {
                'machine_audio_review_complete': True,
                'human_listening_review_required': False,
                'automatic_correction': False,
                'human_reference_available': False,
                'supervised_training_eligible': False,
                'recommended_for_machine_label_training': False,
                'original_transcript_preserved': True,
            }
            write_jsonl(path, rows)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['draft_audio_grounded_review_records'] = 1
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 audio-grounded reviews make an unsupported completion, training, or accuracy claim',
            report['errors'],
        )


if __name__ == '__main__':
    unittest.main()
