"""
Flask app for the AI-vs-human text classification API.

Submission flow (per architecture diagram):
    POST /submit -> LLM signal -> Stylometric signal -> Confidence scoring
                 -> Transparency label -> Audit log -> Response

Status: Both signals (LLM classification + stylometric heuristics) are
wired in, combined via majority vote, and every submission writes a
structured entry to the audit log including both signals' individual
scores alongside the combined confidence.
"""

import uuid
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from llm_classification_signal import llm_classification_signal
from stylometric_signal import stylometric_signal
from scoring import combine_signals
import audit_log

app = Flask(__name__)

# Rate limiting on /submit. Limits chosen to comfortably cover a single
# writer checking multiple drafts/paragraphs in one sitting, while capping
# sustained automated flooding from a single IP. See README for reasoning.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    """
    Accepts a JSON body with at minimum:
        - text: str         (the content to be assessed)
        - creator_id: str   (identifier of the submitter)

    Runs both detection signals, combines them via majority vote, writes a
    record to the audit log keyed by a freshly generated content_id, and
    returns:
        - content_id: unique ID for this submission (needed for /appeal)
        - attribution: combined transparency label ("likely_ai" |
          "uncertain" | "likely_human")
        - confidence: combined majority-vote score (0.0 / 0.5 / 1.0)
        - llm_score: signal 1's own self-reported confidence
        - stylometric_score: signal 2's combined heuristic score
        - votes: each signal's individual binary vote
    """
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text or not creator_id:
        return jsonify(
            {"error": "Both 'text' and 'creator_id' are required fields"}
        ), 400

    content_id = str(uuid.uuid4())

    try:
        llm_result = llm_classification_signal(text)
    except Exception as e:
        # Signal failure shouldn't crash the endpoint — surface it clearly
        # instead.
        return jsonify({
            "content_id": content_id,
            "error": f"llm_classification_signal failed: {e}"
        }), 502

    # Stylometric signal is pure Python — no external call, no failure mode
    # worth catching the way the LLM call's network/API failures are.
    stylo_result = stylometric_signal(text)

    combined = combine_signals(llm_result, stylo_result)
    attribution = combined["label"]                  # "likely_ai" | "uncertain" | "likely_human"
    label_text = combined["transparency_label"]       # exact user-facing wording per spec
    confidence = combined["confidence"]               # 0.0 / 0.5 / 1.0 (majority vote of 2 signals)
    llm_score = llm_result["confidence"]               # signal 1's own self-reported confidence
    stylometric_score = stylo_result["score"]          # signal 2's combined heuristic score

    audit_log.create_entry(
        content_id=content_id,
        creator_id=creator_id,
        text=text,
        attribution=attribution,
        transparency_label=label_text,
        confidence=confidence,
        llm_score=llm_score,
        stylometric_score=stylometric_score,
        votes=combined["votes"],
        status="classified",
    )

    return jsonify({
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "label": label_text,
        "confidence": confidence,
        "llm_score": llm_score,
        "stylometric_score": stylometric_score,
        "votes": combined["votes"],
        "signal_detail": {
            "llm_classification": llm_result,
            "stylometric_heuristics": stylo_result,
        },
    }), 200


@app.route("/log", methods=["GET"])
def log():
    """
    Returns the most recent audit log entries as JSON.

    No auth — intentionally open for documentation/grading visibility per
    spec. A real deployment would lock this down.

    Optional query param: ?limit=N (default 20).
    """
    limit = request.args.get("limit", default=20, type=int)
    return jsonify({"entries": audit_log.get_log(limit=limit)})


# Appeal flow, per the architecture diagram: status update + audit log
# entry, alongside the original classification decision. No automated
# re-classification — that's an explicit non-goal per spec.
@app.route("/appeal", methods=["POST"])
def appeal():
    """
    Accepts a JSON body with:
        - content_id: str        (from a prior /submit response)
        - creator_reasoning: str  (why the creator believes the label is wrong)

    Updates the existing audit log entry's status to "under_review" and
    records the appeal reasoning + timestamp alongside the original
    classification decision (the entry is updated in place, not replaced).
    """
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning")

    if not content_id or not creator_reasoning:
        return jsonify(
            {"error": "Both 'content_id' and 'creator_reasoning' are required fields"}
        ), 400

    existing = audit_log.get_entry(content_id)
    if existing is None:
        return jsonify({"error": f"No submission found for content_id '{content_id}'"}), 404

    updated_entry = audit_log.file_appeal(
        content_id=content_id,
        appeal_reasoning=creator_reasoning,
    )

    return jsonify({
        "content_id": content_id,
        "status": updated_entry["status"],
        "message": "Appeal received and logged for review.",
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)