"""
Flask app for the AI-vs-human text classification API.

Submission flow (per architecture diagram):
    POST /submit -> LLM signal -> Stylometric signal -> Confidence scoring
                 -> Transparency label -> Audit log -> Response

Status: LLM classification signal (Groq) is wired in and every submission
writes a structured entry to the audit log. Stylometric signal and real
majority-vote confidence scoring are not yet implemented — confidence is
currently just signal 1's own score.
"""

import uuid

from flask import Flask, request, jsonify

from signals import llm_classification_signal
import audit_log

app = Flask(__name__)


@app.route("/submit", methods=["POST"])
def submit():
    """
    Accepts a JSON body with at minimum:
        - text: str         (the content to be assessed)
        - creator_id: str   (identifier of the submitter)

    Runs the LLM classification signal, writes a record to the audit log
    keyed by a freshly generated content_id, and returns:
        - content_id: unique ID for this submission (needed for /appeal)
        - attribution: output of the LLM classification signal
        - confidence: placeholder until stylometric signal + majority
          vote scoring are implemented
        - label: placeholder until the above is implemented
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
        signal_result = llm_classification_signal(text)
    except Exception as e:
        # Signal failure shouldn't crash the endpoint — surface it clearly
        # instead. Once a second signal exists, a single signal failing
        # might not need to fail the whole request; revisit then.
        return jsonify({
            "content_id": content_id,
            "error": f"llm_classification_signal failed: {e}"
        }), 502

    llm_score = signal_result["confidence"]
    attribution = "likely_ai" if signal_result["label"] == "ai" else "likely_human"

    # Overall confidence is currently just signal 1's score — this becomes
    # a real majority-vote combination once the stylometric signal exists
    # (Milestone 4). Re-derive this, don't just keep it as-is, once that
    # signal is wired in.
    confidence = llm_score

    audit_log.create_entry(
        content_id=content_id,
        creator_id=creator_id,
        text=text,
        attribution=attribution,
        confidence=confidence,
        llm_score=llm_score,
        status="classified",
    )

    return jsonify({
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "signal_detail": signal_result,
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


# Placeholder for the appeal flow, per the architecture diagram.
# Not implemented yet — included so the route map matches the contract.
@app.route("/appeal", methods=["POST"])
def appeal():
    return jsonify({"status": "not_implemented"}), 501


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)