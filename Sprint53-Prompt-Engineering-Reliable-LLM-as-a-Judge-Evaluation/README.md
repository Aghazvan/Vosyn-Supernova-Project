# Sprint 53 Task 2 — Multi-Prompt Engineering LLM-as-a-Judge Experiment

## Overview

This script evaluates different prompt-engineering strategies for **LLM-as-a-Judge evaluation of English → Mandarin translation**.

The experiment uses **Qwen/Qwen3-8B** as the fixed judge and compares five prompt configurations while keeping the model, evaluation data, and scoring process consistent.

### Prompt configurations

| ID     | Prompt      | Purpose                                                          |
| ------ | ----------- | ---------------------------------------------------------------- |
| **P0** | Baseline    | Existing Sprint 51 judge prompt                                  |
| **P1** | Compliance  | Explicit language, script, leakage, Pinyin, and Cantonese checks |
| **P2** | Semantic    | Prioritizes semantic fidelity and meaning preservation           |
| **P3** | Error-First | Identifies and classifies errors before assigning a score        |
| **P4** | Combined    | Combines compliance, semantic, and structured error evaluation   |

---

## Experiment Design

The script contains two evaluation phases.

### Phase A — Prompt Comparison

All five prompts are evaluated at:

```text
Temperature: 0.0
Runs: 1
```

Two datasets are used:

* **50 human-labeled EN→Mandarin examples** for validity/agreement
* **20 targeted challenge examples** for known failure modes

The gold set measures:

* Pearson correlation
* Spearman correlation
* Mean Absolute Error (MAE)
* Weighted Cohen's kappa
* Coverage
* JSON/parse success

The challenge set measures:

* Critical-failure recall
* Structured-failure recall
* False-positive rate
* Scores for critical vs. non-critical examples
* Failure-category performance

### Phase B — Consistency Test

The top three prompts from Phase A are evaluated repeatedly:

```text
Temperature: 0.2
Runs: 5
```

The script measures:

* Mean run standard deviation
* Mean score range
* Exact agreement rate
* High-disagreement rate
* Judge confidence
* Parse success
* Strict JSON success

This tests whether prompt behavior remains stable under non-zero-temperature generation.

---

## Requirements

The script is designed for a **Kaggle GPU environment**.

Main dependencies include:

* Python
* PyTorch
* Transformers
* Unsloth
* NumPy
* Pandas
* SciPy
* scikit-learn

If Unsloth is not installed, the script installs it automatically.

The judge model is:

```text
Qwen/Qwen3-8B
```

loaded in 4-bit mode.

---

## Configuration

Before running the experiment, update the gold dataset path in `CONFIG`:

```python
"gold_set_csv_path": "/kaggle/input/YOUR_DATASET/YOUR_50_SAMPLE_GOLD.csv"
```

Important settings include:

```python
"model_name": "Qwen/Qwen3-8B"
"phase_a_temperature": 0.0
"phase_a_runs": 1
"phase_b_temperature": 0.2
"phase_b_runs": 5
"base_generation_seed": 5300
```

The output directory is:

```text
/kaggle/working/sprint53_task2_outputs
```

---

## Running the Experiment

Run the Python script in the configured Kaggle GPU environment:

```bash
python Sprint53_Task2_MultiPrompt_LLM_Judge_Experiment.py
```

Make sure the gold-set CSV path is configured before execution.

For testing/debugging, the script also provides a dry-run configuration:

```python
"dry_run": True
```

with:

```python
"dry_run_n": 5
```

---

## Output Structure

The script creates the following directories:

```text
sprint53_task2_outputs/
├── raw_runs/
├── aggregated/
├── summaries/
├── challenge/
└── tables/
```

Important output files include:

### Raw evaluation results

```text
raw_runs/phase_a_gold_raw.csv
raw_runs/phase_a_challenge_raw.csv
```

These contain individual judge outputs, scores, prompts, runs, seeds, errors, compliance flags, and raw model responses.

### Aggregated results

```text
aggregated/phase_a_gold_aggregated.csv
aggregated/phase_a_challenge_aggregated.csv
```

These contain per-example aggregated scores and run-consistency information.

### Metric tables

```text
tables/phase_a_gold_validity_metrics.csv
tables/phase_a_challenge_metrics.csv
tables/phase_b_consistency_metrics.csv
tables/final_prompt_comparison.csv
```

These provide the main comparison between prompt configurations.

The experiment also saves summary information in JSON format.

---

## Reproducibility

Each evaluation run receives a deterministic seed based on:

```text
base_generation_seed
+ example index
+ prompt index
+ run index
```

This allows the experiment to reproduce the same evaluation configuration and clearly associate each result with its prompt and run.

---

## Main Results

The experiment found that different prompts optimize different objectives.

### Human-validity performance

P0 produced the strongest agreement with the human-labeled set:

```text
Spearman  = 0.701
Pearson   = 0.731
MAE       = 0.694
Kappa     = 0.678
```

### Critical-failure detection

P1 Compliance performed best:

```text
Critical-failure recall = 52.9%
```

compared with:

```text
P0 Baseline = 23.5%
```

### Repeated-run consistency

P4 Combined produced the strongest consistency:

```text
Exact agreement = 100%
Mean run SD     = 0.000
Mean run range  = 0.000
```

However, P4 had weaker agreement with human judgments.

---

## Recommended Prompt

**P1 Compliance is the recommended prompt for further validation.**

It provides the best overall balance between:

* human agreement,
* critical-failure detection,
* structured output,
* repeated-run consistency.

P0 should remain the baseline for future comparisons, while P4 is useful as a highly structured and stable alternative.

The current experiment should not be considered final production validation because it uses **50 human-labeled examples and 20 targeted challenge examples**, rather than the complete 200-example evaluation set.

The recommended next step is to validate P1 against the full evaluation set.

---

## Notes

This experiment is designed to measure **prompt effects**, not to compare different judge models.

The main conclusion is:

> **A highly consistent judge is not necessarily a highly valid judge. Prompt evaluation should measure validity, failure detection, consistency, and structured-output reliability separately.**
