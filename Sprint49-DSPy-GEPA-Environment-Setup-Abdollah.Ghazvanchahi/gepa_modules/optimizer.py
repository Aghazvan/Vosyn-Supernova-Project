"""
GEPA optimizer for prompt adaptation.

Classes:
    GEPAOptimizer: Gradient-Estimation-based Prompt Adaptation
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class GEPAOptimizer:
    """GEPA optimizer with live generation + judge scoring."""

    def __init__(self, multi_judge, translator, num_iterations: int = 3):
        """
        Initialize GEPA optimizer.

        Args:
            multi_judge: MultiRunJudge instance
            translator: LocalHFTranslator (or compatible generator) instance
            num_iterations: Number of optimization iterations
        """
        self.multi_judge = multi_judge
        self.translator = translator
        self.num_iterations = num_iterations
        self.history = []

    def generate_prompt_variants(
        self,
        base_prompt: str,
        iteration: int
    ) -> List[str]:
        """
        Generate prompt variants for exploration.
        """
        variants = [base_prompt]

        if iteration == 0:
            modifications = [
                base_prompt + "\nFocus on semantic accuracy and completeness.",
                base_prompt + "\nPrioritize natural, native Mandarin phrasing.",
                base_prompt + "\nPreserve tone, intent, and idiomatic meaning.",
            ]
        else:
            modifications = [
                base_prompt + "\nAvoid overly literal wording when more natural Mandarin exists.",
                base_prompt + "\nPreserve nuance, named entities, and formatting exactly.",
                base_prompt + "\nBalance fidelity with fluent Mandarin syntax.",
            ]

        variants.extend(modifications)
        return variants

    def run_gepa_loop(
        self,
        translation_examples: List[Dict],
        base_prompt: str = ""
    ) -> Dict:
        """
        Run GEPA optimization loop on translation examples.

        Args:
            translation_examples: List of {"english": str, ...}
            base_prompt: Initial system prompt

        Returns:
            {
                "final_best_score": float,
                "final_best_prompt": str,
                "optimization_history": list,
                "status": str,
                "num_variants_tested": int
            }
        """

        if not base_prompt:
            base_prompt = (
                "You are a professional machine translation system.\n"
                "Translate from English to Mandarin Chinese.\n"
                "Rules:\n"
                "1. Output ONLY the translation.\n"
                "2. Do NOT explain.\n"
                "3. Do NOT think aloud.\n"
                "4. Do NOT add notes or comments.\n"
                "5. Preserve the original meaning, tone, and style.\n"
                "6. Use natural, fluent target-language text."
            )

        logger.info(f"Starting GEPA optimization with {self.num_iterations} iterations")

        print("\n" + "=" * 80)
        print("GEPA OPTIMIZATION LOOP: ENGLISH → MANDARIN WITH LOCAL GENERATION")
        print("=" * 80)

        best_score = 0
        best_prompt = base_prompt
        total_variants = 0

        for iteration in range(self.num_iterations):
            print(f"\n[Iteration {iteration + 1}/{self.num_iterations}]")

            variants = self.generate_prompt_variants(best_prompt, iteration)
            variant_scores = []

            for variant_idx, variant in enumerate(variants):
                print(f"\n  Variant {variant_idx + 1}/{len(variants)}")
                print(f"  Prompt: {variant[:100]}...")

                example_scores = []
                example_outputs = []

                for example_idx, example in enumerate(translation_examples):
                    english_text = example.get("english", "")

                    # Step 1: Generate live translation with current prompt variant
                    gen_result = self.translator.translate(english_text, variant)

                    if not gen_result["success"]:
                        example_outputs.append({
                            "example_id": example.get("example_id", example_idx),
                            "english": english_text,
                            "generated_mandarin": None,
                            "score": None,
                            "error": gen_result["error"],
                        })
                        continue

                    mandarin_output = gen_result["translation"]

                    # Step 2: Judge generated translation
                    judge_result = self.multi_judge.evaluate_stable(
                        english=english_text,
                        mandarin=mandarin_output,
                        show_progress=False
                    )

                    if judge_result["final_score"] is not None:
                        example_scores.append(judge_result["final_score"])

                    example_outputs.append({
                        "example_id": example.get("example_id", example_idx),
                        "english": english_text,
                        "reference_mandarin": example.get("reference_mandarin"),
                        "generated_mandarin": mandarin_output,
                        "score": judge_result["final_score"],
                        "stability": judge_result.get("stability"),
                        "feedback": judge_result.get("sample_feedback"),
                    })

                if len(example_scores) > 0:
                    variant_mean_score = round(sum(example_scores) / len(example_scores), 2)
                else:
                    variant_mean_score = 0.0

                variant_scores.append({
                    "variant_id": variant_idx,
                    "prompt": variant,
                    "mean_score": variant_mean_score,
                    "num_examples_scored": len(example_scores),
                    "sample_outputs": example_outputs[:3],
                })

                print(f"    → Mean score: {variant_mean_score}/10 over {len(example_scores)} examples")

                if variant_mean_score > best_score:
                    best_score = variant_mean_score
                    best_prompt = variant
                    print("    ⭐ NEW BEST")

            iteration_log = {
                "iteration": iteration + 1,
                "best_score_so_far": round(best_score, 2),
                "best_prompt": best_prompt,
                "variants_tested": len(variants),
                "variant_details": variant_scores,
            }

            self.history.append(iteration_log)
            total_variants += len(variants)

            print(f"\n  → Best score so far: {best_score:.2f}/10")

        logger.info(f"GEPA optimization complete. Best score: {best_score}")

        return {
            "final_best_score": round(best_score, 2),
            "final_best_prompt": best_prompt,
            "optimization_history": self.history,
            "status": "SUCCESS",
            "num_variants_tested": total_variants,
            "num_iterations": self.num_iterations
        }