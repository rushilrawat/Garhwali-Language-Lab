"""Bundle the existing reference-labeled VAANI split for a private Kaggle input."""

import sys
from pathlib import Path as _Path

# Shared modules (garhwali_lab, metrics, manifests) live one level up in scripts/.
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))


import csv
import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPLITS = ROOT / "data/processed/model_ready/splits/asr"
OUT = ROOT / "data/kaggle/garhwali-asr-reference-v0.1.zip"


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    audio = {}
    for split in ("train", "validation", "test"):
        with (SPLITS / f"{split}.jsonl").open(encoding="utf-8") as stream:
            for line in stream:
                source = json.loads(line)
                digest = source["audio_sha256"]
                path = ROOT / source["local_audio_path"]
                if not path.is_file():
                    raise FileNotFoundError(path)
                audio[digest] = path
                rows.append({
                    "split": split,
                    "audio_file": f"audio/{digest}.wav",
                    "audio_sha256": digest,
                    "transcript": source["asr_target_clean"],
                    "duration_seconds": source["duration_seconds"],
                })
    if len(audio) != len(rows):
        raise ValueError("Duplicate audio hashes in the selected split")
    import io
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        archive.writestr("manifest.csv", buffer.getvalue())
        archive.writestr("ATTRIBUTION.md", "Source: ARTPARK-IISc/Vaani, Garhwali reference-transcribed clips; CC BY 4.0. This is a subset of existing public audio and adds no new recordings or labels. Split manifests were generated locally with speaker-disjoint train/validation/test groups. Dataset source: https://huggingface.co/datasets/ARTPARK-IISc/Vaani\n")
        for digest, path in audio.items():
            archive.write(path, f"audio/{digest}.wav")
    sha = hashlib.sha256()
    with OUT.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    print(json.dumps({"output": str(OUT), "bytes": OUT.stat().st_size, "sha256": sha.hexdigest(), "rows": len(rows), "split_counts": {split: sum(r["split"] == split for r in rows) for split in ("train", "validation", "test")}}))


if __name__ == "__main__":
    main()
