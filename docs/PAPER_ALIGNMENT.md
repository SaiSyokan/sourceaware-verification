# Paper-to-Code Alignment

This repository is aligned to the frozen main manuscript **Source-Aware Multimodal Disinformation Verification via Modality-Level Veracity and Cross-Modal Consistency**.

| Manuscript component | Repository implementation |
|---|---|
| Sec. III-A/B, Eqs. (1)-(6): modality veracity, pairwise consistency, and image-text factor space | `schema.py`, `routing.py`, `labels.py` |
| Sec. IV, Eq. (7): source-specific dataset harmonization | documented in the Supplemental Material; construction tooling remains in the OctantFake/WWW repository |
| Sec. V-A, Eqs. (8)-(11): input analyzer, active factors, and structured output | `InputAnalyzer.analyze`, `VerificationRouter.route`, `SourceAwareVerifier.predict` |
| Sec. V-A, Eq. (12): verifier output `q_f=(d_f,s_f,e_f)` | `FactorResult`, factor validators in `pipeline.py` |
| Sec. V-A, Eq. (13): factor-wise structured aggregation | `FACTORWISE_STRUCTURED_AGGREGATION`, `separate_structured` |
| Sec. V-A, Eq. (14): final structured factor prediction | `StructuredPrediction.final_decisions`, `label_from_decisions` |
| Sec. V-A/B, Eqs. (15)-(18): factor-level supervision and fine-tuning objective | `finetune.py`, `configs/finetune_llava34b_lora.yaml` |
| Sec. V-B: image/text evidence retrieval and image-text verification modules, including LVLM/LLM role separation | `evidence.py`, `prompts.py`, `pipeline.py`, `llava_backend.py`, `text_backend.py` |
| Sec. VI-A: zero-shot, task-specific, and ablation protocols | `docs/DATA.md`, `configs/` |
| Table III: zero-shot results | `results/table_iii_zero_shot.csv` |
| Table IV: task-specific training | `results/table_iv_supervised.csv` |
| Table V: verification and aggregation variants A-E | `configs/framework_ablation.yaml`, `results/table_v_verification_aggregation_ablation.csv` |
| Table VI: verification components and retrieval budget | `configs/module_ablation.yaml`, `results/table_vi_components_retrieval_ablation.csv` |

## Ablation strategy names

The executable strategy names map to manuscript variants as follows:

- **A** `holistic`: one-call direct 8-way prediction.
- **B** `joint_factors`: one call predicts the three binary factors, followed by deterministic 8-way mapping.
- **C** `separate_deterministic`: three independent factor-specific verifier calls; only their initial binary decisions are used.
- **D** `separate_structured`: the proposed method. Each factor is independently refined using only its own `(decision, confidence, explanation)` tuple, then deterministically mapped to the 8-way label.
- **E** `separate_cross_factor`: the same factor-specific verifier outputs as C/D, but aggregation has access to outputs from the other factors.

## Repository scope

The repository intentionally does not reimplement OctantFake source harmonization, reliability-control construction, or coverage-completion tooling. The scientific mapping rules are documented in the Supplemental Material; dataset construction/release tooling remains in the companion OctantFake/WWW artifact linked from the main README.
