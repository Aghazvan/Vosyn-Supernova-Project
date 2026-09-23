# Sprint 52 Task A — Prepare a Mandarin Dataset for Human Review

## Overview

This notebook implements **Sprint 52 Task A: Prepare a Mandarin Dataset for Human Review**. The objective is to create a fresh, traceable Mandarin translation review set that can be evaluated by human reviewers and subsequently used to obtain reliable labels for validating the Mandarin translation judge.

The pipeline creates a balanced **120-example EN→CMN review dataset** from three independently sourced data tiers:

* **Clean:** FLORES-200 `devtest`
* **Domain:** WMT19 `validation`
* **Colloquial:** FradSer/OpenSubtitles-en-zh-cn-20m `train`

Each tier contributes **40 examples**, giving a total of 120 examples.

The notebook also generates Mandarin candidate translations using the **Sprint 51 fine-tuned translation checkpoint** and packages the resulting examples with source/reference text, provenance metadata, and blank human-review fields.

---

## Objectives

The notebook addresses the following Sprint 52 Task A requirements:

1. Select additional examples per direction from data independent of the original Sprint 51 examples.
2. Include different source/domain types rather than only clean benchmark sentences.
3. Record source information for every example.
4. Define the target number of examples before sampling.
5. Package the dataset with clear reviewer instructions and a defined scoring rubric.

The final dataset is designed specifically for **human quality assessment**, not automated model benchmarking.

---

## Dataset Composition

The final review set contains:

| Tier       | Source Dataset                       | Split        | Examples |
| ---------- | ------------------------------------ | ------------ | -------: |
| Clean      | `facebook/flores`                    | `devtest`    |       40 |
| Domain     | `wmt/wmt19`                          | `validation` |       40 |
| Colloquial | `FradSer/OpenSubtitles-en-zh-cn-20m` | `train`      |       40 |
| **Total**  |                                      |              |  **120** |

All examples currently use the:

```text
en2cmn
```

direction.

The three tiers represent different **source/domain characteristics**, rather than objectively measured difficulty levels.

---

## Pipeline Overview

The notebook follows the workflow below:

```text
Sprint 51 Training/Evaluation Data
              │
              ▼
      Build Exclusion Hash Set
              │
              │
     ┌────────┼─────────┐
     ▼        ▼         ▼
  FLORES     WMT19   OpenSubtitles
   Clean     Domain    Colloquial
     │        │         │
     └────────┼─────────┘
              ▼
      Normalize + Filter
              │
              ▼
   Exclude Exact Sprint 51
      Text Overlaps
              │
              ▼
       Random Sampling
       40 per Tier
              │
              ▼
    Sprint 51 Fine-Tuned
       Model Inference
              │
              ▼
       Human Review Set
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
      CSV    JSONL  Manifest
```

---

## 1. Environment and Dependencies

The notebook is designed to run in a Kaggle GPU environment and uses Unsloth for efficient model loading and inference.

Main dependencies include:

```text
datasets
huggingface_hub
unsloth
torch
tqdm
sacremoses
```

The notebook installs the required packages at runtime.

The model is loaded in 4-bit mode to reduce GPU memory requirements. The tested environment used an NVIDIA Tesla T4 GPU.

---

## 2. Configuration

The notebook defines the Sprint 51 source files, fine-tuned checkpoint, output directories, sampling targets, dataset sources, and filtering thresholds.

The target configuration is:

```python
TARGET_PER_DIRECTION_PER_TIER = {
    "clean": 40,
    "domain": 40,
    "colloquial": 40,
}
```

Therefore:

```text
40 + 40 + 40 = 120 examples
```

A fixed random seed is used:

```python
RANDOM_SEED = 52
```

This makes the sampling process reproducible when the same source data and filtering configuration are available.

---

## 3. Sprint 51 Overlap Exclusion

To prevent direct reuse of Sprint 51 examples, the notebook builds an exclusion set from the Sprint 51 training and evaluation splits.

The following Sprint 51 files are checked:

```text
finetune.jsonl
judge_calibration.jsonl
prompt_validation.jsonl
sealed_final_test.jsonl
```

Both source and target texts are normalized and hashed using SHA-256.

The normalization includes:

