# Artifact Scope

This repository is a pre-publication research artifact intended to support evaluation and peer review. It is versioned separately from the future archival release.

## Included

- source-aware input analysis and factor routing;
- image-veracity, text-veracity, and image-text consistency prompt paths;
- factor-wise structured aggregation, cross-factor aggregation ablation, and deterministic mapping path;
- Google Vision Web Detection and Google Custom Search adapters;
- strict output parsing and failure accounting;
- OctantFake manifest validation and factor-level metrics;
- factor-specific fine-tuning instance generation;
- paper-aligned inference/ablation configurations, a recorded fine-tuning configuration, and reported aggregate Tables III-VI;
- synthetic examples and offline continuous-integration tests.

## Intentionally external

- OctantFake media and full manifests: gated Hugging Face release;
- dataset construction: WWW companion repository;
- LLaVA, VILA, ImageBind/Vicuna, and other third-party implementations;
- pretrained or fine-tuned model weights;
- Google service credentials;
- raw web pages and search results, which are time-sensitive and may be copyrighted.

## Requires original experiment artifacts before archival release

- raw per-sample predictions for each reported method and split;
- the selected factor-level LoRA checkpoint or a documented distribution route;
- exact upstream repository commit hashes and environment lockfile;
- hardware/runtime logs and random-seed records from the reported runs;
- training parameters not recorded in the current manuscript, listed in `docs/TRAINING.md`.

These items are not reconstructed or guessed in this repository.
