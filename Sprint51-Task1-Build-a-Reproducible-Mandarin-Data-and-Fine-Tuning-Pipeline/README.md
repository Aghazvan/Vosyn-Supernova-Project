# Sprint 51 – Task 1: Reproducible Mandarin Fine-Tuning Pipeline

## Overview

This notebook implements the **Sprint 51 Task 1** pipeline for preparing reproducible Mandarin translation data, fine-tuning a lightweight language model for **English → Mandarin Chinese (en→zh)** translation, validating the resulting checkpoint, and packaging the artifacts required for downstream evaluation and serving.

The workflow is designed to provide a reproducible training foundation for the Supernova Mandarin translation pipeline. It covers dataset preparation, data validation and hashing, deterministic subsampling, hardware verification, LoRA-based fine-tuning, checkpointing, model export, reload testing, and candidate-manifest generation.

The primary trained candidate uses:

* **Base model:** `unsloth/Llama-3.2-1B-bnb-4bit`
* **Training method:** LoRA on a 4-bit quantized model
* **Language direction:** English → Mandarin Chinese
* **Framework:** Unsloth / Hugging Face Transformers
* **Training seed:** `3407`
* **Training examples:** 40,000
* **Validation examples:** 1,500
* **Epochs:** 2
* **Maximum sequence length:** 1,024 tokens

---

## Task Objectives

The notebook addresses the following objectives:

1. Prepare and validate the Mandarin translation dataset.
2. Preserve clear separation between training, judge-calibration, prompt-validation, and sealed-final-test data.
3. Create deterministic dataset subsets for reproducible experiments.
4. Record dataset versions and SHA-256 hashes.
5. Verify available GPU resources before training.
6. Fine-tune a configurable language model using LoRA.
7. Use a controlled English-to-Mandarin translation prompt.
8. Save intermediate checkpoints and final model artifacts.
9. Reload the trained checkpoint independently.
10. Perform a translation smoke test.
11. Generate a candidate manifest containing training, dataset, hardware, and artifact metadata.

---

## Pipeline

The notebook follows this high-level workflow:

```text
Dataset Preparation
        │
        ▼
Data Validation & Filtering
        │
        ▼
Deduplication
        │
        ▼
Dataset Versioning & SHA-256 Hashing
        │
        ▼
Train / Calibration / Validation / Test Separation
        │
        ▼
Deterministic Training Subsampling
        │
        ▼
GPU / Environment Smoke Test
        │
        ▼
4-bit Base Model Loading
        │
        ▼
LoRA Configuration
        │
        ▼
Prompt Formatting & Tokenization
        │
        ▼
SFT Training
        │
        ▼
Checkpointing & Evaluation
        │
        ▼
Final Adapter / Merged Model Export
        │
        ▼
Independent Reload
        │
        ▼
Mandarin Translation Smoke Test
        │
        ▼
Candidate Manifest
```

---

## Dataset Organization

The pipeline maintains separate datasets for different experimental purposes.

| Dataset                   | Records |
| ------------------------- | ------: |
| Fine-tuning dataset       |  90,000 |
| Judge calibration dataset |   3,000 |
| Prompt validation dataset |   3,500 |
| Sealed final test dataset |   3,500 |

The fine-tuning dataset contains directional translation records covering both `en→zh` and `zh→en`. The training configuration for this candidate is explicitly intended for **English → Mandarin**.

### Dataset Hashes

The notebook records SHA-256 hashes for the packaged datasets:

| Dataset           | SHA-256                                                            |
| ----------------- | ------------------------------------------------------------------ |
| Fine-tuning       | `cbf62f0452d0f695c6b226605e3253e64fb1dee7d0777ce0f1805f1f8a1028fe` |
| Judge calibration | `6b59981b0461fab1373c89e8817e6d19783bc75dc63be9b5627eaf1881a895c1` |
| Prompt validation | `1b27c3844e68452d180ccf36912f3d3c8c571f3922f8410c05829842130ffd22` |
| Sealed final test | `1cfe0efed56f5f545ed1c73feb8e8fccda55e639ac81d66b6e2907fd010c5b02` |

These hashes allow the exact dataset artifacts used by a candidate run to be verified later.

---

## Reproducible Subsampling

