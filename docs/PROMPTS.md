# Prompt Protocol

The executable normalized prompts are stored in `src/sourceaware_verification/prompts.py`. They correspond to the manuscript Appendix B and implement three principles:

1. factor separation: image veracity, text veracity, and cross-modal consistency are judged independently;
2. evidence grounding: `F` requires an identifiable violation; missing evidence alone is not a violation;
3. factorized aggregation: aggregation may reconsider weak/conflicting module outputs but cannot collapse them into one holistic decision.

Every factor validator returns:

```text
Decision: T or F
Confidence: a real number in [0, 1]
Explanation: a brief input/evidence-grounded reason
```

The image description is generated once and reused by image-veracity and image-text consistency modules. The question generator produces at most two questions. The original input text, not those questions and not image information, is the Google Custom Search query.

The parser accepts the manuscript line format and an equivalent strict JSON object for backend interoperability. Missing factors, invalid decisions, out-of-range confidence values, and malformed output are never silently mapped to a majority class.

