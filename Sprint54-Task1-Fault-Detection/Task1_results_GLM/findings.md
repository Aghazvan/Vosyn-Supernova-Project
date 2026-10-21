# Sprint 54 Task 1 — Judge Fault Detection Finding

Judge: zai-org/GLM-4-9B-0414; prompt: P1_compliance; temperature: 0.0.
Input file: `/kaggle/input/datasets/abdighaz/sprint-54-tasks/fault_cases.csv`.
Unique source examples: 43.
Fault-case rows evaluated or retained: 301.

Only pre-generated mutations marked MUTATED were scored. Pre-generated SKIPPED cases remain in the results and are not counted as passes.
Fault thresholds are assessed only on successfully mutated and scored cases.
For punctuation control, a score-drop magnitude of at most 1 point is treated as preserving the score.

## Results

| Fault | Expected drop | Scored | Skipped | Unscorable | Mean drop | Threshold met | Finding |
|---|---:|---:|---:|---:|---:|---:|---|
| untranslated_english | 7 | 43 | 0 | 0 | 7.302 | 40/43 | MEETS_EXPECTATION_ON_TESTED_CASES |
| negation_error | 5 | 31 | 12 | 0 | 4.903 | 19/31 | NOT_RELIABLY_DETECTED_ON_TESTED_CASES |
| entity_error | 4 | 7 | 36 | 0 | 5.714 | 7/7 | MEETS_EXPECTATION_ON_TESTED_CASES |
| number_error | 4 | 20 | 23 | 0 | 4.15 | 13/20 | NOT_RELIABLY_DETECTED_ON_TESTED_CASES |
| dropped_clause | 3 | 34 | 9 | 0 | 6.265 | 30/34 | MEETS_EXPECTATION_ON_TESTED_CASES |
| truncation | 3 | 43 | 0 | 0 | 6.884 | 43/43 | MEETS_EXPECTATION_ON_TESTED_CASES |
| punctuation_control | 0 | 43 | 0 | 0 | 1.116 | 33/43 | NOT_RELIABLY_DETECTED_ON_TESTED_CASES |

## Interpretation

Results apply to the selected high-scoring examples and the specific mutations present in the input CSV. A threshold pass rate of at least 80% with at least three scored cases is labeled as meeting expectations on tested cases; it is not a population-level reliability guarantee.
Review `fault_detection_results.csv` to inspect each original and modified candidate. Mutation quality, especially for negation, entity, number, and dropped-clause errors, should be checked before drawing strong conclusions.
