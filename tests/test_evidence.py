import unittest

from sourceaware_verification.evidence import EvidenceStore, ZERO_BUDGET


class EvidenceRenderingTests(unittest.TestCase):
    def test_image_evidence_retains_description_surrounding_text_and_match_information(self):
        rendered = EvidenceStore.render_image(
            {
                "best_guess_labels": ["example event"],
                "web_entities": [{"description": "example person", "score": 0.9}],
                "pages_with_matching_images": [
                    {
                        "page_title": "Example page",
                        "description": "Page-level description",
                        "surrounding_text": "Relevant surrounding page text",
                        "full_matching_images": ["https://example.org/full.jpg"],
                        "partial_matching_images": ["https://example.org/partial.jpg"],
                        "url": "https://example.org/page",
                    }
                ],
            },
            limit=3,
        )
        self.assertIn("Best-guess labels: example event", rendered)
        self.assertIn("Web entities: example person", rendered)
        self.assertIn("Page description: Page-level description", rendered)
        self.assertIn("Surrounding text: Relevant surrounding page text", rendered)
        self.assertIn("full/identical matches=1", rendered)
        self.assertIn("partial/visually related matches=1", rendered)

    def test_zero_budget_keeps_evidence_enabled_interface(self):
        self.assertEqual(EvidenceStore.render_image(None, limit=0), ZERO_BUDGET)
        self.assertEqual(EvidenceStore.render_text(None, limit=0), ZERO_BUDGET)