* Unicode NFKC normalization
* whitespace normalization
* trimming surrounding whitespace
* consistent text representation before hashing

The completed run produced:

```text
45,938 unique hashes
```

During sampling, an example is rejected if either its normalized source or normalized target matches a hash from the Sprint 51 exclusion set.

Each accepted row receives:

```text
dedup_check = passed
```

### Important methodological qualification

This mechanism guarantees exclusion of **exact normalized-text overlaps**. It does **not** guarantee the absence of semantic or near-duplicate examples.

For example, a paraphrased sentence with different wording could potentially pass the exact-text check.

Therefore, the methodology should be described as:

> The review set was independently sourced from new dataset splits and filtered to exclude exact normalized-text overlaps with Sprint 51 training and evaluation data.

A future version can add embedding-based semantic similarity screening.

---

## 4. Source Loading

### Clean Tier — FLORES-200

The clean tier uses:

```text
facebook/flores
config: eng_Latn-zho_Hans
split: devtest
```

The English and Simplified Chinese fields are extracted and normalized.

Each example receives an identifier such as:

```text
flores200_devtest_184
```

---

### Domain Tier — WMT19

The domain tier uses:

```text
wmt/wmt19
config: zh-en
split: validation
```

The English and Chinese translations are extracted from the dataset's `translation` field.

Each example receives an identifier such as:

```text
wmt19_newstest_<index>
```

The source provides more formal and news/domain-oriented content, including terminology, names, factual statements, and formal language.

---

### Colloquial Tier — OpenSubtitles

The colloquial tier uses:

```text
FradSer/OpenSubtitles-en-zh-cn-20m
config: default
split: train
```

The dataset uses:

```text
source
target
```

rather than `en` and `zh` column names.

Basic filtering is applied for:

* missing source/target text
* character length
* Chinese character presence

Subtitle alignment noise is possible because the data originates from subtitle material. The notebook does not aggressively filter such cases because the objective is to create a realistic human-review set rather than only high-quality reference pairs.

---

## 5. Filtering

The filtering stage performs basic validity checks while intentionally avoiding overly aggressive quality filtering.

For each example:

1. Normalize source and target text.
2. Check minimum and maximum character length.
3. Confirm the target contains CJK characters.
4. Check against the Sprint 51 exact-overlap exclusion set.
5. Keep the eligible example.
6. Shuffle eligible examples using the fixed random seed.
7. Select the required number.

Configured thresholds are:

| Tier       | Minimum | Maximum |
| ---------- | ------: | ------: |
| Clean      |      15 |     300 |
| Domain     |      15 |     300 |
| Colloquial |       2 |     300 |

The shorter minimum for colloquial data accommodates short subtitle/dialogue utterances.

---

## 6. Candidate Translation Generation

Candidate translations are generated using the Sprint 51 fine-tuned Mandarin checkpoint.

The model is instructed to:

* translate English into standard Mainland Mandarin
* output Simplified Chinese
* avoid Cantonese vocabulary and particles
* avoid Pinyin/romanization
* output only the translation
* avoid explanations or commentary
* preserve English proper nouns when no Mandarin equivalent is appropriate

The inference process uses the same chat-template structure used during Sprint 51 fine-tuning.

Generation is deterministic:

```python
do_sample=False
```

The notebook also explicitly disables the model's inherited maximum-length setting:

```python
model.generation_config.max_length = None
```

This avoids a conflict between the checkpoint's generation configuration and the `max_new_tokens` value used during inference.

---

## 7. Model Checkpoint

The notebook uses the Sprint 51 fine-tuned checkpoint:

```text
/kaggle/input/notebooks/abdighaz/
sprint51-task1-full-finetuning-pipeline/
task1_en2zh_outputs/final
```

The checkpoint is loaded with:

```python
FastLanguageModel.from_pretrained(
    model_name=str(CHECKPOINT_DIR),
    max_seq_length=1024,
    dtype=None,
    load_in_4bit=True,
    device_map={"": 0},
)
```

After loading, the model is switched to inference mode using:

```python
FastLanguageModel.for_inference(model)
```

---

## 8. Review Dataset Schema

Each review record contains source information, model output, and blank human-review fields.

The main columns are:

