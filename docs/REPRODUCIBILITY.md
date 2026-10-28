# Reproducibility Guide

## Offline verification path

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
sourceaware validate examples/manifest.synthetic.jsonl
sourceaware evaluate examples/predictions.synthetic.jsonl
```

This verifies factor-space construction, modality routing, parser strictness, factor-instance conversion, structured aggregation, and metric calculation without network calls or benchmark media.

## Full zero-shot path

1. Request OctantFake access and materialize the official split locally.
2. Install and pin both the selected LLaVA checkpoint and the corresponding language-only checkpoint. For the 34B manuscript setting, the latter is `NousResearch/Nous-Hermes-2-Yi-34B`.
3. Collect image/text evidence with `k=3` and retain timestamps; see [`RETRIEVAL.md`](RETRIEVAL.md).
4. Run `separate_structured` with the normalized prompts in [`PROMPTS.md`](PROMPTS.md) and fixed decoding settings.
5. Evaluate the normalized predictions; archive predictions, metrics, config, environment, and run metadata together.

## Proprietary-model result records

Table III also reports five approaches under each of GPT-4V and GPT-6.1 Sol. These rows are transcribed in [`../results/table_iii_zero_shot.csv`](../results/table_iii_zero_shot.csv). The repository does not contain the original proprietary-model API/ChatGPT run records, sample-level predictions, or an executable backend for those models; the LLaVA/Hugging Face example above does not reproduce their results.

## Full supervised path

1. Use the fixed 7,200/800/800 train/validation/held-out protocol.
2. Generate 21,600 factor instances per epoch from the 7,200 training pairs.
3. Prepare the three factor-specific supervision instances described in [`TRAINING.md`](TRAINING.md), then run the original LoRA training configuration with frozen vision encoder.
4. Select the checkpoint using validation macro-F1 only.
5. Evaluate once on the held-out 800-sample test.

## Evidence caveat

Web evidence changes. A later reproduction can validate the method but may not receive identical results unless the original timestamped evidence bundle can be redistributed under source terms.
