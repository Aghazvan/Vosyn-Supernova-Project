"""
Sprint 50 Task A config: wire up the judge configurations to be validated
against the gold set.

Fill in JUDGE_CONFIGS below with each configuration actually proposed this
sprint. Each entry needs a judge_fn: Callable[[english, mt_output, direction],
RunResult] -- wrap whichever judge call already exists (Sprint 47/48's Groq
JudgeModel, Sprint 49's local Qwen3 Local Judge Model, or a new candidate) so
that it returns a RunResult instead of raising or returning None on parse
failure. That's what lets aggregate_runs() detect malformed output instead of
it silently becoming a missing/zero value.
"""
from aggregation import RunResult
from scoring_harness import JudgeConfig
from local_judge import LocalJudgeModel

# --- Example adapter: wrap the Sprint 49 local LocalJudgeModel.evaluate() ---


localJudge_qwen1 = LocalJudgeModel(
        model_name="Qwen/Qwen3-4B-Instruct-2507",   
        max_seq_length=4096,
        max_new_tokens=256,
        temperature=0.0,
        load_in_4bit=True,
    )

localJudge_qwen2 = LocalJudgeModel(
        model_name="Qwen/Qwen3-8B-Instruct",   
        max_seq_length=4096,
        max_new_tokens=256,
        temperature=0.0,
        load_in_4bit=True,
    )

def local_judge_qwen1(english, translated, direction):
    result = localJudge_qwen1.evaluate(english=english, mandarin=translated)  # or cantonese=
    if result.get("success") and result.get("score") is not None:
        return RunResult(score=float(result["score"]), parse_ok=True, raw_response=str(result))
    return RunResult(score=None, parse_ok=False, raw_response=str(result))


def local_judge_qwen2(english, translated, direction):
    result = localJudge_qwen2.evaluate(english=english, mandarin=translated)  # or cantonese=
    if result.get("success") and result.get("score") is not None:
        return RunResult(score=float(result["score"]), parse_ok=True, raw_response=str(result))
    return RunResult(score=None, parse_ok=False, raw_response=str(result))


JUDGE_CONFIGS = [
    JudgeConfig(
        name="local_qwen2_gemba_rrwa",
        judge_fn=local_judge_qwen2,
        num_runs=3,
        notes="Local Qwen3-8B-Instruct backend",
    ),
    JudgeConfig(
        name="local_qwen1_gemba_rrwa",
        judge_fn=local_judge_qwen1,
        num_runs=3,
        notes="Local Qwen3-4B-Instruct backend",
    ),
]