```text
id
direction
quality_tier
source_text
reference_text
candidate_text
source_dataset
source_example_id
license
retrieval_date
dedup_check
Semantic_Accuracy
Fluency
Tone_Register
Emotional_Consistency
Cultural_Appropriateness
Dialect_Correctness
Overall_Comments
```

### Example

A typical record contains:

```text
id:
s52_taskA_00001

direction:
en2cmn

quality_tier:
clean

source_text:
The strain of bird flu lethal to humans...

reference_text:
周一,法国东部...

candidate_text:
野鳥流感病毒H5N1...

source_dataset:
facebook/flores

source_example_id:
flores200_devtest_184

dedup_check:
passed
```

The six scoring columns and `Overall_Comments` are intentionally left blank for human reviewers.

---

## 9. Human Review Rubric

The review package uses six dimensions, each scored from **1 to 5**.

| Dimension                | Evaluation Focus                                        |
| ------------------------ | ------------------------------------------------------- |
| Semantic Accuracy        | Preservation of the source meaning                      |
| Fluency                  | Naturalness and grammatical quality                     |
| Tone / Register          | Preservation of formality and style                     |
| Emotional Consistency    | Preservation of emotion, urgency, humor, sarcasm, etc.  |
| Cultural Appropriateness | Natural handling of idioms and cultural references      |
| Dialect Correctness      | Standard Simplified Mandarin and appropriate vocabulary |

The scoring scale is:

```text
1 = Very poor
2 = Poor
3 = Acceptable / mixed
4 = Good
5 = Excellent
```

Reviewers are instructed to score every dimension independently.

A translation can therefore receive a high Semantic Accuracy score while receiving a lower Fluency or Cultural Appropriateness score.

---

## 10. Reviewer Instructions

The accompanying scoring instructions require reviewers to:

* score each row independently
* evaluate each dimension separately
* avoid automatically penalizing the same problem twice unless it genuinely affects multiple dimensions
* use the reference translation as guidance rather than exact-match ground truth
* avoid guessing when a row is corrupted or incomplete
* flag unusable rows with `FLAG: bad row`

If a source or candidate is blank, corrupted, or clearly truncated, reviewers should leave all six scores blank and add:

```text
FLAG: bad row
```

to `Overall_Comments`.

---

## 11. Mandarin-Specific Review Considerations

The review procedure places particular emphasis on Mandarin correctness because the model is intended to produce standard Mainland Mandarin in Simplified Chinese.

Reviewers should pay attention to:

* Traditional Chinese characters
* Cantonese-specific vocabulary or particles
* inappropriate dialectal wording
* mixed English/Chinese output
* unnatural transliteration
* incorrect names and terminology
* inappropriate handling of Mainland Mandarin vocabulary
* incorrect idiomatic adaptations

For example, candidates containing characters such as:

```text
這
他們
已經
爐子
做飯
```

should be considered when assigning the Dialect Correctness score because the requested output format is Simplified Mandarin.

---

## 12. Output Files

The notebook produces the following files:

```text
review_package/
├── mandarin_human_review_set.csv
├── mandarin_human_review_set.jsonl
└── review_set_manifest.json
```

### CSV

`mandarin_human_review_set.csv` is intended for direct use by human reviewers in spreadsheet software.

### JSONL

`mandarin_human_review_set.jsonl` contains one structured JSON object per review example and is intended for programmatic downstream processing.

### Manifest

`review_set_manifest.json` records package-level information useful for reproducibility, validation, and auditability.

---

## 13. Validation Results

The completed pipeline produced the requested number of examples without a sampling shortfall.

Final distribution:

```text
EN→CMN
├── Clean:      40
├── Domain:     40
└── Colloquial: 40
                ───
Total:          120
```

Candidate generation also completed for all 120 examples.

The final package therefore satisfies the planned sample-size requirement and contains all expected output artifacts.

---

## 14. Observed Candidate Output Characteristics

The final candidate translations intentionally contain a range of model behaviors. Several outputs are reasonably fluent and semantically appropriate, while others contain substantial translation errors.

Observed error categories include:

* semantic omissions
* incorrect facts or terminology
* incorrect names
* incorrect numbers and units
* incomplete translations
* awkward Mandarin
* Traditional Chinese characters
* mixed English and Chinese
* literal idiom translation
* incorrect emotional interpretation
* poor handling of colloquial expressions