To make experiments deterministic, the notebook uses the configured training seed when shuffling and selecting subsets.

The demonstrated run uses:

* **Training subset:** 40,000 examples
* **Validation subset:** 1,500 examples
* **Random seed:** `3407`

This allows the same dataset version and configuration to produce the same selected subsets across repeated runs, assuming the surrounding software and hardware environment is equivalent.

---

## Translation Prompt

The training examples are formatted using a controlled translation instruction.

The system prompt defines the model as an expert translator for:

> English → Mandarin Chinese (普通話)

The prompt specifically requires:

* Simplified Chinese output.
* Mainland China Mandarin vocabulary and grammar.
* No Cantonese particles or Cantonese-specific vocabulary.
* No Pinyin.
* No explanations or additional commentary.
* No repetition of the source sentence.
* Proper nouns may remain in English when appropriate.

The user instruction follows the form:

```text
Translate to Mandarin:
{source_text}
```

The resulting conversation is formatted using the model's ChatML-compatible chat template, with an EOS token appended when required.

---

## Model Configuration

The candidate model is:

```text
unsloth/Llama-3.2-1B-bnb-4bit
```

The model is loaded in 4-bit precision and adapted using LoRA.

### LoRA Configuration

The adapter targets the following modules:

```text
q_proj
k_proj
v_proj
o_proj
gate_proj
up_proj
down_proj
```

The configuration also supports:

* Configurable LoRA rank.
* LoRA alpha.
* LoRA dropout.
* Gradient checkpointing.
* Reproducible random state.

Only a small fraction of the total model parameters is trained.

### Trainable Parameters

The recorded training run reports:

```text
Trainable parameters: 22,544,384
Total parameters:     1,258,358,784
Trainable percentage:  1.79%
```

This substantially reduces the number of parameters that must be updated compared with full-model fine-tuning.

---

## Training Configuration

The demonstrated candidate uses:

| Parameter               |                           Value |
| ----------------------- | ------------------------------: |
| Base model              | `unsloth/Llama-3.2-1B-bnb-4bit` |
| Method                  |                    LoRA / 4-bit |
| Direction               |                           en→zh |
| Seed                    |                            3407 |
| Learning rate           |                          `5e-5` |
| Epochs                  |                               2 |
| Training examples       |                          40,000 |
| Validation examples     |                           1,500 |
| Per-device batch size   |                               4 |
| Gradient accumulation   |                               4 |
| Effective batch size    |                              16 |
| Maximum sequence length |                           1,024 |
| Optimizer               |                    `adamw_8bit` |
| Scheduler               |          Configured in notebook |
| Weight decay            |          Configured in notebook |
| Warmup                  |          Configured in notebook |
| Evaluation frequency    |                 Every 500 steps |
| Checkpoint frequency    |                 Every 500 steps |
| Checkpoint limit        |          Configured in notebook |
| Packing                 |                        Disabled |

The completed run reached:

```text
Global steps: 5,000
Epoch:        2
Training loss: 0.3846675
Runtime:      ~2h 47m 50s
```

---

## Training Progress

The recorded training and validation losses were:

|  Step | Training Loss | Validation Loss |
| ----: | ------------: | --------------: |
|   500 |        0.3877 |          0.3739 |
| 1,000 |        0.3912 |          0.3641 |
| 1,500 |        0.3735 |          0.3595 |
| 2,000 |        0.3760 |          0.3561 |
| 2,500 |        0.3772 |          0.3532 |
| 3,000 |        0.3359 |          0.3531 |
| 3,500 |        0.3510 |          0.3521 |
| 4,000 |        0.3401 |          0.3513 |
| 4,500 |        0.3190 |          0.3508 |
| 5,000 |        0.3221 |          0.3507 |

The validation loss decreased from approximately **0.374 at step 500 to 0.351 at step 5,000**, indicating stable optimization during the recorded run.

---

## Hardware

The notebook includes a hardware/environment probe before training.

The recorded environment contains:

```text
GPU count:       2
GPU:             Tesla T4
GPU memory:      ~14.56 GB each
CUDA:            Available
```

The actual training run was reported by Unsloth as using one GPU.

The notebook dynamically checks the available precision configuration and reports the selected training environment.

---

## Checkpointing

