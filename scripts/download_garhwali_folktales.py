#!/usr/bin/env python3
"""Archive the public Garhwali Folktales RSS feed and its audio enclosures."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "downloads" / "folklore" / "podcast"
FEED_URL = "https://anchor.fm/s/3c077010/podcast/rss"


def safe_name(text: str) -> str:
    text = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE).strip("_")
    return text[:100] or "episode"


def curl(url: str, destination: Path) -> None:
    subprocess.run(
        [
            "curl", "-k", "-L", "--fail", "--retry", "4",
            "--retry-all-errors", "-C", "-", url, "-o", str(destination),
        ],
        check=True,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    feed_path = OUT / "feed.xml"
    curl(FEED_URL, feed_path)
    channel = ET.parse(feed_path).getroot().find("channel")
    if channel is None:
        raise RuntimeError("RSS channel missing")

    records = []
    for index, item in enumerate(channel.findall("item"), start=1):
        title = item.findtext("title") or f"episode-{index}"
        enclosure = item.find("enclosure")
        if enclosure is None or not enclosure.get("url"):
            continue
        url = enclosure.get("url")
        suffix = Path(url.split("?", 1)[0]).suffix or ".mp3"
        destination = OUT / f"{index:03d}_{safe_name(title)}{suffix}"
        curl(url, destination)
        records.append(
            {
                "position": index,
                "title": title,
                "published": item.findtext("pubDate"),
                "guid": item.findtext("guid"),
                "source_url": url,
                "local_file": destination.name,
                "bytes": destination.stat().st_size,
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "rights_status": "publicly_downloadable_creator_copyright",
                "training_eligible": False,
            }
        )

    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "title": channel.findtext("title"),
                "feed_url": FEED_URL,
                "rights_status": "publicly_downloadable_creator_copyright",
                "storage": "gitignored raw archive",
                "episodes": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Archived {len(records)} episodes ({sum(r['bytes'] for r in records)} bytes)")


if __name__ == "__main__":
    main()
