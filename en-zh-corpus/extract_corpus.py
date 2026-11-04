import json
import re
import pandas as pd
from datasets import load_dataset
from langdetect import detect, DetectorFactory

# Force reproducible results from langdetect
DetectorFactory.seed = 42

def safe_extract(item, path_list):
    """
    Extracts text fields safely. Includes structural array fallbacks
    to process conversational blocks dynamically.
    """
    current = item
    for key in path_list:
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list):
            if len(current) > 0 and isinstance(key, int) and key < len(current):
                current = current[key]
            elif len(current) > 0 and isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return ""
        else:
            return ""
    return str(current).strip()

def is_clean_pair(en, zh, skip_lang_detect=False):
    """Linguistic and structural filter suite calibrated for robust processing."""
    if len(en) <= 50:
        return False
    if len(en) >= 250:
        return False

    # Ensure actual Chinese characters exist
    zh_char_pattern = re.compile(r'[\u4e00-\u9fff]')
    if not zh_char_pattern.search(zh):
        return False

    # Filter heavily polluted mixed code entries
    en_words_in_zh = len(re.findall(r'[a-zA-Z]+', zh))
    if en_words_in_zh > 15 or (len(zh) > 0 and en_words_in_zh / len(zh) > 0.45):
        return False

    # Calibrated length bounds ratio 
    ratio = len(en) / (len(zh) * 2.5) if len(zh) > 0 else 0
    if ratio < 0.15 or ratio > 6.0:
        return False
    # ratio = len(en) / len(zh) if len(zh) > 0 else 0
    # if ratio < 0.2 or ratio > 15.0:
    #     return False

    if not skip_lang_detect:
        try:
            if detect(en) != 'en':
                return False
        except Exception:
            return False

    return True

def collect_flat_corpora():
    # 10 Multi-Domain Map with custom types handled seamlessly
    dataset_configs = {
        "Legal & Policy": {
            "path": "Helsinki-NLP/multiun", "name": "en-zh", "split": "train",
            "type": "flat", "keys": (["translation", "en"], ["translation", "zh"]), "skip_ld": False
        },
        "Language Learning": {
            "path": "swaption2009/20k-en-zh-translation-pinyin-hsk", "name": None, "split": "train",
            "type": "custom_swaption", "keys": None, "skip_ld": False
        },
        "Subtitles": {
            "path": "sentence-transformers/parallel-sentences-opensubtitles", "name": "en-zh_cn", "split": "train",
            "type": "flat", "keys": (["english"], ["non_english"]), "skip_ld": False
        },
        "Formal News": {
            "path": "wmt/wmt19", "name": "zh-en", "split": "train",
            "type": "flat", "keys": (["translation", "en"], ["translation", "zh"]), "skip_ld": False
        },
        "General Web": {
            "path": "sentence-transformers/parallel-sentences-opus-100", "name": "en-zh", "split": "train",
            "type": "flat", "keys": (["english"], ["non_english"]), "skip_ld": False
        }
    }

    master_corpus = []
    seen_pairs = set() 
    max_sentences_per_domain = 200  

    for domain, cfg in dataset_configs.items():
        print(f"\n🚀 Streaming domain: [{domain}]...")
        try:
            dataset = load_dataset(cfg["path"], cfg["name"], split=cfg["split"], streaming=True)
            count = 0
            en_txt = None
            # Oversample to hit our clean 2,000 threshold comfortably
            for item in dataset.take(max_sentences_per_domain * 20): 
                if count >= max_sentences_per_domain:
                    break
                
                # Dynamic extraction routing strategy based on schema profile
                if cfg["type"] == "custom_swaption":
                    raw_block = item.get("text", "")
                    if not isinstance(raw_block, str):
                        continue
                    raw_block = raw_block.strip()
                    if raw_block.startswith("english:"):
                        en_txt = raw_block[len("english:"):].strip()
                    elif raw_block.startswith("mandarin:"):
                        zh_txt = raw_block[len("mandarin:"):].strip()

                else:
                    en_path, zh_path = cfg["keys"]
                    en_txt = safe_extract(item, en_path)
                    zh_txt = safe_extract(item, zh_path)
                
                if not en_txt or not zh_txt:
                    continue
                    
                pair_hash = f"{en_txt.lower().strip()}|||{zh_txt.strip()}"
                if pair_hash in seen_pairs:
                    continue 

                if is_clean_pair(en_txt, zh_txt, skip_lang_detect=cfg["skip_ld"]):
                    seen_pairs.add(pair_hash)
                    master_corpus.append({
                        "english": en_txt,
                        "mandarin": zh_txt,
                        "category": domain
                    })
                    count += 1
                    en_txt = None
                    if count % 100 == 0:
                        print(f"   ↳ Progress: {count}/{max_sentences_per_domain} pairs gathered...")

            print(f"✅ Successfully collected exactly {count} clean pairs from {domain}.")
            
        except Exception as e:
            print(f"❌ Skipping {domain} due to a structural error: {e}")

    # Write out data models
    if master_corpus:
        json_file = "ultra_clean_en_zh_corpora.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(master_corpus, f, ensure_ascii=False, indent=4)
        print(f"\n💾 Saved JSON corpus to '{json_file}'")

        csv_file = "en_zh_corpora_1000.csv"
        df = pd.DataFrame(master_corpus)
        df.to_csv(csv_file, index=False, encoding="utf-8-sig") 
        print(f"💾 Saved CSV corpus to '{csv_file}'")
            
        print(f"\n🎉 Finished! Processed {len(master_corpus)} total rows across the domains.")
    else:
        print("\n❌ Error: No text strings matched your data parameters.")

if __name__ == "__main__":
    collect_flat_corpora()

