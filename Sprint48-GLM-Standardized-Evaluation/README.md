# FLORES-200 Translation Evaluation with Qwen3-8B and GLM-4-9B

This project provides a standardized evaluation pipeline for **machine translation** on the **FLORES-200 devtest** set using two open-weight large language models:

- **Qwen/Qwen3-8B**
- **zai-org/GLM-4-9B-0414**

The evaluation covers all four translation directions used in the project:

- **English → Mandarin Chinese (EN→CMN)**
- **Mandarin Chinese → English (CMN→EN)**
- **English → Cantonese (EN→YUE)**
- **Cantonese → English (YUE→EN)**

The notebook/script generates translations, saves model outputs, and computes automatic evaluation metrics including:

- **COMET**
- **BLEU**
- **chrF**
- **ROUGE-1 / ROUGE-2 / ROUGE-L**

This repository is intended to support reproducible comparison between Qwen and GLM under the same evaluation framework.

---

## Project Goal

The purpose of this evaluation pipeline is to compare **Qwen3-8B** and **GLM-4-9B** on translation quality for:

- **EN↔CMN**
- **EN↔YUE**

using a fixed prompt template, fixed inference setup, fixed metrics, and fixed dataset split.

This standardized setup supports model comparison for:
- baseline benchmarking,
- candidate selection,
- and downstream fine-tuning readiness assessment.

---

## Models Evaluated

## 1. Qwen baseline
- **Model name:** `Qwen/Qwen3-8B`

## 2. GLM candidate
- **Model name:** `zai-org/GLM-4-9B-0414`

Both models are evaluated under the same translation workflow and metric pipeline.

---

## Runtime and Loading Setup

The project uses **Unsloth** for model loading and optimized inference.

Example loading code:

```python
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = MODEL_NAME,
    max_seq_length = 4096,
    dtype = None,
    load_in_4bit = True,
)
FastLanguageModel.for_inference(model)