"""
GEPA (Gradient-Estimation-based Prompt Adaptation) Package
For DSPy-based translation prompt optimization.
"""

from .judge import JudgeModel, TranslationJudge
from .aggregator import RRWAAggregator, MultiRunJudge
from .optimizer import GEPAOptimizer

__version__ = "0.1.0"
__all__ = [
    "JudgeModel",
    "TranslationJudge",
    "RRWAAggregator",
    "MultiRunJudge",
    "GEPAOptimizer"
]