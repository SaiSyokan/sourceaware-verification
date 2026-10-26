# Prompt Protocol

The executable normalized prompts are stored in `src/sourceaware_verification/prompts.py`. They implement the prompt/output protocol described by the main manuscript and accompanying Supplemental Material.

Three principles are enforced:

1. **factor separation:** image veracity, text veracity, and image-text consistency are verified independently;
2. **evidence grounding:** `F` requires an identifiable violation under the active verification setting; missing evidence alone is not a violation;
3. **factor-wise aggregation:** the proposed aggregation step refines each factor independently using only that factor's decision, confidence, and explanation.

Every factor validator returns:

```text
Decision: T or F
Confidence: a real number in [0, 1]
Explanation: a brief input/evidence-grounded reason
```

The image description is generated once and reused by the image-veracity and image-text consistency modules. The question generator produces at most two questions. The original input text, not those questions and not image information, is the Google Custom Search query.


## Backend roles in zero-shot verification

The executable pipeline separates image-conditioned and language-only calls in the same way as the frozen manuscript:

- **LVLM backend:** structured image description and image-veracity verification;
- **LLM backend:** verification-question generation, text-veracity verification, image-text consistency from the structured image description plus text, and both aggregation variants.

The CLI accepts the LLaVA checkpoint through `--model-path` and the language-only checkpoint through `--language-model-path`. The latter should be supplied for paper-faithful zero-shot runs.

## Aggregation variants

The proposed method (`separate_structured`, manuscript Variant D) invokes `FACTORWISE_STRUCTURED_AGGREGATION` separately for each active factor. A single invocation receives only:

```text
Factor Decision
Factor Confidence
Factor Explanation
```

and returns:

```text
Final Decision: T or F
```

`CROSS_FACTOR_AGGREGATION` is retained only for manuscript Variant E, where the aggregation call can inspect all factor outputs jointly.

## Evidence ablations

`w/o evidence` and `k=0` are intentionally different:

- `w/o evidence` uses prompt variants in which external evidence is removed from the verification procedure.
- `k=0` keeps the evidence-enabled prompt/interface but supplies zero retrieved evidence instances.

Likewise, the image-description ablation uses prompt paths that omit the structured description rather than inserting it as evidence.

The parser accepts the manuscript line format and, for factor-validator outputs, an equivalent strict JSON object for backend interoperability. Missing factors, invalid decisions, out-of-range confidence values, and malformed output are never silently mapped to a majority class.
