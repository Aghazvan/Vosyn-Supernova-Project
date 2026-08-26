# Sprint 50 - Task A: Judge Validation and Finalization

Scaffold for building the gold set, scoring it with each proposed judge
configuration, measuring agreement with human labels, and locking in one
final judge configuration per language direction.

## Files

- `gepa_modules/gold_set.py` -- gold set schema, CSV loader, validation
  (30-50 samples/direction, score-range checks, duplicate-id checks), and an
  optional inter-annotator agreement check for the gold set itself.
- `gepa_modules/aggregation.py` -- `aggregate_runs()`: robust multi-run
  aggregation. Explicitly handles malformed/out-of-range judge output,
  suspicious near-zero outliers, and high inter-run disagreement (falls back
  to median instead of averaging through it). Returns
  `{final_score, confidence, flag, ...}`, not a bare number.
- `gepa_modules/scoring_harness.py` -- runs each `JudgeConfig` over the gold
  set via a pluggable `judge_fn` callable, so it doesn't matter whether the
  backend is Groq (Sprint 47/48), local Qwen3 (Sprint 49), or a new config.
- `gepa_modules/agreement_metrics.py` -- Pearson r, Spearman rho, MAE,
  quadratic-weighted Cohen's kappa per (config, direction), plus coverage
  (fraction of gold samples the config actually scored). `select_final_config()`
  picks the per-direction winner by Spearman rho, tie-broken by MAE.
- `gepa_modules/config.py` -- **fill this in.** `JUDGE_CONFIGS` is empty by
  default; wire in this sprint's actual candidate judge configurations here,
  each wrapped to return a `RunResult`.
- `gold_set_template.csv` -- schema example with 4 illustrative rows (2 per
  direction). Replace with the real 30-50-per-direction bilingually-reviewed
  set.
- `Task_A_Judge_Validation.ipynb` -- driver notebook: load gold set -> score
  with every config -> compare agreement -> select winners -> write
  `final_judge_config.md`.

## Usage

1. Replace `gold_set_template.csv` with the real reviewed gold set (same columns).
2. Fill in `JUDGE_CONFIGS` in `gepa_modules/config.py` -- adapters for the
   existing Groq and local Qwen3 judges are sketched in comments there.
3. Run `Task_A_Judge_Validation.ipynb` top to bottom.
4. Check the flag breakdown in section 2a before trusting the agreement
   numbers -- a config with a lot of `judge_failed` or `high_disagreement`
   rows needs a look before it's allowed to win on coverage alone.
5. `final_judge_config.md` is the artifact to hand to the team --
   supersedes the scattered Sprint 46-48 judge recommendations.

## Design notes

- Aggregation intentionally returns a confidence/flag alongside every score.
  A `judge_failed` sample should read as missing data to GEPA, not as a
  real low score -- and `select_final_config()` scores configs on coverage
  as well as agreement so a config can't win by silently dropping the
  samples it struggled with.
- Winners are picked **per direction**, not globally -- EN-YUE and EN-CMN
  are allowed to land on different configs given the dialect-specific rubric
  dimension.
- The gold set loader supports an optional pre-reconciliation
  inter-annotator check (`inter_annotator_agreement()`) so the gold labels
  themselves get a sanity check before anything is measured against them.
