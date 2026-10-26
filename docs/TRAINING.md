# Factor-Level Fine-Tuning

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

## Preparing instances

```bash
sourceaware prepare-finetune --manifest train.jsonl --output train.factor-instances.jsonl
```

The command is deterministic and produces exactly three records per complete image-text sample. The resulting JSONL is intentionally compatible with an upstream LLaVA instruction-tuning adapter rather than embedding a fork of LLaVA in this repository.
