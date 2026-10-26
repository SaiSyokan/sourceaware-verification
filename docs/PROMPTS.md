# Prompt Protocol

The executable prompt source of truth is [`src/sourceaware_verification/prompts.py`](../src/sourceaware_verification/prompts.py). This document records the normalized prompt/output protocol used by the paper-facing image-text verification pipeline and explains the ablation-specific variants retained in code.

The prompt design follows three principles:

1. **factor separation:** image veracity, text veracity, and image-text consistency are verified independently;
2. **evidence grounding:** `F` requires an identifiable violation under the active verification setting; missing or inconclusive evidence alone is not a factual violation;
3. **factor-wise aggregation:** the proposed aggregation step refines each factor independently using only that factor's decision, confidence, and explanation.

## Common validator output protocol

Every factor-level validator returns the same structured result

```text
q_f = (d_f, s_f, e_f)
```

where:

- `d_f in {T,F}` is the factor-level decision;
- `s_f in [0,1]` is the confidence score;
- `e_f` is a brief factor-specific explanation grounded in the available input/evidence.

The normalized text format is:

```text
Decision: [T/F]
Confidence: [0-1]
Explanation: [brief explanation]
```

Operational interpretation:

- **modality veracity:** `F` means a verifiable factual violation is identified under the active verification setting; `T` means no such violation is identified;
- **cross-modal consistency:** `F` means a salient semantic conflict is identified between the modalities; `T` means no such conflict is identified.

A `T` decision is not a claim of proof or universal factual correctness; it is scoped to the available evidence and verification setting.

## Backend roles in zero-shot verification

The executable pipeline separates image-conditioned and language-only calls in the same way as the frozen main manuscript:

- **LVLM backend:** structured image description and image-veracity verification;
- **LLM backend:** verification-question generation, text-veracity verification, image-text consistency from the structured image description plus text, and aggregation.

The CLI accepts the LLaVA checkpoint through `--model-path` and the language-only checkpoint through `--language-model-path`. The latter should be supplied for paper-faithful zero-shot runs.

## Prompt 1: Image description

**Role:** Generate a structured description of the input image.

**Input:** `[INPUT IMAGE]`

**Instruction:**

```text
You are given an image. Describe its visually observable content in a structured and factual manner.

Identify the following when visible:
- salient people, entities, or objects;
- actions and interactions;
- scene and environment;
- visible text, symbols, or signs;
- spatial or quantitative information;
- noticeable visual anomalies or potential manipulation cues.

Do not determine whether the image is true or false. Do not infer facts that are not supported by the visible content.

Return a concise structured description that can be used for subsequent verification.
```

**Output:** A concise structured image description.

The description is generated once and reused by the image-veracity and image-text consistency modules in the full setting.

## Prompt 2: Image-veracity validation

**Role:** Verify the factual veracity of the image.

**Input:**

```text
[INPUT IMAGE]
[IMAGE DESCRIPTION]
[RETRIEVED IMAGE EVIDENCE]
```

**Instruction:**

```text
Determine whether the input image contains a factual violation using the image itself, its structured description, and the retrieved evidence.

Evaluate materially checkable factual attributes such as identity, event, action, location, time, quantity, and other contextual information represented by the image.

Output F only when the available evidence supports identifying at least one material factual violation in the image.

Purely cosmetic modifications, such as ordinary color adjustment, cropping, or stylistic editing, should not be treated as factual violations unless they materially alter the factual meaning of the image.

If no factual violation is identified under the available evidence and verification setting, output T.
```

**Output:**

```text
Decision: [T/F]
Confidence: [0-1]
Explanation: [brief evidence-grounded explanation]
```

This validator receives no accompanying input text. Its structured result is the image-veracity output `q_i=(d_i,s_i,e_i)`.

## Prompt 3: Verification-question generation

**Role:** Generate focused fact-checking questions.

**Input:** `[INPUT TEXT]`

**Instruction:**

```text
Based on the text, generate up to two specific fact-checking questions targeting its main factual claims.

- Focus only on claims that are verifiable or falsifiable.
- Prioritize claims that are central to the factual meaning of the text.
- Do not generate questions for subjective, trivial, or overly vague details.
```

