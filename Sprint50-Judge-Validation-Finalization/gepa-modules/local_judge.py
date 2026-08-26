import re
import json
import torch
from typing import Dict
from unsloth import FastLanguageModel


class LocalJudgeModel:
    """
    Local translation judge using Unsloth-loaded model
    and manual prompt formatting.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-8B",
        max_seq_length: int = 4096,
        max_new_tokens: int = 256,
        temperature: float = 0.0,
        load_in_4bit: bool = True,
    ):
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature

        self.model, self.tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq_length,
            dtype=None,
            load_in_4bit=load_in_4bit,
        )
        FastLanguageModel.for_inference(self.model)

    def build_judge_prompt(self, english: str, mandarin: str) -> str:
        return (
            "<|im_start|>system\n"
            "You are a strict professional translation evaluator.\n"
            "Evaluate the Mandarin translation for accuracy, fluency, and fidelity.\n"
            "Return ONLY valid JSON in this exact format:\n"
            '{"score": <number from 1 to 10>, "feedback": "<short explanation>"}\n'
            "Do not add any extra text.\n"
            "Do not think aloud.\n"
            "<|im_end|>\n"
            "<|im_start|>user\n"
            f"English source:\n{english}\n\n"
            f"Mandarin translation:\n{mandarin}\n"
            "<|im_end|>\n"
            "<|im_start|>assistant\n"
            "/no_think\n"
        )

    def clean_output(self, text: str) -> str:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        text = re.sub(r"</?think>", "", text)
        return text.strip()

    def evaluate(self, english: str, cantonese: str = "", mandarin: str = "") -> Dict:
        try:
            full_prompt = self.build_judge_prompt(english, mandarin)

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
            raw_output = self.tokenizer.decode(
                generated_tokens[0],
                skip_special_tokens=True
            )
            raw_output = self.clean_output(raw_output)

            score = None
            feedback = raw_output

            try:
                parsed = json.loads(raw_output)
                score = float(parsed.get("score"))
                feedback = parsed.get("feedback", raw_output)
            except Exception:
                match = re.search(r'(\d+(?:\.\d+)?)', raw_output)
                if match:
                    num = float(match.group(1))
                    if 1 <= num <= 10:
                        score = num

            return {
                "score": round(score, 2) if score is not None else None,
                "feedback": feedback,
                "success": score is not None,
                "error": None if score is not None else f"Could not parse judge output: {raw_output}",
            }

        except Exception as e:
            return {
                "score": None,
                "feedback": None,
                "success": False,
                "error": str(e),
            }