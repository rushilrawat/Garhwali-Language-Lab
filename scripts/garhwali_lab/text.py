"""The project's two text-normalization policies.

* ``clean_text`` is for **stored** text. It applies Unicode NFC and collapses
  whitespace, so distinct characters (including compatibility forms) are kept
  exactly as the source wrote them.
* ``match_key`` is for **comparison**: deduplication, overlap and leakage
  checks, and train/test grouping. It applies NFKC, case folding, and
  whitespace collapsing, so visually equivalent strings compare equal.

Never store a ``match_key`` value as text, and never compare stored text for
equality without passing both sides through ``match_key``.
"""

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")


def clean_text(text: object) -> str:
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFC", str(text))).strip()


def match_key(text: object) -> str:
    return _WHITESPACE.sub(" ", unicodedata.normalize("NFKC", str(text)).casefold()).strip()


def content_key(text: object) -> str:
    """Identity key for deduplication: NFKC, casefold, keep letters, marks, digits.

    Combining marks are kept, so Devanagari words that differ only by a vowel
    sign (for example काम "work" and कम "less") stay distinct.
    """
    folded = unicodedata.normalize("NFKC", str(text or "")).casefold()
    return "".join(char for char in folded if unicodedata.category(char)[0] in {"L", "M", "N"})


def leakage_key(text: object) -> str:
    """Deliberately loose key for train/test leakage and overlap guards.

    Keeps only ``str.isalnum()`` characters, which drops Devanagari vowel signs
    and viramas. Different texts can therefore collide (on the October 2026
    segment corpus, about 1.3% of distinct texts share a key with another
    text). That is the intended trade-off for guards: a false match only costs
    a row its eligibility, while a missed match would leak evaluation data.
    Never use this key to drop or merge records.
    """
    folded = unicodedata.normalize("NFKC", str(text or "")).casefold()
    return "".join(char for char in folded if char.isalnum())
