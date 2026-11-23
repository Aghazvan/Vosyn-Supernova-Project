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