The training process periodically saves checkpoints.

The recorded run produced checkpoints at:

```text
checkpoint-4000
checkpoint-4500
checkpoint-5000
```

Each checkpoint contains the necessary training state and model/adapter information, including items such as:

* Adapter weights
* Adapter configuration
* Optimizer state
* Scheduler state
* Trainer state
* RNG state
* Training arguments
* Tokenizer
* Chat template

This structure supports later checkpoint inspection and continuation of training.

---

## Model Export

The notebook produces both adapter-based and merged model artifacts.

### Final Adapter Model

```text
/kaggle/working/task1_en2zh_outputs/final
```

This directory contains the LoRA adapter and associated configuration/tokenizer files.

### Merged 16-bit Model

```text
/kaggle/working/task1_en2zh_outputs/final_merged_16bit
```

The merged directory contains the exported model weights and tokenizer/configuration information required for downstream use.

---

## Model Reload and Smoke Test

After training, the notebook reloads the final checkpoint rather than relying only on the in-memory training model.

The chat template is verified after reload, and an inference test is performed using:

```text
The weather is nice today.
```

The resulting Mandarin translation was:

```text
今天天气很好。
```

This confirms that:

1. The trained artifact can be reloaded.
2. The tokenizer and chat template are available.
3. The model can perform inference after export.
4. The candidate produces Mandarin output in the expected format.

---

## Candidate Manifest

The notebook creates a machine-readable candidate manifest:

```text
/kaggle/working/task1_en2zh_outputs/manifests/candidate_manifest.json
```

The manifest records important metadata including:

* Run name
* Timestamp
* Base model
* Training method
* Seed
* Learning rate
* Number of epochs
* Batch size
* Gradient accumulation
* Maximum sequence length
* Language direction
* Artifact locations
* Dataset version
* Dataset directions
* Dataset file hashes
* Hardware information
* Smoke-test status
* Smoke-test generation

The recorded run name is:

```text
sprint51_task1_unsloth_llama32_1b_en2zh_full
```

---

## Output Structure

The expected output structure is approximately:

```text
task1_en2zh_outputs/
│
├── final/
│   ├── adapter_model.safetensors
│   ├── adapter_config.json
│   ├── training_args.bin
│   ├── tokenizer files
│   └── chat template
│
├── final_merged_16bit/
│   ├── model.safetensors
│   ├── config.json
│   ├── tokenizer files
│   └── chat template
│
├── checkpoints/
│   ├── checkpoint-4000/
│   ├── checkpoint-4500/
│   └── checkpoint-5000/
│
└── manifests/
    └── candidate_manifest.json
```

---

## Reproducibility

The notebook is designed to make the candidate run reproducible through:

* Fixed random seed.
* Deterministic dataset subsampling.
* Explicit training configuration.
* Versioned dataset package.
* SHA-256 dataset hashes.
* Recorded model configuration.
* Recorded hardware information.
* Saved checkpoints.
* Saved tokenizer and chat template.
* Candidate manifest.
* Post-training model reload test.

A future run can therefore compare its configuration and dataset hashes against the candidate manifest before treating it as an equivalent experiment.

---

## Important Implementation Notes

### 1. Translation Direction

The packaged fine-tuning dataset contains both `en→zh` and `zh→en` records, while this candidate's prompt and training objective are English → Mandarin.

For production-quality reproducibility, the training data selection should explicitly filter for:

```text
direction == en->zh
```

before constructing the 40,000-example training subset. This prevents opposite-direction examples from being presented under the English-to-Mandarin training prompt.

### 2. Completion-Only Data Collator

The notebook defines a `DataCollatorForCompletionOnlyLM` using the assistant response template, but the demonstrated `SFTTrainer` construction does not pass this collator to the trainer.

Therefore, completion-only masking should **not be assumed to be active** in the recorded run.

If completion-only loss masking is required, the trainer configuration should explicitly pass the intended data collator and verify the resulting labels.

### 3. Validation Dataset Usage

The notebook uses the prompt-validation dataset as the evaluation dataset during SFT. Although the datasets remain physically separated, using prompt-validation data for checkpoint evaluation/model selection means that it is not completely untouched by the training workflow.

A stronger experimental design is to create a dedicated validation subset from the fine-tuning dataset and reserve the prompt-validation dataset for downstream prompt evaluation.

