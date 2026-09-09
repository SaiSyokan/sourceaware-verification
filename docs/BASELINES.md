# Baseline Reproduction Notes

The manuscript evaluates SNIFFER, FKA-Owl, DEFAME, and MMD-Agent without task-specific fine-tuning at comparable 7B, 13B, and 34B scales, plus GPT-4V as a proprietary reference. Fakeddit and MTTV are the supervised baselines.

Third-party repositories are not copied here. Their method-specific reasoning, retrieval, and tool-use procedures should be preserved, while their final outputs must be normalized to the ordered OctantFake labels and scored with `sourceaware evaluate`.

Before submission, record for every baseline:

- official repository URL and exact commit hash;
- model/checkpoint identifier and checksum;
- environment and hardware;
- prompt/config file used;
- input and evidence availability;
- random seed and decoding configuration;
- raw output path and normalization log.

Do not infer missing labels from malformed output. Invalid or missing predictions count as incorrect, matching the paper protocol.

