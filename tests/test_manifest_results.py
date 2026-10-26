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
            if row["setting"] == "34B" and row["approach"] == "Source-Aware Framework (Ours)"
        ]
        self.assertEqual(primary[0]["f1"], "30.1")

    def test_table_v_contains_five_variants(self):
        with (ROOT / "results" / "table_v_verification_aggregation_ablation.csv").open(
            encoding="utf-8"
        ) as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([row["variant"] for row in rows], list("ABCDE"))
        self.assertEqual(rows[-1]["macro_f1"], "30.0")

    def test_table_vi_distinguishes_k0_from_without_evidence(self):
        with (ROOT / "results" / "table_vi_components_retrieval_ablation.csv").open(
            encoding="utf-8"
        ) as stream:
            rows = list(csv.DictReader(stream))
        by_setting = {row["setting"]: row for row in rows}
        self.assertEqual(by_setting["k=0"]["evidence"], "true")
        self.assertEqual(by_setting["k=0"]["k"], "0")
        self.assertEqual(by_setting["w/o evidence"]["evidence"], "false")
