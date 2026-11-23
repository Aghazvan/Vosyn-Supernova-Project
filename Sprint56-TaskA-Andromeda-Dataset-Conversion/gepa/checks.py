"""
Validation utilities for the Andromeda-derived Supernova golden pool.

Expected record fields are the original Andromeda JSONL fields:
    id, dataset_source, language_pair, source_language, target_language,
    translation_direction, domain, difficulty, difficulty_tags, source_text,
    reference_translation, candidate_translation, overall_score,
    dimension_scores, errors, judge_explanation, label_source, split,
    provenance_flag

The validator does not rename fields, discard annotations, normalize spans,
or impose a closed vocabulary on error_type. It checks that the information
needed for conversion and later evaluation is present and structurally valid.

By default, scores are checked on Andromeda's original 1-5 scale. If this
validator is run on converted records whose overall_score has been mapped to
another scale, pass the appropriate score_min and score_max explicitly.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


REQUIRED_FIELDS = (
    "id",
    "dataset_source",
    "language_pair",
    "source_language",
    "target_language",
    "translation_direction",
    "domain",
    "difficulty",
    "difficulty_tags",
    "source_text",
    "reference_translation",
    "candidate_translation",
    "overall_score",
    "dimension_scores",
    "errors",
    "judge_explanation",
    "label_source",
    "split",
    "provenance_flag",
)

DIMENSION_SCORE_FIELDS = (
    "accuracy",
    "fluency",
    "grammar",
    "terminology",
    "completeness",
    "style_register",
    "cultural_appropriateness",
    "safety",
)

ALLOWED_LABEL_SOURCES = {
    "human_reviewed",
    "engineered_perturbation",
    "weak_mt_style",
}

ALLOWED_SEVERITIES = {"minor", "major", "critical"}
ALLOWED_SPLITS = {"train", "validation", "test"}

# Direction and language-name checks reflect the values in dataset_v7.jsonl.
LANGUAGE_PAIR_METADATA = {
    "en-zh": {
        "en->zh": ("English", "Mandarin Chinese"),
        "zh->en": ("Mandarin Chinese", "English"),
    },
    "en-yue": {
        "en->yue": ("English", "Cantonese (Yue Chinese)"),
        "yue->en": ("Cantonese (Yue Chinese)", "English"),
    },
}


def _is_number(value: Any) -> bool:
    """True for finite int/float values, excluding bool."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _issue(issues: List[str], record_id: str, message: str) -> None:
    issues.append(f"{record_id}: {message}")


