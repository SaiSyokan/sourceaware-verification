"""Source-aware multimodal disinformation verification."""

from .pipeline import SourceAwareVerifier
from .routing import InputAnalyzer, VerificationRouter
from .schema import FactorKey, FactorResult, StructuredPrediction

__all__ = [
    "FactorKey",
    "FactorResult",
    "InputAnalyzer",
    "SourceAwareVerifier",
    "StructuredPrediction",
    "VerificationRouter",
]

__version__ = "0.1.0"

