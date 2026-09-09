# Sprint 51 – Task 2: Automated Mandarin Inference, Evaluation, and Rollback Pipeline

## Overview

This notebook implements the automated inference and readiness-evaluation pipeline for the Mandarin fine-tuned model produced in **Sprint 51 – Task 1**.

The objective is to evaluate a fine-tuned English → Mandarin candidate model against a reconstructed baseline using a reproducible evaluation workflow. The pipeline combines automated translation generation, local LLM-based quality judging, deterministic language/format/safety checks, memorization detection, latency measurement, regression analysis, sealed-test integrity checks, and rollback validation.

The final pipeline produces an automated readiness decision indicating whether the candidate should:

* **ADVANCE** toward serving,
* **REVIEW-REVISE**, or
* be **REJECTED** because of a critical failure.

The notebook is designed to keep the evaluation process reproducible and to ensure that candidate and baseline models are evaluated under the same conditions.

---

## Task Objectives

The notebook addresses the following objectives:

1. Load and evaluate the Mandarin fine-tuned candidate checkpoint.
2. Reconstruct and evaluate the baseline model.
3. Generate translations over a fixed evaluation subset.
4. Calibrate and validate the local LLM judge.
5. Score candidate and baseline outputs consistently.
6. Detect wrong-language and mixed-language outputs.
7. Detect invalid or malformed outputs.
8. Check for safety violations.
9. Check candidate outputs for memorization of training targets.
10. Measure inference latency.
11. Verify sealed-test integrity and contamination status.
12. Measure domain regression relative to the baseline.
13. Validate that the baseline can still be restored and executed.
14. Apply the predefined readiness policy.
15. Produce reproducible artifacts documenting the final decision.

---

## Models

### Candidate

The candidate is the Mandarin fine-tuned model produced during Task 1.

```text
Version: candidate-v1
Base model: unsloth/Llama-3.2-1B-bnb-4bit
Fine-tuning: LoRA adapter
Task: English → Simplified Mandarin
Inference: 4-bit
```

The candidate prompt explicitly requires:

* Simplified Chinese output
* Mainland Mandarin vocabulary and grammar
* No Cantonese vocabulary or particles
* No Pinyin or romanization
* Translation only
* No explanations or additional text

### Baseline

The baseline is reconstructed independently so that the comparison does not depend on the fine-tuned candidate checkpoint.

```text
Version: baseline-reconstructed-v1
Model: unsloth/Llama-3.2-1B-Instruct-bnb-4bit
Mode: reconstructed baseline
Task: English → Mandarin
```

The baseline uses a separate professional English → Mandarin translation prompt. The prompt configuration is recorded in the evaluation manifest to maintain reproducibility.

---

## Evaluation Pipeline

The notebook follows the workflow below:

```text
Task 1 Dataset
      │
      ▼
Evaluation Subset Selection
      │
      ├───────────────┐
      ▼               ▼
Baseline Model    Candidate Model
      │               │
      ▼               ▼
Baseline Outputs  Candidate Outputs
      │               │
      └───────┬───────┘
              ▼
       Automated Checks
              │
      ┌───────┼────────┐
      │       │        │
      ▼       ▼        ▼
 Language   Format   Safety
      │       │        │
      └───────┼────────┘
              ▼
       Memorization Check
              │
              ▼
        Local LLM Judge
              │
              ▼
      Quality + Regression
              │
              ▼
       Latency Evaluation
              │
              ▼
     Sealed-Test Integrity
              │
              ▼
       Rollback Smoke Test
              │
              ▼
     Readiness Policy Engine
              │
              ▼
       Final Decision
```

---

## Dataset

The notebook uses the **Task 1 prompt-validation dataset** and filters it for English → Mandarin examples.

For the final automated comparison:

```text
Evaluation examples: 200
Sampling: random
Random seed: fixed
Baseline generations: 200/200
Candidate generations: 200/200
Generation failures: 0
```

Both models therefore receive the same evaluation inputs.

Generated outputs are saved as JSONL artifacts so that the evaluation can be inspected and reproduced without regenerating translations unnecessarily.

---

## Hardware and Software

The experiments were executed on Kaggle using:

```text
GPU: 2 × NVIDIA Tesla T4
GPU memory: ~14.56 GB per GPU
PyTorch: 2.10.0
CUDA: 12.8
Unsloth: 2026.9.2
Transformers: 5.5.0
```

The notebook performs a hardware probe and selects the appropriate local judge model based on available GPU memory.

The primary configuration used:

```text
Judge: Qwen/Qwen3-8B
Fallback: Qwen3-4B
Quantization: 4-bit
max_seq_length: 4096
max_new_tokens: 256
temperature: 0
```

---

## Judge Calibration

Translation quality is evaluated using a locally hosted Qwen judge calibrated against human-labeled data.

The calibration set contains:

```text
English → Mandarin: 50 examples
English → Cantonese: 50 examples
Total: 100 examples
```

For the Mandarin task, the 50 English → Mandarin examples are used for calibration.

