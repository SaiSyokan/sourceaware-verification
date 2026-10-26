# Evidence Retrieval and Organization

This document records the evidence-retrieval protocol used by the image-text zero-shot verification framework. It complements the main manuscript and preserves the implementation details that are too operational for the paper itself.

The two modality-veracity branches remain intentionally separated:

- **image veracity:** retrieval uses only the input image through Google Vision API Web Detection;
- **text veracity:** retrieval uses only the original input text through Google Custom Search;
- **image-text consistency:** no external evidence is retrieved for this factor; it uses the structured image description together with the input text.

Verification questions are generated from the input text, but they are **not** used to modify the Google Custom Search query.

## Image retrieval

The input image is submitted directly to Google Vision API Web Detection. The accompanying text is not included in the image-search request, which prevents textual information from influencing the standalone image-veracity judgment.

The repository stores the following fields when available:

| Evidence field | Repository field / representation | Purpose |
|---|---|---|
| Best-guess labels | `best_guess_labels` | High-level labels returned for the visual content of the query image. |
| Web entities | `web_entities` | Entities associated with salient people, objects, events, or concepts. |
| Matched-image pages | `pages_with_matching_images` | External webpages containing identical or visually related images. |
| Page title | `page_title` | Title returned for a matched/related webpage. |
| Page description | `description` | Available page-level description/metadata retained as contextual evidence. |
| Surrounding/page text | `surrounding_text` | Available webpage textual context retained for verification. |
| Full/identical matches | `full_matching_images` | URLs reported by Web Detection as full image matches. |
| Partial/visually related matches | `partial_matching_images` | URLs reported by Web Detection as partial/related image matches. |

`EvidenceStore.render_image()` organizes these fields into a compact context containing best-guess labels, web entities, page title, page description, surrounding/page text, match information, and the source URL.

The retrieved material is treated as **supporting evidence, not ground truth**. A visually similar image, label, or web entity alone is not sufficient to assign image veracity `F`; the verifier considers the input image, its structured description, and the available evidence together.

If no useful image-based evidence is available, the evidence field is marked unavailable and verification proceeds from the image and structured description. For retrieval-budget sensitivity, `k=0` is represented separately: the evidence-enabled verification path is retained, but zero retrieved evidence instances are supplied.

## Text retrieval and query construction

The original input text is submitted directly to Google Custom Search. Information from the accompanying image is not incorporated into the query.

For each retrieved result, the repository retains:

| Component | Repository field / representation | Purpose |
|---|---|---|
| Input text | `query` in the stored retrieval record | Original statement submitted to Google Custom Search and later supplied to the verifier. |
| Verification questions | generated separately by `VERIFICATION_QUESTIONS` | Up to two focused questions that identify central falsifiable claims. They guide verification but do not modify retrieval. |
| Page title | `items[].title` | Title of a retrieved webpage. |
| Search snippet | `items[].snippet` | Short textual excerpt returned by Google Custom Search and used as the primary textual evidence. |
| Link | `items[].link` | Source URL retained for provenance. |

The top-`k` results are organized into the retrieved textual-evidence context supplied to the text-veracity validator. Search ranking is used only to select evidence candidates; it is not itself interpreted as evidence of factual correctness.

If no useful external result is available, the evidence context is marked unavailable. Missing or inconclusive evidence alone does not constitute a factual violation.

## Retrieval budget

The paper selects `k=3` on the development split and fixes that setting for the main test evaluation. The test-set sensitivity analysis additionally reports `k in {0,1,2,3,4,5}` without using those test results for hyperparameter selection.

Two settings that look similar are deliberately distinct:

- **`w/o evidence`:** external evidence is removed from the image- and text-veracity verification procedure, including the evidence fields in their prompts;
- **`k=0`:** the normal evidence-enabled prompt/interface is retained, but no retrieved evidence instances are supplied.

## Commands

Collect image evidence:

```bash
sourceaware collect-image-evidence \
  --manifest manifest.jsonl \
  --output evidence \
  --limit 3 \
  --media-root /path/to/OctantFake
```

Collect text evidence:

```bash
sourceaware collect-text-evidence \
  --manifest manifest.jsonl \
  --output evidence \
  --limit 3
```

The stored records are timestamped because web evidence can change over time. Do not redistribute retrieved images, page text, or other third-party content unless the corresponding source terms permit it.
