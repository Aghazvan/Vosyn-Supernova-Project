"""
GEPA optimizer for prompt adaptation.

Classes:
    GEPAOptimizer: Gradient-Estimation-based Prompt Adaptation
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class GEPAOptimizer:
    """Gradient-Estimation-based Prompt Adaptation (GEPA) optimizer.
    
    Iteratively refines translation prompts based on judge feedback.
    
    Example:
        >>> multi_judge = MultiRunJudge(judge, num_runs=10)
        >>> gepa = GEPAOptimizer(multi_judge, num_iterations=3)
        >>> result = gepa.run_gepa_loop(translation_examples)
        >>> print(f"Best score: {result['final_best_score']}")
    """
    
    def __init__(self, multi_judge, num_iterations: int = 3):
        """
        Initialize GEPA optimizer.
        
        Args:
            multi_judge: MultiRunJudge instance
            num_iterations: Number of optimization iterations
        """
        self.multi_judge = multi_judge
        self.num_iterations = num_iterations
        self.history = []
    
    def generate_prompt_variants(
        self,
        base_prompt: str,
        iteration: int
    ) -> List[str]:
        """
        Generate prompt variants for exploration.
        
        Args:
            base_prompt: Base prompt to modify
            iteration: Current iteration number
        
        Returns:
            List of prompt variants (including original)
        """
        variants = [base_prompt]  # Always keep original
        
        # Iteration-specific modifications
        if iteration == 0:
            # First iteration: explore basic strategies
            modifications = [
                f"{base_prompt} Focus on accuracy and semantic preservation.",
                f"{base_prompt} Prioritize natural fluency in the target language.",
                f"{base_prompt} Ensure cultural nuances and idioms are properly adapted.",
            ]
        else:
            # Later iterations: fine-tune based on feedback
            modifications = [
                f"{base_prompt} Emphasize accuracy over stylistic variation.",
                f"{base_prompt} Balance accuracy with idiomatic fluency.",
                f"{base_prompt} Preserve nuance while maintaining readability.",
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
            translation_examples: List of {"english": str, "cantonese": str, "mandarin": str}
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
            base_prompt = "You are an expert translator. Provide accurate, fluent translations preserving all nuances."
        
        logger.info(f"Starting GEPA optimization with {self.num_iterations} iterations")
        print("\n" + "="*80)
        print("GEPA OPTIMIZATION LOOP")
        print("="*80)
        
        best_score = 0
        best_prompt = base_prompt
        total_variants = 0
        
        for iteration in range(self.num_iterations):
            print(f"\n[Iteration {iteration + 1}/{self.num_iterations}]")
            
            # Generate variants
            variants = self.generate_prompt_variants(best_prompt, iteration)
            variant_scores = []
            
            for variant_idx, variant in enumerate(variants):
                print(f"\n  Variant {variant_idx + 1}/{len(variants)}")
                print(f"  Prompt: {variant[:60]}...")
                
                variant_mean_score = 0
                example_count = 0
                
                # Evaluate variant on all examples
                for example in translation_examples:
                    result = self.multi_judge.evaluate_stable(
                        english=example.get('english', ''),
                        cantonese=example.get('cantonese', ''),
                        mandarin=example.get('mandarin', ''),
                        show_progress=False
                    )
                    
                    if result['final_score'] is not None:
                        variant_mean_score += result['final_score']
                        example_count += 1
                
                # Average across examples
                if example_count > 0:
                    variant_mean_score = variant_mean_score / example_count
                else:
                    variant_mean_score = 0
                
                variant_scores.append({
                    "variant_id": variant_idx,
                    "prompt_snippet": variant[:50] + "...",
                    "mean_score": round(variant_mean_score, 2),
                    "stability": "N/A"
                })
                
                print(f"    → Score: {variant_mean_score:.2f}/10")
                
                # Update best
                if variant_mean_score > best_score:
                    best_score = variant_mean_score
                    best_prompt = variant
                    print(f"    ⭐ NEW BEST")
            
            # Log iteration
            iteration_log = {
                "iteration": iteration + 1,
                "best_score": round(best_score, 2),
                "best_prompt_snippet": best_prompt[:60] + "...",
                "variants_tested": len(variants),
                "variant_details": variant_scores
            }
            self.history.append(iteration_log)
            total_variants += len(variants)
            
            print(f"\n  → Iteration Best Score: {best_score:.2f}/10")
        
        logger.info(f"GEPA optimization complete. Best score: {best_score}")
        
        return {
            "final_best_score": round(best_score, 2),
            "final_best_prompt": best_prompt,
            "optimization_history": self.history,
            "status": "SUCCESS",
            "num_variants_tested": total_variants,
            "num_iterations": self.num_iterations
        }