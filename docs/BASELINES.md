# Baseline Reproduction Notes

The manuscript evaluates SNIFFER, FKA-Owl, DEFAME, MMD-Agent, and our source-aware framework without task-specific fine-tuning at comparable 7B, 13B, and 34B open-source model scales. All five approaches are also evaluated with GPT-4V and GPT-6.1 Sol as proprietary multimodal backbones. Fakeddit and MTTV are the supervised baselines.

Third-party repositories are not copied here. Their method-specific reasoning, retrieval, and tool-use procedures should be preserved, while their final outputs must be normalized to the ordered OctantFake labels and scored with `sourceaware evaluate`. The GPT-4V and GPT-6.1 Sol rows are reported aggregate results; this repository does not provide a proprietary-model inference backend or the original per-sample outputs.

Before submission, record for every baseline:

- official repository URL and exact commit hash;
- model/checkpoint identifier and checksum;
- environment and hardware;
- prompt/config file used;
- input and evidence availability;
- random seed and decoding configuration;
- raw output path and normalization log.

Do not infer missing labels from malformed output. Invalid or missing predictions count as incorrect, matching the paper protocol.

