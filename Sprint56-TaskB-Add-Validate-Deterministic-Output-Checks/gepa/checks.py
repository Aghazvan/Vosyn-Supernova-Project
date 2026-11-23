"""
Deterministic output checks: the failures a judge should not be asked
to catch.

An LLM judge scored an output left entirely in English at ten out of
ten, and another written entirely in Traditional characters at ten out
of ten. Both were caught instantly by a string comparison. The lesson is
not that the judge is bad — it is that asking a probabilistic grader to
police a deterministic property is the wrong tool for the job.

Everything here is a string operation: no model, no API call, no cost,
no variance. The checks are also the *cheapest* thing in the pipeline
and catch the failure class that costs the most, so they run first and
their verdict is not negotiable by a judge's opinion.

What these checks deliberately cannot do:

  * The Cantonese marker set is a curated list of high-signal
    characters, not a linguistic model. It catches vernacular Cantonese
    written in Chinese characters; it will not catch Cantonese phrased
    entirely in words shared with Mandarin, and it cannot distinguish
    a deliberate quotation from an error.
  * The Latin-token check exempts acronyms and anything already present
    in the source, which means a proper noun the model invented in
    Latin script passes. That is the right trade: flagging every
    legitimately-kept name would make the check unusable.
  * Script detection tells you a character has a Simplified form that
    differs. A handful of characters are genuinely shared or ambiguous,
    so a single flagged character is weaker evidence than a sentence
    full of them, and the count is reported for that reason.
  * Number preservation only sees numerals. A quantity spelled out in
    words in either language is invisible to it, so "twelve" rendered
    as 12 passes unexamined and so does 1st rendered as primero.
  * A time or a date rewritten in another convention is reported as a
    missing number: 19时45分 as "7:45 p.m.", or 2004年10月28日 as
    "28.10.04". Converting between clock and calendar conventions is
    beyond a digit comparison.
  * Truncation only reports endings that cannot finish a sentence. An
    output missing its final full stop is not reported, because models
    drop that mark on complete sentences often enough that failing them
    would cost more good translations than it caught truncated ones.

  * Length ratio compares character counts against bounds measured on
    that language pair's own reference translations. It reports only
    output far outside what human translators produced, so a
    translation that drops one short clause from a long sentence stays
    inside the bounds and is not reported.
  * The script checks for a Latin-script target exempt Chinese inside
    brackets, because a translator's gloss such as "Li Bai (李白)" is
    correct. A gloss with no brackets is therefore reported.

Every check here errs toward passing. A false positive scores a correct
translation zero and feeds the optimizer a reason that is not true,
which is worse than missing a failure the judge may still catch.

These limits are written down rather than discovered later, because a
check whose blind spots are undocumented is how a gate ends up under-
reporting its own failure rate while looking like it works.
"""

from __future__ import annotations

import math
import re
import statistics
import unicodedata
from dataclasses import dataclass, field

# Characters that appear in vernacular written Cantonese and effectively
# never in Standard Written Chinese. Curated and deliberately short:
# every addition trades a missed case for a false positive, and a false
# positive on this check blocks a correct translation.
CANTONESE_MARKERS = frozenset("係佢嘅冇咗喺唔啲嗰乜嘢咁噉睇畀嚟攞諗郁掂嘥揾邊咩")

# Latin-script tokens that are legitimate inside Chinese output. Kept
# tiny on purpose; anything in the source text is exempted separately,
# which covers the vast majority of real cases.
_ALWAYS_ALLOWED_LATIN = frozenset({"ok", "tv", "dna", "ai", "app", "email", "wifi"})

# Latin letters with diacritics are part of the token. Without them a
# word such as "hǎo" or "Asunción" was split at the accented letter into
# fragments one character long, which the residual-Latin check ignores,
# so pinyin written with tone marks passed unexamined.
_LATIN_LETTERS = "A-Za-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u024f"
_LATIN_TOKEN = re.compile(rf"[{_LATIN_LETTERS}][{_LATIN_LETTERS}'\-]*")
_CJK = re.compile(r"[一-鿿㐀-䶿]")

# One number, including any grouping or decimal marks inside it. The
# separators are stripped afterwards rather than parsed, so no locale's
# convention has to be hardcoded.
_NUMBER_RUN = re.compile(r"\d(?:[\d.,]*\d)?")

_CHINESE_DIGITS = "零一二三四五六七八九"

# Chinese scale characters. Their presence means the translation is
# grouping by ten thousand rather than by thousand, which makes a
# digit-level comparison against a Western-grouped source meaningless.
_CJK_SCALE = re.compile(r"[万萬亿億千百]")

# Characters that cannot end a finished sentence in any language here.
# A missing full stop is deliberately absent: models drop it routinely
# on complete output, so treating that as truncation would fail good
# translations far more often than it caught cut-off ones.
_MID_CLAUSE_ENDINGS = frozenset(",;:，、；：-–—/")

