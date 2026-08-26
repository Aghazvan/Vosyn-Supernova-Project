"""
Agreement metrics: how well each judge configuration tracks the human gold
labels, per language direction -- the core comparison for Task A.
"""
from typing import List, Dict
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr


def _weighted_kappa(gold: np.ndarray, pred: np.ndarray, n_buckets: int = 10) -> float:
    """Quadratic-weighted Cohen's kappa on 1-10 scores rounded to the nearest bucket."""
    from sklearn.metrics import cohen_kappa_score

    g = np.clip(np.round(gold), 1, n_buckets).astype(int)
    p = np.clip(np.round(pred), 1, n_buckets).astype(int)
    return float(cohen_kappa_score(g, p, weights="quadratic"))


def compute_agreement(gold: List[float], judged: List[float]) -> Dict[str, float]:
    """
    Pass only rows where the judge produced a numeric score (judge_flag !=
    'judge_failed') -- filter those out with compare_configs() below, which
    reports coverage separately so a config isn't rewarded for silently
    dropping the samples it struggled with.
    """
    gold_arr, judged_arr = np.array(gold, dtype=float), np.array(judged, dtype=float)
    if len(gold_arr) < 2:
        return {
            "pearson_r": float("nan"),
            "spearman_rho": float("nan"),
            "mae": float("nan"),
            "weighted_kappa": float("nan"),
            "n": len(gold_arr),
        }

    pearson_r = float(pearsonr(gold_arr, judged_arr)[0])
    spearman_rho = float(spearmanr(gold_arr, judged_arr)[0])
    mae = float(np.mean(np.abs(gold_arr - judged_arr)))
    kappa = _weighted_kappa(gold_arr, judged_arr)

    return {
        "pearson_r": round(pearson_r, 3),
        "spearman_rho": round(spearman_rho, 3),
        "mae": round(mae, 3),
        "weighted_kappa": round(kappa, 3),
        "n": len(gold_arr),
    }


def compare_configs(scored_df: pd.DataFrame) -> pd.DataFrame:
    """
    scored_df: output of scoring_harness.score_gold_set_with_all_configs().
    Returns one row per (config_name, direction) with agreement metrics plus
    coverage -- the fraction of gold samples the config actually scored,
    since a high-agreement config that silently failed on 20% of samples is
    not the same as one that scored everything reliably.
    """
    results = []
    for (config_name, direction), group in scored_df.groupby(["config_name", "direction"]):
        n_total = len(group)
        usable = group[group["judge_flag"] != "judge_failed"]
        n_failed = n_total - len(usable)

        metrics = compute_agreement(usable["gold_overall"].tolist(), usable["judge_final_score"].tolist())
        results.append(
            {
                "config_name": config_name,
                "direction": direction,
                "n_total_samples": n_total,
                "n_judge_failed": n_failed,
                "coverage": round(len(usable) / n_total, 3) if n_total else 0.0,
                **metrics,
            }
        )

    out = pd.DataFrame(results)
    return out.sort_values(["direction", "spearman_rho"], ascending=[True, False])


def select_final_config(comparison_df: pd.DataFrame, min_coverage: float = 0.9) -> pd.DataFrame:
    """
    Picks the winning config per direction: highest Spearman rho among
    configs meeting the coverage bar, tie-broken by lower MAE. Falls back to
    the full candidate set if nothing clears the coverage bar, rather than
    returning an empty result.
    """
    eligible = comparison_df[comparison_df["coverage"] >= min_coverage]
    if eligible.empty:
        eligible = comparison_df

    winners = (
        eligible.sort_values(["spearman_rho", "mae"], ascending=[False, True])
        .groupby("direction")
        .first()
        .reset_index()
    )
    return winners