### 4. Resume Testing

Checkpoint artifacts were successfully produced, but the supplied run does not demonstrate a complete interrupted-training/resume experiment.

A future reproducibility test should:

1. Start training.
2. Stop at an intermediate checkpoint.
3. Restart from that checkpoint.
4. Verify that training resumes correctly.
5. Compare the resulting training state and metrics.

### 5. Model Artifact Hashing

Dataset SHA-256 hashes are included in the manifest. Model and adapter artifact hashes should also be recorded for stronger end-to-end artifact provenance.

---

## Installation / Environment

The notebook is intended to run in a CUDA-enabled environment with the required ML dependencies installed.

The training environment uses components including:

```text
Python
PyTorch
Transformers
Datasets
Unsloth
PEFT / LoRA
bitsandbytes
Accelerate
```

The exact package versions should be retained with the notebook or environment configuration when reproducing the experiment.

---

## Running the Notebook

The notebook should be executed from top to bottom.

### Step 1 – Configure the Experiment

Set:

* Base model
* Dataset paths
* Language direction
* Seed
* Training hyperparameters
* Output directory

### Step 2 – Prepare and Validate Data

Run the dataset preparation and validation cells.

Verify:

* Expected record counts.
* Translation directions.
* Duplicate handling.
* Required fields.
* Dataset hashes.

### Step 3 – Run Hardware Probe

Execute the environment check and confirm that CUDA and the expected GPU resources are available.

### Step 4 – Select Training Data

Create the deterministic training and validation subsets using the configured seed.

### Step 5 – Load the Model

Load the selected 4-bit base model and configure LoRA.

### Step 6 – Format and Tokenize

Apply the Mandarin translation prompt and model chat template, then tokenize with a maximum sequence length of 1,024 tokens.

### Step 7 – Train

Run supervised fine-tuning and monitor:

* Training loss.
* Validation loss.
* Evaluation checkpoints.
* GPU utilization.
* Training runtime.

### Step 8 – Export

Save:

* Final LoRA adapter.
* Merged 16-bit model.
* Tokenizer.
* Chat template.
* Training metadata.

### Step 9 – Reload and Test

Reload the saved model and run the Mandarin smoke test.

### Step 10 – Generate Manifest

Confirm that `candidate_manifest.json` is generated and contains the expected experiment metadata.

---

## Acceptance Criteria Status

| Requirement                                         | Status                     |
| --------------------------------------------------- | -------------------------- |
| Configurable model, dataset, and language direction | **Met**                    |
| Configurable fine-tuning method                     | **Mostly Met**             |
| Hardware/environment smoke test                     | **Met**                    |
| Dataset validation and versioning                   | **Met**                    |
| Dataset SHA-256 hashing                             | **Met**                    |
| Train/validation/test separation                    | **Met structurally**       |
| Fine-tuning with logging                            | **Met**                    |
| Checkpoint generation                               | **Met**                    |
| Final model export                                  | **Met**                    |
| Independent checkpoint reload                       | **Met**                    |
| Mandarin inference smoke test                       | **Met**                    |
| Candidate manifest                                  | **Met**                    |
| Interrupted-run resume demonstration                | **Partially demonstrated** |
| Dedicated direction filtering for en→zh             | **Follow-up required**     |
| Explicit completion-only loss masking               | **Follow-up required**     |
| Model artifact hashes                               | **Follow-up recommended**  |

---

## Result

The notebook successfully demonstrates an end-to-end reproducible foundation for a **Mandarin translation fine-tuning candidate**.

The recorded experiment completed **5,000 training steps over two epochs**, produced intermediate checkpoints and final model artifacts, successfully reloaded the trained model, and generated the expected Mandarin translation in the smoke test.

The resulting candidate is packaged with a machine-readable manifest and dataset hashes, providing a strong basis for subsequent **translation quality evaluation, judge-based evaluation, regression testing, and serving-readiness checks**.

Before using the candidate as a final production checkpoint, the recommended follow-up work is to enforce explicit `en→zh` dataset filtering, verify completion-only loss masking, reserve prompt-validation data for downstream evaluation, test checkpoint resume behavior, and add model artifact hashes to the manifest.
