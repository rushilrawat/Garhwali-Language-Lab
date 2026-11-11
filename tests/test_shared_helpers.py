"""Guard against re-adding local copies of the shared garhwali_lab helpers."""

import ast
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
SHARED = {'sha256_bytes', 'sha256_text', 'sha256_file'}


class SharedHelperTests(unittest.TestCase):
    def test_hash_helpers_are_imported_not_redefined(self):
        offenders = []
        for path in sorted(SCRIPTS.rglob('*.py')):
            if 'garhwali_lab' in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in SHARED:
                    offenders.append(f'{path.relative_to(SCRIPTS)}:{node.lineno} {node.name}')
        self.assertEqual(
            offenders, [],
            'import these from garhwali_lab.hashing instead of redefining them',
        )


if __name__ == '__main__':
    unittest.main()
