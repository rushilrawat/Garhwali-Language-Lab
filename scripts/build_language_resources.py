#!/usr/bin/env python3
"""Build deterministic Garhwali tokenizer, pronunciation, and TTS resources."""

import json
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = ROOT / 'data/processed/model_ready/splits/text/train.jsonl'
LEXICON = ROOT / 'data/processed/model_ready/language_quality/lexicon_candidates.jsonl'
AUDIO = ROOT / 'data/processed/model_ready/audio_normalized/manifests'
OUT = ROOT / 'data/processed/model_ready/language_resources'
SPLITS = ('train', 'validation', 'test')


def read_jsonl(path):
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def orthographic_units(text):
    units = []
    for char in text:
        if char.isspace():
            continue
        if units and (unicodedata.combining(char) or unicodedata.category(char).startswith('M') or units[-1].endswith('्')):
            units[-1] += char
        else:
            units.append(char)
    return units


def source_phonetic_segments(row):
    segments = []
    for provenance in row.get('provenance', []):
        value = provenance.get('linguistic_metadata', {}).get('segments')
        if isinstance(value, str):
            segments.extend(value.split())
        elif isinstance(value, list):
            segments.extend(str(item) for item in value if str(item).strip())
    return list(dict.fromkeys(segments))


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def build_resources(text_path=TEXT, lexicon_path=LEXICON, audio_dir=AUDIO, output_dir=OUT):
    training_texts = [
        row['text'] for row in read_jsonl(text_path)
        if row.get('split', 'train') == 'train' and str(row.get('text') or '').strip()
    ]
    character_counts = Counter()
    word_counts = Counter()
    for text in training_texts:
        normalized = ' '.join(unicodedata.normalize('NFC', text).split())
        character_counts.update('▁' if char.isspace() else char for char in normalized)
        word_counts.update(normalized.split())

    tokens = ['[PAD]', '[UNK]', '[BOS]', '[EOS]']
    tokens.extend(char for char, _ in sorted(character_counts.items(), key=lambda item: (-item[1], item[0])))
    tokenizer = {
        'type': 'unicode_character',
        'language': 'Garhwali (gbm)',
        'normalization': 'Unicode NFC and collapsed whitespace',
        'whitespace_token': '▁',
        'vocab': {token: index for index, token in enumerate(tokens)},
        'frequencies': dict(sorted(character_counts.items(), key=lambda item: (-item[1], item[0]))),
        'training_split_only': True,
    }
    tokenizer_dir = output_dir / 'tokenizer'
    tokenizer_dir.mkdir(parents=True, exist_ok=True)
    (tokenizer_dir / 'tokenizer.json').write_text(
        json.dumps(tokenizer, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    (tokenizer_dir / 'train.txt').write_text('\n'.join(training_texts) + '\n', encoding='utf-8')
    (tokenizer_dir / 'word_frequencies.json').write_text(
        json.dumps(dict(word_counts.most_common()), ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )

    pronunciations = []
    for row in read_jsonl(lexicon_path):
        form = str(row.get('form') or '').strip()
        source_segments = source_phonetic_segments(row)
        pronunciations.append({
            'text_sha256': row['text_sha256'],
            'form': form,
            'graphemes': orthographic_units(form),
            'source_phonetic_segments': source_segments,
            'pronunciation_status': (
                'source_phonetic_segments_unverified'
                if source_segments else 'grapheme_only_unverified'
            ),
            'experimental_training_eligible': True,
            'glosses': row.get('glosses', {}),
            'dialect_quality': row.get('dialect_quality', {}),
            'provenance': row.get('provenance', []),
        })
    pronunciations.sort(key=lambda row: row['text_sha256'])
    write_jsonl(output_dir / 'pronunciation/lexicon.jsonl', pronunciations)

    tts_counts = Counter()
    for split in SPLITS:
        rows = []
        for row in read_jsonl(audio_dir / f'{split}.jsonl'):
            rows.append({
                'audio_sha256': row['audio_sha256'],
                'derived_audio_sha256': row['derived_audio_sha256'],
                'audio': row['derived_audio_path'],
                'text': row['asr_target_clean'],
                'speaker_id': row['speaker_id'],
                'gender': row.get('gender'),
                'district': row.get('district'),
                'split': split,
                'license': row.get('license'),
                'review_status': 'automated_quality_screened',
                'experimental_training_eligible': True,
            })
        write_jsonl(output_dir / 'tts' / f'{split}.jsonl', rows)
        tts_counts[split] = len(rows)

    report = {
        'tokenizer_type': 'unicode_character',
        'tokenizer_training_texts': len(training_texts),
        'tokenizer_vocabulary_size': len(tokens),
        'word_types': len(word_counts),
        'pronunciation_candidates': len(pronunciations),
        'pronunciation_with_source_phonetics': sum(bool(row['source_phonetic_segments']) for row in pronunciations),
        'tts_pairs': sum(tts_counts.values()),
        'tts_split_pairs': dict(sorted(tts_counts.items())),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    return report


if __name__ == '__main__':
    print(json.dumps(build_resources(), ensure_ascii=False, indent=2, sort_keys=True))
