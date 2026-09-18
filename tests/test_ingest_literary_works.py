import json
import tempfile
import unittest
from pathlib import Path

import ingest_literary_works as m


EXPECTED_TITLES = {
    "1335 Dev Prayag temple grant inscription",
    "Ranch Judya Judige Ghimsaan Ji",
    "Sabhaasaar",
    "Garhwali New Testament",
    "Gospel of St. Matthew in Garhwali",
    "Mahabharata (Garhwali translation)",
    "Ramayana (Garhwali translation)",
    "Ramcharitmanas (Garhwali translation)",
    "Shreemad Bhagwat Geeta (Garhwali translation)",
    "Parable of the Prodigal Son (Garhwali)",
    "Bundle of Sticks (Garhwali folk tale)",
    "A Grammar of the Hindí Language",
    "Linguistic Survey of India, Volume IX, Part IV: Pahari Languages & Gujuri",
    "Sadei",
    "Phyunli",
    "Utha Garhwalyun!",
    "Agyaal",
    "Umaal",
    "Parbati",
    "Kuredi phategi",
    "Anjwaal",
    "Mangtu",
    "Nagraja",
    "Khigtaat",
    "Gainika nau par",
    "Hari Hindwaan",
    "Inma kankwei aan basant",
    "Gaad",
    "Myateki Ganga",
    "Bhumyal",
    "Pralhad",
    "Mochhang",
    "Bwari",
    "Mwari",
    "Gaari",
    "Dr. Asaram",
    "Panch Parani Pachis Chhawin",
    "Kya Gori Kya Saunli",
    "Ristaun ki Ahmiyat",
    "Chithi-Patri-Collection",
    "Tabari Ar Abari",
    "Tup-Tap",
    "Pani",
    "Kulla Pichkari",
    "Lagyan Chhaan",
    "Ados-Pados",
    "Hari Singho Baggi Fast",
    "Aar-Parai Ladai",
    "Samsya Khadi Cha",
    "Naaraz Ni Huyaan",
    "Bakki Tumari Marji",
    "Uttarakhand Khabarsar",
    "Rant Raibar",
    "Baduli",
    "Hilaans",
    "Chitthi-patri",
    "Dhaad",
    "Bedu Pako Baro Masa",
    "Chakhul Garhwali Dictionary",
    "Garhpedia",
    "HimLingo Garhwali Dictionary",
    "Achhryun ku Taal",
    "Phanchi",
    "Aandi-jaandi saans",
    "Aunar",
    "Dheet",
}


class LiteraryWorksIngestionTests(unittest.TestCase):
    def test_capture_has_complete_named_work_coverage(self):
        catalog = json.loads(m.CATALOG.read_text(encoding="utf-8"))
        rows = catalog["works"]
        self.assertEqual({row["title"] for row in rows}, EXPECTED_TITLES)
        self.assertEqual(len(rows), 66)
        self.assertEqual(len(catalog["capture_coverage"]["unresolved_mentions"]), 2)
        self.assertEqual(
            set(catalog["capture_coverage"]["named_genres"]),
            {"Mangal", "Bhadiyali", "Panwara"},
        )
        self.assertTrue(
            all(not (m.FORBIDDEN_PAYLOAD_FIELDS & row.keys()) for row in rows)
        )

    def test_run_writes_deduplicated_records_and_audit_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = m.run(output=output)
            rows = [
                json.loads(line)
                for line in (output / "records.jsonl").read_text().splitlines()
            ]
            self.assertEqual(report["records"], 66)
            self.assertEqual(report["status"], "all_named_works_in_capture_catalogued")
            self.assertEqual(report["payload_records_added"], 0)
            self.assertEqual(len({row["record_id"] for row in rows}), 66)
            self.assertEqual(len(report["unresolved_details"]), 2)


if __name__ == "__main__":
    unittest.main()
