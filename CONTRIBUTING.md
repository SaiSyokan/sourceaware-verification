# Contributing

During submission preparation and peer review, changes should be limited to correctness, reproducibility, documentation, and compatibility fixes. Do not change the fixed dataset split, reported values, prompt semantics, or default retrieval budget without documenting the difference from the corresponding manuscript version.

Before proposing a change, run:

```bash
python -m unittest discover -s tests -v
sourceaware validate examples/manifest.synthetic.jsonl
sourceaware evaluate examples/predictions.synthetic.jsonl
```

Never contribute credentials, OctantFake media, private reviewer correspondence, model checkpoints, or retrieved webpage content without explicit redistribution rights.
