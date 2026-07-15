"""
Configuration and constants for GEPA pipeline.
"""

# Model choices
SUPPORTED_MODELS = [
    "gpt-4o",
    "gpt-4",
    "claude-3-opus",
    "claude-3-sonnet",
    "llama-2-70b-chat",
    "gemini-2.5"
]

# Default parameters
DEFAULT_NUM_JUDGE_RUNS = 10
DEFAULT_NUM_GEPA_ITERATIONS = 2
DEFAULT_AGGREGATION_SCHEME = "median"

# Stability thresholds
STABILITY_THRESHOLD_PASS = 0.7
STABILITY_THRESHOLD_WARN = 0.5

# Sample translations for validation
VALIDATION_SAMPLES = [
    {
        "english": "The quick brown fox jumps over the lazy dog.",
        "cantonese": "嗰隻啡色快狐狸跳過嗰隻懶狗。",
        "mandarin": "那只棕色的快狐狸跳过了那只懶狗。"
    },
    {
        "english": "I would like a cup of coffee, please.",
        "cantonese": "我想要一杯咖啡，唔該。",
        "mandarin": "我想要一杯咖啡，请。"
    },
    {
        "english": "The weather is nice today.",
        "cantonese": "今日天气好靓。",
        "mandarin": "今天天气很好。"
    },
    {
        "english": "Where is the nearest train station?",
        "cantonese": "最近嘅火車站喺邊到？",
        "mandarin": "最近的火车站在哪里？"
    },
    {
        "english": "Have a nice day!",
        "cantonese": "祝你有個美好嘅一日！",
        "mandarin": "祝你有美好的一天！"
    }
]