#!/usr/bin/env python3
"""Evaluate both OpenCC script checks on Andromeda's 33 orthography records.

For EN->YUE, traditional Chinese is the expected output. Therefore:
- check_traditional_script detects Simplified-form contamination (positive label:
  simplified_script).
- check_simplified_script detects Traditional characters (positive labels:
  standard_written_chinese and mixed_script).
The four Telugu mixed_script records are reported as not applicable.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gepa.checks import (  # noqa: E402
    CheckUnavailableError,
    check_simplified_script,
    check_traditional_script,
)

SOURCE = ROOT / "data/raw/andromeda/dataset_v7.jsonl"
OUTPUT = ROOT / "reports/script_check_evaluation.json"
TARGET_LABELS = {"standard_written_chinese", "simplified_script", "mixed_script"}
CHINESE_PAIR = "en-yue"


def _new_counts():
    return {"n": 0, "correct": 0, "tp": 0, "fp": 0, "tn": 0, "fn": 0}


def _record(bucket, truth: bool, predicted: bool) -> None:
    bucket["n"] += 1
    key = ("tp" if truth else "fp") if predicted else ("fn" if truth else "tn")
    bucket[key] += 1
    bucket["correct"] += int(truth == predicted)


def _finish(grouped):
    result = {}
    for label, counts in sorted(grouped.items()):
        row = dict(counts)
        row["accuracy"] = round(row["correct"] / row["n"], 4) if row["n"] else None
        result[label] = row
    total_n = sum(row["n"] for row in grouped.values())
    total_correct = sum(row["correct"] for row in grouped.values())
    return {
        "by_sublabel": result,
        "overall": {
            "n": total_n,
            "correct": total_correct,
            "accuracy": round(total_correct / total_n, 4) if total_n else None,
        },
    }


def main() -> int:
    rows = [json.loads(line) for line in SOURCE.open(encoding="utf-8") if line.strip()]
    grouped_simplified = defaultdict(_new_counts)
    grouped_traditional = defaultdict(_new_counts)
    not_applicable = defaultdict(int)
    labelled_rows = []
    for row in rows:
        labels = {
            error.get("error_type")
            for error in (row.get("errors") or [])
            if isinstance(error, dict)
        } & TARGET_LABELS
        if labels:
            if len(labels) != 1:
                raise ValueError(f"Expected one orthography label for {row.get('id')}: {labels}")
            labelled_rows.append((row, next(iter(labels))))
    total_labelled = len(labelled_rows)
    chinese_rows = []
    for row, label in labelled_rows:
        if row.get("language_pair") == CHINESE_PAIR:
            chinese_rows.append((row, label))
        else:
            not_applicable[f"{row.get('language_pair')}::{label}"] += 1

    try:
        for row, label in chinese_rows:
            candidate = row.get("candidate_translation") or ""
            simplified_result = check_simplified_script(candidate)
            traditional_result = check_traditional_script(candidate)

            # A traditional-character detector should fire on standard written
            # Chinese and mixed-script Cantonese, but not simplified_script rows.
            simplified_truth = label in {"standard_written_chinese", "mixed_script"}
            _record(grouped_simplified[label], simplified_truth, not simplified_result.passed)

            # A simplified-character detector should fire on simplified_script rows.
            traditional_truth = label == "simplified_script"
            _record(grouped_traditional[label], traditional_truth, not traditional_result.passed)
    except CheckUnavailableError as exc:
        report = {
            "status": "blocked_dependency_missing",
            "reason": str(exc),
            "labelled_records": total_labelled,
            "chinese_applicable_records": len(chinese_rows),
            "expected_labelled_records": 33,
            "non_chinese_not_applicable": dict(not_applicable),
            "check_simplified_script": None,
            "check_traditional_script": None,
        }
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    report = {
        "status": "completed",
        "evaluation_set": "Andromeda dataset_v7.jsonl / all 33 script_orthography records",
        "labelled_records": total_labelled,
        "chinese_applicable_records": sum(x["n"] for x in grouped_simplified.values()),
        "non_chinese_not_applicable": dict(not_applicable),
        "check_simplified_script": {
            "prediction_semantics": "flag if OpenCC t2s changes candidate text (Traditional characters present)",
            "positive_labels": ["standard_written_chinese", "mixed_script"],
            **_finish(grouped_simplified),
        },
        "check_traditional_script": {
            "prediction_semantics": "flag if OpenCC s2t changes candidate text (Simplified-form characters present)",
            "positive_labels": ["simplified_script"],
            **_finish(grouped_traditional),
        },
        "notes": [
            "The two checks have opposite target-script semantics and are reported separately.",
            "The four en-te mixed_script rows are Telugu and are excluded from Chinese script accuracy.",
            "mixed_script in en-yue means Traditional Chinese mixed with Latin words; it is not a Simplified-vs-Traditional mixed-character label.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
