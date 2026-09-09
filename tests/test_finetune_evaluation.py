import json
import tempfile
import unittest
from pathlib import Path

from sourceaware_verification.evaluation import evaluate_factor_predictions, evaluate_predictions
from sourceaware_verification.finetune import factor_instances, prepare_factor_dataset


class FinetuneEvaluationTests(unittest.TestCase):
    def test_each_pair_produces_three_factor_instances(self):
        rows = factor_instances(
            {"sample_id": "x", "image_path": "x.jpg", "text": "claim", "label": "TFF"}
        )
        self.assertEqual(
            [row["factor"] for row in rows],
            ["veracity:image", "veracity:text", "consistency:image:text"],
        )
        self.assertEqual([row["target"] for row in rows], ["T", "F", "F"])

    def test_prepare_factor_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            source.write_text(
                json.dumps(
                    {"sample_id": "x", "image_path": "x.jpg", "text": "claim", "label": "FFT"}
                )
                + "\n",
                encoding="utf-8",
            )
            destination = root / "factors.jsonl"
            self.assertEqual(prepare_factor_dataset(source, destination), 3)
            self.assertEqual(len(destination.read_text(encoding="utf-8").splitlines()), 3)

    def test_complete_synthetic_predictions_are_perfect(self):
        source = Path(__file__).parents[1] / "examples" / "predictions.synthetic.jsonl"
        metrics = evaluate_predictions(source)
        self.assertEqual(metrics["total"], 8)
        self.assertEqual(metrics["macro_f1"], 1.0)
        self.assertTrue(
            all(value["macro_f1"] == 1.0 for value in metrics["factor_metrics"].values())
        )

    def test_factor_evaluation_uses_only_available_factors(self):
        source = Path(__file__).parents[1] / "examples" / "factor_predictions.synthetic.jsonl"
        metrics = evaluate_factor_predictions(source)
        self.assertEqual(metrics["factors"]["veracity:image"]["total"], 4)
        self.assertEqual(metrics["factors"]["veracity:text"]["total"], 4)
        self.assertEqual(metrics["factors"]["consistency:image:text"]["total"], 2)
        self.assertTrue(
            all(value["macro_f1"] == 1.0 for value in metrics["factors"].values())
        )
