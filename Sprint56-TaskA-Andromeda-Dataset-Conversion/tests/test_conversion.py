"""Independent regression tests for Sprint 56 Task A.

Run from the repository root:
    python3 -m pytest -v tests/test_conversion.py

These tests deliberately do not import converter functions. They independently
read the source JSONL, derive the expected selection, and compare every output
record with its source counterpart.
"""

import json
import math
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "data/raw/andromeda/dataset_v7.jsonl"
GOLDEN_ROOT = ROOT / "data"

EXPECTED_TOTAL = 179
PAIR_TO_POOL = {"en-zh": "cmn", "en-yue": "yue"}
SUPPORTED_LABELS = {
    "human_reviewed",
    "engineered_perturbation",
    "weak_mt_style",
}
EXPECTED_COUNTS = {
    ("en-zh", "human_reviewed"): 18,
    ("en-zh", "engineered_perturbation"): 16,
    ("en-zh", "weak_mt_style"): 19,
    ("en-yue", "human_reviewed"): 48,
    ("en-yue", "engineered_perturbation"): 47,
    ("en-yue", "weak_mt_style"): 31,
}

ORIGINAL_SCORE_FIELD = "andromeda_original_overall_score"
CONVERSION_FIELD = "andromeda_conversion"
SCORE_FIELD = "overall_score"
CANDIDATE_FIELD = "candidate_translation"

EXPECTED_OUTPUT_FILES = {
    GOLDEN_ROOT / pool / "golden" / f"{label}.jsonl"
    for pool in ("cmn", "yue")
    for label in SUPPORTED_LABELS
}
ADDED_FIELDS = {ORIGINAL_SCORE_FIELD, CONVERSION_FIELD}


def read_jsonl_strict(path):
    """Read every physical JSONL row; blank or malformed rows fail the test."""
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            assert raw_line.strip(), (
                f"Blank line in {path} at line {line_number}"
            )
            try:
                value = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                pytest.fail(
                    f"Invalid JSON in {path}, line {line_number}: {exc}"
                )
            assert isinstance(value, dict), (
                f"Non-object JSON value in {path}, line {line_number}"
            )
            records.append(value)
    return records


@pytest.fixture(scope="session")
def source_records():
    assert SOURCE_FILE.is_file(), f"Missing source dataset: {SOURCE_FILE}"
    return read_jsonl_strict(SOURCE_FILE)


@pytest.fixture(scope="session")
def selected_source(source_records):
    # This mirrors the documented selection criterion, not converter code.
    return [
        record for record in source_records
        if record.get("language_pair") in PAIR_TO_POOL
    ]


@pytest.fixture(scope="session")
def source_by_id(selected_source):
    result = {}
    for record in selected_source:
        assert "id" in record, "Selected source record has no id"
        record_id = record["id"]
        assert record_id not in result, (
            f"Duplicate selected source ID: {record_id!r}"
        )
        assert record.get("label_source") in SUPPORTED_LABELS, (
            f"Selected source record {record_id!r} has unsupported "
            f"label_source {record.get('label_source')!r}"
        )
        result[record_id] = record
    return result


@pytest.fixture(scope="session")
def output_records():
    result = {}
    for path in sorted(EXPECTED_OUTPUT_FILES):
        assert path.is_file(), f"Missing output file: {path}"
        result[path] = read_jsonl_strict(path)
    return result


@pytest.fixture(scope="session")
def combined_output(output_records):
    return [
        record
        for records in output_records.values()
        for record in records
    ]


@pytest.fixture(scope="session")
def output_by_id(combined_output):
    result = {}
    for record in combined_output:
        assert "id" in record, "Output record has no id"
        record_id = record["id"]
        assert record_id not in result, (
            f"Duplicate output ID: {record_id!r}"
        )
        result[record_id] = record
    return result


def expected_score_result(original_score):
    """Independently implement the documented score policy."""
    if (
        isinstance(original_score, bool)
        or not isinstance(original_score, (int, float))
    ):
        return original_score, {
            "overall_score_mapping": "failed",
            "issue": (
                f"overall_score {original_score!r} is not numeric; left unchanged"
            ),
        }

    if (
        not math.isfinite(float(original_score))
        or not 1.0 <= float(original_score) <= 5.0
    ):
        return original_score, {
            "overall_score_mapping": "failed",
            "issue": (
                f"overall_score {original_score!r} is outside [1, 5]; "
                "left unchanged"
            ),
        }

    mapped = 2.5 * (float(original_score) - 1.0)
    mapped = int(mapped) if mapped.is_integer() else mapped
    return mapped, {"overall_score_mapping": "mapped"}


def test_exactly_six_output_files():
    golden_root = GOLDEN_ROOT
    actual_files = {
        path
        for pool in ("cmn", "yue")
        for path in (golden_root / pool / "golden").rglob("*")
        if path.is_file()
    }

    assert actual_files == EXPECTED_OUTPUT_FILES, (
        f"Output file set differs.\n"
        f"Missing: {sorted(EXPECTED_OUTPUT_FILES - actual_files)}\n"
        f"Unexpected: {sorted(actual_files - EXPECTED_OUTPUT_FILES)}"
    )