These errors are not automatically removed because the goal of the task is to obtain human labels that characterize model quality.

The presence of poor translations is therefore an expected and useful property of the review dataset.

---

## 15. Licensing and Data-Use Considerations

The notebook records the available license metadata for each source in the review dataset.

The currently recorded licenses include:

```text
FLORES-200: CC-BY-SA 4.0
WMT19: Unknown
OpenSubtitles repository: MIT
```

These values are recorded for traceability and should not be interpreted as a complete legal assessment of commercial redistribution rights.

In particular, the repository-level MIT designation for the OpenSubtitles-derived dataset should not automatically be interpreted as blanket permission for commercial use of all underlying subtitle content. Any external or commercial redistribution should undergo the appropriate licensing review.

---

## 16. Reproducibility

The notebook is designed to make the dataset construction process reproducible.

Important reproducibility parameters include:

```text
Random seed: 52
Target per tier: 40
Total target: 120
Direction: EN→CMN
Model checkpoint: Sprint 51 fine-tuned checkpoint
Inference: deterministic
Deduplication: SHA-256 of normalized text
```

The source dataset names, configurations, splits, filtering thresholds, system prompt, checkpoint path, and output structure are explicitly defined in the notebook.

Reproducing the exact dataset may still depend on the availability and version of the external source datasets and model checkpoint.

---

## 17. Limitations

The primary methodological limitation is the scope of the independence check. The pipeline excludes exact normalized-text overlaps with Sprint 51 data but does not perform semantic similarity or paraphrase detection.

A second limitation is that OpenSubtitles data can contain context-dependent or imperfect subtitle alignments. Some examples may therefore be difficult to evaluate without surrounding dialogue. Such cases are retained because the dataset is intended to represent realistic translation conditions.

The candidate translations should also not be interpreted as a quantitative model benchmark. Human scores have to be collected before aggregate quality conclusions can be drawn.

---

## 18. Future Improvements

The most important future improvement is to introduce semantic near-duplicate detection. Embedding-based similarity could be calculated between newly sampled examples and Sprint 51 training/evaluation examples. Highly similar examples could then be flagged for manual inspection.

Additional improvements could include:

* embedding-based semantic deduplication
* automated Traditional/Simplified Chinese detection
* automated corrupted-row detection
* candidate length and truncation checks
* source/tier distribution statistics
* stronger manifest metadata
* model checkpoint hashing
* automated CSV/JSONL consistency validation
* reviewer agreement analysis after human labels are collected

Future filtering should remain conservative. The objective is to remove invalid or corrupted examples, not to remove difficult examples simply because the model translated them poorly.

---

## 19. Acceptance Criteria

The final implementation satisfies all five Sprint 52 Task A acceptance criteria.

| Acceptance Criterion                      | Result      |
| ----------------------------------------- | ----------- |
| Additional examples independently sourced | ✅ Completed |
| Range of quality/source types             | ✅ Completed |
| Source traceability                       | ✅ Completed |
| Target number defined upfront             | ✅ Completed |
| Clear scoring instructions and rubric     | ✅ Completed |

Final result:

```text
Acceptance Criteria: 5 / 5 Completed
Review Examples:     120 / 120
Clean:               40
Domain:              40
Colloquial:          40
Direction:           EN → CMN
```

---

## 20. Conclusion

This notebook successfully implements Sprint 52 Task A and produces a complete Mandarin human-review package. The final dataset contains 120 independently sourced EN→CMN examples distributed equally across clean, domain, and colloquial source categories.

The pipeline provides exact normalized-text overlap protection against Sprint 51 training and evaluation data, deterministic candidate generation using the Sprint 51 fine-tuned model, complete source provenance, reproducible sampling, structured output formats, and a detailed six-dimensional human-review rubric.

The resulting package is ready for human evaluation and can subsequently provide fresh labels for Mandarin translation judge validation. The principal methodological qualification is that the current independence check detects **exact normalized-text overlap rather than semantic near-duplicates**. This limitation is explicitly documented and provides a clear direction for improving the dataset-construction pipeline in a future iteration.
