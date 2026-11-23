import json
from collections import Counter
from pathlib import Path

import pytest

from gepa.checks import (
    CHECK_REGISTRY,
    CheckUnavailableError,
    check_no_cantonese_markers,
    check_no_residual_cjk,
    check_no_residual_latin,
    check_pinyin,
    check_length_ratio,
    derive_length_ratio_bounds,
    check_simplified_script,
    check_target_script,
    check_traditional_script,
    run_checks,
)
from gepa.output_check_config import DIRECTION_CONFIGS, get_direction_config

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load_dataset():
    rows = []
    for path in sorted(DATA.glob("*/golden/*.jsonl")):
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return rows


class FakeOpenCC:
    def __init__(self, converted):
        self.converted = converted

    def convert(self, text):
        return self.converted


def test_all_four_directions_have_explicit_configs():
    assert set(DIRECTION_CONFIGS) == {"en->zh", "en->yue", "zh->en", "yue->en"}
    for direction in DIRECTION_CONFIGS:
        config = get_direction_config(direction)
        assert config["output_checks"]
        assert "target_script" in config["output_checks"]


def test_configs_do_not_apply_mandarin_rules_to_cantonese_or_english():
    cmn_checks = get_direction_config("en->zh")["output_checks"]
    assert "no_cantonese_markers" in cmn_checks
    # The converted CMN references commonly use ASCII commas/semicolons;
    # this punctuation rule would reject many reference translations.
    assert "cjk_punctuation" not in cmn_checks
    assert "no_cantonese_markers" not in get_direction_config("en->yue")["output_checks"]
    assert "simplified_script" not in get_direction_config("en->yue")["output_checks"]
    assert "traditional_script" in get_direction_config("en->yue")["output_checks"]
    assert "pinyin" in cmn_checks
    assert "pinyin" in get_direction_config("en->yue")["output_checks"]
    for direction in ("zh->en", "yue->en"):
        assert "pinyin" not in get_direction_config(direction)["output_checks"]
    for direction in ("zh->en", "yue->en"):
        checks = get_direction_config(direction)["output_checks"]
        assert "no_residual_cjk" in checks
        assert "no_fullwidth_punctuation" in checks
        assert "no_residual_latin" not in checks


def test_registry_includes_traditional_script_and_all_requested_checks():
    assert {
        "not_empty", "not_source_copy", "target_script", "simplified_script",
        "traditional_script", "no_cantonese_markers", "no_residual_latin", "pinyin", "length_ratio",
        "no_residual_cjk", "numbers_preserved", "not_truncated",
        "no_degeneration", "cjk_punctuation", "no_fullwidth_punctuation",
    } <= set(CHECK_REGISTRY)


def test_mandarin_config_flags_cantonese_markers():
    config = get_direction_config("en->zh")
    config["output_checks"].remove("simplified_script")  # OpenCC is tested separately.
    report = run_checks("我哋唔知道。", "We do not know.", config)
    assert "no_cantonese_markers" in {r.name for r in report.failures}


def test_cantonese_config_does_not_flag_cantonese_markers():
    config = get_direction_config("en->yue")
    config["output_checks"].remove("traditional_script")  # OpenCC is tested separately.
    report = run_checks("我哋唔知道。", "We do not know.", config)
    assert "no_cantonese_markers" not in {r.name for r in report.results}


def test_residual_latin_is_checked_inside_cjk_output():
    result = check_no_residual_latin("這個 app 很好。", "This app is good.")
    assert result.passed is True  # source-carried token is permitted
    result = check_no_residual_latin("這個 dashboard 很好。", "This is good.")
    assert result.passed is False


def test_residual_cjk_is_checked_in_english_output():
    assert check_no_residual_cjk("The patient is stable.").passed
    assert not check_no_residual_cjk("The patient 病人 is stable.").passed



def test_pinyin_detects_untranslated_romanization_and_tone_variants():
    assert not check_pinyin("這個 ni hao 很好。", "This is good.").passed
    assert not check_pinyin("這個 nǐ hǎo 很好。", "This is good.").passed
    assert not check_pinyin("這個 ni3 hao3 很好。", "This is good.").passed
    assert check_pinyin("這個你好。", "This is good.").passed
    assert check_pinyin("a man is waiting", "Someone is waiting.").passed


def test_pinyin_respects_residual_latin_exemptions():
    # These words are present in the source and therefore already exempted by
    # check_no_residual_latin; the Pinyin detector must make the same choice.
    assert check_pinyin("這個 Li Wei 很好。", "Meet Li Wei tomorrow.").passed
    assert check_pinyin("這個 NASA AI 很好。", "The NASA AI team.").passed
    assert check_pinyin("這個 An Na 很好。", "This is good.", allowed_latin_terms={"An", "Na"}).passed


