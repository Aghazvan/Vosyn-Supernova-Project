#!/usr/bin/env python3
"""Summarize Andromeda orthography labels and calibrate Task B length checks."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from gepa.checks import derive_length_ratio_bounds  # noqa: E402

SOURCE = ROOT / "data/raw/andromeda/dataset_v7.jsonl"
OUTPUT = ROOT / "reports/task_b_corpus_audit.json"
SCRIPT_EVALUATION = ROOT / "reports/script_check_evaluation.json"
SCRIPT_LABELS = {"standard_written_chinese", "simplified_script", "mixed_script"}
DIRECTIONS = ("en->zh", "en->yue", "zh->en", "yue->en")


def read_rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    rows = read_rows(SOURCE)
    labels = Counter()
    pairs = defaultdict(list)
    for row in rows:
        error_types = {
            error.get("error_type")
            for error in (row.get("errors") or [])
            if isinstance(error, dict)
        }
        for label in SCRIPT_LABELS & error_types:
            labels[(row.get("language_pair"), label)] += 1

        direction = row.get("translation_direction")
        source = row.get("source_text") or ""
        reference = row.get("reference_translation") or ""
        if direction in DIRECTIONS and source.strip() and reference.strip():
            pairs[direction].append((source, reference))

    calibration = {}
    for direction in DIRECTIONS:
        try:
            calibration[direction] = derive_length_ratio_bounds(
                pairs.get(direction, []), direction
            )
            calibration[direction]["status"] = "calibrated_from_reference_pairs"
        except ValueError as exc:
            calibration[direction] = {
                "status": "insufficient_data",
                "pairs": len(pairs.get(direction, [])),
                "reason": str(exc),
            }

    if SCRIPT_EVALUATION.exists():
        script_status = json.loads(SCRIPT_EVALUATION.read_text(encoding="utf-8"))
    else:
        script_status = {
            "status": "not_run",
            "reason": "Run python scripts/evaluate_script_check.py after installing requirements-task-b.txt.",
            "accuracy": None,
            "per_label_accuracy": None,
        }

    report = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_records": len(rows),
        "script_orthography_records": sum(labels.values()),
        "script_label_counts": {
            f"{pair}::{label}": count for (pair, label), count in sorted(labels.items())
        },
        "script_check_evaluation": script_status,
        "length_ratio_calibration": calibration,
        "length_ratio_thresholds": {
            direction: {
                "min": calibration[direction].get("min"),
                "max": calibration[direction].get("max"),
                "min_source_units": calibration[direction].get("min_source_units"),
            }
            for direction in DIRECTIONS
        },
        "length_ratio_method": (
            "EN->ZH/YUE: CJK output characters divided by English source words; "
            "ZH/YUE->EN: English output words divided by CJK source characters."
        ),
        "threshold_rationale": (
            "The 0.70-2.60 EN->ZH, 0.70-2.80 EN->YUE, and 0.35-1.45 reverse bounds are conservative "
            "operational guardrails widened from the Andromeda reference-pair P05/P95 "
            "tails. Minimum source-unit cutoffs use the lower-tail source length. "
            "These are first-pass anomaly screens, not semantic adequacy metrics; "
            "review false positives and recalibrate on larger production samples."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