# A leading list or paragraph marker: "37.", "1.2", "j.", "- ", "• ".
# Stripped before numbers are compared because a numbering prefix on
# one side only is a property of the document, not of the translation.
_ENUMERATION_PREFIX = re.compile(r"^\s*(?:[-•*]\s*)?(?:\d+(?:\.\d+)*|[a-zA-Z])[.、)]\s+")
_PAIRED = {"(": ")", "[": "]", "{": "}", "（": "）", "「": "」", "『": "』", "《": "》"}

# Three or more consecutive repeats of the same fragment. Three rather
# than two so Chinese reduplication and ordinary doubling pass.
_LOOP = re.compile(r"(\S.{1,39}?)\1{2,}")

_SENTENCE_SPLIT = re.compile(r"[.!?。！？]+")

_ASCII_PUNCT = frozenset(",.!?;:")

# Fullwidth marks that have no place in Latin-script output. Curly
# quotes are deliberately absent: they are ordinary English typography.
_FULLWIDTH_PUNCT = frozenset("，。！？；：、（）「」『』《》")

# Chinese inside brackets in Latin-script output is a translator's
# gloss, e.g. "Li Bai (李白)", and is correct.
_BRACKETED = re.compile(r"[(（\[][^()（）\[\]]*[)）\]]")

# A number written with a Chinese scale character, e.g. 2 900万. The
# digits are not comparable with a Western-grouped translation.
_SCALED_NUMBER = re.compile(r"\d[\d ,.]*\s*[万萬亿億千百]")

# A footnote marker left at the very end of a line, e.g. "...的信，4".
_TRAILING_FOOTNOTE = re.compile(r"(?<=[，。,.;；])\s*\d{1,2}\s*$")

_CJK_MONTH = re.compile(r"(\d{1,2})\s*月")
_ENGLISH_MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)  # fmt: skip

_ENGLISH_UNITS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
)  # fmt: skip
_ENGLISH_TENS = ("twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_ENGLISH_ORDINALS = (
    "zeroth", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
    "eighth", "ninth", "tenth", "eleventh", "twelfth",
)  # fmt: skip

_WORD = re.compile(r"[^\W\d_]+")

# How many robust standard deviations from the median a length ratio
# may sit before it is reported. See derive_length_ratio_bounds.
LENGTH_RATIO_SIGMAS = 3.0


class CheckUnavailableError(RuntimeError):
    """
    A requested check could not run at all, for example because the
    library it depends on is not installed. Raised rather than reported
    as a pass: a check that silently does nothing looks exactly like a
    check that found nothing.
    """


@dataclass
class CheckResult:
    """One check's verdict on one output."""

    name: str
    passed: bool
    detail: str = ""
    evidence: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed


@dataclass
class CheckReport:
    """Every check's verdict on one output, plus the overall answer."""

    results: list[CheckResult]

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed]

    def as_dict(self) -> dict:
        return {
            "passed": self.passed,
            "failed_checks": [r.name for r in self.failures],
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "detail": r.detail,
                    "evidence": r.evidence,
                }
                for r in self.results
            ],
        }



# Mandarin Pinyin syllables used by the conservative romanization detector.
# This is intentionally a heuristic inventory, not a language identifier.
_PINYIN_SYLLABLES = frozenset("""
    "a ai an ang ao ba bai ban bang bao bei ben beng bi bian biao bie bin bing bo bu "
    "ca cai can cang cao ce cei cen ceng cha chai chan chang chao che chen cheng chi "
    "chong chou chu chuai chuan chuang chui chun chuo ci cong cou cu cuan cui cun cuo "
    "da dai dan dang dao de dei den deng di dia dian diao die ding diu dong dou du duan "
    "dui dun duo e ei en eng er fa fan fang fei fen feng fo fou fu ga gai gan gang gao "
    "ge gei gen geng gong gou gu gua guai guan guang gui gun guo ha hai han hang hao "
    "he hei hen heng hong hou hu hua huai huan huang hui hun huo ji jia jian jiang "
    "jiao jie jin jing jiong jiu ju juan jue jun ka kai kan kang kao ke ken keng kong "
    "kou ku kua kuai kuan kuang kui kun kuo la lai lan lang lao le lei leng li lia lian "
    "liang liao lie lin ling liu long lou lu luan lun luo lü lüe ma mai man mang mao me "
    "mei men meng mi mian miao mie min ming miu mo mou mu na nai nan nang nao ne nei nen "
    "neng ni nian niang niao nie nin ning niu nong nou nu nuan nuo nü nüe o ou pa pai "
    "pan pang pao pei pen peng pi pian piao pie pin ping po pou pu qi qia qian qiang "
    "qiao qie qin qing qiong qiu qu quan que qun ran rang rao re ren reng ri rong rou "
    "ru ruan rui run ruo sa sai san sang sao se sen seng sha shai shan shang shao she "
    "shei shen sheng shi shou shu shua shuai shuan shuang shui shun shuo si song sou "
    "su suan sui sun suo ta tai tan tang tao te teng ti tian tiao tie ting tong tou tu "
    "tuan tui tun tuo wa wai wan wang wei wen weng wo wu xi xia xian xiang xiao xie xin "
    "xing xiong xiu xu xuan xue xun ya yan yang yao ye yi yin ying yo yong you yu yuan "
    "yue yun za zai zan zang zao ze zei zen zeng zha zhai zhan zhang zhao zhe zhei zhen "
    "zheng zhi zhong zhou zhu zhua zhuai zhuan zhuang zhui zhun zhuo zi zong zou zu zuan "
    "zui zun zuo"
""".replace('"', '').split())