def test_length_ratio_uses_direction_aware_counts():
    forward_bounds = {"min": 0.70, "max": 2.60, "min_source_units": 0}
    reverse_bounds = {"min": 0.35, "max": 1.45, "min_source_units": 0}
    assert not check_length_ratio("你好", "we need to go home", forward_bounds, "en->zh").passed
    assert not check_length_ratio("你好世界你好世界你好世界你好世界", "we need to go home", forward_bounds, "en->zh").passed
    assert not check_length_ratio("hello", "你好世界", reverse_bounds, "zh->en").passed
    assert check_length_ratio("hello there", "你好世界", reverse_bounds, "zh->en").passed


def test_length_ratio_calibration_uses_same_units_as_runtime():
    pairs = [("we need to go home", "我們需要回家") for _ in range(12)]
    bounds = derive_length_ratio_bounds(pairs, "en->zh")
    assert bounds["pairs"] == 12
    assert bounds["min"] == 0.70 and bounds["max"] == 2.60
    assert bounds["method"].startswith("CJK characters / English words")
    result = check_length_ratio("我們需要回家", "we need to go home", bounds, "en->zh")
    assert result.passed


def test_script_checks_with_controlled_converter():
    assert not check_simplified_script("时间", converter=FakeOpenCC("時間")).passed
    assert check_simplified_script("時間", converter=FakeOpenCC("時間")).passed
    assert not check_traditional_script("时间", converter=FakeOpenCC("時間")).passed


def test_opencc_dependency_fails_loudly_when_unavailable(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "opencc":
            raise ImportError("simulated missing OpenCC")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    with pytest.raises(CheckUnavailableError, match="needs the 'opencc' package"):
        check_simplified_script("时间")


def test_target_script_rejects_wrong_script_only_output():
    assert not check_target_script("ni hao", "hello", "cjk").passed
    assert not check_target_script("你好", "hello", "latin").passed
    assert check_target_script("Hello", "你好", "latin").passed



def test_andromeda_orthography_slice_contains_all_33_labelled_records():
    source = DATA / "raw" / "andromeda" / "dataset_v7.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = Counter()
    for row in rows:
        for error in row.get("errors", []):
            if isinstance(error, dict) and error.get("error_type") in {
                "standard_written_chinese", "simplified_script", "mixed_script"
            }:
                counts[(row.get("language_pair"), error["error_type"])] += 1
    assert sum(counts.values()) == 33
    assert counts == {
        ("en-yue", "standard_written_chinese"): 12,
        ("en-yue", "simplified_script"): 12,
        ("en-yue", "mixed_script"): 5,
        ("en-te", "mixed_script"): 4,
    }


def test_unknown_direction_fails_loudly():
    with pytest.raises(ValueError, match="Unsupported translation direction"):
        get_direction_config("en->fr")


def test_converted_dataset_has_expected_179_records_and_direction_counts():
    rows = load_dataset()
    assert len(rows) == 179
    assert Counter(r["translation_direction"] for r in rows) == {
        "en->zh": 27, "en->yue": 111, "zh->en": 26, "yue->en": 15,
    }


def test_every_converted_record_can_run_its_direction_config():
    rows = load_dataset()
    assert rows
    for record in rows:
        config = get_direction_config(record["translation_direction"])
        # OpenCC-dependent script checks are run in dedicated unit tests.
        config["output_checks"] = [n for n in config["output_checks"]
                                   if n not in {"simplified_script", "traditional_script"}]
        report = run_checks(record["candidate_translation"], record["source_text"], config)
        names = {r.name for r in report.results}
        assert {"not_empty", "not_source_copy", "target_script"} <= names


def test_all_records_preserve_conversion_annotations():
    rows = load_dataset()
    for record in rows:
        assert record["label_source"] in {"human_reviewed", "engineered_perturbation", "weak_mt_style"}
        assert isinstance(record["errors"], list)
        for error in record["errors"]:
            assert {"error_type", "severity", "source_span", "candidate_span", "note"} <= set(error)


def test_direction_configs_enable_calibrated_length_ratio():
    expected = {
        "en->zh": (0.70, 2.60, 8),
        "en->yue": (0.70, 2.80, 6),
        "zh->en": (0.35, 1.45, 12),
        "yue->en": (0.35, 1.45, 6),
    }
    for direction, (low, high, min_units) in expected.items():
        config = get_direction_config(direction)
        assert "length_ratio" in config["output_checks"]
        assert config["direction"] == direction
        assert config["length_ratio"]["min"] == low
        assert config["length_ratio"]["max"] == high
        assert config["length_ratio"]["min_source_units"] == min_units
