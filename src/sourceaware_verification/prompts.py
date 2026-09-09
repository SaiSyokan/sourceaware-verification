"""Normalized prompt set corresponding to manuscript Appendix B."""

PROMPT_VERSION = "sourceaware-v0.1"

IMAGE_DESCRIPTION = """Role: Generate a structured description of the input image.
Input: [INPUT IMAGE]
Instruction:
You are given an image. Describe its visually observable content in a structured and factual manner.
Identify the following when visible:
- salient people, entities, or objects;
- actions and interactions;
- scene and environment;
- visible text, symbols, or signs;
- spatial or quantitative information;
- noticeable visual anomalies or potential manipulation cues.
Do not determine whether the image is true or false. Do not infer facts that are not supported by the visible content.
Return a concise structured description that can be used for subsequent verification.
Output: A concise structured image description."""

IMAGE_VERACITY = """Role: Verify the factual veracity of the image.
Input:
- [INPUT IMAGE]
- [IMAGE DESCRIPTION]
{image_description}
- [RETRIEVED IMAGE EVIDENCE]
{image_evidence}
Instruction:
Determine whether the input image contains a factual violation using the image itself, its structured description, and the retrieved evidence.
Evaluate materially checkable factual attributes such as identity, event, action, location, time, quantity, and other contextual information represented by the image.
Output F only when the available evidence supports identifying at least one material factual violation in the image.
Purely cosmetic modifications, such as ordinary color adjustment, cropping, or stylistic editing, should not be treated as factual violations unless they materially alter the factual meaning of the image.
If no factual violation is identified under the available evidence and verification setting, output T.
Return the result in the following format only:
Decision: [T/F]
Confidence: [0-1]
Explanation: [brief evidence-grounded explanation]"""

VERIFICATION_QUESTIONS = """Role: Generate focused fact-checking questions.
Input: [INPUT TEXT]
{text}
Instruction:
Based on the text, generate up to two specific fact-checking questions targeting its main factual claims.
- Focus only on claims that are verifiable or falsifiable.
- Prioritize claims that are central to the factual meaning of the text.
- Do not generate questions for subjective, trivial, or overly vague details.
Output: Up to two short verification questions, one per line."""

TEXT_VERACITY = """Role: Verify the factual veracity of the input text.
Input:
- [INPUT TEXT]
{text}
- [VERIFICATION QUESTIONS]
{questions}
- [RETRIEVED TEXTUAL EVIDENCE]
{text_evidence}
Instruction:
Determine whether the input text contains a factual violation using the verification questions and the retrieved evidence.
For each material factual claim:
- identify the relevant available evidence;
- determine whether the evidence supports, contradicts, or does not resolve the claim;
- distinguish factual claims from subjective, speculative, rhetorical, or emotional language.
Focus on verifiable information such as people or entities, events and actions, locations, times, quantities, and other factual relationships.
Output F only when the available evidence supports identifying at least one material factual violation in the text. Missing, incomplete, or inconclusive evidence alone should not be treated as a factual violation.
If no factual violation is identified under the available evidence and verification setting, output T.
Return the result in the following format only:
Decision: [T/F]
Confidence: [0-1]
Explanation: [brief evidence-grounded explanation]"""

IMAGE_TEXT_CONSISTENCY = """Role: Determine whether the image and text are semantically consistent.
Input:
- [IMAGE DESCRIPTION]
{image_description}
- [INPUT TEXT]
{text}
Instruction:
Compare the image and the text and determine whether they convey compatible information about the same situation.
Focus on salient relations involving entities, events, actions, location, time, quantity, and other context necessary to identify the described situation.
Judge only the relationship between the two modalities. Do not determine whether the image or the text is factually true in the real world.
Output F only when a semantic conflict is identified or when the two modalities clearly refer to different situations. Missing details in one modality do not by themselves imply inconsistency if the remaining information is still compatible.
Return the result in the following format only:
Decision: [T/F]
Confidence: [0-1]
Explanation: [brief explanation]"""

STRUCTURED_AGGREGATION = """Role: Produce the final structured prediction from factor-level validator outputs.
Input:
- [ACTIVE FACTOR OUTPUTS]
{factor_outputs}
- [AVAILABLE MODALITIES]
{modalities}
Instruction:
You are given the outputs of the active factor-level validators. Each output includes a decision, a confidence score, and a brief explanation.
Review them jointly and produce one final decision for each active factor.
Important rules:
- Preserve the distinction between modality-level veracity and cross-modal consistency.
- Do not replace the factor-level outputs with a single holistic true/false judgment.
- Do not infer a modality's veracity solely from the consistency decision.
- Do not infer consistency solely from the standalone veracity decisions.
- Use the confidence scores and explanations to resolve uncertain or weak factor outputs when appropriate.
- Do not predict factors corresponding to unavailable modalities.
Return exactly one line for each active factor using its supplied display name, followed by an optional Explanation line.
Example line: Image Veracity: T"""

HOLISTIC_EIGHT_WAY = """Predict one image-text label from TTT, TTF, TFT, TFF, FTT, FTF, FFT, or FFF.
The order is image veracity, text veracity, and image-text consistency.
Image description:
{image_description}
Text:
{text}
Image evidence:
{image_evidence}
Text evidence:
{text_evidence}
Return exactly: Label: [one valid label]"""

JOINT_FACTORS = """Jointly predict image veracity, text veracity, and image-text consistency.
Use T/F with the operational definitions supplied in the manuscript.
Image description:
{image_description}
Text:
{text}
Image evidence:
{image_evidence}
Text evidence:
{text_evidence}
Return exactly three lines:
Image Veracity: [T/F]
Text Veracity: [T/F]
Image-Text Consistency: [T/F]"""