def validate_record(
    record: Mapping[str, Any],
    *,
    score_min: float = 1.0,
    score_max: float = 5.0,
    dimension_score_min: float = 1.0,
    dimension_score_max: float = 5.0,
) -> List[str]:
    """
    Validate one Andromeda-shaped record.

    candidate_translation may be an empty string: Andromeda uses this for
    explicit no_output cases, which are represented in the errors list.
    source_span and candidate_span may be None, as in no_output annotations.
    """
    issues: List[str] = []
    if not isinstance(record, Mapping):
        return ["<unknown-id>: record must be a JSON object"]
    record_id = str(record.get("id", "<missing-id>"))

    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        _issue(issues, record_id, f"missing required fields: {missing}")
        # Continue validating present fields to provide a useful full report.

    for field in (
        "id",
        "dataset_source",
        "language_pair",
        "source_language",
        "target_language",
        "translation_direction",
        "domain",
        "difficulty",
        "source_text",
        "reference_translation",
        "judge_explanation",
        "label_source",
        "split",
    ):
        if field in record and not _non_empty_string(record[field]):
            _issue(issues, record_id, f"{field} must be a non-empty string")

    if "difficulty_tags" in record:
        tags = record["difficulty_tags"]
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            _issue(issues, record_id, "difficulty_tags must be a list of strings")

    # Empty candidate text is valid only when the record explicitly identifies
    # the absence of output; it is not silently treated as a missing field.
    if "candidate_translation" in record:
        candidate = record["candidate_translation"]
        if not isinstance(candidate, str):
            _issue(issues, record_id, "candidate_translation must be a string")

    if "overall_score" in record:
        score = record["overall_score"]
        if not _is_number(score):
            _issue(issues, record_id, "overall_score must be a finite number")
        elif not (score_min <= float(score) <= score_max):
            _issue(
                issues,
                record_id,
                f"overall_score {score} outside [{score_min}, {score_max}]",
            )

    if "dimension_scores" in record:
        dimensions = record["dimension_scores"]
        if not isinstance(dimensions, dict):
            _issue(issues, record_id, "dimension_scores must be an object")
        else:
            missing_dimensions = [
                name for name in DIMENSION_SCORE_FIELDS if name not in dimensions
            ]
            extra_dimensions = [
                name for name in dimensions if name not in DIMENSION_SCORE_FIELDS
            ]
            if missing_dimensions:
                _issue(
                    issues,
                    record_id,
                    f"dimension_scores missing dimensions: {missing_dimensions}",
                )
            if extra_dimensions:
                _issue(
                    issues,
                    record_id,
                    f"dimension_scores contains unexpected dimensions: {extra_dimensions}",
                )
            for name, value in dimensions.items():
                if not _is_number(value):
                    _issue(issues, record_id, f"dimension_scores.{name} must be numeric")
                elif not (dimension_score_min <= float(value) <= dimension_score_max):
                    _issue(
                        issues,
                        record_id,
                        f"dimension_scores.{name}={value} outside "
                        f"[{dimension_score_min}, {dimension_score_max}]",
                    )

    if "errors" in record:
        errors = record["errors"]
        if not isinstance(errors, list):
            _issue(issues, record_id, "errors must be a list")
        else:
            for index, error in enumerate(errors):
                prefix = f"errors[{index}]"
                if not isinstance(error, dict):
                    _issue(issues, record_id, f"{prefix} must be an object")
                    continue

                for field in ("error_type", "severity", "source_span", "candidate_span", "note"):
                    if field not in error:
                        _issue(issues, record_id, f"{prefix} missing {field}")

                if "error_type" in error and not _non_empty_string(error["error_type"]):
                    _issue(issues, record_id, f"{prefix}.error_type must be a non-empty string")

                if "severity" in error:
                    severity = error["severity"]
                    if severity not in ALLOWED_SEVERITIES:
                        _issue(
                            issues,
                            record_id,
                            f"{prefix}.severity {severity!r} is not one of "
                            f"{sorted(ALLOWED_SEVERITIES)}",
                        )

                for span_field in ("source_span", "candidate_span"):
                    if span_field in error:
                        span = error[span_field]
                        if span is not None and not isinstance(span, str):
                            _issue(
                                issues,
                                record_id,
                                f"{prefix}.{span_field} must be a string or null",
                            )

                if "note" in error and not isinstance(error["note"], str):
                    _issue(issues, record_id, f"{prefix}.note must be a string")

    if "label_source" in record and record["label_source"] not in ALLOWED_LABEL_SOURCES:
        _issue(
            issues,
            record_id,
            f"unsupported label_source {record['label_source']!r}; "
            f"expected one of {sorted(ALLOWED_LABEL_SOURCES)}",
        )

    if "split" in record and record["split"] not in ALLOWED_SPLITS:
        _issue(
            issues,
            record_id,
            f"unsupported split {record['split']!r}; expected one of {sorted(ALLOWED_SPLITS)}",
        )

    # Validate the relationship between language_pair, direction, and names.
    pair = record.get("language_pair")
    direction = record.get("translation_direction")
    if pair not in LANGUAGE_PAIR_METADATA:
        _issue(
            issues,
            record_id,
            f"language_pair {pair!r} is not one of {sorted(LANGUAGE_PAIR_METADATA)}",
        )
    elif direction not in LANGUAGE_PAIR_METADATA[pair]:
        _issue(
            issues,
            record_id,
            f"translation_direction {direction!r} is invalid for {pair!r}",
        )
    else:
        expected_source, expected_target = LANGUAGE_PAIR_METADATA[pair][direction]
        if record.get("source_language") != expected_source:
            _issue(
                issues,
                record_id,
                f"source_language should be {expected_source!r} for {pair}/{direction}",
            )
        if record.get("target_language") != expected_target:
            _issue(
                issues,
                record_id,
                f"target_language should be {expected_target!r} for {pair}/{direction}",
            )

    # provenance_flag is explicitly nullable in the source dataset.
    if "provenance_flag" in record:
        provenance = record["provenance_flag"]
        if provenance is not None and not isinstance(provenance, str):
            _issue(issues, record_id, "provenance_flag must be a string or null")

    return issues


