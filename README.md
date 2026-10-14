# Supernova: Multilingual Translation and Evaluation Pipeline

## Overview

**Supernova** is an end-to-end framework developed at **Vosyn** for multilingual translation, model fine-tuning, and automated evaluation.

The project uses open-weight language models to translate text and subtitles while preserving meaning, tone, formatting, and regional language differences. It also provides tools for preparing training data, improving translation quality, evaluating model performance, and deploying models using Google Cloud Platform (GCP).

Supernova combines data processing, model training, automated evaluation, prompt optimization, and cloud deployment into a unified workflow.

## Core Objectives

- **Model Integration:** Integrate and evaluate open-weight language models for multilingual translation and localization.
- **Timestamp and Metadata Preservation:** Preserve timestamps, subtitle structure, formatting, and other metadata during translation.
- **Scalable Cloud Infrastructure:** Use GCP services, including Google Cloud Storage (GCS), Cloud Run, Vertex AI, and GKE, to support scalable model deployment and processing.
- **Efficient Fine-Tuning:** Apply LoRA, QLoRA, and other parameter-efficient fine-tuning methods to improve translation quality for specific domains and dialects.
- **Automated Evaluation:** Use LLM-as-a-Judge to evaluate translation quality and identify common errors.
- **Prompt Optimization:** Use DSPy and GEPA to improve translator and evaluator prompts through systematic experimentation.

## Architecture and Workflow

The Supernova pipeline consists of two main stages: translation and evaluation.

```text
                                  ┌─────────────────────────────────────────┐
                                  │           Input Source Metadata         │
                                  └────────────────────┬────────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Google Cloud Platform (GCS Upload Event Trigger)                                                        │
│                                                                                                         │
│   ┌─────────────────────────┐       ┌──────────────────────────┐       ┌────────────────────────────┐   │
│   │   Cloud Run Function    │ ───►  │    Data Preprocessing    │ ───►  │  Model Inference Engine    │   │
│   │   (Inference Trigger)   │       │ (LaBSE Filter & Hashing) │       │ (Foundation & Fine-Tuned)  │   │
│   └─────────────────────────┘       └──────────────────────────┘       └─────────────┬──────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────┼──────────────────┘
                                                                                       │
                                                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Continuous Evaluation & Prompt Optimization Loop                                                        │
│                                                                                                         │
│   ┌─────────────────────────┐       ┌──────────────────────────┐       ┌────────────────────────────┐   │
│   │   LLM-as-a-Judge        │ ───►  │  6-Dim MQM Scoring       │ ───►  │  DSPy / GEPA Prompt Loop   │   │
│   │  (Robust Score Agg.)    │       │  (Compliance Prompting)  │       │  (Automatic Prompt Tuning) │   │
│   └─────────────────────────┘       └──────────────────────────┘       └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘

```

## Core Technical Components

### 1. Data Processing and Dataset Preparation

Supernova uses carefully prepared datasets to train and evaluate translation models.

- **Multiple Dataset Types:** Combines benchmark datasets, domain-specific translation pairs, and conversational text to cover both formal and informal language.
- **Data Filtering:** Uses LaBSE semantic similarity scores to identify unsuitable translation pairs and improve dataset quality.
- **Deduplication:** Uses SHA-256 hashing to identify exact duplicates and reduce the risk of data leakage between training and evaluation datasets.
- **Reproducible Experiments:** Uses dataset manifests, fixed random seeds, and separate data splits to make experiments easier to reproduce and compare.
- **Data Separation:** Maintains separate training, validation, judge calibration, prompt validation, and test sets to support reliable evaluation.

### 2. Model Fine-Tuning and Alignment

Supernova supports efficient model training and experiments with different model architectures.

- **Parameter-Efficient Fine-Tuning:** Uses LoRA and QLoRA, with frameworks such as Unsloth, to reduce the computational resources required for fine-tuning.
- **Preference Optimization:** Supports Direct Preference Optimization (DPO) to align model outputs with preferred translation styles and quality requirements.
- **Model Comparison:** Evaluates different model architectures, including general-purpose LLMs, neural machine translation (NMT) models, and Mixture-of-Experts (MoE) models.
- **Performance Evaluation:** Compares translation quality, inference speed, and resource usage to help identify suitable models for different deployment requirements.

### 3. Translation Evaluation with LLM-as-a-Judge

Supernova uses an LLM-as-a-Judge framework to evaluate translations across multiple quality dimensions.

- **Six Evaluation Dimensions:** Measures semantic accuracy, fluency, tone and register, emotional consistency, cultural appropriateness, and dialect correctness.
- **MQM-Based Scoring:** Uses a Multidimensional Quality Metrics (MQM)-inspired rubric to assess translation errors and their severity.
- **Score Aggregation:** Applies Robust Rank-Weighted Aggregation (RRWA) to combine evaluation results and improve the stability of model comparisons.
- **Failure Detection:** Uses specialized evaluation prompts to identify problems such as untranslated text, source-language leakage, incorrect writing systems, and dialect mismatches.
- **Evaluation Reliability:** Tests whether the judge produces consistent and meaningful scores across repeated runs and different evaluation prompts.

### 4. Automated Prompt Optimization

Supernova uses DSPy and GEPA to systematically improve prompts for translation and evaluation tasks.

- **Prompt Optimization:** Experiments with different prompts to improve translation quality and judge performance.
- **Automated Feedback:** Uses evaluation results to identify weaknesses and guide prompt improvements.
- **Controlled Experiments:** Compares prompt variants using consistent datasets and evaluation metrics.
- **Efficient Execution:** Supports local, quantized model execution on GPUs to reduce computational requirements during experimentation.

### 5. Cloud Infrastructure and Deployment

Supernova uses cloud-based infrastructure to support automated processing, model inference, and deployment.

- **Event-Driven Processing:** Uses Google Cloud Storage upload events to trigger Cloud Run Functions and start processing workflows.
- **Cloud Integration:** Uses GCP services, including GCS, Cloud Run, Vertex AI, and GKE, to support data processing and model deployment.
- **Deployment Benchmarking:** Evaluates inference engines such as vLLM and TensorRT-LLM to compare latency, cost, and GPU utilization.
- **CI/CD Automation:** Uses GitLab CI/CD to automate development and deployment workflows.
- **Scalable Inference:** Evaluates deployment options based on model performance, resource requirements, and production needs.

## Conclusion

Supernova brings together multilingual translation, dataset preparation, efficient model fine-tuning, automated quality evaluation, prompt optimization, and cloud deployment in one framework.

Its goal is to improve translation quality while making model development and evaluation more systematic, reproducible, and scalable.

The project also provides a structured way to identify translation errors, compare models, and use evaluation results to guide future improvements.
