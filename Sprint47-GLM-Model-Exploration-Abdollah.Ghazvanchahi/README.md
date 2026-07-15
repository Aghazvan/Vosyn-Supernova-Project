# GLM-4-9B FLORES-200 Zero-Shot Translation Evaluation

This notebook evaluates the **unsloth/GLM-4-9B-0414-unsloth-bnb-4bit** model on the FLORES-200 dataset for four translation directions:

- EN ↔ CMN (Mandarin)
- EN ↔ YUE (Cantonese)

It performs zero-shot translation, extracts clean translations, and computes **COMET**, **BLEU**, **chrF**, and **ROUGE** scores.

---

## 📋 Table of Contents

- [Requirements](#requirements)
- [Notebook Structure](#notebook-structure)
- [How to Use](#how-to-use)
- [Supported Translation Directions](#supported-translation-directions)
- [Final Evaluation Results](#final-evaluation-results)
- [Output Files](#output-files)
- [Important Notes](#important-notes)
- [Troubleshooting](#troubleshooting)

---

## Requirements

- Kaggle / Colab / local GPU environment with CUDA
- Recommended: TPU/GPU runtime (at least 16 GB VRAM recommended)
- Packages are installed in **Cell 1**

---

## Notebook Structure

| Cell | Purpose |
|------|---------|
| **Cell 1** | High-stability installer (installs all required packages) |
| **Cell 2** | Imports and environment verification |
| **Cell 3** | Full evaluation pipeline (model loading, generation, extraction, metric calculation) |
| **Cell 4** | Metric computation (COMET, BLEU, chrF, ROUGE) and final reporting |

---

## How to Use

1. **Open the notebook** in Kaggle or Colab.
2. **Run Cell 1** → Restart the runtime when prompted (`Runtime → Restart session`).
3. **Run Cell 2** to verify the environment.
4. **Run Cell 3** (main evaluation):
   - Uncomment **only one** of the four dataset lines depending on the direction you want to evaluate:
     ```python
     test_dataset = load_dataset("csv", data_files={"test": "/input/datasets/flores_200_cmn_en.csv"})
     # test_dataset = load_dataset("csv", data_files={"test": "/input/datasets/flores_200_en_cmn.csv"})
     # test_dataset = load_dataset("csv", data_files={"test": "/input/datasets/flores_200_yue_en.csv"})
     # test_dataset = load_dataset("csv", data_files={"test": "/input/datasets/flores_200_en_yue.csv"})
     ```
   - Change the prompt function call in the generation loop:
     ```python
     prompt = make_prompt_cmn_en(src)   # ← change this line for each direction
     ```
5. **Run Cell 4** to compute COMET and other metrics and save the final report.
6. Download the generated CSV files from the output directory.

---

## Supported Translation Directions & Prompt Functions

| Direction     | Prompt Function       | Dataset File                  |
|---------------|-----------------------|-------------------------------|
| CMN → EN      | `make_prompt_cmn_en`  | `flores_200_cmn_en.csv`       |
| EN → CMN      | `make_prompt_en_cmn`  | `flores_200_en_cmn.csv`       |
| YUE → EN      | `make_prompt_yue_en`  | `flores_200_yue_en.csv`       |
| EN → YUE      | `make_prompt_en_yue`  | `flores_200_en_yue.csv`       |

---

## Final Evaluation Results

**GLM-4-9B (unsloth/GLM-4-9B-0414-unsloth-bnb-4bit)** zero-shot results on FLORES-200:

| Direction   | COMET   | BLEU  | chrF  | ROUGE-1 | ROUGE-2 | ROUGE-L |
|-------------|---------|-------|-------|---------|---------|---------|
| **EN→CMN** | 0.8739  | 39.91 | 34.41 | 0.2585  | 0.0888  | 0.2557  |
| **CMN→EN** | 0.8697  | 27.67 | 58.41 | 0.6539  | 0.3797  | 0.5749  |
| **YUE→EN** | 0.8553  | 26.10 | 56.46 | 0.6314  | 0.3605  | 0.5517  |
| **EN→YUE** | 0.8431  | 27.35 | 24.87 | 0.1894  | 0.0579  | 0.1857  |

---

## Output Files

- `GLM4_9B_<direction>_results.csv` → Source, reference, and hypothesis translations
- `GLM4_9B_<direction>_metrics.csv` → Final scores (COMET, BLEU, chrF, ROUGE-1/2/L)
- `GLM4_9B_<direction>_metrics_report.csv` → Copy saved to `/kaggle/working/`

---

## Important Notes

- **Extraction function** (`extract_translation`) removes `<think>` blocks and GLM special tokens, keeping only the clean translation.
- The model is loaded in **4-bit** quantization (`bnb-4bit`) to save memory.
- Use **one dataset + one prompt function** per run.
- For best results, evaluate one direction at a time.
- COMET model (`Unbabel/wmt22-comet-da`) is downloaded automatically in Cell 4.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Runtime restart required after Cell 1 | Restart session, then continue from Cell 2 |
| Out of memory | Reduce `max_new_tokens` or batch size in COMET prediction |
| No Chinese characters in output | Check that you are using the correct prompt function |
| Slow generation | Ensure GPU is selected and `device_map="cuda:0"` is set |

---

## License

This notebook is provided for research and evaluation purposes only.

---

*Last updated: July 2026*