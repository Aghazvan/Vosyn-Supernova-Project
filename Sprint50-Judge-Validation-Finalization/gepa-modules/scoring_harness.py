"""
Scoring harness: run each proposed judge configuration over the gold set and
collect aggregated scores alongside the human gold labels.

Plugs into whichever judge backend is live this sprint (Groq JudgeModel from
Sprint 47/48, the local Qwen3 LocalJudgeModel from Sprint 49, or a new
config) through a simple callable interface -- this harness doesn't need to
know which backend produced the scores, only that it returns a RunResult.
"""
from dataclasses import dataclass
from typing import Callable, List
import pandas as pd

from aggregation import RunResult, aggregate_runs
from gold_set import GoldSample

# A JudgeCallable takes (english, translated, direction) and returns a RunResult.
JudgeCallable = Callable[[str, str, str], RunResult]


@dataclass
class JudgeConfig:
    name: str          # e.g. "groq_llama33_gemba_rrwa", "local_qwen3_v2"
    judge_fn: JudgeCallable
    num_runs: int = 3
    notes: str = ""


def score_gold_set_with_config(config: JudgeConfig, gold_set: List[GoldSample]) -> pd.DataFrame:
    """Runs config.judge_fn config.num_runs times per gold sample and aggregates each."""
    rows = []
    for sample in gold_set:
        raw_runs = [
            config.judge_fn(sample.source_en, sample.mt_output, sample.direction)
            for _ in range(config.num_runs)
        ]
        agg = aggregate_runs(raw_runs)
        rows.append(
            {
                "config_name": config.name,
                "sample_id": sample.sample_id,
                "direction": sample.direction,
                "gold_overall": sample.overall_gold,
                "judge_final_score": agg["final_score"],
                "judge_confidence": agg["confidence"],
                "judge_flag": agg["flag"],
                "n_valid_runs": agg["n_valid_runs"],
                "n_total_runs": agg["n_total_runs"],
            }
        )
    return pd.DataFrame(rows)


def score_gold_set_with_all_configs(configs: List[JudgeConfig], gold_set: List[GoldSample]) -> pd.DataFrame:
    frames = [score_gold_set_with_config(c, gold_set) for c in configs]
    return pd.concat(frames, ignore_index=True)
