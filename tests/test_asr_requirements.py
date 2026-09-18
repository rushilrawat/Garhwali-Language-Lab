import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AsrRequirementsTests(unittest.TestCase):
    def test_sravaani_tokenizer_dependency_is_pinned(self):
        requirements = (ROOT / 'requirements-asr.txt').read_text(encoding='utf-8').splitlines()
        self.assertIn('sentencepiece==0.2.2', requirements)


if __name__ == '__main__':
    unittest.main()