**Output:** Up to two short verification questions.

The questions guide subsequent reasoning. They are not used to alter the Google Custom Search query; retrieval uses the original input text.

## Prompt 4: Text-veracity validation

**Role:** Verify the factual veracity of the input text.

**Input:**

```text
[INPUT TEXT]
[VERIFICATION QUESTIONS]
[RETRIEVED TEXTUAL EVIDENCE]
```

**Instruction:**

```text
Determine whether the input text contains a factual violation using the verification questions and the retrieved evidence.

For each material factual claim:
- identify the relevant available evidence;
- determine whether the evidence supports, contradicts, or does not resolve the claim;
- distinguish factual claims from subjective, speculative, rhetorical, or emotional language.

Focus on verifiable information such as people or entities, events and actions, locations, times, quantities, and other factual relationships.

Output F only when the available evidence supports identifying at least one material factual violation in the text. Missing, incomplete, or inconclusive evidence alone should not be treated as a factual violation.

If no factual violation is identified under the available evidence and verification setting, output T.
```

**Output:**

```text
Decision: [T/F]
Confidence: [0-1]
Explanation: [brief evidence-grounded explanation]
```

The structured result is the text-veracity output `q_t=(d_t,s_t,e_t)`.

## Prompt 5: Image-text consistency validation

**Role:** Determine whether a salient semantic conflict is present between the image and text.

**Input:**

```text
[IMAGE DESCRIPTION]
[INPUT TEXT]
```

**Instruction:**

```text
Compare the image and the text and determine whether a salient semantic conflict is identified between them.

Focus on salient relations involving entities, events, actions, location, time, quantity, and other context necessary to identify the described situation.

Judge only the relationship between the two modalities. Do not determine whether the image or the text is factually true in the real world.

Output F only when a salient semantic conflict is identified or when the two modalities clearly refer to different situations. Missing details in one modality do not by themselves imply inconsistency if the remaining information is still compatible.

If no such conflict is identified, output T.
```

**Output:**

```text
Decision: [T/F]
Confidence: [0-1]
Explanation: [brief explanation]
```

The structured result is `q_it=(d_it,s_it,e_it)`. The consistency module does not consume external evidence.

## Prompt 6: Factor-wise structured aggregation

The proposed method is manuscript Variant D / executable strategy `separate_structured`.

**Role:** Produce the final decision for one verification factor from its structured validator output.

**Input:**

```text
[FACTOR DECISION]
[FACTOR CONFIDENCE]
[FACTOR EXPLANATION]
```

**Instruction:**

```text
You are given the structured output of one factor-level validator. The output contains an initial decision, a confidence score, and a brief explanation for the same verification factor.

Determine the final T/F decision for this factor by considering only the provided decision, confidence score, and explanation.

Do not use information from, infer, or revise any other verification factor.
```

**Output:**

```text
Final Decision: [T/F]
```

For image-text inputs, the same aggregation procedure is applied independently to `q_i`, `q_t`, and `q_it` to obtain the refined predictions `(v_hat_i, v_hat_t, c_hat_it)`, which are then deterministically mapped to one of the eight image-text cases.

## Cross-factor aggregation ablation (Variant E)

`CROSS_FACTOR_AGGREGATION` is retained only for the ablation corresponding to Variant E. It receives the structured outputs of all active factors jointly and returns a final decision for each active factor. It is **not** the proposed default aggregation strategy.

## Evidence and image-description ablations

The code contains explicit ablation prompt variants rather than silently substituting placeholders:

- **`w/o evidence`:** external-evidence fields are removed from image/text veracity prompts;
- **`k=0`:** the evidence-enabled prompt/interface is retained, but zero retrieved evidence instances are supplied;
- **`w/o image description`:** image-veracity and consistency prompt paths omit the shared structured description;
- **`w/o both`:** both external evidence and the structured image description are removed according to the ablation setting.

The parser accepts the normalized line format above and, for factor-validator outputs, an equivalent strict JSON object for backend interoperability. Missing factors, invalid decisions, out-of-range confidence values, and malformed output are never silently mapped to a majority class.
