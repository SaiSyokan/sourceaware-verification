# Manuscript alignment update (2026-10-28)

- Added the five GPT-6.1 Sol results from the revised manuscript's Table III and aligned the related documentation and result checks.
- Matched the image-text consistency fine-tuning instruction to the documented protocol, fixing the local-source offline test failure.
- No new proprietary inference backend, original per-sample predictions, or dataset construction process is introduced in this update.

# v0.1.0

Pre-publication artifact for the manuscript **Source-Aware Multimodal Disinformation Verification via Modality-Level Veracity and Cross-Modal Consistency**.

## Included

- dynamic modality analysis and source-aware factor routing;
- independent image-veracity, text-veracity, and image-text consistency modules;
- explicit LVLM/LLM backend separation for the paper-faithful zero-shot path;
- factor-wise structured aggregation for the proposed method and cross-factor aggregation as a separate ablation;
- all five framework-level ablation paths (A-E);
- exact prompt protocol and strict output parsing, with complete prompt documentation in `docs/PROMPTS.md`;
- Google Vision Web Detection and Google Custom Search evidence adapters, including page-description, surrounding-text, and visual-match metadata rendering, documented in `docs/RETRIEVAL.md`;
- distinct implementations of `w/o evidence` and evidence-enabled `k=0`;
- factor-level fine-tuning instance generation and documented supervision templates;
- image-text and factor-level evaluation;
- paper-aligned inference/ablation configurations, a recorded fine-tuning configuration, and Tables III-VI as CSV;
- source-specific dataset license/usage checklist;
- synthetic examples and offline tests.

## External resources

- OctantFake: https://huggingface.co/datasets/Syokan/OctantFake
- Dataset/construction repository: https://github.com/SaiSyokan/8way-multimodal-disinformation

This review release does not include third-party model weights, API credentials, dataset media, raw web evidence, reconstructed training logs, or fabricated per-sample predictions.
