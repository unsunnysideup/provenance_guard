"""
Detection Signal #2: Stylometric heuristics (pure Python, no external API).

Computes three metrics per the spec, normalizes each into a 0-1
"human-likeness" component, combines them into a single score, and casts
a binary vote ("human" or "ai") by thresholding that score at 0.5 — the
same kind of binary vote signal 1 produces, so the two can be combined via
majority vote per the spec.

Metrics (direction: higher score = more human-like):
    1. Sentence length variance — AI text tends toward uniform sentence
       length; human text varies more. Higher variance -> more human-like.
    2. Average sentence complexity — sentence length plus clause-connector
       density (commas, subordinating conjunctions like "while"/"because",
       and formal connectives like "furthermore"/"however"). Higher
       complexity -> more AI-like (the hedging, multi-clause "It is
       important to note that... it is equally essential to..." pattern).
       So this metric's normalized contribution is INVERTED relative to
       the other two: higher complexity -> LOWER human-likeness.
    3. Punctuation density — punctuation marks per word. The weakest/
       noisiest of the three metrics, given the lowest weight.

WHY THIS REPLACED TYPE-TOKEN RATIO:
An earlier version used type-token ratio (vocabulary diversity) instead of
sentence complexity. On short inputs (40-60 words), TTR is naturally high
for *any* text regardless of origin — there isn't enough length for words
to repeat yet — so it had almost no discriminating power and, in testing,
caused a textbook AI-generated paragraph to incorrectly vote "human"
(TTR alone said 0.88, dragging the combined score above the 0.5 threshold
despite the text being full of AI-style hedging language). Average
sentence complexity catches that hedging pattern directly. On the same
test paragraph, this single change flipped the vote from "human" (0.647)
to the correct "ai" (0.382) — see test_stylometric_signal.py.

KNOWN LIMITATION OF THIS METRIC (documented, not hidden):
The clause-connector word list is a fixed heuristic set, not real parsing.
It under-counts complexity in long sentences that pack in compound noun
phrases without using commas or connector words (e.g. dense academic
prose like "...face a fundamental tension between their mandate for price
stability and the unintended consequences of prolonged low interest
rates..."). That's why sentence length (word count) is also folded into
this metric, not just connector words alone — length alone catches what
connector-counting misses, partially.
"""

import re
import statistics

# Subordinating conjunctions, relative pronouns, and formal connective
# words/phrases associated with multi-clause, hedging sentence structure.
_CLAUSE_MARKERS = {
    "because", "although", "though", "while", "since", "whereas", "unless",
    "if", "when", "whenever", "after", "before", "until", "that", "which",
    "who", "whom", "whose", "as", "given", "furthermore", "moreover",
    "however", "therefore", "thus", "consequently", "nonetheless",
    "nevertheless", "additionally",
}


def _split_sentences(text):
    """Naive sentence splitter on . ! ? boundaries."""
    text = text.replace("\n", " ")
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _word_tokens(text):
    """Lowercased word tokens, stripping punctuation."""
    return re.findall(r"[A-Za-z']+", text.lower())


def _punctuation_chars(text):
    return re.findall(r"[.,!?;:\-—']", text)


def compute_sentence_length_variance(text):
    """Population variance of sentence lengths, measured in words."""
    sentences = _split_sentences(text)
    lengths = [len(_word_tokens(s)) for s in sentences]
    if len(lengths) < 2:
        return 0.0
    return statistics.pvariance(lengths)


def _sentence_complexity(sentence):
    """Complexity score for one sentence: word count (scaled down) plus
    a +1 per comma and +1 per clause-marker word."""
    words = _word_tokens(sentence)
    word_count = len(words)
    commas = sentence.count(",")
    marker_hits = sum(1 for w in words if w in _CLAUSE_MARKERS)
    return (word_count / 8.0) + commas + marker_hits


def compute_average_sentence_complexity(text):
    """Mean per-sentence complexity score across the whole text.
    Returns 0.0 for empty input."""
    sentences = _split_sentences(text)
    if not sentences:
        return 0.0
    return statistics.mean(_sentence_complexity(s) for s in sentences)


def compute_punctuation_density(text):
    """Punctuation marks per word. Returns 0.0 for empty input."""
    words = _word_tokens(text)
    if not words:
        return 0.0
    return len(_punctuation_chars(text)) / len(words)


def _normalize_variance(variance, scale=40.0):
    """Map variance to 0-1; scale chosen so typical short-prose variance
    (roughly 20-50 for 2-5 sentence samples) spans most of the range."""
    return min(variance / scale, 1.0)


def _normalize_complexity_to_human_likeness(avg_complexity, low=1.5, high=4.0):
    """Map average complexity to a 0-1 HUMAN-LIKENESS score (inverted:
    higher complexity -> lower human-likeness). `low`/`high` bracket the
    range seen across casual-to-formal/AI prose in calibration testing."""
    normalized = max(0.0, min((avg_complexity - low) / (high - low), 1.0))
    return 1.0 - normalized


def _normalize_punctuation(density, center=0.10, band=0.04, scale=0.12):
    """Punctuation density near `center` (typical clean/formal prose) is
    treated as more AI-like; density that deviates substantially in
    either direction (very sparse or very heavy use) is treated as more
    human-like/idiosyncratic. `band` is a tolerance zone around the
    center where deviation doesn't count yet."""
    deviation = max(0.0, abs(density - center) - band)
    return min(deviation / scale, 1.0)


def stylometric_signal(text, weights=(0.3, 0.6, 0.1)):
    """
    Run the stylometric heuristics signal on a piece of text.

    Args:
        text: the text to assess.
        weights: (variance_weight, complexity_weight, punctuation_weight)
            — must sum to 1.0.

    Returns:
        dict with:
            - signal: "stylometric_heuristics"
            - label: "human" or "ai"  (the binary vote, for majority vote)
            - score: combined 0-1 human-likeness score
            - metrics: raw metric values (variance, avg_sentence_complexity,
              punctuation_density)
            - normalized: each metric's normalized 0-1 human-likeness
              component (complexity is already inverted before this point)
    """
    variance = compute_sentence_length_variance(text)
    avg_complexity = compute_average_sentence_complexity(text)
    punct_density = compute_punctuation_density(text)

    norm_variance = _normalize_variance(variance)
    norm_complexity_human = _normalize_complexity_to_human_likeness(avg_complexity)
    norm_punct = _normalize_punctuation(punct_density)

    w_var, w_complexity, w_punct = weights
    score = (
        (w_var * norm_variance)
        + (w_complexity * norm_complexity_human)
        + (w_punct * norm_punct)
    )

    label = "human" if score >= 0.5 else "ai"

    return {
        "signal": "stylometric_heuristics",
        "label": label,
        "score": round(score, 4),
        "metrics": {
            "sentence_length_variance": round(variance, 4),
            "average_sentence_complexity": round(avg_complexity, 4),
            "punctuation_density": round(punct_density, 4),
        },
        "normalized": {
            "sentence_length_variance": round(norm_variance, 4),
            "average_sentence_complexity_human_likeness": round(norm_complexity_human, 4),
            "punctuation_density": round(norm_punct, 4),
        },
    }