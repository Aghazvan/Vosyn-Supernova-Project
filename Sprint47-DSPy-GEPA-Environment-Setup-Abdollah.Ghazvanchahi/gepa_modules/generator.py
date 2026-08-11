import os
import requests
from typing import Dict

class GLMTranslator:
    def __init__(self, model_name: str = "glm-4", max_tokens: int = 512, temperature: float = 0.3):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_key = os.getenv("GLM_API_KEY")
        
        if not self.api_key:
            raise ValueError("GLM_API_KEY not found in environment.")

        # Replace with actual GLM-compatible endpoint used by your team/provider
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    def translate(self, english: str, prompt: str) -> Dict:
        system_prompt = prompt or (
            "You are an expert English to Mandarin translator. "
            "Translate accurately, naturally, and fluently into Mandarin Chinese."
        )

        user_prompt = f"Source English:\n{english}\n\nReturn only the Mandarin translation."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            translation = data["choices"][0]["message"]["content"].strip()

            return {
                "success": True,
                "translation": translation,
                "raw_response": data,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "translation": None,
                "raw_response": None,
                "error": str(e)
            }