"""
Lyrics → music parameter suggestions.
No LLM. Uses:
  - NRC Emotion Lexicon (direct JSON, no NLTK/TextBlob dependency)
  - VADER (rule-based sentiment) for valence/arousal
  - pronouncing (CMU dict) for syllable count + stress patterns
  - plain heuristics for line density and repetition
"""
import re
import json
import random
import hashlib
from collections import Counter
from pathlib import Path

# ── NRC lexicon — direct load, no TextBlob/NLTK needed ───────────────────────
def _find_nrc_json() -> Path | None:
    import sys
    # frozen bundle: PyInstaller places datas at _MEIPASS/nrclex/data/nrc_en.json
    if getattr(sys, "frozen", False):
        p = Path(sys._MEIPASS) / "nrclex" / "data" / "nrc_en.json"
        return p if p.exists() else None
    # dev mode: search .venv
    for p in Path(__file__).parents:
        cand = p / ".venv" / "lib"
        if cand.exists():
            hits = list(cand.rglob("nrc_en.json"))
            if hits:
                return hits[0]
    return None

_NRC: dict = {}
_nrc_path = _find_nrc_json()
if _nrc_path:
    try:
        with open(_nrc_path, encoding="utf-8") as _f:
            _NRC = json.load(_f)  # {word: [emotion, ...]}
    except Exception:
        pass

HAS_NRC = bool(_NRC)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
    HAS_VADER = True
except Exception:
    HAS_VADER = False

try:
    import pronouncing
    # force-load the CMU dict now so we know immediately if the data file is missing
    pronouncing.phones_for_word("test")
    HAS_PRONOUNCING = True
except Exception:
    HAS_PRONOUNCING = False


# ── emotion → parameter mapping tables ───────────────────────────────────────

_EMOTION_TO_MODE = {
    "fear":         "Phrygian — dark, tense, minor ♭2",
    "sadness":      "Aeolian — natural minor (melancholic base)",
    "anger":        "Phrygian Dominant / Hijaz — Armenian, alien, flamenco",
    "disgust":      "Locrian — tritone root, maximum instability",
    "trust":        "Dorian — minor raised 6th (jazzy, hopeful shadow)",
    "joy":          "Mixolydian — major flat 7 (blues / vaporwave warmth)",
    "anticipation": "Dorian — minor raised 6th (jazzy, hopeful shadow)",
    "surprise":     "Double Harmonic / Byzantine — two augmented 2nds",
}

_EMOTION_TO_MOOD = {
    "fear":         "cold / electronic",
    "sadness":      "nostalgic / melancholic",
    "anger":        "dark / heavy",
    "disgust":      "dark / heavy",
    "trust":        "dreamy / dissociated",
    "joy":          "euphoric / hollow",
    "anticipation": "dreamy / dissociated",
    "surprise":     "lo-fi / hazed",
}

_AROUSAL_TO_TEMPO = {
    # (high-arousal=True, valence_positive=True/False)
    (True,  True):  "Drive (100–130 BPM) — post-punk energy",
    (True,  False): "Aggro (140–180 BPM) — industrial / metal",
    (False, True):  "Walk (80–100 BPM) — lo-fi groove",
    (False, False): "Drift (60–80 BPM) — slowed vaporwave core",
}

_DENSITY_TO_SYNCOPATION = {
    "high":   "Heavy",
    "medium": "Moderate",
    "low":    "Light — occasional off-beat",
}

_DENSITY_TO_PHRASING = {
    "high":   "Syllabic — one note per syllable",
    "medium": "Syllabic — one note per syllable",
    "low":    "Sparse — lots of space between phrases",
}


# ── public API ────────────────────────────────────────────────────────────────

