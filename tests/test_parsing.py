import unittest

from sourceaware_verification.parsing import (
    parse_factor,
    parse_final_decision,
    parse_questions,
    parse_structured_decisions,
)
from sourceaware_verification.schema import FactorKey


class ParsingTests(unittest.TestCase):
    def test_factor_line_protocol(self):
        result = parse_factor("Decision: F\nConfidence: 0.75\nExplanation: contradicted")
        self.assertEqual(result.decision, "F")
        self.assertEqual(result.confidence, 0.75)

    def test_factor_json_interoperability(self):
        result = parse_factor('{"decision":"T","confidence":0.4,"explanation":"not refuted"}')
        self.assertEqual(result.decision, "T")

    def test_questions_are_limited_to_two(self):
        self.assertEqual(
            parse_questions("1. First?\n2. Second?\n3. Third?"), ("First?", "Second?")
        )

    def test_aggregator_must_return_every_active_factor(self):
        factors = [FactorKey("veracity", "image"), FactorKey("veracity", "text")]
        with self.assertRaisesRegex(ValueError, "Text Veracity"):
            parse_structured_decisions("Image Veracity: T", factors)

    def test_factorwise_aggregator_final_decision(self):
        self.assertEqual(parse_final_decision("Final Decision: F"), "F")

    def test_out_of_range_confidence_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "confidence"):
            parse_factor("Decision: T\nConfidence: 1.2\nExplanation: invalid score")
