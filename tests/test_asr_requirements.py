import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AsrRequirementsTests(unittest.TestCase):
    def test_sravaani_tokenizer_dependency_is_pinned(self):
        lines = (ROOT / 'requirements-asr.txt').read_text(encoding='utf-8').splitlines()
        # Lock lines look like "pkg==1.2.3 \\" followed by hash lines.
        pins = {line.split(' ')[0] for line in lines if line and not line[0].isspace() and not line.startswith('#')}
        self.assertIn('sentencepiece==0.2.2', pins)

    def test_asr_lock_includes_pyarrow(self):
        lines = (ROOT / 'requirements-asr.txt').read_text(encoding='utf-8').splitlines()
        self.assertTrue(any(line.startswith('pyarrow==') for line in lines))


if __name__ == '__main__':
    unittest.main()
