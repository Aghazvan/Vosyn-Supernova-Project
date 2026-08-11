"""
Multi-run aggregation for robust judge scoring.

Classes:
    RRWAAggregator: Robust Round-Robin Weighted Averaging
    MultiRunJudge: Judge wrapper with multi-run aggregation
"""

import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RRWAAggregator:
    """Robust Round-Robin Weighted Averaging (RRWA).
    
    Aggregates multiple judge runs to produce stable, reliable scores.
    
    Example:
        >>> aggregator = RRWAAggregator(num_runs=10)
        >>> scores = [8, 8, 7, 8, 9, 8, 8, 8, 7, 8]
        >>> result = aggregator.aggregate_scores(scores)
        >>> print(f"Final: {result['final_score']}, Stability: {result['stability']}")
    """
    
    WEIGHTING_SCHEMES = ["median", "mean", "trimmed_mean", "iqr_weighted"]
    
    def __init__(self, num_runs: int = 10, weighting_scheme: str = "median"):
        """
        Initialize aggregator.
        
        Args:
            num_runs: Number of judge runs per input
            weighting_scheme: Method to aggregate scores
                - "median": Use median (robust to outliers)
                - "mean": Use arithmetic mean
                - "trimmed_mean": Remove top/bottom 20%
                - "iqr_weighted": Weight by inverse of IQR
        """
        if weighting_scheme not in self.WEIGHTING_SCHEMES:
            raise ValueError(f"Scheme must be one of {self.WEIGHTING_SCHEMES}")
        
        self.num_runs = num_runs
        self.weighting_scheme = weighting_scheme
    
    def aggregate_scores(self, scores: List[int]) -> Dict:
        """
        Aggregate multiple judge runs into stable score + metrics.
        
        Args:
            scores: List of scores from N judge runs
        
        Returns:
            {
                "final_score": float (0-10),
                "mean": float,
                "median": float,
                "std": float,
                "stability": float (0-1, higher = more stable),
                "all_scores": list,
                "scheme_used": str
            }
        """
        scores = np.array(scores, dtype=float)
        
        # Basic statistics
        mean_score = np.mean(scores)
        median_score = np.median(scores)
        std_score = np.std(scores)
        
        # Stability: 1 - (normalized std dev)
        # Normalize by max possible std (5.0 for scores 0-10)
        max_std = 5.0
        stability = max(0, 1.0 - (std_score / max_std))
        
        # Select final score based on scheme
        if self.weighting_scheme == "median":
            final_score = median_score
        
        elif self.weighting_scheme == "mean":
            final_score = mean_score
        
        elif self.weighting_scheme == "trimmed_mean":
            # Remove scores in bottom 20% and top 20%
            lower_bound = np.percentile(scores, 20)
            upper_bound = np.percentile(scores, 80)
            trimmed = scores[(scores >= lower_bound) & (scores <= upper_bound)]
            final_score = np.mean(trimmed) if len(trimmed) > 0 else median_score
        
        elif self.weighting_scheme == "iqr_weighted":
            # Weight scores by inverse of IQR distance
            q1, q3 = np.percentile(scores, [25, 75])
            iqr = q3 - q1 if q3 > q1 else 1.0
            
            # Weights: higher for scores near median
            weights = 1.0 / (1.0 + np.abs(scores - median_score) / iqr)
            weights = weights / np.sum(weights)
            
            final_score = np.sum(scores * weights)
        
        else:
            final_score = median_score
        
        return {
            "final_score": round(final_score, 2),
            "mean": round(mean_score, 2),
            "median": round(median_score, 2),
            "std": round(std_score, 2),
            "stability": round(stability, 3),
            "all_scores": list(scores),
            "scheme_used": self.weighting_scheme
        }


class MultiRunJudge:
    """Judge wrapper that performs multi-run aggregation for stable scores.
    
    Example:
        >>> judge = JudgeModel(model_choice="gpt-4o")
        >>> multi_judge = MultiRunJudge(judge, num_runs=10)
        >>> result = multi_judge.evaluate_stable(
        ...     english="Hello",
        ...     cantonese="你好"
        ... )
        >>> print(f"Score: {result['final_score']}/10, Stability: {result['stability']}")
    """
    
    def __init__(
        self,
        judge,
        num_runs: int = 10,
        aggregation_scheme: str = "median",
        verbose: bool = False
    ):
        """
        Initialize multi-run judge.
        
        Args:
            judge: JudgeModel instance
            num_runs: Number of times to run judge per input
            aggregation_scheme: RRWA scheme
            verbose: Print progress
        """
        self.judge = judge
        self.num_runs = num_runs
        self.verbose = verbose
        self.aggregator = RRWAAggregator(
            num_runs=num_runs,
            weighting_scheme=aggregation_scheme
        )
    
    def evaluate_stable(
        self,
        english: str,
        cantonese: str = "",
        mandarin: str = "",
        show_progress: bool = True
    ) -> Dict:
        """
        Run judge N times and return aggregated score with stability metrics.
        
        Args:
            english: Source English text
            cantonese: Cantonese translation
            mandarin: Mandarin translation
            show_progress: Print progress to stdout
        
        Returns:
            {
                "final_score": float,
                "stability": float,
                "mean": float,
                "median": float,
                "std": float,
                "individual_scores": list,
                "sample_feedback": str,
                "num_successful_runs": int
            }
        """
        scores = []
        feedbacks = []
        
        if show_progress:
            print(f"Running judge {self.num_runs} times...")
        
        for run_num in range(self.num_runs):
            result = self.judge.evaluate(english, cantonese, mandarin)
            
            if result['success']:
                scores.append(result['score'])
                feedbacks.append(result['feedback'])
            else:
                if self.verbose:
                    logger.warning(f"Run {run_num + 1} failed: {result['error']}")
            
            if show_progress:
                status = f"✓" if result['success'] else "✗"
                print(f"  {status} Run {run_num + 1}/{self.num_runs}: Score = {result['score']}")
        
        # Aggregate
        if len(scores) == 0:
            logger.error("No successful judge runs!")
            return {
                "final_score": None,
                "stability": 0.0,
                "individual_scores": [],
                "num_successful_runs": 0
            }
        
        aggregation = self.aggregator.aggregate_scores(scores)
        
        return {
            "final_score": aggregation['final_score'],
            "stability": aggregation['stability'],
            "mean": aggregation['mean'],
            "median": aggregation['median'],
            "std": aggregation['std'],
            "individual_scores": aggregation['all_scores'],
            "sample_feedback": feedbacks[0] if feedbacks else None,
            "num_successful_runs": len(scores),
            "aggregation_scheme": aggregation['scheme_used']
        }
    
    def batch_evaluate_stable(self, examples: list, language: str = "both") -> list:
        """
        Evaluate multiple examples with stability aggregation.
        
        Args:
            examples: List of translation examples
            language: "cantonese", "mandarin", or "both"
        
        Returns:
            List of aggregated evaluation results
        """
        results = []
        
        for i, example in enumerate(examples):
            print(f"\n[Example {i + 1}/{len(examples)}]")
            
            result = self.evaluate_stable(
                english=example.get("english", ""),
                cantonese=example.get("cantonese", "") if language in ["cantonese", "both"] else "",
                mandarin=example.get("mandarin", "") if language in ["mandarin", "both"] else "",
                show_progress=False
            )
            result["example_id"] = i
            results.append(result)
        
        return results