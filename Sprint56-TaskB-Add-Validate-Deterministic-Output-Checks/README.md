# Sprint 56 Task B — deterministic output checks

## Scope

Task B adds deterministic candidate-output checks while preserving the Task A
Andromeda conversion and JSONL validation workflow. The existing
`scripts/convert_andromeda.py` is intentionally unchanged: conversion is Task A,
while the Task B checks run against its converted records.

The updated files are:

- `gepa/checks.py`: current check implementation, extended with Pinyin detection
  and direction-aware length-ratio checks. The existing `CheckResult`,
  `CheckReport`, registry, and fail-closed OpenCC behavior are retained.
- `gepa/output_check_config.py`: per-direction check activation and calibrated
  length-ratio bounds.
- `scripts/analyze_task_b.py`: reproducible Andromeda label and reference-pair
  calibration summary.
- `scripts/evaluate_script_check.py`: evaluates both script-check directions
  against all 33 orthography-labelled rows, reporting each sublabel.
- `scripts/audit_output_checks.py`: runs checks on all 179 converted records and
  compares reference translations as a false-positive warning baseline.
- `tests/test_adapted_output_checks.py`: extends the existing tests; no new test
  file is required.

## Direction-specific activation

| Direction | Target | Task B-specific checks |
|---|---|---|
| EN → CMN (`en->zh`) | Simplified Chinese | `simplified_script`, `pinyin`, `length_ratio` |
| EN → YUE (`en->yue`) | Traditional Chinese | `traditional_script`, `pinyin`, `length_ratio` |
| CMN → EN (`zh->en`) | English | `length_ratio` |
| YUE → EN (`yue->en`) | English | `length_ratio` |

The existing checks for target script, residual Latin/CJK, numbers, truncation,
degeneration, and Cantonese markers remain configured as appropriate. Pinyin is
only enabled for Chinese-target directions. It detects runs of at least two
Pinyin-looking syllables, including tone-marked and tone-number forms. Its
exemptions mirror `check_no_residual_latin`: words carried over from the source,
the existing built-in allowlist, and uppercase acronyms. A caller may also pass
approved names through `allowed_latin_terms`. Pinyin detection is heuristic and
should not be treated as a general language identifier.

## Script validation

The source has 33 orthography-labelled records: 29 EN→YUE Chinese rows and four
EN→TE Telugu rows. The four Telugu rows are reported as not applicable to a
Chinese script detector. The evaluator reports both functions because they
check opposite target scripts:

- `check_simplified_script` uses OpenCC `t2s` and detects Traditional characters
  (expected in `standard_written_chinese` and `mixed_script` EN→YUE rows).
- `check_traditional_script` uses OpenCC `s2t` and detects Simplified-form
  characters (expected in `simplified_script` EN→YUE rows).

Each check reports accuracy and TP/FP/TN/FN by all three Chinese sublabels and
overall. If OpenCC is missing, the evaluation is marked blocked and exits with a
non-zero status; the check itself never silently passes.

Run it after installing dependencies:

```bash
python -m pip install -r requirements-task-b.txt
python scripts/evaluate_script_check.py
```

The result is written to `reports/script_check_evaluation.json`.

## Length-ratio calibration

Calibration and runtime checking now use the same direction-aware units:

- EN→CMN/YUE: CJK output characters divided by English source words.
- CMN/YUE→EN: English output words divided by CJK source characters.

Andromeda reference-pair distributions:

| Direction | n | P05 | Median | P95 | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| `en->zh` | 27 | 1.133 | 1.455 | 2.000 | 1.083 | 2.000 |
| `en->yue` | 111 | 1.042 | 1.667 | 2.125 | 0.778 | 3.000 |
| `zh->en` | 26 | 0.507 | 0.723 | 1.115 | 0.500 | 1.143 |
| `yue->en` | 15 | 0.532 | 0.769 | 1.000 | 0.500 | 1.000 |

Enabled first-pass guardrails:

| Direction | Min | Max | Minimum source units |
|---|---:|---:|---:|
| `en->zh` | 0.70 | 2.60 | 8 English words |
| `en->yue` | 0.70 | 2.80 | 6 English words |
| `zh->en` | 0.35 | 1.45 | 12 CJK characters |
| `yue->en` | 0.35 | 1.45 | 6 CJK characters |

The bounds widen the observed reference-pair tails and are anomaly-screening
guardrails, not universal translation laws or semantic adequacy metrics. The
EN→YUE maximum is 2.80 because one curated reference pair has a ratio of 2.67;
a 2.60 ceiling would flag that reference. Short sources below the lower-tail
source-unit cutoff are not assessed because their ratios are unstable. All four
directions are enabled, but audit failures and reference warnings must be
reviewed before using the check as a blocking production gate.

Reproduce the calibration summary with:

```bash
python scripts/analyze_task_b.py
```

It writes `reports/task_b_corpus_audit.json`.

## Full corpus audit

Run:

```bash
python scripts/audit_output_checks.py
```

It writes `reports/output_check_audit.json`, including per-direction check
counts, failed examples, reference-check warnings, annotation-to-check
diagnostics, and the calibration summary. Missing OpenCC checks are recorded
as unavailable, never as passes.

## Tests and current validation

Run the existing project suite:

```bash
python -m pytest -v
```

The updated suite has **28 passing tests** in this build. It covers Pinyin
plain/tone-marked/tone-number forms, source-carried proper names, acronyms,
allowlisted terms, script-check behavior, missing-OpenCC failure, direction-aware
length measurement/calibration, configuration activation, and Task A conversion
regressions.

The isolated build environment used for this update does not have OpenCC and
cannot reach package indexes. Therefore the real 29-record OpenCC accuracy run
could not be executed here. The evaluator is updated and ready to run in the
user's environment, where `opencc-python-reimplemented` was previously
confirmed installed. Do not claim the labelled script-accuracy criterion is
complete until `scripts/evaluate_script_check.py` produces its completed JSON
report.

## Production integration boundary

This project bundle does not include the production GEPA runner or its live
language configuration files. The updated `gepa/checks.py` and
`gepa/output_check_config.py` are validated within this Sprint 56 project, but
that does not prove they are wired into the production Supernova runtime. The
production owner must still adapt the result protocol and connect these configs
in the actual runner before deployment.
