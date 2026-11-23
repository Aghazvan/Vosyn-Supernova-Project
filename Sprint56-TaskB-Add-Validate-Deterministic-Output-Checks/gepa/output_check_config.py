"""Target-specific deterministic output-check configuration for Sprint 56 Task B."""

from gepa.checks import LENGTH_RATIO_BOUNDS

DIRECTION_CONFIGS = {
    # English -> Mandarin Chinese: simplified Chinese is the expected script.
    "en->zh": {
        "direction": "en->zh",
        "length_ratio": dict(LENGTH_RATIO_BOUNDS["en->zh"]),
        "target_language": "cmn",
        "target_script": "cjk",
        "output_checks": [
            "target_script",
            "simplified_script",
            "pinyin",
            "no_cantonese_markers",
            "no_residual_latin",
            "numbers_preserved",
            "not_truncated",
            "no_degeneration",
            "length_ratio",
        ],
    },
    # English -> Cantonese: this pool uses traditional Chinese orthography.
    "en->yue": {
        "direction": "en->yue",
        "length_ratio": dict(LENGTH_RATIO_BOUNDS["en->yue"]),
        "target_language": "yue",
        "target_script": "cjk",
        "output_checks": [
            "target_script",
            "traditional_script",
            "pinyin",
            "no_residual_latin",
            "numbers_preserved",
            "not_truncated",
            "no_degeneration",
            "length_ratio",
        ],
    },
    # Mandarin -> English.
    "zh->en": {
        "direction": "zh->en",
        "length_ratio": dict(LENGTH_RATIO_BOUNDS["zh->en"]),
        "target_language": "en",
        "target_script": "latin",
        "output_checks": [
            "target_script",
            "no_residual_cjk",
            "no_fullwidth_punctuation",
            "numbers_preserved",
            "not_truncated",
            "no_degeneration",
            "length_ratio",
        ],
    },
    # Cantonese -> English.
    "yue->en": {
        "direction": "yue->en",
        "length_ratio": dict(LENGTH_RATIO_BOUNDS["yue->en"]),
        "target_language": "en",
        "target_script": "latin",
        "output_checks": [
            "target_script",
            "no_residual_cjk",
            "no_fullwidth_punctuation",
            "numbers_preserved",
            "not_truncated",
            "no_degeneration",
            "length_ratio",
        ],
    },
}


def get_direction_config(direction: str) -> dict:
    """Return a fresh config so callers cannot mutate the shared defaults."""
    try:
        config = DIRECTION_CONFIGS[direction]
    except KeyError as exc:
        raise ValueError(f"Unsupported translation direction: {direction!r}") from exc
    return {**config, "output_checks": list(config["output_checks"]), "length_ratio": dict(config["length_ratio"])}
