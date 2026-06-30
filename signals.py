"""
Detection Signal #1: LLM-based classification (Groq)

Per the spec, this signal asks a model to assess whether a piece of text
reads as human- or AI-generated, capturing semantic/stylistic coherence
holistically. It outputs a single binary flag: "human" or "ai".

This file is meant to be testable on its own (see test_signals.py) before
being wired into the /submit endpoint.
"""

import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # reads .env in the current working directory into os.environ

_client = None


def _get_client():
    """Lazily create the Groq client so importing this module doesn't
    require an API key to be present (useful for unit tests that mock
    this function)."""
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is not set. "
                "Get a key from https://console.groq.com and set it before "
                "calling llm_classification_signal()."
            )
        _client = Groq(api_key=api_key)
    return _client


SYSTEM_PROMPT = """You are a text-provenance classifier. Given a passage of \
text, assess whether it reads as HUMAN-written or AI-generated.

Consider holistic semantic and stylistic coherence: things like overly \
uniform sentence construction, generic phrasing, hedging patterns, lack of \
idiosyncratic voice, or unnaturally tidy structure are signs of AI-generated \
text. Idiosyncrasies, inconsistencies, informal asides, and uneven pacing \
are signs of human-written text.

Respond ONLY with a JSON object in exactly this shape, no extra text:
{
  "label": "human" | "ai",
  "confidence": <float between 0.0 and 1.0, how confident you are in label>,
  "rationale": "<one or two sentence justification>"
}
"""


def llm_classification_signal(text, model="llama-3.3-70b-versatile"):
    """
    Run the LLM-based classification signal on a piece of text.

    Args:
        text: the text to assess.
        model: Groq model id to use.

    Returns:
        dict with:
            - signal: "llm_classification"
            - label: "human" or "ai"   (the binary flag per spec)
            - rationale: short model-provided justification
            - raw_response: full parsed JSON from the model

    Raises:
        RuntimeError: if GROQ_API_KEY isn't set.
        ValueError: if the model response isn't valid JSON or doesn't
            contain a recognizable label.
    """
    client = _get_client()

    user_prompt = f'Text to assess:\n"""\n{text}\n"""'

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw_content = response.choices[0].message.content

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {raw_content!r}") from e

    label = parsed.get("label")
    if label not in ("human", "ai"):
        raise ValueError(f"Unexpected or missing label from model: {label!r}")

    confidence = parsed.get("confidence")
    if not isinstance(confidence, (int, float)):
        raise ValueError(f"Missing or non-numeric confidence from model: {confidence!r}")
    confidence = float(confidence)
    # Be lenient if the model returns a 0-100 scale instead of 0-1.
    if confidence > 1.0:
        confidence = confidence / 100.0
    confidence = max(0.0, min(1.0, confidence))

    return {
        "signal": "llm_classification",
        "label": label,
        "confidence": confidence,
        "rationale": parsed.get("rationale"),
        "raw_response": parsed,
    }