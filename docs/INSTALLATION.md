# Installation and Environment

## Core/offline inspection

- Python 3.10 or later
- no GPU, model download, dataset media, or network credentials required

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Evidence collection

```bash
python -m pip install -e '.[evidence]'
```

Google Vision uses Application Default Credentials through `GOOGLE_APPLICATION_CREDENTIALS`. Text retrieval requires `GOOGLE_CUSTOM_SEARCH_API_KEY` and `GOOGLE_CUSTOM_SEARCH_ENGINE_ID`. The collectors never read `.env` automatically; export variables through your preferred secret manager or shell.

## Zero-shot inference backends

```bash
python -m pip install -e '.[inference]'
```

Install the upstream LLaVA code compatible with the selected LLaVA-1.6 checkpoint. The adapter imports the upstream `llava` package but does not vendor or silently download it. The `inference` extra also installs `transformers`/`accelerate` for the language-only backend.

For the paper-faithful zero-shot image-text path:

- image description and image-veracity verification use the LLaVA/LVLM backend;
- verification-question generation, text-veracity verification, image-text consistency, and aggregation use the language-only causal-LM backend.

For the 34B setting reported in the manuscript, the language model is `NousResearch/Nous-Hermes-2-Yi-34B`. Supply it with `--language-model-path`. Omitting that option activates a compatibility fallback in which the multimodal backend is called without an image; that fallback is useful for code inspection but is not the canonical paper configuration.

A 34B checkpoint normally requires multi-GPU or quantized/offloaded execution; record any deviation from the paper setting in the run metadata.

## Reproducible environment capture

Before the submission freeze, export the environment actually used for reported runs, record the LLaVA and baseline commit hashes, CUDA/cuDNN versions, GPU model/count, precision, quantization, and any distributed launcher settings. The included `environment.yml` is a portable starting point, not a claim that the reported runs were produced from a newly reconstructed environment.
