# Sprint 54 Task 1 — Measure What Our Judge Can Actually Detect

## Overview

This task evaluates whether our LLM-as-a-Judge system can detect common errors in English-to-Mandarin (EN→CMN) translations. It compares the original translation score with the score assigned after introducing a specific fault.

Two judge models were evaluated: **Qwen3-8B** and **GLM-4-9B-0414**, using the same fault cases and P1 compliance evaluation prompt.

## Fault Categories

The experiment tests six translation errors and one control condition:

- Untranslated English
- Negation errors
- Entity errors
- Number errors
- Dropped clauses
- Truncation
- Punctuation-only changes as a control

Each error has a predefined expected score drop. Punctuation-only changes should have an absolute score change of no more than one point.

## Methodology

1. Load the fault cases from `fault_cases.csv`.
2. Score the original and modified translations using each judge.
3. Calculate the score drop for each case.
4. Compare score drops against predefined thresholds.
5. Report threshold pass rates, average score drops, skipped cases, and results by fault category.

The experiment contains **301 fault rows across 43 unique source examples**. Skipped or inapplicable mutations are excluded from pass-rate calculations.

## Key Findings

- **GLM-4-9B-0414** showed stronger fault detection overall, particularly for untranslated English and truncation.
- Both judges performed well on dropped-clause detection.
- Negation and number errors remain challenging for both models.
- **Qwen3-8B** was more stable on punctuation-only controls, while GLM sometimes penalized harmless punctuation changes.
- Entity-error results require further testing because many cases were skipped.

Neither judge should yet be considered a fully reliable standalone translation evaluator.

## Outputs

The experiment produces evaluation results for both judges, including per-case score comparisons, fault-category summaries, threshold pass rates, and skipped-case information.

