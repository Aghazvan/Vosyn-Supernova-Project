#!/usr/bin/env python3
"""Run proposed deterministic output checks over every converted Sprint 56 record.

This is a diagnostic audit, not a translation-quality score. Annotated semantic
errors are not assumed detectable by deterministic string checks.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gepa.checks import run_checks, derive_length_ratio_bounds, CheckUnavailableError  # noqa: E402
from gepa.output_check_config import DIRECTION_CONFIGS, get_direction_config  # noqa: E402


def load_records(data_dir: Path):
    for path in sorted(data_dir.glob("*/golden/*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                if line.strip():
                    record = json.loads(line)
                    record["_file"] = str(path.relative_to(data_dir))
                    record["_line"] = line_no
                    yield record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "output_check_audit.json")
    args = parser.parse_args()

    records = list(load_records(args.data_dir))
    direction_counts = Counter(r["translation_direction"] for r in records)
    check_counts = defaultdict(Counter)
    reference_check_counts = defaultdict(Counter)
    examples = defaultdict(list)
    annotation_counts = defaultdict(Counter)
    label_detection = defaultdict(Counter)
    length_calibration = {}

    for record in records:
        direction = record["translation_direction"]
        config = get_direction_config(direction)
        try:
            report = run_checks(record["candidate_translation"], record["source_text"], config)
        except CheckUnavailableError:
            # Continue the corpus audit without pretending the missing script
            # check passed. Its unavailable count is recorded explicitly.
            script_names = {"simplified_script", "traditional_script"}
            unavailable = [n for n in config["output_checks"] if n in script_names]
            for name in unavailable:
                check_counts[direction][name + ":unavailable"] += 1
            config["output_checks"] = [n for n in config["output_checks"] if n not in script_names]
            report = run_checks(record["candidate_translation"], record["source_text"], config)
        for result in report.results:
            check_counts[direction][result.name] += 1
            if not result.passed:
                check_counts[direction][result.name + ":failed"] += 1
                if len(examples[(direction, result.name)]) < 5:
                    examples[(direction, result.name)].append({
                        "id": record["id"], "detail": result.detail,
                        "evidence": result.evidence,
                    })
        # Reference translations are the available human/curated baseline.
        # Failures here are warning signs for false positives, not proof that
        # the reference is flawless.
        ref_config = get_direction_config(direction)
        try:
            ref_report = run_checks(record["reference_translation"], record["source_text"], ref_config)
        except CheckUnavailableError:
            ref_config["output_checks"] = [n for n in ref_config["output_checks"]
                                            if n not in {"simplified_script", "traditional_script"}]
            ref_report = run_checks(record["reference_translation"], record["source_text"], ref_config)
        for result in ref_report.results:
            if not result.passed:
                reference_check_counts[direction][result.name] += 1

        for error in record.get("errors", []):
            error_type = error.get("error_type", "<missing>")
            annotation_counts[direction][error_type] += 1
            # Only direct, narrowly defined links are counted as diagnostic hits.
            expected = {
                "no_output": "not_empty",
                "untranslated_text": "not_source_copy",
                "degenerate_repetition": "no_degeneration",
                "truncation": "not_truncated",
                "simplified_script": "traditional_script" if direction == "en->yue" else "simplified_script",
            }.get(error_type)
            if expected:
                result = next((x for x in report.results if x.name == expected), None)
                if result is None:
                    label_detection[direction][error_type + ":unavailable"] += 1
                elif not result.passed:
                    label_detection[direction][error_type + ":detected"] += 1
                else:
                    label_detection[direction][error_type + ":not_detected"] += 1

    # Recompute the reference-pair distribution using the same direction-aware
    # metric as the runtime checker. The operational guardrails are enabled in
    # each direction config and remain first-pass anomaly thresholds.
    for direction in DIRECTION_CONFIGS:
        pairs = [(r["source_text"], r["reference_translation"]) for r in records
                 if r["translation_direction"] == direction]
        try:
            length_calibration[direction] = derive_length_ratio_bounds(pairs, direction)
            length_calibration[direction]["status"] = "calibrated_and_enabled"
        except ValueError as exc:
            length_calibration[direction] = {"status": "insufficient_data", "reason": str(exc), "pairs": len(pairs)}

    result = {
        "record_count": len(records),
        "direction_counts": dict(sorted(direction_counts.items())),
        "check_counts": {d: dict(sorted(c.items())) for d, c in sorted(check_counts.items())},
        "reference_check_failures": {d: dict(sorted(c.items())) for d, c in sorted(reference_check_counts.items())},
        "annotation_counts": {d: dict(sorted(c.items())) for d, c in sorted(annotation_counts.items())},
        "direct_annotation_detection": {d: dict(sorted(c.items())) for d, c in sorted(label_detection.items())},
        "failure_examples": {f"{d}:{n}": v for (d, n), v in sorted(examples.items())},
        "length_ratio_calibration": length_calibration,
        "notes": [
            "A failed deterministic check is not automatically a semantic translation failure.",
            "Annotation detection is reported only for narrowly mapped error labels.",
            "Length-ratio checks are enabled with direction-aware Andromeda-derived guardrails; audit values are re-estimated from reference pairs.",
            "EN->YUE upper bound is 2.80 because a curated reference pair measured 2.67; the narrower 2.60 bound would flag that reference.",
            "OpenCC-dependent script checks are counted as unavailable, never as passed, if OpenCC is missing in the runtime.",
            "Length ratios use CJK-character/English-word counts in the direction appropriate to each language pair; short sources below the P05 source-unit cutoff are exempt.",
            "Reference-check failures are potential false positives; inspect them before enabling any check as a hard gate.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "records": len(records),
        "directions": dict(direction_counts),
        "length_ratio_calibration": length_calibration,
        "audit_file": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
