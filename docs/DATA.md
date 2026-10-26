# Data and Split Protocol

## Zero-shot protocol

- Dataset: OctantFake v1.0.0
- Calibration: 800 samples, 100 per class
- Test: 8,000 samples, 1,000 per class
- No task-specific parameter learning
- Calibration determines prompt format, parsing, retrieval, and inference-time settings
- All settings are frozen before test evaluation
- Missing or invalid predictions count as incorrect

## Task-specific protocol

- Validation: original 800-sample calibration split
- Training: 7,200 samples stratified from the original zero-shot test split, 900 per class
- Held-out test: remaining 800 samples, 100 per class
- All supervised and fine-tuned methods use the same partitions
- Each training pair produces image-veracity, text-veracity, and consistency supervision instances

The supervised protocol deliberately reuses and repartitions the original zero-shot test split. Results from the 800-sample held-out supervised test must not be compared as if they were evaluated on the 8,000-sample zero-shot test.

## Manifest fields

Required: `sample_id` and at least one supported modality field (`image_path` or `text`). Image-text evaluation additionally uses `label` in the ordered form image veracity / text veracity / image-text consistency.

Do not commit downloaded media to this repository.


## Evidence representation

Image-based retrieval records best-guess labels, web entities, pages containing full or partial visual matches, page titles, page descriptions, surrounding page text, and match information when available. The verifier receives these fields as supporting context; retrieval output is not treated as ground truth. Text-based retrieval retains the original query, page titles, snippets, and links.


## Licenses and redistribution

Source-specific dataset licenses and usage conditions are summarized in [`DATA_LICENSES.md`](DATA_LICENSES.md). Do not assume that a code or annotation license grants redistribution rights over underlying third-party media.