def test_exactly_179_records_and_expected_partition_counts(
    selected_source, output_records, combined_output
):
    assert len(selected_source) == EXPECTED_TOTAL
    assert len(combined_output) == EXPECTED_TOTAL

    expected_counts = Counter(
        (record["language_pair"], record["label_source"])
        for record in selected_source
    )
    actual_counts = Counter(
        (record["language_pair"], record["label_source"])
        for record in combined_output
    )

    assert dict(expected_counts) == EXPECTED_COUNTS
    assert dict(actual_counts) == EXPECTED_COUNTS

    for path, records in output_records.items():
        pool = path.parent.parent.name
        label = path.stem
        pair = {"cmn": "en-zh", "yue": "en-yue"}[pool]
        assert len(records) == EXPECTED_COUNTS[(pair, label)], (
            f"{path}: expected {EXPECTED_COUNTS[(pair, label)]} records, "
            f"found {len(records)}"
        )


def test_every_selected_source_record_appears_exactly_once(
    source_by_id, combined_output, output_by_id
):
    source_ids = [record["id"] for record in source_by_id.values()]
    output_ids = [record["id"] for record in combined_output]

    assert len(source_ids) == EXPECTED_TOTAL
    assert len(output_ids) == EXPECTED_TOTAL
    assert all(count == 1 for count in Counter(source_ids).values())
    assert all(count == 1 for count in Counter(output_ids).values())
    assert set(source_ids) == set(output_ids)


def test_records_are_written_to_the_correct_partition(
    source_by_id, output_records
):
    for path, records in output_records.items():
        pool = path.parent.parent.name
        label = path.stem
        expected_pair = {"cmn": "en-zh", "yue": "en-yue"}[pool]

        for output in records:
            record_id = output["id"]
            assert record_id in source_by_id
            assert output["language_pair"] == expected_pair
            assert output["label_source"] == label


def test_all_original_fields_are_preserved_and_only_documented_fields_added(
    source_by_id, output_by_id
):
    assert set(source_by_id) == set(output_by_id)

    for record_id, source in source_by_id.items():
        output = output_by_id[record_id]

        expected_keys = set(source) | ADDED_FIELDS
        assert set(output) == expected_keys, (
            f"Unexpected key-set change for record {record_id!r}. "
            f"Missing: {expected_keys - set(output)}; "
            f"extra: {set(output) - expected_keys}"
        )

        for field, original_value in source.items():
            if field == SCORE_FIELD:
                continue
            assert output[field] == original_value, (
                f"Record {record_id!r}, field {field!r} changed: "
                f"source={original_value!r}, output={output[field]!r}"
            )


def test_original_overall_score_is_retained_exactly(
    source_by_id, output_by_id
):
    for record_id, source in source_by_id.items():
        output = output_by_id[record_id]
        assert output[ORIGINAL_SCORE_FIELD] == source.get(SCORE_FIELD)


def test_overall_score_mapping_and_conversion_status_are_correct(
    source_by_id, output_by_id
):
    for record_id, source in source_by_id.items():
        output = output_by_id[record_id]
        original_score = source.get(SCORE_FIELD)
        expected_score, expected_status = expected_score_result(original_score)

        assert output[SCORE_FIELD] == expected_score, (
            f"Incorrect overall_score for {record_id!r}: "
            f"expected {expected_score!r}, got {output[SCORE_FIELD]!r}"
        )

        actual_status = output[CONVERSION_FIELD]
        assert actual_status == expected_status, (
            f"Incorrect conversion status for {record_id!r}: "
            f"expected {expected_status!r}, got {actual_status!r}"
        )


def test_dimension_scores_errors_and_candidate_translation_are_unchanged(
    source_by_id, output_by_id
):
    empty_candidate_ids = []

    for record_id, source in source_by_id.items():
        output = output_by_id[record_id]

        for field in (
            "dimension_scores",
            "errors",
            CANDIDATE_FIELD,
        ):
            assert field in source, (
                f"Expected source field {field!r} missing in {record_id!r}"
            )
            assert output[field] == source[field], (
                f"Record {record_id!r}: {field!r} changed"
            )

        if source[CANDIDATE_FIELD] == "":
            empty_candidate_ids.append(record_id)
            assert output[CANDIDATE_FIELD] == ""

        # Explicitly verify nested error annotations and spans, including
        # null spans used by no-output annotations.
        for index, source_error in enumerate(source["errors"]):
            output_error = output["errors"][index]
            assert output_error == source_error
            for span_field in ("source_span", "candidate_span"):
                if span_field in source_error:
                    assert output_error[span_field] == source_error[span_field]

    # The source/checker contract explicitly includes empty candidate strings
    # for no_output cases; fail if the test dataset no longer exercises this.
    assert empty_candidate_ids, (
        "No selected source records with an empty candidate_translation "
        "were found; verify that the expected no_output cases are present."
    )


def test_problematic_and_unusual_source_content_is_not_repaired_or_discarded(
    source_by_id, output_by_id
):
    """Compare all source values recursively, not just known schema fields."""
    for record_id, source in source_by_id.items():
        output = output_by_id[record_id]

        for field, original_value in source.items():
            if field == SCORE_FIELD:
                continue
            assert output[field] == original_value, (
                f"Potential silent repair/filtering in record {record_id!r}, "
                f"field {field!r}: source={original_value!r}, "
                f"output={output[field]!r}"
            )
