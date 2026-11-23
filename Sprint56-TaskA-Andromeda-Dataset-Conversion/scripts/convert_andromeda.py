#!/usr/bin/env python3
"""Losslessly partition Andromeda Chinese records into six golden-pool JSONL files.

The converter does not validate, repair, normalize, or clean records. It selects
all 179 records whose language_pair is en-zh or en-yue, preserves every source
field (including error annotations and spans), and partitions by language pool
and label_source. The only value transformation is the documented overall_score
scale mapping; the original 1-5 value is retained in
andromeda_original_overall_score.

Outputs (relative to --output-root):
  data/cmn/golden/{human_reviewed,engineered_perturbation,weak_mt_style}.jsonl
  data/yue/golden/{human_reviewed,engineered_perturbation,weak_mt_style}.jsonl
  reports/conversion_report.json

Validation is intentionally separate. Run gepa/checks.py on each output and
on the combined 179-record pool; do not use validation to filter records.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

EXPECTED_TOTAL = 179
EXPECTED_PAIR_COUNTS = {"en-zh": 53, "en-yue": 126}
PAIR_TO_POOL = {"en-zh": "cmn", "en-yue": "yue"}
LABEL_SOURCES = (
    "human_reviewed",
    "engineered_perturbation",
    "weak_mt_style",
)
# Endpoint-preserving linear transformation: 1 -> 0, 3 -> 5, 5 -> 10.
SCORE_MAPPING = {
    "name": "endpoint_preserving_linear_1_to_10",
    "formula": "score_10 = 2.5 * (score_5 - 1)",
    "input_min": 1.0,
    "input_max": 5.0,
    "output_min": 0.0,
    "output_max": 10.0,
    "anchors": {"1": 0.0, "2": 2.5, "3": 5.0, "4": 7.5, "5": 10.0},
    "scope": "overall_score only; dimension_scores remain in their original 1-5 scale",
    "rationale": (
        "Maps both endpoints to the full 0-10 target range while preserving "
        "equal intervals and the ordering of the original ordinal score values. "
        "The original overall_score is retained separately for auditability."
    ),
}


class ConversionError(RuntimeError):
    """Raised when complete, unambiguous conversion cannot be guaranteed."""


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read every physical source row; malformed rows fail loudly with line number."""
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                raise ConversionError(f"Blank source line {line_number}; no rows were converted")
            try:
                value = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise ConversionError(
                    f"Invalid JSON at source line {line_number}: {exc.msg}; "
                    "no rows were converted"
                ) from exc
            if not isinstance(value, dict):
                raise ConversionError(
                    f"Source line {line_number} is not a JSON object; no rows were converted"
                )
            value["__converter_source_line"] = line_number
            records.append(value)
    return records


def _clean_source_line(record: Mapping[str, Any]) -> Dict[str, Any]:
    result = dict(record)
    result.pop("__converter_source_line", None)
    return result


def score_to_10(value: Any) -> Tuple[Any, str | None]:
    """Map valid 1-5 scores; return the untouched value plus an issue otherwise."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return value, f"overall_score {value!r} is not numeric; left unchanged"
    if not math.isfinite(float(value)) or not 1.0 <= float(value) <= 5.0:
        return value, f"overall_score {value!r} is outside [1, 5]; left unchanged"
    mapped = 2.5 * (float(value) - 1.0)
    return (int(mapped) if mapped.is_integer() else mapped), None


def select_and_partition(
    source_records: Sequence[Mapping[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[Tuple[str, str], List[Dict[str, Any]]]]:
    selected: List[Dict[str, Any]] = []
    seen_ids = set()
    partitions = {
        (pool, label): []
        for pool in ("cmn", "yue")
        for label in LABEL_SOURCES
    }

    for source_record in source_records:
        pair = source_record.get("language_pair")
        if pair not in PAIR_TO_POOL:
            continue
        record = _clean_source_line(source_record)
        record_id = record.get("id")
        source_line = source_record.get("__converter_source_line", "unknown")
        if record_id is None or (isinstance(record_id, str) and not record_id.strip()):
            raise ConversionError(
                f"Selected source line {source_line} has no usable id; record not discarded"
            )
        if record_id in seen_ids:
            raise ConversionError(
                f"Duplicate selected id {record_id!r} at source line {source_line}; "
                "conversion stopped to avoid ambiguous traceability"
            )
        seen_ids.add(record_id)

        label = record.get("label_source")
        if label not in LABEL_SOURCES:
            raise ConversionError(
                f"Selected record {record_id!r} at source line {source_line} has "
                f"unsupported label_source {label!r}; conversion stopped, record not discarded"
            )

        # Preserve the original overall score explicitly before mapping it.
        original_score = record.get("overall_score")
        record["andromeda_original_overall_score"] = original_score
        mapped_score, score_issue = score_to_10(original_score)
        if score_issue is None:
            record["overall_score"] = mapped_score
            record["andromeda_conversion"] = {"overall_score_mapping": "mapped"}
        else:
            # Keep the row in its required partition. Do not guess, clamp, or
            # repair the score; make the failed transformation explicit.
            record["overall_score"] = original_score
            record["andromeda_conversion"] = {
                "overall_score_mapping": "failed",
                "issue": score_issue,
            }

        # Keep source content and nested annotations/spans untouched.
        selected.append(record)
        partitions[(PAIR_TO_POOL[pair], label)].append(record)

    if len(selected) != EXPECTED_TOTAL:
        raise ConversionError(
            f"Selected {len(selected)} records; expected exactly {EXPECTED_TOTAL}. "
            "No output files were written. Check the source snapshot."
        )

    pair_counts = Counter(r["language_pair"] for r in selected)
    if dict(pair_counts) != EXPECTED_PAIR_COUNTS:
        raise ConversionError(
            f"Language-pair counts are {dict(pair_counts)}; expected "
            f"{EXPECTED_PAIR_COUNTS}. No output files were written."
        )

    # Prove the six partitions are disjoint and collectively exhaustive.
    emitted_ids = [r["id"] for rows in partitions.values() for r in rows]
    selected_ids = [r["id"] for r in selected]
    if len(emitted_ids) != EXPECTED_TOTAL or Counter(emitted_ids) != Counter(selected_ids):
        raise ConversionError("Partition accounting mismatch; no output files were written")
    return selected, partitions


def _atomic_write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def _error_audit(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Count records per error bucket and annotations separately (multi-label aware)."""
    result: Dict[str, Any] = {}
    dimensions = sorted({r["translation_direction"] for r in records})
    for direction in dimensions:
        rows = [r for r in records if r["translation_direction"] == direction]
        record_bucket_counts: Counter[str] = Counter()
        annotation_counts: Counter[str] = Counter()
        severity_counts: Counter[str] = Counter()
        for record in rows:
            errors = record.get("errors")
            if isinstance(errors, list) and errors:
                seen_for_record = set()
                for annotation in errors:
                    if isinstance(annotation, dict):
                        error_type = str(annotation.get("error_type", "<missing-error-type>"))
                        annotation_counts[error_type] += 1
                        seen_for_record.add(error_type)
                        if "severity" in annotation:
                            severity_counts[str(annotation["severity"])] += 1
                record_bucket_counts.update(seen_for_record)
            else:
                record_bucket_counts["no_error"] += 1
        result[direction] = {
            "n_records": len(rows),
            "record_counts_by_error_bucket": dict(sorted(record_bucket_counts.items())),
            "annotation_counts_by_error_type": dict(sorted(annotation_counts.items())),
            "annotation_counts_by_severity": dict(sorted(severity_counts.items())),
        }
    return result


