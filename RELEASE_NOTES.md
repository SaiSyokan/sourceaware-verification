# v0.1.0

Pre-publication artifact for the manuscript **Source-Aware Multimodal Disinformation Verification via Modality-Level Veracity and Cross-Modal Consistency**.

## Included

- dynamic modality analysis and source-aware factor routing;
- independent image-veracity, text-veracity, and image-text consistency modules;
- factor-wise structured aggregation for the proposed method and cross-factor aggregation as a separate ablation;
- all five framework-level ablation paths (A-E);
- exact prompt protocol and strict output parsing;
- Google Vision Web Detection and Google Custom Search evidence adapters;
- distinct implementations of `w/o evidence` and evidence-enabled `k=0`;
- factor-level fine-tuning instance generation;
- image-text and factor-level evaluation;
- paper-aligned configurations and Tables III-VI as CSV;
- synthetic examples and offline tests.

## External resources

- OctantFake: https://huggingface.co/datasets/Syokan/OctantFake
- Dataset/construction repository: https://github.com/SaiSyokan/8way-multimodal-disinformation

This review release does not include third-party model weights, API credentials, dataset media, raw web evidence, reconstructed training logs, or fabricated per-sample predictions.
