
import pandas as pd
from datasets import load_dataset

DATASET_NAME = "swaption2009/20k-en-zh-translation-pinyin-hsk"
OUTPUT_FILE = "english_mandarin_2000.csv"
TARGET_PAIRS = 2000


def main():
    print("Loading dataset...")

    dataset = load_dataset(
        DATASET_NAME,
        split="train",
        streaming=True
    )

    print("Dataset columns:", dataset.column_names)

    # Create an empty DataFrame
    df = pd.DataFrame(columns=["english", "mandarin"])

    current_english = None

    # Process one dataset row at a time
    for row in dataset:
        text = row.get("text", "")

        if not isinstance(text, str):
            continue

        text = text.strip()

        if text.startswith("english:"):
            current_english = text[len("english:"):].strip()

        elif text.startswith("mandarin:"):
            mandarin = text[len("mandarin:"):].strip()

            if current_english and mandarin:
                # Add one complete pair to the DataFrame
                df.loc[len(df)] = [current_english, mandarin]

                current_english = None

                if len(df) % 100 == 0:
                    print(f"Collected {len(df)} pairs")

                if len(df) >= TARGET_PAIRS:
                    break

    # Save the DataFrame
    if not df.empty:
        df.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        print(f"\nSuccessfully saved {len(df)} pairs.")
        print(f"File: {OUTPUT_FILE}")
        print(df.head())
    else:
        print("No pairs found. Please inspect the dataset's next rows.")


if __name__ == "__main__":
    main()
