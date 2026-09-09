# Paper-to-Code Alignment

| Manuscript component | Repository implementation |
|---|---|
| Sec. III, Eqs. (1)-(7): modality veracity and pairwise consistency space | `schema.py`, `routing.py` |
| Sec. V-A, Eq. (8): input analyzer | `InputAnalyzer.analyze` |
| Sec. V-A/B, Eqs. (9)-(13): active verification factors | `VerificationRouter.route`, `SourceAwareVerifier.predict` |
| Sec. V-C, Eqs. (14)-(16): factor-level supervision | `finetune.py`, `configs/finetune_llava34b_lora.yaml` |
| Appendix B: normalized prompts and output protocol | `prompts.py`, `parsing.py` |
| Appendix C-A: Google Vision Web Detection | `evidence.collect_image_evidence` |
| Appendix C-B: Google Custom Search | `evidence.collect_text_evidence` |
| Appendix C-C: three instances per image-text sample | `factor_instances` |
| Sec. VI-A: zero-shot and supervised splits | `docs/DATA.md`, `configs/` |
| Table III: zero-shot results | `results/table_iii_zero_shot.csv` |
| Table IV: task-specific training | `results/table_iv_supervised.csv` |
| Table V: modality configurations | `results/table_v_modalities.csv` |
| Tables VI-VII: ablations | `pipeline.py`, `results/table_vi_framework_ablation.csv`, `table_vii_module_ablation.csv` |

The repository intentionally does not reimplement the dataset construction stages in Sec. IV and Appendix D. Those belong to the published OctantFake/WWW artifact and are linked from the main README.

