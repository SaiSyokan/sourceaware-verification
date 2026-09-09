# Factor-Level Fine-Tuning

## Recorded manuscript configuration

| Item | Value |
|---|---|
| Backbone | shared LLaVA-1.6-34B |
| Vision encoder | frozen |
| Adaptation | LoRA |
| Optimizer | AdamW |
| Learning rate | 2e-5 |
| Effective batch size | 64 |
| LoRA rank | 16 |
| LoRA dropout | 0.05 |
| Maximum epochs | 3 |
| Instances per epoch | 21,600 |
| Maximum optimization steps | approximately 1,014 |
| Checkpoint selection | highest validation macro-F1 |
| Retrieval during fine-tuning | none |
| Supervised target | factor decision only; no confidence/explanation target |

## Fields requiring confirmation from the original run

The current manuscript does not state the LoRA alpha/target modules, micro-batch and gradient-accumulation decomposition, optimizer beta/epsilon/weight decay, learning-rate schedule/warmup, numerical precision, gradient clipping, random seeds, checkpoint cadence, or GPU topology. These values must be taken from the original training command/log rather than guessed. They are represented as `null` in `configs/finetune_llava34b_lora.yaml` so this repository does not make unsupported reproducibility claims.

## Preparing instances

```bash
sourceaware prepare-finetune --manifest train.jsonl --output train.factor-instances.jsonl
```

The command is deterministic and produces exactly three records per complete image-text sample. The resulting JSONL is intentionally compatible with an upstream LLaVA instruction-tuning adapter rather than embedding a fork of LLaVA in this repository.
