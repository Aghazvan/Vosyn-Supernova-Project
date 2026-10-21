# Sprint 54 — Task 2: Establish the Judge’s Smallest Score Difference

## Objective
Measure how much the LLM-as-a-Judge score changes when the same English-to-Mandarin translation is evaluated repeatedly without changing the input. The goal is to understand score repeatability and establish a practical threshold for interpreting score differences.

## Method
- Evaluated **50 English-to-Mandarin gold examples** using the same dataset and `P1_compliance` judge prompt.
- Tested two models: **Qwen3-8B** and **GLM-4-9B-0414**.
- Ran each example three times at temperatures **0.0** and **0.2**.
- Measured per-example score ranges, within-example standard deviation, and the percentage of identical scores across runs.
- Compared repeatability between the two models.

## Key Findings
- At temperature **0.0**, both models returned identical scores across all three runs for all 50 examples.
- At temperature **0.2**, Qwen3-8B was more repeatable than GLM-4-9B, with identical scores for 84% of examples versus 64%.
- A **0.5-point score difference** was used as a provisional practical threshold, not as a statistically validated significance boundary.
- Repeatability does not guarantee translation-quality accuracy; the judge's fault-detection performance must also be considered.

## Conclusion
Qwen3-8B showed less score variation than GLM-4-9B at temperature 0.2. Both models were fully repeatable at temperature 0.0. These results help establish a baseline for interpreting score differences, but further validation against known translation errors and human judgments is needed.

## Outputs
The experiment outputs include configuration details, per-example scores, repeatability metrics, and summary results for both models.