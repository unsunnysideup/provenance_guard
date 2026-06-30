"""
Confidence scoring: combines signal 1 (LLM classification) and signal 2
(stylometric heuristics) via majority vote, per the spec:

    "I'll combine these two detection signals into a confidence score
    through majority vote. Essentially, each signal will vote on a label,
    and the confidence score will be the proportion of votes for human
    label."

Transparency label thresholds (per spec):
    Likely AI:     0.0  - 0.40
    Uncertain:     0.41 - 0.60
    Likely Human:  0.61 - 1.0

Note: with exactly 2 binary-vote signals, there are only three possible
outcomes — 0/2 = 0.0, 1/2 = 0.5, or 2/2 = 1.0 — which map cleanly onto the
three label buckets above. A 1/2 split lands at 0.5, which falls inside
the "Uncertain" band — matching the spec's own example ("a confidence
score of 0.6 means uncertain") almost exactly: whenever the two signals
disagree, the system calls it uncertain rather than picking a side.
"""

LIKELY_AI_MAX = 0.40
UNCERTAIN_MAX = 0.60

# Exact wording from the Transparency Label Design section of the spec.
# Do not reword these — the spec calls these out as the literal text to
# return to the user.
TRANSPARENCY_LABELS = {
    "likely_ai": "This text is likely to be written by AI",
    "likely_human": "This text is likely to be written by human",
    "uncertain": "I am unable to determine whether this text is written by a human or an AI.",
}


def label_from_confidence(confidence):
    """Map a 0-1 confidence score to one of the three label *codes*
    ("likely_ai" | "uncertain" | "likely_human") — used internally and in
    the audit log's "attribution" field."""
    if confidence <= LIKELY_AI_MAX:
        return "likely_ai"
    elif confidence <= UNCERTAIN_MAX:
        return "uncertain"
    else:
        return "likely_human"


def transparency_label(confidence):
    """Map a 0-1 confidence score directly to the user-facing transparency
    label *text*, per the spec's exact wording. This is what /submit
    should return to the caller — not the internal code."""
    code = label_from_confidence(confidence)
    return TRANSPARENCY_LABELS[code]


def combine_signals(llm_result, stylometric_result):
    """
    Combine signal 1 and signal 2 outputs into a final confidence score
    and transparency label via majority vote.

    Args:
        llm_result: dict returned by llm_classification_signal() — must
            have a "label" key ("human" or "ai").
        stylometric_result: dict returned by stylometric_signal() — must
            have a "label" key ("human" or "ai").

    Returns:
        dict with:
            - confidence: proportion of votes for "human" (0.0, 0.5, or 1.0)
            - label: "likely_ai" | "uncertain" | "likely_human"  (code)
            - transparency_label: user-facing label text, per spec wording
            - votes: the individual signal votes, for transparency/audit
    """
    votes = {
        "llm_classification": llm_result["label"],
        "stylometric_heuristics": stylometric_result["label"],
    }

    human_votes = sum(1 for v in votes.values() if v == "human")
    confidence = human_votes / len(votes)
    label = label_from_confidence(confidence)

    return {
        "confidence": confidence,
        "label": label,
        "transparency_label": TRANSPARENCY_LABELS[label],
        "votes": votes,
    }