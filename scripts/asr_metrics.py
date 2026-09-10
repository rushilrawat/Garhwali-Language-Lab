#!/usr/bin/env python3
"""Dependency-free normalization and WER/CER metrics for ASR evaluation."""
import re
import unicodedata


def normalize(text):
    value = unicodedata.normalize('NFC', text).casefold()
    value = ''.join(' ' if unicodedata.category(char).startswith(('P', 'S')) else char for char in value)
    return re.sub(r'\s+', ' ', value).strip()


def edit_distance(reference, hypothesis):
    previous = list(range(len(hypothesis) + 1))
    for index, left in enumerate(reference, 1):
        current = [index]
        for other, right in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[other] + 1,
                               previous[other - 1] + (left != right)))
        previous = current
    return previous[-1]


def score(reference, hypothesis):
    ref = normalize(reference); hyp = normalize(hypothesis)
    ref_words, hyp_words = ref.split(), hyp.split()
    word_errors = edit_distance(ref_words, hyp_words)
    character_errors = edit_distance(list(ref.replace(' ', '')), list(hyp.replace(' ', '')))
    reference_characters = len(ref.replace(' ', ''))
    return {
        'word_errors': word_errors, 'reference_words': len(ref_words),
        'wer': word_errors / max(1, len(ref_words)),
        'character_errors': character_errors, 'reference_characters': reference_characters,
        'cer': character_errors / max(1, reference_characters),
    }
