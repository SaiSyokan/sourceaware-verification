# Source-Aware Multimodal Disinformation Verification

Companion implementation for **Source-Aware Multimodal Disinformation Verification via Modality-Level Veracity and Cross-Modal Consistency**.

> Manuscript status: **revision/pre-publication artifact**. The repository is aligned to the frozen main-manuscript method, evaluation protocols, and Tables III-VI. Exact upstream model/evidence artifacts remain subject to the reproducibility notes below.

[Method](#method) · [Installation](#installation) · [Data](#data) · [Prompts](docs/PROMPTS.md) · [Retrieval](docs/RETRIEVAL.md) · [Fine-tuning](docs/TRAINING.md) · [Licenses](docs/DATA_LICENSES.md) · [Results](#reported-results) · [Paper alignment](docs/PAPER_ALIGNMENT.md)

## What belongs here

This repository contains the **journal-extension verification code**: modality analysis, dynamic routing, factor-level validation, evidence interfaces, structured aggregation, task-specific factor-instance generation, evaluation, and paper-aligned experiment records.

OctantFake construction and release tooling remain in the separate [WWW repository](https://github.com/SaiSyokan/8way-multimodal-disinformation). The gated dataset is hosted at [Syokan/OctantFake](https://huggingface.co/datasets/Syokan/OctantFake). Dataset media, third-party model weights, credentials, and copyrighted web evidence are intentionally not duplicated here.

## Implementation documentation

Implementation-oriented material that would otherwise lengthen the Supplemental Material is maintained here:

- [Prompt protocol](docs/PROMPTS.md): normalized Prompts 1-6, validator outputs, aggregation, and ablation prompt semantics;
- [Retrieval and evidence](docs/RETRIEVAL.md): image/text queries, retained evidence fields, organization, and retrieval-budget semantics;
- [Factor-level training](docs/TRAINING.md): supervision-instance formats and fine-tuning notes;
- [Dataset licenses and usage conditions](docs/DATA_LICENSES.md): source-specific provenance and redistribution checklist.

The Supplemental Material remains the scientific source for operational examples and the detailed dataset-construction rationale (source mappings, reliability control, and coverage completion).

## Method

For an input with available modalities \(M_X\), the analyzer builds the pairwise relation set \(R_X\). The router activates

$$
F_X = \{v_m \mid m \in M_X\} \cup \{c_{mn} \mid (m,n) \in R_X\}.
$$

Each active validator returns a decision, confidence, and evidence-grounded explanation. In the proposed method, each factor is then independently refined using only its own structured output before the final factor tuple is deterministically mapped to the image-text label. The diagram below shows the evaluated image-text instantiation: image-based and text-based retrieval remain separated, verification questions are generated only from the text, and the consistency branch does not consume external evidence.

```mermaid
flowchart LR
    X["Image-text input"] --> A["Input analyzer"]
    A --> R["Dynamic factor router"]

    R --> VI["Image-veracity module (LVLM)"]
    R --> VT["Text-veracity module (LLM)"]
    R --> C["Image-text consistency module (LLM)"]

    X -->|image| D["Structured image description (LVLM)"]
    X -->|image only| RI["Image-based retrieval"]
    X -->|text only| RT["Text-based retrieval"]
    X -->|text| Q["Verification questions (LLM)"]

    X -->|image| VI
    D --> VI
    RI --> VI

    X -->|text| VT
    Q --> VT
    RT --> VT

    D --> C
    X -->|text| C

    VI --> GI["Factor-wise aggregation (LLM)"]
    VT --> GT["Factor-wise aggregation (LLM)"]
    C --> GC["Factor-wise aggregation (LLM)"]

    GI --> Y["Refined factor tuple"]
    GT --> Y
    GC --> Y
    Y --> M["Deterministic 8-way mapping"]
    M --> L["Final image-text label"]
```

The released implementation supports image-only, text-only, and image-text routing paths for code-level validation. The manuscript experiments evaluate the image-text instantiation. The general formulation permits additional modalities, but audio/video validators were not evaluated and are therefore not presented as implemented results.

## Installation

Python 3.10 or later is required. The core install has no model or network dependency:

```bash
git clone https://github.com/SaiSyokan/fine-grained-multimodal-verification.git
cd fine-grained-multimodal-verification
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
```

Install optional components only when needed:

```bash
python -m pip install -e '.[evidence,inference]'
```

LLaVA is not vendored. Install a compatible upstream LLaVA implementation for image-conditioned calls. Language-only zero-shot calls use a Hugging Face causal-LM backend. See [installation and environment notes](docs/INSTALLATION.md).

## Data

Request access to [OctantFake on Hugging Face](https://huggingface.co/datasets/Syokan/OctantFake), accept its terms, authenticate, and download the complete snapshot. The official zero-shot protocol uses:

| Split | Samples | Purpose |
|---|---:|---|
| Development (official calibration split) | 800 | Prompt development, design selection, and retrieval-budget selection |
| Test | 8,000 | Final zero-shot evaluation |

The supervised protocol uses the original 800-sample calibration split as validation and stratifies the original test split into 7,200 training and 800 held-out test samples (900/100 per class). See [data protocol](docs/DATA.md).

Validate a local manifest:

```bash
sourceaware validate /path/to/manifest.jsonl --check-files --media-root /path/to/OctantFake
```

## Evidence collection

Use `.env.example` as a credential checklist and export the variables through your shell or secret manager. The image query uses only the image; the text query uses only the original text. Verification questions guide reasoning but do not alter the search query.

```bash
sourceaware collect-image-evidence --manifest manifest.jsonl --output evidence --limit 3 --media-root /path/to/OctantFake
sourceaware collect-text-evidence --manifest manifest.jsonl --output evidence --limit 3
```

Image evidence preserves best-guess labels, web entities, page titles, page descriptions, surrounding/page text, and full/partial visual-match information when available. Text evidence preserves result titles, snippets, and links. Evidence is timestamped and should be treated as a time-sensitive run artifact. Raw evidence is ignored by Git to avoid accidental redistribution. See the detailed [retrieval and evidence protocol](docs/RETRIEVAL.md).

## Zero-shot inference

The primary paper configuration performs separate factor checks followed by structured aggregation:

```bash
sourceaware run \
  --manifest manifest.jsonl \
  --media-root /path/to/OctantFake \
  --evidence-root evidence \
  --model-path /path/to/llava-v1.6-34b \
  --language-model-path NousResearch/Nous-Hermes-2-Yi-34B \
  --strategy separate_structured \
  --output predictions.jsonl

sourceaware evaluate predictions.jsonl --output metrics.json
sourceaware evaluate-factors predictions.jsonl --output factor-metrics.json
```

The five framework-ablation strategies are `holistic` (A), `joint_factors` (B), `separate_deterministic` (C), `separate_structured` (D, proposed), and `separate_cross_factor` (E). Module ablations use `--no-evidence`, `--no-image-description`, and `--retrieval-limit {0,1,2,3,4,5}`. `k=0` is distinct from `--no-evidence`: it retains the evidence-enabled verification path but provides zero retrieved evidence instances.

For the paper-faithful zero-shot path, image description and image-veracity calls use the LLaVA/LVLM backend, while verification-question generation, text veracity, image-text consistency, and factor aggregation use the language-only backend. If `--language-model-path` is omitted, the CLI falls back to using the multimodal backend without images for language-only calls; that compatibility fallback is not the canonical paper configuration.

## Factor-level fine-tuning

Each labeled image-text pair produces three supervision instances, one per factor:

```bash
sourceaware prepare-finetune \
  --manifest train.jsonl \
  --output train.factor-instances.jsonl
```

The frozen main manuscript specifies a shared LLaVA-1.6-34B backbone, LoRA adaptation, a frozen vision encoder, factor-level supervision, and checkpoint selection by validation macro-F1. External retrieval is not used during fine-tuning. Additional training values carried by this pre-publication artifact must be checked against the original training command/log before they are treated as archival settings; see the [factor-level training protocol](docs/TRAINING.md). Exact zero-shot prompt templates are documented separately in [Prompt Protocol](docs/PROMPTS.md).

## Reported results

Machine-readable transcriptions of manuscript Tables III-VI are in [`results/`](results/README.md). They are reference records, not regenerated claims. Raw per-sample predictions and model checkpoints must come from the original experiment runs and are not fabricated by this package.

## Repository layout

```text
.
├── configs/                 # Paper-aligned inference/training settings
├── docs/                    # Prompts, retrieval, training, licenses, data, baselines, and paper alignment
├── examples/                # Synthetic, non-benchmark examples
├── results/                 # Manuscript table transcriptions
├── src/sourceaware_verification/
│   ├── routing.py           # Analyzer and F_X construction
│   ├── prompts.py           # Exact validator and aggregation prompts
│   ├── evidence.py          # Google retrieval adapters and evidence store
│   ├── llava_backend.py     # LVLM backend for image-conditioned calls
│   ├── text_backend.py      # LLM backend for language-only calls
│   ├── pipeline.py          # Factor modules and aggregation
│   ├── finetune.py          # Factor-specific supervision conversion
│   └── evaluation.py        # 8-way and factor-level metrics
└── tests/                   # Offline tests; no keys, media, or model required
```

## Responsible use

Outputs are evidence-budget-dependent verification decisions, not guarantees of truth. A `T` decision means that no violation was detected under the available evidence and fixed verification setting. Review the [dataset license/usage checklist](docs/DATA_LICENSES.md) and [third-party notice](THIRD_PARTY.md) before use.

## License

Code in this repository is released under the MIT License. This license does not apply to OctantFake media, third-party datasets, model weights, or retrieved web content.
