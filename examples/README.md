# Synthetic Examples

These records demonstrate schemas and offline commands. They are not OctantFake samples, the image path intentionally does not exist, and the `.invalid` evidence URLs cannot resolve.

Run manifest validation without `--check-files` and evaluate the complete synthetic prediction set:

```bash
sourceaware validate examples/manifest.synthetic.jsonl
sourceaware evaluate examples/predictions.synthetic.jsonl
sourceaware evaluate-factors examples/factor_predictions.synthetic.jsonl
```