Each example is evaluated using three independent judge runs. The aggregation procedure requires at least two valid runs and provides additional handling for unstable or low-score outlier judgments.

The normal aggregation uses a GEMBA-weighted mean. When judge disagreement exceeds the defined stability threshold, the aggregation falls back to a more robust median-based result.

### Calibration Results

| Metric          | Result | Threshold | Status |
| --------------- | -----: | --------: | ------ |
| Coverage        |  1.000 |   ≥ 0.900 | PASS   |
| Spearman ρ      |  0.701 |   ≥ 0.450 | PASS   |
| Pearson r       |  0.731 |         — | PASS   |
| MAE             |  0.694 |         — | PASS   |
| Weighted κ      |  0.678 |         — | PASS   |
| Mean confidence |  1.000 |   ≥ 0.700 | PASS   |
| Judge failures  |   0/50 |         — | PASS   |

The calibrated judge configuration is frozen in the judge registry and reused for candidate and baseline scoring.

---

## Sealed-Test Integrity

The final sealed test set is intentionally not opened during this evaluation.

The notebook verifies the dataset manifest and records the sealed-test hash:

```text
1cfe0efed56f5f545ed1c73feb8e8fccda55e639ac81d66b6e2907fd010c5b02
```

Integrity status:

```text
Sealed test opened: False
Contamination detected: False
```

This prevents accidental exposure of the final test set during candidate development and evaluation.

---

## Automated Guardrails

### 1. Wrong-Language Detection

The notebook checks generated translations for evidence that the output is not valid Mandarin.

The checks include:

* CJK character proportion
* Latin-character proportion
* Pinyin-like patterns
* Cantonese-specific vocabulary and particles
* mixed-language output

Examples of Cantonese markers checked include:

```text
佢
咗
喺
啲
冇
哋
嚟
嘅
```

These checks are intended to identify outputs that technically contain Chinese characters but do not satisfy the required Mandarin variety.

---

### 2. Invalid Output Detection

The pipeline checks for:

* empty outputs
* extremely short outputs
* role tags
* prompt leakage
* unwanted explanation prefixes
* Pinyin/romanization
* malformed responses
* outputs that do not follow the translation-only requirement

---

### 3. Safety Checks

Deterministic Mandarin and English pattern checks are applied to identify dangerous or disallowed concepts.

The final evaluation produced:

```text
Baseline safety violations: 0
Candidate safety violations: 0
```

Safety is treated as a critical gate rather than merely another quality metric.

---

### 4. Memorization Detection

Candidate translations are normalized and compared against Mandarin target strings contained in the training data.

The evaluated training-target reference set contained:

```text
1,500 training target examples
```

Results:

```text
Candidate memorization flags: 0
Memorization flag rate: 0.0%
```

A memorization or leakage failure is considered a critical rejection condition.

---

## Final Candidate vs. Baseline Results

| Metric                  | Baseline |   Candidate |       Change |
| ----------------------- | -------: | ----------: | -----------: |
| Mean quality score      |     5.75 |    **7.89** |    **+2.14** |
| Wrong-language rate     |    16.5% |    **2.5%** | **−14.0 pp** |
| Invalid-output rate     |     2.0% |    **0.0%** |  **−2.0 pp** |
| Safety violation rate   |     0.0% |    **0.0%** |    No change |
| Memorization flag rate  |     0.0% |    **0.0%** |    No change |
| Format-invalid rate     |     2.0% |    **0.0%** |  **−2.0 pp** |
| Generation failure rate |     0.0% |    **0.0%** |    No change |
| p95 latency             |  0.672 s | **0.735 s** |     +0.063 s |

The candidate improves the mean quality score from **5.75 to 7.89**, representing approximately a **37.2% relative improvement** over the reconstructed baseline.

Wrong-language output decreases from **16.5% to 2.5%**, an approximately **84.8% relative reduction**.

The candidate also eliminates the invalid and format-invalid outputs observed in the baseline evaluation.

---

## Latency

The notebook measures inference latency and reports the p95 value.

```text
Baseline p95: 0.672 s
Candidate p95: 0.735 s
Difference:    0.063 s
```

The candidate therefore introduces a small latency increase while remaining substantially below the readiness-policy latency limit.

---

## Domain Regression

Candidate quality is compared against the reconstructed baseline.

The measured quality delta is:

```text
Candidate - Baseline = +2.14
```

Therefore:

```text
Domain regression: False
```

There is no evidence from this evaluation that the fine-tuned candidate degraded performance on the evaluated English → Mandarin domain.

---

## Rollback Validation

Rollback readiness is verified by executing a smoke test against the reconstructed baseline.

Test input:

```text
Her sister also sings very beautifully.
```

Baseline output:

```text
她姐姐也很好地唱歌。
```

Result:

```text
Rollback smoke test failed: False
```

The reconstructed baseline remains operational and can therefore serve as the rollback path if the candidate is not approved for serving.

---

## Readiness Policy

The notebook applies three levels of automated decision criteria.

### Advance

The candidate must satisfy:

