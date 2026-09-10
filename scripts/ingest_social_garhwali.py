#!/usr/bin/env python3
"""Build a provenance-rich seed corpus from public Garhwali social posts."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "extracted" / "social_garhwali"

SOURCES = [
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1h41ans",
        "title": "GARHWALI WORDS list #1",
        "content_type": "vocabulary_list",
        "text": """पानी = पाणी
फूल = फूल
काँटा = कांडो
रास्ता = बाटो
बच्चा = नौना
जानवर = जानबर
आँख = आंखी
मुंह = गिच्च
नाखून = नङ
क्योंकि = किलैकि
नाम = नौ
दिल = जिकुड़ि
टांग = खुट्टु
कान = कन्दूड़, कन्याल
गरदन = मौण
कुत्ता = कुकुर
चिड़िया = चखुलि, चखुल, चखुलु
मछली = माछि, माछु, मच्छि""",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1guz0u4",
        "title": "Pahari word of the day #1",
        "content_type": "word_with_example",
        "text": "Khud / खुद = to miss, to remember. Example: Me Uttarakhand ta khud chh.",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1gvpcyi",
        "title": "Pahari word of the day #2",
        "content_type": "word_with_example",
        "text": "Khoob / ख़ूब = good or fine. Example: Me khoob chh. Alternatives discussed: Me thik cha; me bhalu cha.",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1gx7wg7",
        "title": "Pahari word of the day #3",
        "content_type": "word_with_example",
        "text": "Kaans / कांस = young or younger. Example: Myaar bwe myaar baba batin kaans chh. The author requested correction.",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/tfgf22",
        "title": "An attempt to talk in Garhwali",
        "content_type": "conversation_examples",
        "text": """Te kaan chh, myaar Garhwali or Kumaoni bhulla?
Mil yakh Garhwali ma baat kari chh?
Me garhwali m bunu cho!
Mi theek chon bheji. Sab Raaji khushi.
Badiya dajyu! Our tum? Holik taiyari kas chal ryan?
Me bhi badiya chhu, holik taiyari bhi badiya chal ryan.
Bas meithe koi kumaoni sikhe dyava, myar byo kumaon m honu ch. Garhwali t mithe aand ch.
Theek cha bal.""",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1i79cz7",
        "title": "Proper original Garhwali/Kumaoni vocabulary — Tehriyali contribution",
        "content_type": "dialect_vocabulary",
        "dialect": "Tehriyali",
        "text": """Yakulaans = loneliness
Chyudhki = without making a sound, sneaking
Chidh = waterfall
Rawa = pool of water, usually below waterfalls
Gaadh / gadgera = river or waterbody
Syuli = pregnant woman
Kyarkha = farming land near water
Danda = mountain tops
Kantha = ridge
Chwaya = natural source of water
Dokhra = farm
Khadu = male sheep
Bhedu = female sheep
Bukhtya = male goat
Chenkha = goat child
Guldaar = leopard
Banka = beautiful
Baand = beautiful woman
Marsa / Baikh = man
Bairban / Kajyaan = woman
Shyeda = cross-eyed
Baangu = bent
Kulein = pine tree""",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1i79cz7",
        "title": "Proper original Garhwali/Kumaoni vocabulary — Rudraprayag contribution",
        "content_type": "dialect_vocabulary",
        "dialect": "Rudraprayag Garhwali",
        "text": """Pwatla = bird
Mandan = wave of dance
Rouns = good feeling in a romantic context
Libochi = instruction to cattle to go ahead
Gwiṇi = langur, uncertain
Bwe = mother
Baikh = men
Nona / Loda = boy; Noni / Lodi = girl
Masaan = goblin
Rautyelu = beautiful
Galwadi = cheeks
Bingaan / bingdun = to understand
Birala = cat
Fwangada = farm
Bhad = a physically and mentally powerful or brave person
Dagda / dagdiya = together, friend
Latu = simpleton
Rasyan = aroma
Dhadam = bang
Farkhi = slipped
Mo = family
Samhun = souvenir
Baduli = hiccup
Munaru = headache
Thulu = elder
Sular = trousers
Gwad = lock someone inside a room
Sagor = etiquette
Aachri = fairy
Birana = strangers
Chwi = talk or gossip
Jyeti maa = mother's sister
Phupu = father's sister
Mankhi = human
Hyun = snow
Bata = way
Myalu = loving
Chakki = much
Chyu = mushrooms
Siranu = pillow
Dida = elder brother
Bulha = tomorrow
Byali = yesterday
Por = last year
Parar = year before last
Kimla = aunt
Dhaaṇ = work
Unanediyo = yawn
Batyaṇ = yell
Seṇu = plain terrain
Giccha = mouth
Asuk = ill or a bad habit""",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1i79cz7",
        "title": "Proper original Garhwali/Kumaoni vocabulary — Devanagari contribution",
        "content_type": "dialect_vocabulary",
        "dialect": "Rudraprayag Garhwali",
        "text": """सेमन्या = नमस्ते
