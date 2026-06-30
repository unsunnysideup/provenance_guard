"""
Standalone tests for llm_classification_signal — run this directly to sanity
check the signal BEFORE wiring it into the /submit endpoint.

Usage:
    export GROQ_API_KEY=your_key_here
    python test_signals.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from llm_classification_signal import llm_classification_signal

TEST_CASES = [
    {
        "name": "likely_ai_generic",
        "text": (
            "In today's fast-paced world, it is important to recognize the "
            "significance of effective communication. Whether in personal "
            "relationships or professional settings, clear communication "
            "fosters understanding and collaboration. By actively listening "
            "and articulating thoughts clearly, individuals can build "
            "stronger connections and achieve their goals."
        ),
    },
    {
        "name": "likely_human_informal",
        "text": (
            "ok so i tried to fix the bug for like 3 hours last night and "
            "turns out it was just a missing semicolon lol. classic. "
            "anyway i'm exhausted, going to grab coffee before the standup, "
            "someone please tell me the deploy didn't break prod again"
        ),
    },
    {
        "name": "ambiguous_short",
        "text": "The weather was nice yesterday so we went for a walk.",
    },
]


def run_tests():
    for case in TEST_CASES:
        print(f"\n=== {case['name']} ===")
        print(f"Input: {case['text'][:80]}...")
        try:
            result = llm_classification_signal(case["text"])
            print(f"Label:     {result['label']}")
            print(f"Rationale: {result['rationale']}")
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    run_tests()