def summarize_records(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Return useful pool statistics without changing the records."""
    pair_counts = Counter(str(r.get("language_pair")) for r in records)
    direction_counts = Counter(str(r.get("translation_direction")) for r in records)
    category_counts = Counter(str(r.get("label_source")) for r in records)
    split_counts = Counter(str(r.get("split")) for r in records)
    error_type_counts: Counter = Counter()
    severity_counts: Counter = Counter()
    records_with_errors = 0
    annotation_count = 0

    for record in records:
        errors = record.get("errors", [])
        if isinstance(errors, list) and errors:
            records_with_errors += 1
            for error in errors:
                if isinstance(error, dict):
                    annotation_count += 1
                    if "error_type" in error:
                        error_type_counts[str(error["error_type"])] += 1
                    if "severity" in error:
                        severity_counts[str(error["severity"])] += 1

    return {
        "n_total": len(records),
        "language_pair_counts": dict(sorted(pair_counts.items())),
        "direction_counts": dict(sorted(direction_counts.items())),
        "label_source_counts": dict(sorted(category_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "records_with_errors": records_with_errors,
        "n_error_annotations": annotation_count,
        "error_type_counts": dict(sorted(error_type_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
    }


def validate_records(
    records: Sequence[Mapping[str, Any]],
    *,
    expected_total: Optional[int] = None,
    score_min: float = 1.0,
    score_max: float = 5.0,
    dimension_score_min: float = 1.0,
    dimension_score_max: float = 5.0,
) -> Dict[str, Any]:
    """
    Validate a collection of Andromeda records and return counts + failures.

    Set expected_total=179 when validating the complete initial Chinese pool.
    For individual category/language partitions, leave expected_total=None.
    """
    issues: List[str] = []
    seen_ids = set()

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            issues.append(f"record index {index}: record must be a JSON object")
            continue

        record_id = record.get("id")
        if record_id in seen_ids:
            issues.append(f"Duplicate id: {record_id!r}")
        else:
            seen_ids.add(record_id)

        issues.extend(
            validate_record(
                record,
                score_min=score_min,
                score_max=score_max,
                dimension_score_min=dimension_score_min,
                dimension_score_max=dimension_score_max,
            )
        )

    if expected_total is not None and len(records) != expected_total:
        issues.append(
            f"Pool contains {len(records)} records; expected exactly {expected_total}"
        )

    summary = summarize_records(records)
    summary["n_unique_ids"] = len(seen_ids)
    summary["n_issues"] = len(issues)
    summary["issues"] = issues
    summary["valid"] = not issues
    return summary


def load_jsonl(path: str | Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Load JSONL while reporting malformed lines instead of dropping them silently."""
    records: List[Dict[str, Any]] = []
    issues: List[str] = []
    file_path = Path(path)

    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                issues.append(f"Line {line_number}: blank line")
                continue
            try:
                value = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                issues.append(f"Line {line_number}: invalid JSON: {exc}")
                continue
            if not isinstance(value, dict):
                issues.append(f"Line {line_number}: JSONL record must be an object")
                continue
            records.append(value)

    return records, issues


def validate_jsonl(
    path: str | Path,
    *,
    expected_total: Optional[int] = None,
    score_min: float = 1.0,
    score_max: float = 5.0,
    language_pairs: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Load and validate JSONL, optionally selecting language pairs first."""
    records, parse_issues = load_jsonl(path)
    source_total = len(records)
    if language_pairs:
        selected_pairs = set(language_pairs)
        records = [r for r in records if r.get("language_pair") in selected_pairs]
    report = validate_records(
        records,
        expected_total=expected_total,
        score_min=score_min,
        score_max=score_max,
    )
    report["n_records_in_file"] = source_total
    report["language_pair_filter"] = list(language_pairs) if language_pairs else None
    report["issues"] = parse_issues + report["issues"]
    report["n_parse_issues"] = len(parse_issues)
    report["n_issues"] = len(report["issues"])
    report["valid"] = report["n_issues"] == 0
    report["path"] = str(path)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate Andromeda-structured JSONL records for the Supernova pool."
    )
    parser.add_argument("jsonl", help="Path to JSONL file")
    parser.add_argument(
        "--expected-total",
        type=int,
        default=None,
        help="Expected record count (use 179 for the complete initial Chinese pool)",
    )
    parser.add_argument("--score-min", type=float, default=1.0)
    parser.add_argument("--score-max", type=float, default=5.0)
    parser.add_argument(
        "--language-pairs",
        default=None,
        help="Optional comma-separated filter, e.g. en-zh,en-yue",
    )
    args = parser.parse_args(argv)
    language_pairs = (
        [item.strip() for item in args.language_pairs.split(",") if item.strip()]
        if args.language_pairs
        else None
    )

    report = validate_jsonl(
        args.jsonl,
        expected_total=args.expected_total,
        score_min=args.score_min,
        score_max=args.score_max,
        language_pairs=language_pairs,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
