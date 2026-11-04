# Sprint 54 Task 1 — Judge Fault Detection Finding

Judge: zai-org/GLM-4-9B-0414; prompt: P1_compliance; temperature: 0.0.
Input file: `/kaggle/input/datasets/abdighaz/sprint-54-tasks/fault_cases_test2.csv`.
Unique source examples: 70.
Fault-case rows evaluated or retained: 70.

Only pre-generated mutations marked MUTATED were scored. Pre-generated SKIPPED cases remain in the results and are not counted as passes.
Fault thresholds are assessed only on successfully mutated and scored cases.
For punctuation control, a score-drop magnitude of at most 1 point is treated as preserving the score.

## Results

| Fault | Expected drop | Scored | Skipped | Unscorable | Mean drop | Threshold met | Finding |
|---|---:|---:|---:|---:|---:|---:|---|
| untranslated_english | 7 | 10 | 0 | 0 | 6.1 | 8/10 | MEETS_EXPECTATION_ON_TESTED_CASES |
| negation_error | 5 | 10 | 0 | 0 | 5.3 | 6/10 | NOT_RELIABLY_DETECTED_ON_TESTED_CASES |
| entity_error | 4 | 10 | 0 | 0 | 4.1 | 7/10 | NOT_RELIABLY_DETECTED_ON_TESTED_CASES |
| number_error | 4 | 10 | 0 | 0 | 5.3 | 8/10 | MEETS_EXPECTATION_ON_TESTED_CASES |
| dropped_clause | 3 | 10 | 0 | 0 | 5.1 | 9/10 | MEETS_EXPECTATION_ON_TESTED_CASES |
| truncation | 3 | 10 | 0 | 0 | 6.3 | 9/10 | MEETS_EXPECTATION_ON_TESTED_CASES |
| punctuation_control | 0 | 10 | 0 | 0 | 0.0 | 10/10 | MEETS_EXPECTATION_ON_TESTED_CASES |

## Interpretation

Results apply to the selected high-scoring examples and the specific mutations present in the input CSV. A threshold pass rate of at least 80% with at least three scored cases is labeled as meeting expectations on tested cases; it is not a population-level reliability guarantee.
Review `fault_detection_results.csv` to inspect each original and modified candidate. Mutation quality, especially for negation, entity, number, and dropped-clause errors, should be checked before drawing strong conclusions.
