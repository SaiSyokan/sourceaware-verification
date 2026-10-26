# Reported Aggregate Results

These CSV files are machine-readable transcriptions of the aggregate values in the frozen main manuscript Tables III-VI. They make result claims easy to audit and plot; they are not substitutes for raw predictions.

- `table_iii_zero_shot.csv`: Table III, zero-shot results on the 8,000-sample test split
- `table_iv_supervised.csv`: Table IV, task-specific training on the 800-sample held-out test split
- `table_v_verification_aggregation_ablation.csv`: Table V, verification/aggregation variants A-E
- `table_vi_components_retrieval_ablation.csv`: Table VI, evidence, image-description, and retrieval-budget analysis

Percentages are stored on the manuscript's 0-100 scale. The selected retrieval setting is `k=3`; alternative test-set `k` values are sensitivity results rather than hyperparameter-selection results.