def analyze(lyrics: str) -> dict:
    """Return a dict of suggested wizard answers keyed by STEPS key names."""
    if not lyrics.strip():
        return _random_spec(seed=None)

    suggestions = {}

    emotions  = _detect_emotions(lyrics)
    valence   = _detect_valence(lyrics)
    arousal   = _detect_arousal(lyrics)
    density   = _syllable_density(lyrics)
    lines     = [l.strip() for l in lyrics.splitlines() if l.strip()]
    rep_ratio = _repetition_ratio(lines)

    dominant_emo = emotions[0][0] if emotions else "sadness"

    suggestions["mood"]    = _EMOTION_TO_MOOD.get(dominant_emo, "nostalgic / melancholic")
    suggestions["mode"]    = _EMOTION_TO_MODE.get(dominant_emo, "Aeolian — natural minor (melancholic base)")
    suggestions["tempo_range"] = _AROUSAL_TO_TEMPO.get((arousal, valence > 0),
                                  "Drift (60–80 BPM) — slowed vaporwave core")
    suggestions["syncopation"] = _DENSITY_TO_SYNCOPATION.get(density, "Light — occasional off-beat")
    suggestions["phrasing_density"] = _DENSITY_TO_PHRASING.get(density, "Syllabic — one note per syllable")

    # high repetition → chorus structure
    if rep_ratio > 0.35:
        suggestions["structure"] = "Intro → Verse → Chorus → Bridge → Chorus → Outro"
    elif rep_ratio < 0.1:
        suggestions["structure"] = "Minimal: Intro → Part A → Part B → Outro"

    # dark/angry → more distortion and compression
    if dominant_emo in ("anger", "fear", "disgust"):
        suggestions["guitar_texture"]   = "Heavy distorted"
        suggestions["compression"]      = "Punchy — transient-heavy"
        suggestions["mix_density"]      = "Lush and layered"
        suggestions["reverb_amount"]    = "Hall — spacious"
        suggestions["synth_char"]       = "Cold digital"
    elif dominant_emo in ("sadness", "trust"):
        suggestions["guitar_texture"]   = "Angular single-note (post-punk)"
        suggestions["reverb_amount"]    = "Wash — ambient high wet (shoegaze / vapor)"
        suggestions["synth_char"]       = "Detuned / detached (vaporwave classic)"
        suggestions["atmo_fx"]          = "Vinyl crackle (lo-fi / vaporwave)"
    elif dominant_emo in ("joy", "anticipation"):
        suggestions["guitar_texture"]   = "Arpeggiated clean"
        suggestions["reverb_amount"]    = "Room — subtle space"
        suggestions["synth_char"]       = "FM bell / electric piano (vaporwave warmth)"

    # fill remaining with seeded random to keep it coherent
    suggestions.update(_random_spec(seed=_lyrics_seed(lyrics), skip=set(suggestions.keys())))

    return suggestions


def _random_spec(seed=None, skip: set = None) -> dict:
    """Seeded-random spec for all STEPS not already in skip."""
    # lazy import to avoid circular
    from wizard.steps import STEPS
    skip = skip or set()
    rng  = random.Random(seed)
    return {
        s["key"]: rng.choice(s["options"])
        for s in STEPS
        if s["key"] not in skip
    }


# ── analysis helpers ──────────────────────────────────────────────────────────

def _detect_emotions(lyrics: str) -> list:
    words = re.findall(r"[a-z']+", lyrics.lower())
    counts: dict = {}
    for w in words:
        for emo in _NRC.get(w, []):
            if emo not in ("positive", "negative"):
                counts[emo] = counts.get(emo, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


def _detect_valence(lyrics: str) -> float:
    if HAS_VADER:
        return _vader.polarity_scores(lyrics)["compound"]
    # fallback: count positive/negative words via NRC
    if HAS_NRC:
        nrc = NRCLex(lyrics)
        freq = nrc.affect_frequencies
        return freq.get("positive", 0) - freq.get("negative", 0)
    return -0.3


def _detect_arousal(lyrics: str) -> bool:
    """True = high arousal (energetic). Estimated from word density + punctuation."""
    words = lyrics.split()
    if not words:
        return False
    excl_ratio  = lyrics.count("!") / max(len(words), 1)
    cap_ratio   = sum(1 for w in words if w.isupper()) / max(len(words), 1)
    short_lines = sum(1 for l in lyrics.splitlines() if 1 <= len(l.strip().split()) <= 4)
    total_lines = max(len([l for l in lyrics.splitlines() if l.strip()]), 1)
    score = excl_ratio * 3 + cap_ratio * 2 + (short_lines / total_lines) * 1
    return score > 0.3


def _syllable_density(lyrics: str) -> str:
    """high / medium / low based on syllables-per-line average."""
    lines = [l.strip() for l in lyrics.splitlines() if l.strip()]
    if not lines:
        return "medium"
    if HAS_PRONOUNCING:
        totals = []
        for line in lines:
            syl = sum(
                len(pronouncing.phones_for_word(w))
                for w in re.findall(r"[a-z']+", line.lower())
                if pronouncing.phones_for_word(w)
            ) or len(line.split())
            totals.append(syl)
        avg = sum(totals) / len(totals)
    else:
        avg = sum(len(l.split()) for l in lines) / len(lines)

    if avg >= 9:
        return "high"
    if avg >= 5:
        return "medium"
    return "low"


def _repetition_ratio(lines: list) -> float:
    if not lines:
        return 0.0
    counts = Counter(l.lower() for l in lines)
    repeated = sum(v for v in counts.values() if v > 1)
    return repeated / len(lines)


def _lyrics_seed(lyrics: str) -> int:
    return int(hashlib.md5(lyrics.encode()).hexdigest(), 16) % (2 ** 32)
