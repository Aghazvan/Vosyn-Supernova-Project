import re
import torch
from typing import Dict
from unsloth import FastLanguageModel


class LocalHFTranslator:
    """
    Local English -> Mandarin translator using Unsloth-loaded model
    and manual chat prompt formatting.
    """

    def __init__(
        self,
        model_name: str = "zai-org/GLM-4-9B-0414",
        max_seq_length: int = 4096,
        max_new_tokens: int = 256,
        temperature: float = 0.0,
        load_in_4bit: bool = True,
        source_lang: str = "English",
        target_lang: str = "Mandarin Chinese",
    ):
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.source_lang = source_lang
        self.target_lang = target_lang

        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq_length,
            dtype=None,
            load_in_4bit=load_in_4bit,
        )
        FastLanguageModel.for_inference(self.model)

    def build_translation_prompt(self, src: str, prompt: str = None) -> str:
        if prompt:
            system_text = prompt
        else:
            system_text = (
                "You are a professional machine translation system.\n"
                f"Translate from {self.source_lang} to {self.target_lang}.\n"
                "Rules:\n"
                "1. Output ONLY the translation.\n"
                "2. Do NOT explain.\n"
                "3. Do NOT think aloud.\n"
                "4. Do NOT add notes or comments.\n"
                "5. Preserve the original meaning, tone, and style.\n"
                "6. Use natural, fluent target-language text."
            )

        return (
            "<|im_start|>system\n"
            f"{system_text}\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"{src}\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
            "/no_think\n"
        )

    def clean_output(self, text: str) -> str:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"</?think>", "", text)
        text = "\n".join(
            dict.fromkeys(
                line for line in (l.strip() for l in text.split("\n")) if line
            )
        )
        return text.strip()

    def translate(self, english: str, prompt: str = None) -> Dict:
        try:
            full_prompt = self.build_translation_prompt(english, prompt=prompt)

            inputs = self.tokenizer(
                full_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_seq_length,
            ).to(self.model.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.max_new_tokens,
                    do_sample=self.temperature > 0,
                    temperature=self.temperature if self.temperature > 0 else None,
                    renormalize_logits=True,
                    use_cache=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )

            generated_tokens = outputs[:, inputs.input_ids.shape[1]:]
            translation = self.tokenizer.decode(
                generated_tokens[0],
                skip_special_tokens=True
            )
            cleaned_translation = self.clean_output(translation)

            return {
                "success": True,
                "translation": cleaned_translation,
                "raw_translation": translation,
                "prompt_used": full_prompt,
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "translation": None,
                "raw_translation": None,
                "prompt_used": None,
                "error": str(e),
            }