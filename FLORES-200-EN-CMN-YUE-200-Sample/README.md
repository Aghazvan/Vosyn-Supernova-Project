# FLORES-200 Evaluation Corpora (English → Mandarin & English → Cantonese)

## Overview

This repository contains two small parallel corpora extracted from the **FLORES-200** benchmark for evaluating machine translation models.

The datasets are intended **only for evaluation and benchmarking** of English-to-Chinese translation models Each corpus contains **200 parallel sentence pairs** and is designed as a lightweight evaluation set.

## Included Datasets

| Dataset                 | Source Language | Target Language               | Language Code | Sentence Pairs |
| ----------------------- | --------------- | ----------------------------- | ------------- | -------------: |
| `flores200_en_cmn.csv`  | English         | Mandarin Chinese (Simplified) | EN → CMN      |            200 |
| `flores200_en_yue.csv`  | English         | Cantonese (Traditional)       | EN → YUE      |            200 |

## File Format

Both datasets are stored as CSV files with the following columns:

| Column | Description                                  |
| ------ | -------------------------------------------- |
| `src`  | Source sentence in English                   |
| `tgt`  | Reference translation in the target language |

### Example (English → Cantonese)

```csv
src,tgt
"Following the process, HJR-3 will be reviewed again by the next elected legislature in either 2015 or 2016 to remain in process.","按照程序，HJR-3 將會喺 2015 年或 2016 年由下一屆民選立法機關再次審議，以保持程序繼續進行。"
"Vautier's achievements outside of directing include a hunger strike in 1973 against what he viewed as political censorship.","除咗導演工作之外，禾迪亞其他成就包括喺 1973 年進行絕食，以抗議佢認為係政治審查嘅行為。"
```

### Example (English → Mandarin)

```csv
src,tgt
"Following the process, HJR-3 will be reviewed again by the next elected legislature in either 2015 or 2016 to remain in process.","按照这一程序，HJR-3将由下一届选出的立法机构在2015年或2016年再次审议，以继续推进该程序。"
"Vautier's achievements outside of directing include a hunger strike in 1973 against what he viewed as political censorship.","除了导演工作外，沃蒂埃的成就还包括1973年为抗议他所认为的政治审查而进行的绝食行动。"
```

## Intended Use

These corpora are designed for:

* Benchmarking machine translation models
* Zero-shot translation evaluation
* Comparing translation quality across different models
* Computing automatic evaluation metrics such as:

  * COMET
  * BLEU
  * chrF
  * TER
  * METEOR
  * BERTScore

Typical evaluation workflow:

1. Read the English (`src`) sentences.
2. Generate translations using a translation model.
3. Compare the generated translations against the reference (`tgt`) translations.
4. Compute evaluation metrics.

## Dataset Characteristics

* Parallel sentence pairs
* High-quality human translations
* News and general-domain content
* Diverse sentence lengths and topics
* Standard benchmark for multilingual machine translation

## Repository Structure

```text
.
├── flores200_en_zh.csv      # English → Mandarin (200 sentence pairs)
├── flores200_en_yue.csv     # English → Cantonese (200 sentence pairs)
└── README.md
```

## Loading the Dataset

```python
import pandas as pd

# English → Mandarin
df_cmn = pd.read_csv("flores200_en_zh.csv")

# English → Cantonese
df_yue = pd.read_csv("flores200_en_yue.csv")

print(df_cmn.head())
print(df_yue.head())
```

## Notes

* These datasets are intended **only for evaluation**.
* Because each corpus contains only **200 sentence pairs**, they should **not** be used for model training or fine-tuning.
* For reproducible benchmarking, evaluate on the complete dataset without modifying the reference translations.

## Source

The sentence pairs originate from the **FLORES-200** multilingual evaluation benchmark developed for machine translation research.

## License

Please follow the licensing terms of the original FLORES-200 dataset when redistributing or using these files.
