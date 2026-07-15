"""
Judge model for evaluating translations using DSPy 3.2.1.

Classes:
    TranslationJudge: DSPy Signature for translation evaluation
    JudgeModel: Wrapper around DSPy judge
"""

import dspy
from typing import Dict, Optional
import os
import re

class TranslationJudge(dspy.Signature):
    """Evaluate English-to-Cantonese/Mandarin translations.
    
    Assess quality on:
    - Accuracy: Does the translation preserve meaning?
    - Fluency: Is the target language natural?
    - Fidelity: Are idioms/nuances captured?
    
    Provide a score (1-10) and brief written feedback.
    Keep reasoning concise (2-3 sentences) before giving your score and feedback.
    """
    
    english_source: str = dspy.InputField(desc="Original English text")
    cantonese_translation: str = dspy.InputField(desc="Cantonese translation (or empty if not evaluated)")
    mandarin_translation: str = dspy.InputField(desc="Mandarin translation (or empty if not evaluated)")
    
    score: str = dspy.OutputField(desc="Quality score as a number (1-10)")
    feedback: str = dspy.OutputField(desc="Detailed written feedback on translation quality")


class JudgeModel:
    """Wrapper for DSPy-based translation judge (DSPy 3.2.1).
    
    Supports multiple LLM providers:
    - Gemini (gemini-2.5-flash)
    - Groq (groq-llama-3.3-70b)
    - OpenAI (GPT-4o, GPT-4, GPT-3.5-turbo)
    - Anthropic (Claude-3-opus, Claude-3-sonnet)
    - Together (Llama-2-70b-chat, others)
    
    Example:
        >>> judge = JudgeModel(model_choice="gpt-4o")
        >>> result = judge.evaluate(
        ...     english="Hello world",
        ...     cantonese="你好世界"
        ... )
        >>> print(f"Score: {result['score']}/10")
    """
    
    def __init__(self, model_choice: str = "gpt-4o", max_tokens: int = 1500):
        """
        Initialize judge model.
        
        Args:
            model_choice: "gemini-2.5", "groq-llama-3.3", "gpt-4o", "gpt-4", 
            "claude-3-opus", "claude-3-sonnet", or "llama-2-70b-chat"
            max_tokens: Maximum tokens for judge response
            
        Raises:
            ValueError: If model_choice is not supported
        """
        self.model_choice = model_choice
        self.max_tokens = max_tokens
        self.judge = dspy.ChainOfThought(TranslationJudge)
        
        # Configure LM based on choice
        self._configure_lm()
    
    def _configure_lm(self) -> None:
        """Configure language model based on model_choice (DSPy 3.2.1 API)."""
        
        try:
            if self.model_choice == "gpt-4o":
                lm = dspy.LM(model="openai/gpt-4o", max_tokens=self.max_tokens)
            elif self.model_choice == "gpt-4":
                lm = dspy.LM(model="openai/gpt-4", max_tokens=self.max_tokens)
            elif self.model_choice == "gemini-2.5":
                lm = dspy.LM(model="gemini/gemini-2.5-flash", max_tokens=self.max_tokens)
            elif self.model_choice == "groq-llama-3.3":
                lm = dspy.LM(model="groq/llama-3.3-70b-versatile", max_tokens=self.max_tokens)
            elif self.model_choice == "claude-3-opus":
                lm = dspy.LM(model="anthropic/claude-3-opus-20240229", max_tokens=self.max_tokens)
            elif self.model_choice == "claude-3-sonnet":
                lm = dspy.LM(model="anthropic/claude-3-sonnet-20240229", max_tokens=self.max_tokens)
            elif self.model_choice == "llama-2-70b-chat":
                lm = dspy.LM(model="together_ai/meta-llama/Llama-2-70b-chat-hf", max_tokens=self.max_tokens)
            else:
                raise ValueError(
                    f"Unknown model: {self.model_choice}. "
                    f"Choose from: gpt-4o, gpt-4, claude-3-opus, claude-3-sonnet, llama-2-70b-chat"
                )
            
            dspy.configure(lm=lm)
            
        except Exception as e:
            raise RuntimeError(f"Failed to configure LM: {e}")
    
    def evaluate(
        self,
        english: str,
        cantonese: str = "",
        mandarin: str = ""
    ) -> Dict:
        """
        Evaluate a translation and return score + feedback.
        
        Args:
            english: Source English text
            cantonese: Cantonese translation (optional)
            mandarin: Mandarin translation (optional)
        
        Returns:
            {
                "score": int (1-10) or None,
                "feedback": str,
                "success": bool,
                "error": str (if failed)
            }
        """
        try:
            result = self.judge(
                english_source=english,
                cantonese_translation=cantonese,
                mandarin_translation=mandarin
            )
            
            # Parse score from string safely
            score = None
            try:
                score_str = str(result.score).strip()
                for word in score_str.split():
                    try:
                        num = int(word)
                        if 1 <= num <= 10:
                            score = num
                            break
                    except ValueError:
                        continue
                if score is None:
                    score = int(float(score_str.split()[0]))
                    if not (1 <= score <= 10):
                        score = None
            except (ValueError, TypeError, IndexError):
                score = None

            # With this:
            score = None
            raw_score = str(result.score)
            print(raw_score)
            match = re.search(r'(\d+(?:\.\d+)?)', raw_score)
            if match:
                num = float(match.group(1))
                if 1 <= num <= 10:
                    score = int(round(num))

            # score = None
            # try:
            #     score_str = str(result.score).strip()
                
            #     # Try to extract first number from the score string
            #     for word in score_str.split():
            #         try:
            #             num = int(word)
            #             if 1 <= num <= 10:
            #                 score = num
            #                 break
            #         except ValueError:
            #             continue
                
            #     # Fallback: try direct conversion
            #     if score is None:
            #         score = int(float(score_str.split()[0]))
            #         if not (1 <= score <= 10):
            #             score = None
                        
            # except (ValueError, TypeError, IndexError) as parse_error:
            #     score = None
            
            feedback = result.feedback if hasattr(result, 'feedback') else str(result)
            
            return {
                "score": score,
                "feedback": feedback,
                "success": score is not None,
                "error": None if score is not None else f"Failed to parse score: {result.score}"
            }
        
        except Exception as e:
            return {
                "score": None,
                "feedback": None,
                "success": False,
                "error": str(e)
            }
    
    def batch_evaluate(
        self,
        examples: list,
        language: str = "both"
    ) -> list:
        """
        Evaluate multiple translation examples.
        
        Args:
            examples: List of dicts with keys: english, [cantonese], [mandarin]
            language: "cantonese", "mandarin", or "both"
        
        Returns:
            List of evaluation results
        """
        results = []
        
        for i, example in enumerate(examples):
            english = example.get("english", "")
            cantonese = example.get("cantonese", "") if language in ["cantonese", "both"] else ""
            mandarin = example.get("mandarin", "") if language in ["mandarin", "both"] else ""
            
            result = self.evaluate(english, cantonese, mandarin)
            result["example_id"] = i
            results.append(result)
        
        return results