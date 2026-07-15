"""
Utility functions for GEPA pipeline.
"""

import pandas as pd
import json
from typing import Dict, List
import logging


def create_results_dataframe(results: List[Dict]) -> pd.DataFrame:
    """Convert evaluation results to pandas DataFrame."""
    return pd.DataFrame(results)


def save_results_json(results: List[Dict], filepath: str) -> None:
    """Save results to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)


def log_validation_summary(results: Dict) -> None:
    """Print validation summary."""
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("VALIDATION SUMMARY")
    logger.info("="*80)
    
    for key, value in results.items():
        logger.info(f"{key}: {value}")


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )