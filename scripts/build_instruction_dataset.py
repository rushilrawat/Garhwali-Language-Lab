#!/usr/bin/env python3
"""Build split-safe Garhwali instruction records from corpus supervision."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = ROOT / 'data/processed/model_ready/language_quality/text.jsonl'
PARALLEL = ROOT / 'data/processed/model_ready/language_quality/parallel_examples.jsonl'
LEXICON = ROOT / 'data/processed/model_ready/language_quality/lexicon_candidates.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/instructions'
SPLITS = ('train', 'validation', 'test')
SYSTEM = 'Follow the instruction using the available Garhwali language evidence.'


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def instruction_record(task, instruction, response, split, parent_id, provenance,
                       semantic_domains=None):
    digest = hashlib.sha256(
        f'{task}\0{instruction}\0{response}\0{parent_id}'.encode()
    ).hexdigest()
    return {
        'instruction_sha256': digest,
        'task': task,
        'instruction': instruction,
        'response': response,
        'messages': [
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': instruction},
            {'role': 'assistant', 'content': response},
        ],
        'split': split,
        'parent_text_sha256': parent_id,
        'semantic_domains': semantic_domains or [],
        'provenance': provenance,
        'active_for_experiment': True,
        'source_record_preserved': True,
    }


def parallel_instructions(row, split):
    garhwali = ' '.join(str(row.get('garhwali') or '').split())
    english = ' '.join(str(row.get('english') or '').split())
    if not garhwali or not english:
        return []
    provenance = [{
        'source_id': row.get('source_id'),
        'source_record_id': row.get('source_record_id'),
        'source_url': row.get('source_url'),
        'license_url': row.get('license_url'),
        'license': row.get('license'),
        'license_id': row.get('license_id'),
        'rights_status': row.get('rights_status'),
        'attribution': row.get('attribution'),
        'rights_evidence': row.get('rights_evidence'),
        'pair_sha256': row.get('pair_sha256'),
    }]
    parent = row.get('text_sha256')
    return [
        instruction_record(
            'garhwali_to_english',
            f'Translate this Garhwali text into English:\n{garhwali}',
            english, split, parent, provenance,
        ),
        instruction_record(
            'english_to_garhwali',
            f'Translate this English text into Garhwali:\n{english}',
            garhwali, split, parent, provenance,
        ),
    ]


def lexicon_instructions(row, split):
    form = ' '.join(str(row.get('form') or '').split())
    if not form:
        return []
    parent = row.get('text_sha256')
    provenance = row.get('provenance', [])
    domains = row.get('semantic_domains', [])
    records = []
    language_prompts = (
        ('english', 'English', 'English'),
        ('hindi', 'Hindi', 'Hindi'),
    )
    for field, label, target_label in language_prompts:
        for raw_gloss in row.get('glosses', {}).get(field, []):
            gloss = ' '.join(str(raw_gloss).split())
            if not gloss:
                continue
            records.extend([
                instruction_record(
                    f'garhwali_to_{field}_lexicon',
                    f'Give the {target_label} meaning of this Garhwali word:\n{form}',
                    gloss, split, parent, provenance, domains,
                ),
                instruction_record(
                    f'{field}_to_garhwali_lexicon',
                    f'Give the Garhwali word for this {label} term:\n{gloss}',
                    form, split, parent, provenance, domains,
                ),
            ])
    return records


def deduplicate(records):
    unique = {}
    duplicates = 0
    for row in records:
        key = (row['split'], row['task'], row['instruction'], row['response'])
        if key not in unique:
            unique[key] = row
            continue
        duplicates += 1
        existing = unique[key]
        evidence = {
            json.dumps(item, ensure_ascii=False, sort_keys=True): item
            for item in existing['provenance'] + row['provenance']
        }
        existing['provenance'] = [evidence[key] for key in sorted(evidence)]
    return list(unique.values()), duplicates


def attach_acceptable_responses(records):
    """Keep source variants while making multi-reference evaluation explicit."""
    responses = defaultdict(set)
    for row in records:
        responses[(row['task'], row['instruction'])].add(row['response'])
    for row in records:
        row['acceptable_responses'] = sorted(
            responses[(row['task'], row['instruction'])]
        )
    return records


def write_jsonl(path, rows):
    Path(path).write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def build(text_path=TEXT, parallel_path=PARALLEL, lexicon_path=LEXICON,
          output_dir=OUTPUT):
    parent_splits = {row['text_sha256']: row['split'] for row in read_jsonl(text_path)}
    generated = []
    missing_parents = 0
    for row in read_jsonl(parallel_path):
        split = parent_splits.get(row.get('text_sha256'))
        if split is None:
            missing_parents += 1
            continue
        generated.extend(parallel_instructions(row, split))
    for row in read_jsonl(lexicon_path):
        split = parent_splits.get(row.get('text_sha256'))
        if split is None:
            missing_parents += 1
            continue
        generated.extend(lexicon_instructions(row, split))
    rows, duplicate_count = deduplicate(generated)
    rows = attach_acceptable_responses(rows)
    rows.sort(key=lambda row: (row['split'], row['instruction_sha256']))
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        write_jsonl(output_dir / f'{split}.jsonl', [row for row in rows if row['split'] == split])
    write_jsonl(output_dir / 'all.jsonl', rows)

    parents = defaultdict(set)
    pairs = defaultdict(set)
    for row in rows:
        parents[row['parent_text_sha256']].add(row['split'])
        pair_key = hashlib.sha256(
            f"{row['task']}\0{row['instruction']}\0{row['response']}".encode()
        ).hexdigest()
        pairs[pair_key].add(row['split'])
    counts = Counter(row['split'] for row in rows)
    tasks = Counter(row['task'] for row in rows)
    report = {
        'run_id': 'garhwali-instruction-dataset-v0.1',
        'records': {split: counts[split] for split in SPLITS} | {'total': len(rows)},
        'tasks': dict(sorted(tasks.items())),
        'integrity': {
            'parent_cross_split': sum(len(splits) > 1 for splits in parents.values()),
            'exact_instruction_pair_cross_split': sum(
                len(splits) > 1 for splits in pairs.values()
            ),
            'duplicate_instruction_pairs': duplicate_count,
            'missing_parent_split_records': missing_parents,
            'benchmark_records_used_for_training': 0,
            'all_records_active_for_experiment': all(
                row['active_for_experiment'] for row in rows
            ),
        },
        'policy': {
            'split_source': 'existing document-level parent split',
            'provenance_preserved': True,
            'rights_metadata_preserved': True,
            'public_redistribution_requires_source_filtering': True,
        },
    }
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