```text
Mean quality score       >= 8.0
Quality delta            >= 0
Wrong-language rate      <= 2%
Invalid-output rate      <= 2%
Safety violations        = 0
Memorization flags       = 0
Format-invalid rate      <= 2%
Failure rate             <= 2%
p95 latency              <= 8 s
```

### Review-Revise

A candidate can remain eligible for further improvement when it satisfies the broader review thresholds:

```text
Mean quality score       >= 6.5
Quality delta            >= -0.5
Wrong-language rate      <= 10%
Invalid-output rate      <= 8%
Format-invalid rate      <= 10%
Failure rate             <= 10%
p95 latency              <= 15 s
```

### Critical Rejection

The candidate is rejected when any critical condition occurs, including:

* safety violation
* memorization/leakage
* sealed-test contamination
* rollback failure

---

## Final Decision

The automated decision for `candidate-v1` is:

```text
REVIEW-REVISE
```

No critical rejection condition was triggered.

However, the candidate does not yet satisfy the strict **ADVANCE** gates:

### Quality

```text
Required:  >= 8.0
Observed:  7.89
Gap:       -0.11
```

### Wrong-language rate

```text
Required:  <= 2.0%
Observed:  2.5%
Gap:       +0.5 percentage points
```

The candidate therefore passes the broader review/revise thresholds but requires additional improvement before production advancement.

---

## Interpretation

The evaluation provides strong evidence that the Task 1 Mandarin fine-tuning process produced a meaningful improvement over the reconstructed baseline.

The primary improvements are:

* substantially higher translation quality
* much lower wrong-language output
* elimination of invalid outputs
* elimination of detected format violations
* zero safety violations
* zero memorization flags
* zero generation failures
* successful rollback validation
* no sealed-test contamination
* only a small latency increase

The remaining issues are concentrated around **quality and strict Mandarin-language adherence** rather than safety, reliability, contamination, or infrastructure stability.

The candidate is therefore best characterized as **technically healthy but not yet ready for unrestricted advancement under the strict production gates**.

---

## Recommended Next Steps

1. Improve the mean quality score from **7.89 to ≥8.0**.
2. Reduce wrong-language output from **2.5% to ≤2.0%**.
3. Manually inspect the remaining wrong-language cases.
4. Categorize failures into:

   * Cantonese vocabulary/particles
   * Traditional Chinese
   * English leakage
   * Pinyin
   * mixed-language output
   * malformed/short translations
   * possible heuristic false positives
5. Add representative failure cases to the training or validation data.
6. Produce a new candidate version.
7. Rerun the complete readiness pipeline using the same frozen judge and readiness policy.
8. Preserve the previous candidate and reconstructed baseline as rollback references.

---

## Generated Artifacts

The notebook produces or references the following artifacts:

```text
Frozen judge registry
Frozen readiness policy
Baseline outputs
Candidate outputs
Enriched evaluation results
Gold-set calibration results
Evaluation summary
Rollback smoke-test evidence
Readiness report
JSON readiness report
Submission manifest
Submission ZIP archive
```

Example submission archive:

```text
sprint51_task2_20260908T152058Z_task2_submission.zip
```

---

## Reproducibility

To reproduce the evaluation:

1. Use the same Task 1 dataset and manifest.
2. Use the fixed evaluation random seed.
3. Keep the sealed-test set closed.
4. Load the same candidate checkpoint and baseline configuration.
5. Use the frozen judge registry.
6. Use the same judge generation parameters.
7. Apply the same deterministic guardrails.
8. Use the same readiness-policy thresholds.
9. Preserve all generated JSONL and evaluation artifacts.
10. Record hardware and software versions with the run.

The evaluation should not be modified between candidate versions unless the judge, dataset, guardrails, or readiness policy are intentionally versioned and the change is explicitly documented.

---

## Notebook Structure

The notebook is organized around the following logical stages:

```text
1. Environment and dependency setup
2. Hardware/GPU detection
3. Candidate model loading
4. Baseline reconstruction
5. Evaluation dataset preparation
6. Candidate inference
7. Baseline inference
8. Judge loading and calibration
9. Quality scoring
10. Language and format guardrails
11. Safety checks
12. Memorization checks
13. Latency evaluation
14. Candidate/baseline comparison
15. Domain regression analysis
16. Sealed-test integrity verification
17. Rollback smoke test
18. Readiness-policy evaluation
19. Final decision
20. Artifact generation
```

---

## Final Status

```text
Candidate: candidate-v1
Task: English → Simplified Mandarin
Decision: REVIEW-REVISE

Quality improvement:       PASS
Language adherence:        NEAR GATE
Safety:                     PASS
Memorization:               PASS
Format validity:            PASS
Generation reliability:     PASS
Latency:                    PASS
Domain regression:          PASS
Sealed-test integrity:      PASS
Rollback readiness:         PASS

Production advancement:     NOT YET APPROVED
```

The next candidate should focus primarily on **raising translation quality above 8.0 and reducing wrong-language outputs to 2% or below** while preserving the safety, memorization, format, reliability, and rollback properties demonstrated by `candidate-v1`.
