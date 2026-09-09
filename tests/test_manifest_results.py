import csv
import unittest
from pathlib import Path

from sourceaware_verification.manifest import validate_manifest


ROOT = Path(__file__).parents[1]


class ManifestResultTests(unittest.TestCase):
    def test_synthetic_manifest_covers_three_input_settings(self):
        result = validate_manifest(ROOT / "examples" / "manifest.synthetic.jsonl")
        self.assertTrue(result["valid"])
        self.assertEqual(
            result["modality_counts"], {"image+text": 1, "image": 1, "text": 1}
        )

    def test_table_iii_transcription_contains_reported_primary_result(self):
        with (ROOT / "results" / "table_iii_zero_shot.csv").open(encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 20)
        primary = [
            row
            for row in rows
            if row["setting"] == "34B" and row["approach"] == "Source-Aware Framework"
        ]
        self.assertEqual(primary[0]["test_f1"], "30.1")
