# Andromeda Dataset Conversion — Sprint 56 Task A

## Overview

This task converts the selected Chinese and Cantonese records from the Andromeda dataset into the GEPA golden-pool JSONL format. The conversion is performed by a reproducible script; records are not manually edited, silently filtered, or repaired.

**Current scope:** dataset conversion and structural validation only. This task does not perform a new human rescoring or inter-annotator agreement study.

## Source

- **Dataset:** Andromeda
- **Source file:** `data/raw/andromeda/dataset_v7.jsonl`
- **Records read:** 675
- **Selected records:** 179
- **Selection:** records with `language_pair` equal to `en-zh` or `en-yue`
- **Conversion status:** `converted_without_record_filtering`

The selected 179 records cover both translation directions for each language pair:

| Language pair | Translation direction | Records |
|---|---|---:|
| English–Cantonese (`en-yue`) | English → Cantonese (`en->yue`) | 111 |
| English–Mandarin (`en-zh`) | English → Mandarin (`en->zh`) | 27 |
| English–Cantonese (`en-yue`) | Cantonese → English (`yue->en`) | 15 |
| English–Mandarin (`en-zh`) | Mandarin → English (`zh->en`) | 26 |
| **Total** | | **179** |

Pair totals:

| Language pair | Records |
|---|---:|
| `en-yue` | 126 |
| `en-zh` | 53 |
| **Total** | **179** |

## Pre-conversion error-bucket audit

The following counts were computed from the selected source records before conversion. `no_error` is included as a record bucket where applicable. These are **record counts by bucket**, not counts of individual annotations. The report also records annotation counts by error type and severity.

### English → Cantonese (`en->yue`)

**Records audited: 111**

| Error bucket | Records |
|---|---:|
| hallucination | 12 |
| mixed_script | 5 |
| no_error | 40 |
| omission | 12 |
| simplified_script | 12 |
| standard_written_chinese | 12 |
| unsafe_mistranslation | 6 |
| wrong_entity_or_number | 12 |
| **Total** | **111** |

Annotation counts by severity: critical 16, major 31, minor 24.

### English → Mandarin (`en->zh`)

**Records audited: 27**

| Error bucket | Records |
|---|---:|
| currency_unit_error | 1 |
| degenerate_repetition | 1 |
| hallucination | 2 |
| homonym_mistranslation | 1 |
| idiom_mistranslation | 1 |
| idiom_suboptimal | 1 |
| mistranslation | 1 |
| negation_flip | 2 |
| no_error | 9 |
| no_output | 1 |
| omission | 2 |
| register | 2 |
| untranslated_text | 1 |
| wrong_entity_or_number | 2 |
| **Total** | **27** |

Annotation counts by severity: critical 7, major 9, minor 2.

### Cantonese → English (`yue->en`)

**Records audited: 15**

| Error bucket | Records |
|---|---:|
| hallucination | 1 |
| mistranslation | 1 |
| negation_flip | 2 |
| no_error | 8 |
| omission | 1 |
| register | 1 |
| truncation | 1 |
| **Total** | **15** |

Annotation counts by severity: critical 4, major 3, minor 0.

### Mandarin → English (`zh->en`)

**Records audited: 26**

| Error bucket | Records |
|---|---:|
| currency_unit_error | 1 |
| hallucination | 1 |
| homonym_mistranslation | 1 |
| idiom_mistranslation | 1 |
| idiom_suboptimal | 1 |
| mistranslation | 1 |
| negation_flip | 2 |
| no_error | 9 |
| no_output | 1 |
| omission | 2 |
| register | 2 |
| truncation | 1 |
| untranslated_text | 1 |
| wrong_entity_or_number | 2 |
| **Total** | **26** |

Annotation counts by severity: critical 7, major 8, minor 2.

### Combined pre-conversion annotation totals

Across the selected records, the source audit reports:

| Severity | Annotation count |
|---|---:|
| Critical | 34 |
| Major | 51 |
| Minor | 28 |
| **Total annotations** | **113** |

The 113 annotations are not 113 distinct records necessarily; a record may have more than one annotation. The conversion preservation check confirms that error annotations and spans were retained identically.

## Overall-score mapping