कज्याणी / घौरवाली = पत्नी
ज्यून = चंद्रमा
ज्यूण = जीना
मुंड / कपाळ = सिर
हिया = हृदय
भैजि = बड़ा भाई
भुल्ला = छोटा भाई
भुल्ली = छोटी बहन
दीदि = बड़ी बहन
बो / बोजी = भाभी
ब्वारी = बहू
छालू = हल्के रंग का
मठु मठु = धीरे-धीरे
हिटण = चलना""",
    },
    {
        "platform": "reddit",
        "url": "https://www.reddit.com/r/PahadiTalks/comments/1i79cz7",
        "title": "Proper original Garhwali/Kumaoni vocabulary — Bhilangna contribution",
        "content_type": "dialect_vocabulary",
        "dialect": "Tehri Garhwal, Bhilangna valley",
        "text": """Ring = घूमना
Aukhu = मुश्किल
Gaas = निवाला
Taata / niwatu = गरम
Neda naadi = पास-पास
Ghadyek = थोड़ी देर
Raibaar = सूचना
Jandira = देवता को पहनाने वाली माला
Unda funda = इधर-उधर
Ubba unda = ऊपर-नीचे
Pithon = परेशान करना
Bijen / kunkya / chakki = बहुत ज़्यादा
Garva = भारी
Isk = घिन आना
Kuchyan = घुसना
Junkha = कपड़े
Baatha = हिस्से का
Tip = उठाना
Atkan = भागना
Bashi = बोलता हुआ
Mundaru = सिरदर्द
Bathku = कटोरी
Sal = किसी चीज़ को ठीक करना
Paiti jawa = तैयार होना""",
    },
    {
        "platform": "youtube",
        "url": "https://www.youtube.com/watch?v=YnLS7qL8sfw",
        "title": "जंदरि क बान — उत्तराखंड की लोक कहानियां 117",
        "content_type": "garhwali_folktale_video_metadata",
        "text": "गढ़वाली हास्य मिश्रित कथा — जंदरि क बान। बड़बोले लोगों से दूर रहने की सीख देने वाली कहानी।",
        "transcript_status": "no_public_transcript_available",
    },
    {
        "platform": "youtube",
        "url": "https://www.youtube.com/watch?v=kwZWaXw_f-g",
        "title": "लाटा गौं क लोग — उत्तराखंड की लोक कहानियां 126",
        "content_type": "garhwali_folktale_video_metadata",
        "text": "लाटा गौं क लोग। गढ़वाली में कही गई पुरानी लोककथा; वीडियो में हिंदी उपशीर्षक दिखाई देते हैं।",
        "transcript_status": "no_public_transcript_available",
    },
    {
        "platform": "youtube",
        "url": "https://www.youtube.com/watch?v=AtVd-Hz08xs",
        "title": "उत्तराखंड की 50 लोक कहानियां",
        "content_type": "folktale_compilation_video_metadata",
        "text": "उत्तराखंड की 50 लोक कहानियां — Garhwali and Kumaoni folktale compilation by Ghaseri.",
        "transcript_status": "not_checked",
    },
]

CATALOG = [
    {"platform": "facebook", "url": "https://www.facebook.com/ghaseri", "name": "Ghaseri", "status": "public_profile_catalogued_text_not_exposed"},
    {"platform": "instagram", "url": "https://www.instagram.com/garhwali.bhasha", "name": "garhwali.bhasha", "status": "public_profile_catalogued_text_not_exposed"},
    {"platform": "instagram", "url": "https://www.instagram.com/garhkumaon_linguist", "name": "garhkumaon_linguist", "status": "public_profile_catalogued_text_not_exposed"},
    {"platform": "instagram", "url": "https://www.instagram.com/dmpant31", "name": "dmpant31 / Ghaseri", "status": "public_profile_catalogued_text_not_exposed"},
    {"platform": "youtube", "url": "https://www.youtube.com/@ghaseri", "name": "Ghaseri", "status": "public_channel_catalogued"},
    {"platform": "youtube", "url": "https://www.youtube.com/@Learn_garhwali", "name": "Learn Garhwali", "status": "public_channel_catalogued"},
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    for source in SOURCES:
        text = normalize(source["text"])
        digest = hashlib.sha256(text.encode()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        rows.append(
            {
                "id": f"social-garhwali:{len(rows) + 1:04d}",
                **{k: v for k, v in source.items() if k != "text"},
                "text": text,
                "text_sha256": digest,
                "language_scope": "Garhwali; mixed Hindi/English glosses possible",
                "rights_status": "public_social_post_no_open_license_recorded",
                "training_eligible": False,
                "quality_flags": ["community_contributed", "native_review_required"],
            }
        )
    (OUT / "records.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    (OUT / "catalog.json").write_text(
        json.dumps({"profiles": CATALOG}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "manifest.json").write_text(
        json.dumps({"records": len(rows), "platform_counts": {p: sum(r["platform"] == p for r in rows) for p in sorted({r["platform"] for r in rows})}, "profiles_catalogued": len(CATALOG)}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(json.loads((OUT / "manifest.json").read_text())))


if __name__ == "__main__":
    main()
