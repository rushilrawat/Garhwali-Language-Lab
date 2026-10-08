"""Small, dependency-free helpers shared by text training examples."""

from __future__ import annotations

import hashlib
import math


def is_recommended_training_row(row: dict) -> bool:
    """Read the Hub boolean or its CSV-exported string representation."""
    value = row.get("recommended_for_training")
    return value is True or str(value).strip().casefold() == "true"


def deterministic_train_dev_split(
    rows: list[dict], *, seed: int = 17, dev_fraction: float = 0.1
) -> tuple[list[dict], list[dict]]:
    """Split rows reproducibly by stable ID, preserving a stable output order.

    The returned development rows are a convenience for monitoring training
    loss. A record-level split does not make the result an independent
    benchmark or account for speaker/source-family overlap.
    """
    if len(rows) < 2:
        raise ValueError("at least two rows are required for a train/dev split")
    if not 0 < dev_fraction < 1:
        raise ValueError("dev_fraction must be strictly between 0 and 1")

    id_by_object = []
    seen_ids = set()
    for row in rows:
        value = row.get("id")
        if value is None or not str(value).strip() or str(value) in seen_ids:
            raise ValueError("rows must have a unique non-empty id")
        stable_id = str(value)
        seen_ids.add(stable_id)
        id_by_object.append((stable_id, row))

    dev_count = min(len(rows) - 1, max(1, math.ceil(len(rows) * dev_fraction)))
    ranked = sorted(
        id_by_object,
        key=lambda item: hashlib.sha256(f"{seed}\0{item[0]}".encode("utf-8")).digest(),
    )
    dev_ids = {stable_id for stable_id, _ in ranked[:dev_count]}
    train = sorted(
        (row for stable_id, row in id_by_object if stable_id not in dev_ids),
        key=lambda row: str(row["id"]),
    )
    development = sorted(
        (row for stable_id, row in id_by_object if stable_id in dev_ids),
        key=lambda row: str(row["id"]),
    )
    return train, development
