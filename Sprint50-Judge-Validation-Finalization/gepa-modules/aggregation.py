"""
Robust aggregation for multi-run judge scoring (Sprint 50 Task A).

Extends the Sprint 48 GEMBA-inspired RRWA formula with explicit handling for:
  - malformed judge output (failed parse / out-of-range values)
  - suspicious zero-like scores (outliers relative to the sample's own other
    runs, likely a parsing miss or refusal rather than a genuine 1/10)
  - high inter-run disagreement (falls back to plain median instead of the
    confidence-weighted mean, since weighting assumes the spread is noise
    around a real signal, not the judge genuinely being split)

Returns a dict, not a bare float, so GEPA and any reporting downstream can
tell a confident score apart from a shaky one instead of it being silently
folded into a simple average.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import statistics as stats

SCORE_MIN, SCORE_MAX = 1.0, 10.0
ZERO_OUTLIER_STD_THRESHOLD = 2.0       # low scores this many std devs below median get flagged
HIGH_DISAGREEMENT_STD = 1.5            # std at/above this triggers median fallback
MIN_VALID_RUNS_FOR_SCORE = 2           # fewer valid runs than this -> judge_failed
MALFORMED_RUN_FAILURE_FRACTION = 0.5   # >=50% malformed runs -> judge_failed
GEMBA_LAMBDA = 0.5                     # Sprint 48 RRWA weighting parameter


@dataclass
class RunResult:
    """One raw judge call's outcome for a single sample."""
    score: Optional[float]     # None if parsing failed
    parse_ok: bool
    raw_response: Optional[str] = None


def _is_out_of_range(score: float) -> bool:
    return not (SCORE_MIN <= score <= SCORE_MAX)


def aggregate_runs(runs: List[RunResult]) -> Dict[str, Any]:
    """Aggregate N raw judge runs for one sample into a score + confidence signal."""
    n_total = len(runs)

    # Step 1: separate malformed / out-of-range runs from valid numeric ones.
    valid_scores: List[float] = []
    malformed_count = 0
    for r in runs:
        if not r.parse_ok or r.score is None or _is_out_of_range(r.score):
            malformed_count += 1
        else:
            valid_scores.append(r.score)

    malformed_fraction = malformed_count / n_total if n_total else 1.0

    if malformed_fraction >= MALFORMED_RUN_FAILURE_FRACTION or len(valid_scores) < MIN_VALID_RUNS_FOR_SCORE:
        return {
            "final_score": None,
            "confidence": 0.0,
            "flag": "judge_failed",
            "aggregation_method": None,
            "n_total_runs": n_total,
            "n_valid_runs": len(valid_scores),
            "malformed_fraction": round(malformed_fraction, 3),
            "flagged_outlier_scores": [],
            "valid_scores": valid_scores,
        }

    # Step 2: flag suspicious near-zero outliers relative to this sample's own runs.
    median = stats.median(valid_scores)
    std = stats.pstdev(valid_scores) if len(valid_scores) > 1 else 0.0

    clean_scores, flagged_outliers = [], []
    for s in valid_scores:
        is_low_outlier = std > 0 and (median - s) > ZERO_OUTLIER_STD_THRESHOLD * std
        if s <= 1.0 and is_low_outlier:
            flagged_outliers.append(s)
        else:
            clean_scores.append(s)

    # If every run got flagged (all similarly low), don't over-strip -- that's
    # likely a genuinely bad translation, not a parsing artifact.
    scores_for_agg = clean_scores if clean_scores else valid_scores

    # Step 3: recompute on the cleaned set and pick an aggregation strategy.
    median2 = stats.median(scores_for_agg)
    std2 = stats.pstdev(scores_for_agg) if len(scores_for_agg) > 1 else 0.0
    stability = max(0.0, 1 - std2 / 5.0)
    high_disagreement = std2 >= HIGH_DISAGREEMENT_STD

    if high_disagreement:
        final_score = median2  # robust to a single remaining bad run
        agg_method = "median_fallback_high_disagreement"
    else:
        weights = [1.0 / (1.0 + GEMBA_LAMBDA * abs(s - median2)) for s in scores_for_agg]
        wsum = sum(weights)
        final_score = sum(w * s for w, s in zip(weights, scores_for_agg)) / wsum
        agg_method = "gemba_weighted_mean"

    flag = "ok"
    if flagged_outliers:
        flag = "zero_outliers_excluded"
    if high_disagreement:
        flag = "high_disagreement" if flag == "ok" else flag + "+high_disagreement"

    return {
        "final_score": round(final_score, 3),
        "confidence": round(stability, 3),
        "flag": flag,
        "aggregation_method": agg_method,
        "n_total_runs": n_total,
        "n_valid_runs": len(valid_scores),
        "n_used_in_final": len(scores_for_agg),
        "malformed_fraction": round(malformed_fraction, 3),
        "flagged_outlier_scores": flagged_outliers,
        "median": round(median2, 3),
        "std": round(std2, 3),
        "valid_scores": valid_scores,
    }
