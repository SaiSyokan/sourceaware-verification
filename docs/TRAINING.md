# Factor-Level Fine-Tuning

Task-specific fine-tuning follows the same factor decomposition used during verification. Each complete labeled image-text pair

```text
(x_i, x_t; v_i, v_t, c_it)
```

is converted into three factor-specific supervision instances. External retrieval evidence is not used during fine-tuning; supervision targets only the factor-level `T/F` decisions.

## Settings explicitly stated in the frozen main manuscript

| Item | Value |
|---|---|
| Backbone | shared LLaVA-1.6-34B |
| Vision encoder | frozen |
| Adaptation | LoRA |
| Training instances | three factor-specific instances per complete image-text pair |
| Supervised target | factor-level `T/F` decision only; confidence/explanation are not supervision targets |
| Checkpoint selection | highest validation macro-F1 |
| Retrieval during fine-tuning | none |

## Factor-specific supervision instances

| Factor | Input | Task instruction | Target |
|---|---|---|---|
| Image veracity | input image | Determine whether the image contains a factual violation according to the operational definition of image veracity. | `v_i` |
| Text veracity | input text | Determine whether the text contains a factual violation according to the operational definition of text veracity. | `v_t` |
| Image-text consistency | input image + text | Determine whether a salient semantic conflict is present between the image and text. Return F if a conflict is present and T otherwise, without judging their standalone factual veracity. | `c_it` |

The executable instruction strings are defined in [`src/sourceaware_verification/finetune.py`](../src/sourceaware_verification/finetune.py).

### Image-veracity training instance

```text
Input: [INPUT IMAGE]
Instruction: Determine whether the image contains a factual violation according to the operational definition of image veracity.
Target: T or F, according to v_i.
```

### Text-veracity training instance

```text
Input: [INPUT TEXT]
Instruction: Determine whether the text contains a factual violation according to the operational definition of text veracity.
Target: T or F, according to v_t.
```

### Image-text consistency training instance

```text
Input: [INPUT IMAGE] + [INPUT TEXT]
Instruction: Determine whether a salient semantic conflict is present between the image and text. Return F if a conflict is present and T otherwise, without judging their standalone factual veracity.
Target: T or F, according to c_it.
```

Only the factor-level decision is used as the supervised target. Confidence scores and explanations are not treated as ground-truth supervision. For example, a sample with image-veracity label `v_i=F` yields an image-veracity instance whose target is simply `F`; the model is not trained directly on the final eight-case label.

The three instance types share one fine-tuned LLaVA-1.6-34B backbone. This task-specific training setup is separate from the zero-shot LVLM/LLM role split used by the inference pipeline.

## Preparing instances

```bash
sourceaware prepare-finetune --manifest train.jsonl --output train.factor-instances.jsonl
```

The command is deterministic and produces exactly three records per complete image-text sample. The resulting JSONL is intentionally compatible with an upstream LLaVA instruction-tuning adapter rather than embedding a fork of LLaVA in this repository.

For the paper protocol, 7,200 training pairs produce 21,600 factor-specific instances per epoch.

## Repository-carried values requiring original-run confirmation

Earlier versions of this review artifact recorded the following training values. They are retained in `configs/finetune_llava34b_lora.yaml` for traceability, but the frozen main manuscript does not state them. Confirm them against the original training command/log before archival release or before claiming exact reproduction:

| Item | Repository-carried value |
|---|---|
| Optimizer | AdamW |
| Learning rate | 2e-5 |
| Effective batch size | 64 |
| LoRA rank | 16 |
| LoRA dropout | 0.05 |
| Maximum epochs | 3 |
| Instances per epoch | 21,600 |
| Approximate maximum steps | 1,014 |

The LoRA alpha/target modules, micro-batch and gradient-accumulation decomposition, optimizer beta/epsilon/weight decay, learning-rate schedule/warmup, numerical precision, gradient clipping, random seeds, checkpoint cadence, and GPU topology are also not established by the frozen manuscript. These values must not be guessed.
