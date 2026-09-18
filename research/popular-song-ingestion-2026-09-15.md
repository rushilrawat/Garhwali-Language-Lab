# Garhwali popular-song ingestion — 2026-09-15

This pass adds a source-addressable popular-music layer for Garhwali. It starts
with the most widely cited Narendra Singh Negi songs and adds documented classics
associated with Jeet Singh Negi, Chander Singh Rahi, and the traditional Chaita
performance repertoire.

## What was added

- **30 metadata records** (**16 new in this update**), each with a stable `record_id`, title, artists,
  Garhwali language label, genre, popularity evidence, listening URL, theme
  summary, and rights status.
- **21 records include Narendra Singh Negi**, including *Thando Re Thando*, *Nauchami
  Naraina*, *Chali Bhai Motor Chali*, *Tehri Dubana Lagu*, and *Dharti Hamara
  Garhwala Ki*.
- The 16 newly added songs are *Hey Ramiye*, *Fwa Baga Re*, *Mera Aun Se*,
  *Sauna Ka Mahina*, *Bhol Jab Phir Raat Khulali*, *Dait Sanghaar*, *Tumari Maya
  Ma*, *Ghughuti Ghuraona Laigi*, *Teri Khud Teru Khyal*, *Chullu Jagandi Bagat
  Aayi*, *Naya Jamano Ka Chhoron*, *Maachhi Pani Si*, *Raimasi Ko Phool*,
  *Bhaiji Ku Byo*, *Aege Gindi Myala*, and *Rajula*.
- **Five lyric-source pointers** and **three meaning/translation pointers**. The
  catalog stores links and original summaries; it does not reproduce full lyric
  or translation bodies.
- **Six public caption checks**. The checked YouTube responses exposed no public
  timed-text track on 2026-09-15; the remaining 24 records are marked
  `not_checked`.

## Rights and data boundary

Public listening access is not a reuse license. This layer therefore preserves
all discovered song metadata and source URLs for research, while leaving modern
lyrics, third-party translations, and audio outside the tracked corpus until an
explicit compatible license or permission is documented. No audio was downloaded
and no full lyric or translation text was copied in this pass.

## Source evidence

- [eUttaranchal Narendra Singh Negi profile](https://www.euttarakhand.com/narendrasinghnegi)
  supplies the editorial ten-song starting list and listening links.
- [Narendra Singh Negi official YouTube channel](https://www.youtube.com/channel/UCl1oDpiuEzmcg6zyxh_1Now)
  and [Apple Music artist catalog](https://music.apple.com/us/artist/narendra-singh-negi/1188574932)
  provide artist and release metadata.
- [T-Series Regional: Dharti Hamara Garhwala Ki](https://www.youtube.com/watch?v=TzcHbGNO_Vs)
  and [Jeet Singh Negi remembrance](https://www.amarujala.com/dehradun/uttarakhand-famous-garhwali-folk-singer-and-artist-jeet-singh-negi-passed-away)
  support classic and label-upload attribution.
- [Amit Saagar: Chaita Ki Chaitwali](https://www.youtube.com/watch?v=QKCO0rAwSEI)
  documents the Anchari Jagar and Chait tradition recording.
- [T-Series Regional's Garhwali playlist](https://www.tseries.com/videos/tseriesregional/PL5D852955814668F8/JvjEM78D9Nw)
  provides official label pages for *Bhaiji Ku Byo*, *Naya Jamano Ka Chhoron*,
  *Maachhi Pani Si*, *Chullu Jagandi Bagat Aayi*, and related tracks.
- [Anahad Foundation's Raimasi Ko Phool](https://www.youtube.com/watch?v=qaPWQJXQmh0)
  provides a credited devotional folk recording and an English theme description.
- Lyric and meaning pointers are retained in
  [`garhwali-popular-song-catalog.json`](garhwali-popular-song-catalog.json).

## Reproduce

```bash
PYTHONPATH=scripts .venv/bin/python scripts/ingest_popular_songs.py
PYTHONPATH=scripts .venv/bin/python -m unittest tests.test_ingest_popular_songs
```

The generated `data/extracted/popular_songs/records.jsonl` and `report.json`
remain ignored by Git. The tracked catalog is the durable provenance and review
input for a later licensed lyric/transcript pass.
