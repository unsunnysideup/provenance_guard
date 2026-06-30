"""
Test combine_signals() against all three possible vote outcomes, using
mocked signal outputs (no API key needed — this isolates the scoring
logic itself from whether Groq is reachable).

For an end-to-end test with the *real* LLM signal, see
test_full_pipeline.py instead (requires GROQ_API_KEY).

Usage:
    python test_scoring.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from scoring import combine_signals

def mock_signal(label):
    return {"label": label}

CASES = [
    ("both_say_ai", mock_signal("ai"), mock_signal("ai")),         # 0/2 -> likely_ai
    ("signals_disagree", mock_signal("ai"), mock_signal("human")), # 1/2 -> uncertain
    ("both_say_human", mock_signal("human"), mock_signal("human")), # 2/2 -> likely_human
]

def run_tests():
    for name, llm_result, stylo_result in CASES:
        result = combine_signals(llm_result, stylo_result)
        print(f"{name:20s} confidence={result['confidence']}  label={result['label']}  votes={result['votes']}")

if __name__ == "__main__":
    run_tests()