def convert(input_path: Path, output_root: Path) -> Dict[str, Any]:
    source_records = read_jsonl(input_path)
    selected, partitions = select_and_partition(source_records)

    # Pre-conversion inventory is based on original source records and is
    # computed before the output score mapping is applied.
    source_selected = [
        _clean_source_line(r)
        for r in source_records
        if r.get("language_pair") in PAIR_TO_POOL
    ]
    pair_counts = Counter(r["language_pair"] for r in source_selected)
    direction_counts = Counter(r["translation_direction"] for r in source_selected)
    label_counts = Counter(r["label_source"] for r in source_selected)

    output_counts: Dict[str, int] = {}
    record_destinations: List[Dict[str, str]] = []
    conversion_failures: List[Dict[str, str]] = []
    for record in selected:
        status = record.get("andromeda_conversion", {})
        if status.get("overall_score_mapping") == "failed":
            conversion_failures.append({"id": str(record["id"]), "issue": status["issue"]})
    for (pool, label), rows in partitions.items():
        destination = output_root / "data" / pool / "golden" / f"{label}.jsonl"
        _atomic_write_jsonl(destination, rows)
        relative = destination.relative_to(output_root).as_posix()
        output_counts[relative] = len(rows)
        for record in rows:
            record_destinations.append({"id": str(record["id"]), "destination": relative})

    report = {
        "status": "converted_without_record_filtering",
        "source_file": str(input_path),
        "source_records_read": len(source_records),
        "selected_records": len(selected),
        "expected_selected_records": EXPECTED_TOTAL,
        "language_pair_counts": dict(sorted(pair_counts.items())),
        "translation_direction_counts": dict(sorted(direction_counts.items())),
        "label_source_counts": dict(sorted(label_counts.items())),
        "pre_conversion_error_audit": _error_audit(source_selected),
        "score_mapping": SCORE_MAPPING,
        "score_value_counts_original": dict(sorted(Counter(str(r.get("overall_score")) for r in source_selected).items())),
        "output_file_counts": output_counts,
        "records_written": len(record_destinations),
        "score_mapping_failures": conversion_failures,
        "record_destinations": sorted(record_destinations, key=lambda x: x["id"]),
        "preservation_policy": {
            "source_fields": "all source fields retained",
            "error_annotations_and_spans": "copied without modification",
            "candidate_translation": "copied without modification, including empty strings",
            "problematic_records": "not repaired, removed, or filtered; an unconvertible score is retained unchanged and recorded as a visible conversion failure",
            "original_overall_score": "retained in andromeda_original_overall_score",
            "dimension_scores": "retained unchanged on the original 1-5 scale",
        },
        "validation": {
            "performed_by_converter": False,
            "instruction": "Run gepa/checks.py independently on all six files and the concatenated 179-record pool; retain and report all failures.",
        },
    }
    report_path = output_root / "reports" / "conversion_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_tmp = report_path.with_suffix(".json.tmp")
    report_tmp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(report_tmp, report_path)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Original Andromeda JSONL source")
    parser.add_argument("--output-root", type=Path, default=Path("."), help="Repository root; outputs are written under data/ and reports/")
    args = parser.parse_args(argv)
    try:
        report = convert(args.input.expanduser().resolve(), args.output_root.expanduser().resolve())
    except (ConversionError, OSError) as exc:
        print(f"CONVERSION FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in report.items() if k != "record_destinations"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
