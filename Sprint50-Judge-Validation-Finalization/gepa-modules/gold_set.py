"""
Gold set schema and loader for Sprint 50 Task A: Judge Validation.

A gold sample is one bilingually-reviewed reference translation with
human-assigned scores on the team's 6-dimension rubric (from the Sprint 46
GEMBA-MQM V2 framework) plus a reconciled overall score.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd

RUBRIC_DIMENSIONS = [
    "semantic_accuracy",
    "fluency",
    "tone_register",
    "emotional_consistency",
    "cultural_appropriateness",
    "dialect_correctness",
]

REQUIRED_COLUMNS = (
    ["sample_id", "direction", "source_en", "mt_output", "reference", "reviewer_ids"]
    + [f"{d}_gold" for d in RUBRIC_DIMENSIONS]
    + ["overall_gold", "notes"]
)


@dataclass
class GoldSample:
    sample_id: str
    direction: str                  # "EN_YUE" or "EN_CMN"
    source_en: str
    mt_output: str
    reference: Optional[str]
    reviewer_ids: str
    dim_scores: Dict[str, float]
    overall_gold: float
    notes: Optional[str] = None


def load_gold_set(csv_path: str) -> List[GoldSample]:
    df = pd.read_csv(csv_path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Gold set CSV is missing required columns: {missing}")

    samples = []
    for _, row in df.iterrows():
        dim_scores = {d: float(row[f"{d}_gold"]) for d in RUBRIC_DIMENSIONS}
        samples.append(
            GoldSample(
                sample_id=str(row["sample_id"]),
                direction=str(row["direction"]).upper(),
                source_en=str(row["source_en"]),
                mt_output=str(row["mt_output"]),
                reference=(str(row["reference"]) if pd.notna(row.get("reference")) else None),
                reviewer_ids=str(row["reviewer_ids"]),
                dim_scores=dim_scores,
                overall_gold=float(row["overall_gold"]),
                notes=(str(row["notes"]) if pd.notna(row.get("notes")) else None),
            )
        )
    return samples


def validate_gold_set(
    samples: List[GoldSample], min_per_direction: int = 30, max_per_direction: int = 50
) -> Dict:
    """Sanity checks: enough samples per direction, scores in range, no duplicate ids."""
    issues = []
    counts: Dict[str, int] = {}
    seen_ids = set()

    for s in samples:
        counts[s.direction] = counts.get(s.direction, 0) + 1
        if s.sample_id in seen_ids:
            issues.append(f"Duplicate sample_id: {s.sample_id}")
        seen_ids.add(s.sample_id)

        if not (1 <= s.overall_gold <= 10):
            issues.append(f"{s.sample_id}: overall_gold {s.overall_gold} out of 1-10 range")
        for dim, val in s.dim_scores.items():
            if not (1 <= val <= 10):
                issues.append(f"{s.sample_id}: {dim} score {val} out of 1-10 range")

    for direction, n in counts.items():
        if not (min_per_direction <= n <= int(max_per_direction * 1.2)):
            issues.append(f"Direction {direction} has {n} samples (expected {min_per_direction}-{max_per_direction})")

    return {"counts": counts, "issues": issues, "n_total": len(samples)}


def inter_annotator_agreement(raw_scores_a: List[float], raw_scores_b: List[float]) -> Dict[str, float]:
    """
    Optional sanity check on the gold set itself: if pre-reconciliation scores
    from both reviewers were kept, compare them before trusting the reconciled
    overall_gold as ground truth.
    """
    import numpy as np
    from scipy.stats import pearsonr

    a, b = np.array(raw_scores_a), np.array(raw_scores_b)
    mae = float(np.mean(np.abs(a - b)))
    r = float(pearsonr(a, b)[0]) if len(a) > 1 else float("nan")
    return {"mae": mae, "pearson_r": r}
