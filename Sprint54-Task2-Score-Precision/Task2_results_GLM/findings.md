# Sprint 54 Task 2 — Judge Score Precision Finding

Judge: zai-org/GLM-4-9B-0414; prompt: P1_compliance; runs per example/temperature: 3.
Examples: 50 EN→Mandarin gold-set rows. Temperatures: 0.0 and 0.2.

**Minimum actionable score difference: 0.500/10.** This is the larger of the predeclared practical floor (0.500) and twice the largest observed set-mean SEM. It is a provisional operational threshold, not proof that smaller differences are meaningless.

## Results

| Temperature | Examples | Mean range | Max range | Mean within-example SD | Identical-run examples | Set-mean SEM | Approx. 95% margin |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 50 | 0.000 | 0.000 | 0.000 | 50 | 0.174 | 0.341 |
| 0.2 | 50 | 0.400 | 2.000 | 0.231 | 32 | 0.149 | 0.292 |

## Interpretation

Within-example score range and SD measure run-to-run repeatability. The set-mean SEM instead describes uncertainty in the average score across this finite set of examples; these quantities must not be confused. If all temperature-0 scores repeat identically, the observed within-example SD is zero, but systematic judge errors remain possible. Temperature 0.2 can reveal sampling variability, though three runs give only a rough estimate.

The sample-size table uses a normal-approximation planning calculation with the observed between-example SD and a predeclared difference. It is a planning proxy for the set mean, not a direct estimate of the number of examples needed for every paired model comparison. For a future baseline-versus-candidate decision, estimate the SD of paired per-example score differences and calculate power from those differences.

See `experiment_config.json` for the configuration fingerprint, dataset hash, and environment versions; `raw_runs.csv` retains each raw judge response for audit.
