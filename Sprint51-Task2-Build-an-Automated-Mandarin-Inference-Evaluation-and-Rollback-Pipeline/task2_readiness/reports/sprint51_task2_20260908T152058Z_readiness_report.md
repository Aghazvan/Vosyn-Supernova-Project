# Sprint 51 Task 2 Readiness Report

## Decision
**REVIEW-REVISE**

## Reasons
- met review-revise thresholds but not advance thresholds

## Candidate
- Version: candidate-v1
- Type: lora_adapter
- Base model: unsloth/Llama-3.2-1B-bnb-4bit
- Manifest: /kaggle/input/notebooks/abdighaz/sprint51-task1-full-finetuning-pipeline/task1_en2zh_outputs/manifests/candidate_manifest.json

## Baseline
- Version: baseline-reconstructed-v1
- Mode: reconstruct

## Judge
- Model: Qwen/Qwen3-8B
- Tier: primary
- Golden direction: EN_CMN
- Coverage: 1.0
- Spearman rho: 0.701
- Pearson r: 0.731
- MAE: 0.694
- Weighted kappa: 0.678
- Mean confidence: 1.0

## Candidate vs Baseline
| Metric | Baseline | Candidate |
|---|---:|---:|
| Mean quality score | 5.75 | 7.89 |
| Wrong-language rate | 0.165 | 0.025 |
| Invalid-output rate | 0.02 | 0.0 |
| Safety violation rate | 0.0 | 0.0 |
| Memorization flag rate | 0.0 | 0.0 |
| Format-invalid rate | 0.02 | 0.0 |
| Failure rate | 0.0 | 0.0 |
| Latency p95 (s) | 0.6717799999999999 | 0.7352499999999995 |

## Domain regression
- Quality delta vs baseline: 2.1399999999999997
- Regressed: False

## Rollback
- Baseline smoke test failed: False
- Sealed test contamination detected: False
- Leakage scan flagged outputs: 0
