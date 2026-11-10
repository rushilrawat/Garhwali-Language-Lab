import json
import unittest

import yaml

import prepare_hf_additive_upload as m


def card(configs, info, body='# Card\n'):
    lines = ['---', 'license: other', 'configs:']
    for name, path in configs:
        lines += [f'- config_name: {name}', '  data_files:', '  - split: train', f'    path: {path}']
    lines.append('dataset_info: ' + json.dumps(info, separators=(',', ':')))
    return '\n'.join(lines) + '\n---\n' + body


NEW = card(
    [('text', 'releases/v0.2.9/data/text/train-*.jsonl')],
    [{'config_name': 'text', 'features': [{'name': 'text', 'dtype': 'string'}]}],
    body='# Card v0.2.9\n',
)
LIVE = card(
    [('text', 'releases/v0.2.7/data/text/train-*.jsonl'),
     ('screened_meta_gbm', 'releases/v0.2.8/data/screened_meta_gbm/train-00000.jsonl'),
     ('legacy_root', 'data/legacy/train.jsonl')],
    [{'config_name': 'text', 'features': []},
     {'config_name': 'screened_meta_gbm', 'features': [{'name': 'id', 'dtype': 'string'}]}],
)


class CarryForwardTests(unittest.TestCase):
    def front(self, text):
        return yaml.safe_load(text.split('\n---\n', 1)[0][4:])

    def test_keeps_configs_from_earlier_release_prefixes(self):
        merged, carried = m.carry_forward_configs(NEW, LIVE, 'releases/v0.2.9')
        self.assertEqual(carried, ['screened_meta_gbm'])
        meta = self.front(merged)
        self.assertEqual([c['config_name'] for c in meta['configs']], ['text', 'screened_meta_gbm'])
        self.assertEqual(meta['configs'][1]['data_files'][0]['path'],
                         'releases/v0.2.8/data/screened_meta_gbm/train-00000.jsonl')
        self.assertEqual([e['config_name'] for e in meta['dataset_info']], ['text', 'screened_meta_gbm'])
        self.assertTrue(merged.endswith('# Card v0.2.9\n'))

    def test_new_card_versions_win_and_root_paths_are_not_carried(self):
        _, carried = m.carry_forward_configs(NEW, LIVE, 'releases/v0.2.9')
        self.assertNotIn('text', carried)
        self.assertNotIn('legacy_root', carried)

    def test_nothing_to_carry_returns_card_unchanged(self):
        merged, carried = m.carry_forward_configs(NEW, NEW, 'releases/v0.2.9')
        self.assertEqual((merged, carried), (NEW, []))


if __name__ == '__main__':
    unittest.main()