Andromeda's `overall_score` uses a 1–5 scale, while the GEPA golden-pool validator is configured for an overall-score range of 0–10. The conversion uses an endpoint-preserving linear mapping:

\[
\text{score}_{10} = 2.5 \times (\text{score}_{5} - 1)
\]

| Original score (1–5) | Converted score (0–10) |
|---:|---:|
| 1 | 0 |
| 2 | 2.5 |
| 3 | 5 |
| 4 | 7.5 |
| 5 | 10 |

### Rationale

The mapping sends the original minimum score (1) to the target minimum (0), and the original maximum score (5) to the target maximum (10). It preserves the ordering of the original score values and uses equal intervals between the five original score levels.

The transformation applies **only to `overall_score`**. The `dimension_scores` remain unchanged on their original 1–5 scale. For auditability, the original overall score is retained in `andromeda_original_overall_score`.

Original overall-score value counts in the selected source records, combining equivalent numeric representations:

| Original score | Records |
|---:|---:|
| 1 | 24 |
| 2 | 52 |
| 3 | 11 |
| 4 | 26 |
| 5 | 66 |
| **Total** | **179** |

The conversion report recorded **zero score-mapping failures**.

## Agreement figure

**Inter-annotator / independent-rescoring agreement: Not calculated for this task.**

No numeric agreement figure is available from the conversion and validation results. The planned independent second-person rescoring of 30 records and associated agreement analysis were put on hold; the agreed scope for this task is dataset conversion, not score evaluation.

Accordingly, this README does not report a fabricated agreement percentage or treat schema-validation success as annotator agreement. GEPA validation measures structural/schema compliance, not agreement between annotators or scorers.

If a numeric agreement figure is required for final acceptance, it must be produced in a separate evaluation task using independently scored records and a documented agreement method. The method, sample size, and result should be added here once that work is authorized and completed.

## Conversion outputs

The converter writes six JSONL files:

| Output file | Records |
|---|---:|
| `data/cmn/golden/human_reviewed.jsonl` | 18 |
| `data/cmn/golden/engineered_perturbation.jsonl` | 16 |
| `data/cmn/golden/weak_mt_style.jsonl` | 19 |
| `data/yue/golden/human_reviewed.jsonl` | 48 |
| `data/yue/golden/engineered_perturbation.jsonl` | 47 |
| `data/yue/golden/weak_mt_style.jsonl` | 31 |
| **Total** | **179** |

Label-source totals:

| Label source | Records |
|---|---:|
| `human_reviewed` | 66 |
| `engineered_perturbation` | 63 |
| `weak_mt_style` | 50 |
| **Total** | **179** |

The output pool's direction totals are:

| Direction | Records |
|---|---:|
| `en->yue` | 111 |
| `en->zh` | 27 |
| `yue->en` | 15 |
| `zh->en` | 26 |
| **Total** | **179** |

## Preservation policy and checks

The conversion preserves the source data rather than attempting to correct it:

- All original source fields are retained.
- Error annotations and their `source_span` / `candidate_span` values are copied without modification.
- `dimension_scores` are retained unchanged.
- `candidate_translation` is copied unchanged, including empty strings.
- Problematic records are not repaired, removed, or filtered.
- The original `overall_score` is retained in `andromeda_original_overall_score`.
- A score that cannot be mapped is retained unchanged and recorded as a visible conversion failure; it is not silently dropped.

The conversion report's preservation check records:

| Check | Result |
|---|---|
| Selected source records | 179 |
| Output records | 179 |
| Unique output IDs | 179 |
| All original source fields retained | `true` |
| Error annotations and spans identical | `true` |
| Dimension scores identical | `true` |
| Score mapping failures | 0 |

An independent test suite in `tests/test_conversion.py` verifies the output-file count, record counts, unique/source-record coverage, partition placement, field preservation, score transformation, and preservation of annotations and unusual source content.

## GEPA validation

The six output files were run through `gepa/checks.py` with the following score ranges:

- `overall_score`: 0–10
- `dimension_scores`: 1–5

All six individual files passed:

| Output file | Records checked | Unique IDs | Issues | Valid |
|---|---:|---:|---:|---|
| `data/cmn/golden/engineered_perturbation.jsonl` | 16 | 16 | 0 | Yes |
| `data/cmn/golden/human_reviewed.jsonl` | 18 | 18 | 0 | Yes |
| `data/cmn/golden/weak_mt_style.jsonl` | 19 | 19 | 0 | Yes |
| `data/yue/golden/engineered_perturbation.jsonl` | 47 | 47 | 0 | Yes |
| `data/yue/golden/human_reviewed.jsonl` | 48 | 48 | 0 | Yes |
| `data/yue/golden/weak_mt_style.jsonl` | 31 | 31 | 0 | Yes |
| **Combined pool** | **179** | **179** | **0** | **Yes** |

The combined-pool validation reported 179 unique IDs and zero issues. No records were dropped as a consequence of validation; failures, if encountered, are to be reported and investigated rather than silently removed.

**Validation result:** 179 records checked; 179 unique IDs; 0 issues.

## Reproducing the conversion and tests

From the repository root, run:

```bash
python3 scripts/convert_andromeda.py
python3 -m pytest -v tests/test_conversion.py
```

Run the GEPA checker on each generated JSONL file using the repository's documented invocation and the score ranges above. The converter report explicitly states that GEPA validation is performed independently of the converter.

## Reported test result

The independent conversion test run completed with:

```text
9 passed, 1 warning
```

The warning was a `PytestRemovedIn10Warning` emitted by the installed `anyio` pytest plugin concerning pytest's deprecated `CallSpec2` alias. It did not cause a test failure.

## Summary

- Source: Andromeda `dataset_v7.jsonl`.
- Source records read: 675.
- Selected and converted: 179.
- Output files: six, under `data/cmn/golden/` and `data/yue/golden/`.
- Pre-conversion error-bucket audit: reported for all four translation directions.
- Overall-score mapping: documented endpoint-preserving linear mapping from 1–5 to 0–10.
- Original fields, annotations, spans, and dimension scores: preserved.
- Score mapping failures: zero.
- GEPA validation: all six files and the combined pool valid, with zero issues.
- Independent conversion tests: nine passed.
- Agreement figure: not calculated; independent rescoring/agreement analysis is outside the current conversion scope.

---

# Sprint 56 Task B — deterministic output checks

## Scope

Task B adds deterministic candidate-output checks while preserving the Task A
Andromeda conversion and JSONL validation workflow. The existing
`scripts/convert_andromeda.py` is intentionally unchanged: conversion is Task A,
while the Task B checks run against its converted records.

The updated files are:

- `gepa/checks.py`: current check implementation, extended with Pinyin detection
  and direction-aware length-ratio checks. The existing `CheckResult`,
  `CheckReport`, registry, and fail-closed OpenCC behavior are retained.
- `gepa/output_check_config.py`: per-direction check activation and calibrated
  length-ratio bounds.
- `scripts/analyze_task_b.py`: reproducible Andromeda label and reference-pair
  calibration summary.
- `scripts/evaluate_script_check.py`: evaluates both script-check directions
  against all 33 orthography-labelled rows, reporting each sublabel.
- `scripts/audit_output_checks.py`: runs checks on all 179 converted records and
  compares reference translations as a false-positive warning baseline.
- `tests/test_adapted_output_checks.py`: extends the existing tests; no new test
  file is required.

## Direction-specific activation

| Direction | Target | Task B-specific checks |
|---|---|---|
| EN → CMN (`en->zh`) | Simplified Chinese | `simplified_script`, `pinyin`, `length_ratio` |
| EN → YUE (`en->yue`) | Traditional Chinese | `traditional_script`, `pinyin`, `length_ratio` |
| CMN → EN (`zh->en`) | English | `length_ratio` |
| YUE → EN (`yue->en`) | English | `length_ratio` |

The existing checks for target script, residual Latin/CJK, numbers, truncation,
degeneration, and Cantonese markers remain configured as appropriate. Pinyin is
only enabled for Chinese-target directions. It detects runs of at least two
Pinyin-looking syllables, including tone-marked and tone-number forms. Its
exemptions mirror `check_no_residual_latin`: words carried over from the source,
the existing built-in allowlist, and uppercase acronyms. A caller may also pass
approved names through `allowed_latin_terms`. Pinyin detection is heuristic and
should not be treated as a general language identifier.