_PINYIN_TOKEN = re.compile(r"[A-Za-z\u00C0-\u024FüÜvV]+(?:[1-5])?")


def _normalize_pinyin_syllable(token: str) -> str:
    """Remove tone marks/numbers and normalize ü to the Pinyin spelling v."""
    token = unicodedata.normalize("NFKD", token.casefold())
    token = "".join(ch for ch in token if not unicodedata.combining(ch))
    token = token.rstrip("12345").replace("u:", "v").replace("ü", "v")
    return token


_PINYIN_SYLLABLES = frozenset(_normalize_pinyin_syllable(x) for x in _PINYIN_SYLLABLES)


def check_pinyin(
    text: str,
    source: str = "",
    *,
    allowed_latin_terms: set[str] | list[str] | tuple[str, ...] | None = None,
    min_syllables: int = 2,
) -> CheckResult:
    """Flag runs of Pinyin-looking Latin syllables in Chinese-target output.

    Exemptions intentionally mirror ``check_no_residual_latin``: source-carried
    words, its built-in allowlist, and all-uppercase acronyms are not reported.
    An optional configured allowlist supports approved names not present in the
    source. The detector is heuristic and should be reviewed on real outputs.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not _CJK.search(text):
        return CheckResult("pinyin", True, "no Chinese output; target_script handles wrong-language output")
    if min_syllables < 2:
        raise ValueError("min_syllables must be at least 2")

    source_terms = _source_words(source)
    allowed = set(_ALWAYS_ALLOWED_LATIN) | source_terms
    for term in (allowed_latin_terms or ()):
        allowed.update(_source_words(unicodedata.normalize("NFKC", term)))

    matches: list[str] = []
    run: list[str] = []

    def flush() -> None:
        nonlocal run
        if len(run) >= min_syllables:
            matches.append(" ".join(run))
        run = []

    previous_end = None
    for match in _PINYIN_TOKEN.finditer(text):
        token = match.group(0)
        normalized = _normalize_pinyin_syllable(token)
        gap = "" if previous_end is None else text[previous_end:match.start()]
        # Only whitespace may join syllables. Punctuation, digits, or symbols
        # separate a candidate phrase.
        if previous_end is not None and gap.strip():
            flush()

        # Mirror no_residual_latin's exemptions at token level. This also
        # prevents an allowed proper noun from joining two Pinyin-looking words.
        token_allowed = (
            token.isupper()
            or normalized in allowed
            or token.casefold() in allowed
        )
        if token_allowed or normalized not in _PINYIN_SYLLABLES:
            flush()
        else:
            run.append(token)
        previous_end = match.end()
    flush()

    if not matches:
        return CheckResult("pinyin", True, "no Pinyin-like Latin syllable run detected")
    return CheckResult(
        "pinyin", False,
        f"{len(matches)} Pinyin-like Latin syllable run(s) detected",
        evidence=matches,
    )


def _normalize(text: str) -> str:
    """Strip case, punctuation and spacing, for comparisons that should ignore them."""
    folded = unicodedata.normalize("NFKC", text).casefold()
    return "".join(ch for ch in folded if ch.isalnum())


def check_simplified_script(text: str, *, converter=None) -> CheckResult:
    """
    Flag Traditional characters in output that should be Simplified.

    Uses OpenCC's t2s conversion: any character that changes under it
    has a distinct Simplified form and therefore was not written in
    Simplified. This is the check that catches a fluent, grammatical,
    entirely wrong-script translation — which a semantic judge reads as
    perfectly good Chinese, because it is.
    """
    if converter is None:
        try:
            from opencc import OpenCC
        except ImportError as e:
            # Fail closed: missing dependency must never look like a pass.
            raise CheckUnavailableError(
                "simplified_script needs the 'opencc' package, which is not installed. "
                "Run: pip install -r requirements-task-b.txt"
            ) from e
        converter = OpenCC("t2s")

    converted = converter.convert(text)
    if converted == text:
        return CheckResult("simplified_script", True, "no Traditional characters found")

    differing = [orig for orig, conv in zip(text, converted, strict=False) if orig != conv]
    return CheckResult(
        "simplified_script",
        False,
        f"{len(differing)} Traditional character(s) present",
        evidence=sorted(set(differing)),
    )



def check_traditional_script(text: str, *, converter=None) -> CheckResult:
    """Flag Simplified-only characters in output expected to use Traditional Chinese.

    OpenCC s2t leaves Traditional characters unchanged and converts
    Simplified-only forms. This is an orthographic heuristic, not a
    dialect or language-identification check.
    """
    if converter is None:
        try:
            from opencc import OpenCC
        except ImportError as e:
            raise CheckUnavailableError(
                "traditional_script needs the 'opencc' package. Run: pip install -r requirements-task-b.txt"
            ) from e
        converter = OpenCC("s2t")

    converted = converter.convert(text)
    if converted == text:
        return CheckResult("traditional_script", True, "no Simplified-only characters found")

    differing = [orig for orig, conv in zip(text, converted, strict=False) if orig != conv]
    return CheckResult(
        "traditional_script",
        False,
        f"{len(differing)} Simplified-form character(s) present",
        evidence=sorted(set(differing)),
    )

def check_no_cantonese_markers(text: str) -> CheckResult:
    """Flag vernacular Cantonese characters in output that should be Mandarin."""
    found = sorted({ch for ch in text if ch in CANTONESE_MARKERS})
    if not found:
        return CheckResult("no_cantonese_markers", True, "no Cantonese markers found")
    return CheckResult(
        "no_cantonese_markers",
        False,
        f"{len(found)} Cantonese marker character(s) present",
        evidence=found,
    )


def _source_words(source: str) -> set[str]:
    """
    The Latin words of a source, casefolded, each also without a
    possessive ending. "Rosie's" in the source has to exempt "Rosie" in
    the translation: the name was kept correctly, and without this it
    was reported as an untranslated word on real model output.
    """
    words = set()
    for token in _LATIN_TOKEN.findall(source):
        folded = token.casefold()
        words.add(folded)
        if folded.endswith("'s"):
            words.add(folded[:-2])
        words.add(folded.strip("'"))
    return words


def check_no_residual_latin(text: str, source: str) -> CheckResult:
    """
    Flag Latin-script words left untranslated inside CJK output.

    Tokens present in the source are exempt, since a proper noun kept
    from the source is correct behavior, not leakage. Acronyms are
    exempt for the same reason. What remains is the pattern that recurs
    in real runs: an ordinary English noun sitting in a Chinese
    sentence, which a ratio-based gate passes because the output is
    still overwhelmingly CJK.
    """
    if not _CJK.search(text):
        return CheckResult(
            "no_residual_latin", True, "output is not CJK; this check does not apply"
        )

    source_tokens = _source_words(source)
    leaked = [
        token
        for token in _LATIN_TOKEN.findall(text)
        if token.casefold() not in source_tokens
        and token.casefold() not in _ALWAYS_ALLOWED_LATIN
        and not token.isupper()  # acronyms
        and len(token) > 1
    ]
    if not leaked:
        return CheckResult("no_residual_latin", True, "no untranslated Latin words found")
    return CheckResult(
        "no_residual_latin",
        False,
        f"{len(leaked)} Latin word(s) not present in the source",
        evidence=sorted(set(leaked)),
    )


def check_not_source_copy(text: str, source: str) -> CheckResult:
    """
    Flag output that is just the source handed back.

    Checked on normalized text so that a copy with different spacing or
    punctuation still counts as a copy.
    """
    if not _normalize(text):
        return CheckResult("not_source_copy", False, "output is empty")
    if _normalize(text) == _normalize(source):
        return CheckResult(
            "not_source_copy", False, "output is identical to the source", evidence=[source[:80]]
        )
    return CheckResult("not_source_copy", True, "output differs from the source")


def check_not_empty(text: str) -> CheckResult:
    if text and text.strip():
        return CheckResult("not_empty", True, "output is non-empty")
    return CheckResult("not_empty", False, "output is empty or whitespace only")


def _digit_runs(text: str) -> list[str]:
    """
    Every number in the text, reduced to its digits.

    Grouping and decimal marks are stripped rather than interpreted,
    because they are exactly what differs between locales: 1,000 and
    1.000 are the same quantity, and 3.5 and 3,5 are too. Comparing
    digits sidesteps having to know which convention a language uses.

    A leading list or paragraph marker is removed first. Measured
    against real reference translations, a numbering prefix present on
    one side and not the other was the single largest source of false
    reports, and it is a property of the document rather than of the
    translation.
    """
    normalized = _ENUMERATION_PREFIX.sub("", unicodedata.normalize("NFKC", text).strip())
    runs = []
    for run in _NUMBER_RUN.findall(normalized):
        # Two or more separators means a date or a reference like
        # 28.10.04, not one quantity. Joining those digits invents a
        # number that appears in neither text.
        parts = [p for p in re.split(r"[.,]", run) if p]
        runs.extend(parts if len(parts) > 2 else [re.sub(r"\D", "", run)])
    return runs


def _as_chinese_numeral(digits: str) -> str | None:
    """
    Render a small integer the way Chinese writes it, or None.

    Needed because a correct translation of "12" is as likely to be
    十二 as 12, and flagging that would block a good translation. Only
    values a translator plausibly spells out are covered; anything
    larger is left to the digit comparison.
    """
    try:
        value = int(digits)
    except ValueError:
        return None
    if not 0 <= value <= 99:
        return None
    if value < 10:
        return _CHINESE_DIGITS[value]
    tens, ones = divmod(value, 10)
    return (
        ("" if tens == 1 else _CHINESE_DIGITS[tens])
        + "十"
        + ("" if ones == 0 else _CHINESE_DIGITS[ones])
    )


def _as_english_words(digits: str) -> list[str]:
    """
    The ways English spells a small number out, or an empty list.

    The mirror of _as_chinese_numeral: a correct English translation of
    "4名" is as likely to say "four" as 4. Cardinals to 99 and ordinals
    to twelfth are covered; anything larger is left to the digits.
    """
    try:
        value = int(digits)
    except ValueError:
        return []
    if not 0 <= value <= 99:
        return []
    words = []
    if value < 20:
        words.append(_ENGLISH_UNITS[value])
    else:
        tens, ones = divmod(value, 10)
        tens_word = _ENGLISH_TENS[tens - 2]
        words.append(tens_word if ones == 0 else f"{tens_word}-{_ENGLISH_UNITS[ones]}")
        if ones:
            words.append(f"{tens_word} {_ENGLISH_UNITS[ones]}")
    if value < len(_ENGLISH_ORDINALS):
        words.append(_ENGLISH_ORDINALS[value])
    return words


def _contains_word(text: str, word: str) -> bool:
    pattern = rf"(?<![^\W\d_]){re.escape(word)}(?![^\W\d_])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _months_named(source: str, text: str) -> list[str]:
    """
    Month numbers in a Chinese source whose English name is in the text.

    Chinese writes a month as a number (7月) and English as a name
    (July), so the digit legitimately disappears. Measured on reversed
    reference pairs this was the largest single source of false reports.
    """
    named = []
    for match in _CJK_MONTH.finditer(source):
        month = int(match.group(1))
        if not 1 <= month <= 12:
            continue
        name = _ENGLISH_MONTHS[month - 1]
        # Any abbreviation of three letters or more: Sep, Sept, September.
        if any(len(w) >= 3 and name.startswith(w.casefold()) for w in _WORD.findall(text)):
            named.append(str(month))
    return named


def check_numbers_preserved(text: str, source: str) -> CheckResult:
    """
    Flag numbers present in the source and missing from the translation.

    A wrong or dropped number is a serious error that reads as
    perfectly fluent, which is the combination a semantic judge is
    worst at. It is also one of the few meaning-level properties that
    can be settled without a model.

    Comparison is on digits only, so locale differences in grouping and
    decimal marks do not register, and a missing number is additionally
    tested against its Chinese spelled-out form.

    Only the missing direction is reported. Numbers appearing in the
    translation and not the source were measured on real reference
    translations and are dominated by document numbering, footnote
    markers and date reordering rather than by invented quantities, so
    reporting them would fail far more correct translations than it
    would catch hallucinated ones.

    A translation containing 万, 亿, 千 or 百 is passed without
    comparison. Chinese groups by ten thousand rather than by thousand,
    so 29 million is correctly written 2 900万 and 130 million as
    1亿3千万 — the same quantity carrying different digits. On real
    Mandarin references this one difference produced almost every
    remaining report, and no digit comparison can resolve it.

    The same holds with Chinese as the source. A number the source
    writes with a scale character is left out of the comparison, a
    month number is accepted as its English name, a small number is
    accepted spelled out in English, and a footnote marker at the very
    end of the source is ignored. Each of these was a false report on
    human reference translations before it was allowed for.
    """
    comparable = _TRAILING_FOOTNOTE.sub("", _SCALED_NUMBER.sub(" ", source))
    in_source = _digit_runs(comparable)
    if not in_source:
        return CheckResult("numbers_preserved", True, "no numerals in the source")

    if _CJK_SCALE.search(text):
        return CheckResult(
            "numbers_preserved",
            True,
            "translation uses Chinese scale characters; digits are not comparable",
        )

    remaining = _digit_runs(text)
    months = _months_named(source, text)
    missing = []
    for number in in_source:
        if number in remaining:
            remaining.remove(number)
            continue
        spelled = _as_chinese_numeral(number)
        if spelled and spelled in text:
            continue
        if number.lstrip("0") in months:
            months.remove(number.lstrip("0"))
            continue
        if len(number) == 4 and f"{number[2:]}年代" in text:
            # A decade: "the 1980s" is correctly 80年代, with the
            # century left to context or given as 上世纪.
            continue
        if any(_contains_word(text, word) for word in _as_english_words(number)):
            continue
        missing.append(number)

    if not missing:
        return CheckResult(
            "numbers_preserved", True, f"all {len(in_source)} numeral(s) accounted for"
        )
    return CheckResult(
        "numbers_preserved",
        False,
        f"{len(missing)} numeral(s) in the source and not the translation",
        evidence=sorted(set(missing)),
    )


def check_not_truncated(text: str, source: str = "") -> CheckResult:
    """
    Flag output that stops mid-clause when the source did not.

    Only endings that cannot finish a sentence are considered: a
    trailing comma or connector, or a bracket or quote opened and never
    closed. A missing full stop is not treated as truncation, because
    models routinely drop the final mark on complete output.

    The source is compared too. A list item, a preambular clause or a
    sentence introducing a list legitimately ends on a semicolon or a
    colon, and a translation that ends the same way has preserved the
    source rather than been cut off. Measured on real references, every
    reported truncation was of this kind.
    """
    stripped = text.strip()
    if not stripped:
        return CheckResult("not_truncated", True, "empty output is covered by not_empty")

    source_stripped = source.strip()
    source_ends_open = bool(source_stripped) and source_stripped[-1] in _MID_CLAUSE_ENDINGS

    if stripped[-1] in _MID_CLAUSE_ENDINGS and not source_ends_open:
        return CheckResult(
            "not_truncated",
            False,
            f"output ends on {stripped[-1]!r} where the source does not",
            evidence=[stripped[-40:]],
        )

    unclosed = [
        f"{opener}{closer}"
        for opener, closer in _PAIRED.items()
        if stripped.count(opener) > stripped.count(closer)
        and source.count(opener) <= source.count(closer)
    ]
    if unclosed:
        return CheckResult(
            "not_truncated",
            False,
            f"{len(unclosed)} bracket or quote pair opened and not closed",
            evidence=unclosed,
        )

    return CheckResult("not_truncated", True, "output ends on a complete clause")


def _repeats_needed(text: str, start: int, end: int) -> int:
    """
    How many repetitions make a loop, given what is being repeated.

    Only whole words inside the match are counted. The pattern finds
    "eah, yeah, yeah, y" inside "Yeah, yeah, yeah, you can", and the
    question is whether one word is being repeated, so the fragments
    of "Yeah" and "you" at either edge are set aside.
    """
    span = text[start:end]
    if _CJK.search(span):
        return 3
    words = [
        match.group(0).casefold()
        for match in _WORD.finditer(text)
        if match.start() >= start
        and match.end() <= end
        and (match.start() > start or start == 0 or not text[start - 1].isalpha())
        and (match.end() < end or end == len(text) or not text[end].isalpha())
    ]
    return 5 if len(set(words)) == 1 else 3


def check_no_degeneration(text: str) -> CheckResult:
    """
    Flag looping output: the same fragment emitted three or more times
    in a row, or the same sentence repeated.

    Small models under a constrained token budget fail this way, and
    the result is fluent enough per fragment that a judge reading for
    meaning can score it generously.

    Three repetitions is the threshold rather than two, so that Chinese
    reduplication (看看, 高高兴兴) and ordinary English doubling are not
    reported.

    One word said over and over needs five. "Yeah, yeah, yeah, you can"
    is how people talk, it appears in human reference translations, and
    at three repetitions it was reported as a loop.
    """
    collapsed = re.sub(r"\s+", " ", text.strip())
    if not collapsed:
        return CheckResult("no_degeneration", True, "empty output is covered by not_empty")

    # A trailing space lets a phrase repeated right up to the end of
    # the text count its last repetition, which otherwise lacks the
    # space the earlier ones end on.
    padded = collapsed + " "
    for loop in _LOOP.finditer(padded):
        repeats = len(loop.group(0)) // len(loop.group(1))
        if repeats >= _repeats_needed(padded, loop.start(), loop.end()):
            return CheckResult(
                "no_degeneration",
                False,
                f"fragment repeated {repeats} times in a row",
                evidence=[loop.group(1)],
            )

    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(collapsed) if len(s.strip()) > 3]
    repeated = {s for s in sentences if sentences.count(s) > 1}
    if repeated:
        return CheckResult(
            "no_degeneration",
            False,
            f"{len(repeated)} sentence(s) emitted more than once",
            evidence=sorted(repeated)[:3],
        )

    return CheckResult("no_degeneration", True, "no repeated fragments found")


def check_cjk_punctuation(text: str) -> CheckResult:
    """
    Flag ASCII punctuation used where CJK text requires fullwidth marks.

    A native reader sees this immediately and a judge scoring for
    meaning does not see it at all, which is what makes it worth a
    deterministic check rather than a rubric line.

    Only punctuation directly touching a CJK character is reported, so
    a decimal point inside 3.5, a kept acronym, and a URL are all left
    alone. So is an ellipsis typed as dots.
    """
    if not _CJK.search(text):
        return CheckResult("cjk_punctuation", True, "output is not CJK; this check does not apply")

    found = []
    for i, ch in enumerate(text):
        if ch not in _ASCII_PUNCT:
            continue
        before = text[i - 1] if i else ""
        after = text[i + 1] if i + 1 < len(text) else ""
        if ch == "." and "." in (before, after):
            # An ellipsis typed as three dots. Chinese has its own mark
            # for it, but "但..." is how a trailing-off line is commonly
            # written and it was reported on real model output that had
            # nothing else wrong with it.
            continue
        if _CJK.match(before) or _CJK.match(after):
            found.append(ch)

    if not found:
        return CheckResult("cjk_punctuation", True, "punctuation is fullwidth throughout")
    return CheckResult(
        "cjk_punctuation",
        False,
        f"{len(found)} halfwidth mark(s) adjacent to CJK text",
        evidence=sorted(set(found)),
    )


def _letters(text: str) -> tuple[int, int]:
    """How many CJK characters and how many Latin letters a text holds."""
    return len(_CJK.findall(text)), sum(len(token) for token in _LATIN_TOKEN.findall(text))


def check_target_script(text: str, source: str, script: str | None) -> CheckResult:
    """
    Flag output containing no character of the script it should be in.

    This is the check for a translation written entirely in the wrong
    writing system: Chinese given as pinyin, or an English paraphrase
    where Chinese was asked for. The residual-Latin check cannot see
    either, because it only examines output that is already CJK, and
    the source-copy check passes anything that differs from the source.

    `script` is "cjk" or "latin" and comes from the language's config.
    Output with no letters at all, such as a bare number or a symbol,
    is passed: there is no script to be wrong about. So is output made
    only of acronyms already in the source, which is how "IBM PC" is
    correctly carried across. Ordinary source words are not exempt,
    because that would pass the first half of the English source
    handed back as the translation.
    """
    if script not in ("cjk", "latin"):
        raise ValueError(
            "The target_script check needs `target_script: cjk` or `target_script: latin` "
            f"in the language config; got {script!r}"
        )

    cjk, latin = _letters(text)
    expected, other = (cjk, latin) if script == "cjk" else (latin, cjk)
    if expected:
        return CheckResult("target_script", True, f"output contains {script} text")
    if not other:
        return CheckResult("target_script", True, "output has no letters to check")

    source_tokens = set(_LATIN_TOKEN.findall(source))
    carried = all(t.isupper() and t in source_tokens for t in _LATIN_TOKEN.findall(text))
    if script == "cjk" and carried:
        return CheckResult("target_script", True, "output is only acronyms kept from the source")

    return CheckResult(
        "target_script",
        False,
        f"output contains no {script} text at all",
        evidence=[text.strip()[:60]],
    )


def check_no_residual_cjk(text: str) -> CheckResult:
    """
    Flag Chinese characters left inside Latin-script output.

    The mirror of the residual-Latin check, for translation out of
    Chinese. Characters inside brackets are exempt, since a gloss such
    as "Li Bai (李白)" is a translator being helpful. None of the
    English reference translations measured contained any Chinese.
    """
    leaked = _CJK.findall(_BRACKETED.sub("", text))
    if not leaked:
        return CheckResult("no_residual_cjk", True, "no untranslated Chinese found")
    return CheckResult(
        "no_residual_cjk",
        False,
        f"{len(leaked)} Chinese character(s) left in the output",
        evidence=sorted(set(leaked))[:10],
    )


def check_no_fullwidth_punctuation(text: str) -> CheckResult:
    """
    Flag fullwidth punctuation in Latin-script output.

    The mirror of the CJK punctuation check. A model translating out of
    Chinese sometimes carries the source's ，and 。across unchanged,
    which a judge reading for meaning does not notice.
    """
    found = sorted({ch for ch in _BRACKETED.sub("", text) if ch in _FULLWIDTH_PUNCT})
    if not found:
        return CheckResult("no_fullwidth_punctuation", True, "no fullwidth punctuation found")
    return CheckResult(
        "no_fullwidth_punctuation",
        False,
        f"{len(found)} kind(s) of fullwidth punctuation in the output",
        evidence=found,
    )


_ENGLISH_WORD = re.compile(r"\b[A-Za-z0-9]+(?:['’.-][A-Za-z0-9]+)*\b")


def _length_units(source: str, text: str, direction: str) -> tuple[int, int]:
    """Return (source_units, output_units) using the corpus audit convention.

    EN->Chinese: English source words and CJK output characters.
    Chinese->EN: CJK source characters and English output words.
    """
    if direction in {"en->zh", "en->yue"}:
        return len(_ENGLISH_WORD.findall(source)), len(_CJK.findall(text))
    if direction in {"zh->en", "yue->en"}:
        return len(_CJK.findall(source)), len(_ENGLISH_WORD.findall(text))
    raise ValueError(f"Unsupported length-ratio direction: {direction!r}")


def _percentile(values: list[float], q: float) -> float:
    values = sorted(values)
    if not values:
        raise ValueError("Cannot calculate a percentile from no values")
    position = (len(values) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


# Operational guardrails selected from the Andromeda reference-pair tails.
# They are intentionally wider than the observed 5th-95th percentile range.
LENGTH_RATIO_BOUNDS = {
    "en->zh": {"min": 0.70, "max": 2.60, "min_source_units": 8},
    "en->yue": {"min": 0.70, "max": 2.80, "min_source_units": 6},
    "zh->en": {"min": 0.35, "max": 1.45, "min_source_units": 12},
    "yue->en": {"min": 0.35, "max": 1.45, "min_source_units": 6},
}


def derive_length_ratio_bounds(
    pairs: list[tuple[str, str]],
    direction: str,
    *,
    min_pairs: int = 10,
) -> dict:
    """Summarize reference ratios and return the corpus-calibrated guardrails.

    Ratios use the same direction-aware units as ``check_length_ratio``.
    The selected limits widen the observed 5th/95th percentile tails and are
    first-pass anomaly screens, not semantic adequacy thresholds.
    """
    usable = []
    for source, translation in pairs:
        if not source.strip() or not translation.strip():
            continue
        source_units, output_units = _length_units(source, translation, direction)
        if source_units > 0 and output_units > 0:
            usable.append((source_units, output_units, output_units / source_units))
    if len(usable) < min_pairs:
        raise ValueError(
            f"Need at least {min_pairs} usable {direction} reference pairs; got {len(usable)}"
        )

    ratios = [row[2] for row in usable]
    source_lengths = sorted(row[0] for row in usable)
    bounds = dict(LENGTH_RATIO_BOUNDS[direction])
    return {
        **bounds,
        "direction": direction,
        "pairs": len(usable),
        "p05": round(_percentile(ratios, 0.05), 3),
        "median": round(statistics.median(ratios), 3),
        "p95": round(_percentile(ratios, 0.95), 3),
        "min_source_units": source_lengths[max(0, int((len(source_lengths) - 1) * 0.05))],
        "method": "CJK characters / English words for EN->ZH/YUE; English words / CJK characters for ZH/YUE->EN",
        "threshold_rationale": "Operational bounds widened from Andromeda reference-pair P05/P95 tails; first-pass anomaly screening only.",
    }


def check_length_ratio(
    text: str, source: str, bounds: dict | None, direction: str | None = None
) -> CheckResult:
    """Flag output far shorter or longer than reference translations imply."""
    if not isinstance(bounds, dict) or "min" not in bounds or "max" not in bounds:
        raise ValueError(
            "The length_ratio check requires per-direction `length_ratio: {min, max}` bounds."
        )
    direction = direction or bounds.get("direction")
    if not direction:
        raise ValueError("The length_ratio check requires a translation direction")
    if not text.strip():
        return CheckResult("length_ratio", True, "empty output is covered by not_empty")

    source_units, output_units = _length_units(source, text, direction)
    if source_units < int(bounds.get("min_source_units", 0)) or source_units <= 0:
        return CheckResult("length_ratio", True, "source is too short for the calibrated bounds")

    ratio = output_units / source_units
    low, high = float(bounds["min"]), float(bounds["max"])
    if low <= ratio <= high:
        return CheckResult("length_ratio", True, f"length ratio {ratio:.2f} is within bounds")
    side = "shorter" if ratio < low else "longer"
    return CheckResult(
        "length_ratio", False,
        f"output is far {side} than the source implies: ratio {ratio:.2f}, allowed {low:.2f} to {high:.2f}",
        evidence=[f"{output_units} output units for {source_units} source units ({direction})"],
    )


# Every check the pipeline knows how to run, by the name a language
# config uses to request it. Adding a check means adding an entry here
# and naming it in a config — never editing a language's code path,
# because there isn't one.
#
# Each entry takes the output, the source and the language config. Most
# ignore the config; the ones that need a per-language setting read it
# from there, so a threshold is never a constant in this file.
CHECK_REGISTRY = {
    "not_empty": lambda text, source, config: check_not_empty(text),
    "not_source_copy": lambda text, source, config: check_not_source_copy(text, source),
    "simplified_script": lambda text, source, config: check_simplified_script(text),
    "traditional_script": lambda text, source, config: check_traditional_script(text),
    "no_cantonese_markers": lambda text, source, config: check_no_cantonese_markers(text),
    "no_residual_latin": lambda text, source, config: check_no_residual_latin(text, source),
    "pinyin": lambda text, source, config: check_pinyin(
        text, source, allowed_latin_terms=config.get("allowed_latin_terms")
    ),
    "numbers_preserved": lambda text, source, config: check_numbers_preserved(text, source),
    "not_truncated": lambda text, source, config: check_not_truncated(text, source),
    "no_degeneration": lambda text, source, config: check_no_degeneration(text),
    "cjk_punctuation": lambda text, source, config: check_cjk_punctuation(text),
    "target_script": lambda text, source, config: check_target_script(
        text, source, config.get("target_script")
    ),
    "no_residual_cjk": lambda text, source, config: check_no_residual_cjk(text),
    "no_fullwidth_punctuation": lambda text, source, config: check_no_fullwidth_punctuation(text),
    "length_ratio": lambda text, source, config: check_length_ratio(
        text, source, config.get("length_ratio"), config.get("direction")
    ),
}

# Applied to every language whether or not its config asks. An empty
# output and a copied source are failures in any language.
UNIVERSAL_CHECKS = ("not_empty", "not_source_copy")


def run_checks(text: str, source: str, config: dict) -> CheckReport:
    """
    Run the checks a language's config asks for, plus the universal ones.

    Which checks apply is a property of the target language, so it lives
    in that language's config rather than in a branch here. A config
    naming an unknown check fails loudly: silently skipping a check
    someone believed was running is exactly how a detection gap goes
    unnoticed.
    """
    requested = list(config.get("output_checks") or [])
    names = list(UNIVERSAL_CHECKS) + [n for n in requested if n not in UNIVERSAL_CHECKS]

    unknown = [n for n in names if n not in CHECK_REGISTRY]
    if unknown:
        raise ValueError(
            f"Unknown output_checks {unknown} in language config; "
            f"available: {sorted(CHECK_REGISTRY)}"
        )

    return CheckReport([CHECK_REGISTRY[name](text, source, config) for name in names])