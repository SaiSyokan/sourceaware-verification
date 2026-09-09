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

## LLaVA inference

```bash
python -m pip install -e '.[inference]'
```

Install the upstream LLaVA code compatible with the selected LLaVA-1.6 checkpoint. The adapter imports the upstream `llava` package but does not vendor or silently download it. A 34B checkpoint normally requires multi-GPU or quantized/offloaded execution; record any deviation from the paper setting in the run metadata.

## Reproducible environment capture

Before the submission freeze, export the environment actually used for reported runs, record the LLaVA and baseline commit hashes, CUDA/cuDNN versions, GPU model/count, precision, quantization, and any distributed launcher settings. The included `environment.yml` is a portable starting point, not a claim that the reported runs were produced from a newly reconstructed environment.