## Script validation

The source has 33 orthography-labelled records: 29 EN→YUE Chinese rows and four
EN→TE Telugu rows. The four Telugu rows are reported as not applicable to a
Chinese script detector. The evaluator reports both functions because they
check opposite target scripts:

- `check_simplified_script` uses OpenCC `t2s` and detects Traditional characters
  (expected in `standard_written_chinese` and `mixed_script` EN→YUE rows).
- `check_traditional_script` uses OpenCC `s2t` and detects Simplified-form
  characters (expected in `simplified_script` EN→YUE rows).

Each check reports accuracy and TP/FP/TN/FN by all three Chinese sublabels and
overall. If OpenCC is missing, the evaluation is marked blocked and exits with a
non-zero status; the check itself never silently passes.

Run it after installing dependencies:

```bash
python -m pip install -r requirements-task-b.txt
python scripts/evaluate_script_check.py
```

The result is written to `reports/script_check_evaluation.json`.

## Length-ratio calibration

Calibration and runtime checking now use the same direction-aware units:

- EN→CMN/YUE: CJK output characters divided by English source words.
- CMN/YUE→EN: English output words divided by CJK source characters.

Andromeda reference-pair distributions:

| Direction | n | P05 | Median | P95 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| `en->zh` | 27 | 1.133 | 1.455 | 2.000 | 1.083 | 2.000 |
| `en->yue` | 111 | 1.042 | 1.667 | 2.125 | 0.778 | 3.000 |
| `zh->en` | 26 | 0.507 | 0.723 | 1.115 | 0.500 | 1.143 |
| `yue->en` | 15 | 0.532 | 0.769 | 1.000 | 0.500 | 1.000 |

Enabled first-pass guardrails:

| Direction | Min | Max | Minimum source units |
|---|---:|---:|---:|
| `en->zh` | 0.70 | 2.60 | 8 English words |
| `en->yue` | 0.70 | 2.80 | 6 English words |
| `zh->en` | 0.35 | 1.45 | 12 CJK characters |
| `yue->en` | 0.35 | 1.45 | 6 CJK characters |

The bounds widen the observed reference-pair tails and are anomaly-screening
guardrails, not universal translation laws or semantic adequacy metrics. The
EN→YUE maximum is 2.80 because one curated reference pair has a ratio of 2.67;
a 2.60 ceiling would flag that reference. Short sources below the lower-tail
source-unit cutoff are not assessed because their ratios are unstable. All four
directions are enabled, but audit failures and reference warnings must be
reviewed before using the check as a blocking production gate.

Reproduce the calibration summary with:

```bash
python scripts/analyze_task_b.py
```

It writes `reports/task_b_corpus_audit.json`.

## Full corpus audit

Run:

```bash
python scripts/audit_output_checks.py
```

It writes `reports/output_check_audit.json`, including per-direction check
counts, failed examples, reference-check warnings, annotation-to-check
diagnostics, and the calibration summary. Missing OpenCC checks are recorded
as unavailable, never as passes.

## Tests and current validation

Run the existing project suite:

```bash
python -m pytest -v
```

The updated suite has **28 passing tests** in this build. It covers Pinyin
plain/tone-marked/tone-number forms, source-carried proper names, acronyms,
allowlisted terms, script-check behavior, missing-OpenCC failure, direction-aware
length measurement/calibration, configuration activation, and Task A conversion
regressions.

The isolated build environment used for this update does not have OpenCC and
cannot reach package indexes. Therefore the real 29-record OpenCC accuracy run
could not be executed here. The evaluator is updated and ready to run in the
user's environment, where `opencc-python-reimplemented` was previously
confirmed installed. Do not claim the labelled script-accuracy criterion is
complete until `scripts/evaluate_script_check.py` produces its completed JSON
report.

## Production integration boundary

This project bundle does not include the production GEPA runner or its live
language configuration files. The updated `gepa/checks.py` and
`gepa/output_check_config.py` are validated within this Sprint 56 project, but
that does not prove they are wired into the production Supernova runtime. The
production owner must still adapt the result protocol and connect these configs
in the actual runner before deployment.
