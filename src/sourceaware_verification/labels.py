"""Image-text label mapping for the paper's ordered factor tuple."""

LABELS = ("TTT", "TTF", "TFT", "TFF", "FTT", "FTF", "FFT", "FFF")

IMAGE_FACTOR = "veracity:image"
TEXT_FACTOR = "veracity:text"
CONSISTENCY_FACTOR = "consistency:image:text"


def label_from_decisions(decisions: dict[str, str]) -> str | None:
    required = (IMAGE_FACTOR, TEXT_FACTOR, CONSISTENCY_FACTOR)
    if not all(key in decisions for key in required):
        return None
    label = "".join(str(decisions[key]).upper() for key in required)
    if label not in LABELS:
        raise ValueError(f"invalid image-text factor tuple: {label!r}")
    return label


def decisions_from_label(label: str) -> dict[str, str]:
    normalized = label.strip().upper()
    if normalized not in LABELS:
        raise ValueError(f"invalid image-text label: {label!r}")
    return {
        IMAGE_FACTOR: normalized[0],
        TEXT_FACTOR: normalized[1],
        CONSISTENCY_FACTOR: normalized[2],
    }

