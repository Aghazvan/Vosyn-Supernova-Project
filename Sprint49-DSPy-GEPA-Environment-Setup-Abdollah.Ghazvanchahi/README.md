# Sprint 49: DSPy & GEPA Live Local Optimization

**Live English → Mandarin Translation Prompt Optimization using Local Models on Kaggle**

This sprint proves that the full **DSPy + GEPA optimization loop** can run **at scale without any paid API credits** by using local open-weight models on Kaggle.

---

## Objective

Run a **live, end-to-end optimization loop** for English → Mandarin translation using:

- Local GLM generation (`zai-org/GLM-4-9B-0414`)
- Local LLM judging (`Qwen/Qwen3-4B-Instruct-2507`)
- Multi-run stable scoring
- GEPA prompt optimization
- FLORES-200 parallel data

**Goal:** Prove the optimization pipeline works live at meaningful scale while the team is blocked on paid API credits.

---

## Key Results (50 FLORES Examples)

| Metric              | Value     |
|---------------------|-----------|
| Baseline Score      | **8.9 / 10** |
| Optimized Score     | **9.02 / 10** |
| Improvement         | **+0.12** |
| Examples Used       | 50        |
| GEPA Iterations     | 2         |
| Variants Tested     | 8         |

**Best Prompt** was found in the first iteration and maintained in the second.

---

## Environment

- **Platform:** Kaggle Notebook (Tesla T4 GPU)
- **Inference Framework:** Unsloth + Transformers (4-bit quantized)
- **Generator:** `zai-org/GLM-4-9B-0414`
- **Judge:** `Qwen/Qwen3-4B-Instruct-2507`
- **Dataset:** FLORES-200 English–Mandarin (`flores_200_en_cmn_updated.csv`)