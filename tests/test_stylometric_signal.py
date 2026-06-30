"""
Standalone tests for stylometric_signal() — run directly, no API key needed
(unlike test_signals.py, this signal is pure Python).

Usage:
    python test_stylometric_signal.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from stylometric_signal import stylometric_signal

TEST_CASES = [
    {
        "name": "clearly_ai_generated",
        "text": (
            "Artificial intelligence represents a transformative paradigm shift in modern society. "
            "It is important to note that while the benefits of AI are numerous, it is equally "
            "essential to consider the ethical implications. Furthermore, stakeholders across "
            "various sectors must collaborate to ensure responsible deployment."
        ),
    },
    {
        "name": "clearly_human_casual",
        "text": (
            "ok so i finally tried that new ramen place downtown and honestly? "
            "underwhelming. the broth was fine but they put WAY too much sodium in it and "
            "i was thirsty for like three hours after. my friend got the spicy version and "
            "said it was better. probably won't go back unless someone drags me there"
        ),
    },
    {
        "name": "borderline_formal_human",
        "text": (
            "The relationship between monetary policy and asset price inflation has been "
            "extensively studied in the literature. Central banks face a fundamental tension "
            "between their mandate for price stability and the unintended consequences of "
            "prolonged low interest rates on equity and real estate valuations."
        ),
    },
    {
        "name": "borderline_lightly_edited_ai",
        "text": (
            "I've been thinking a lot about remote work lately. There are genuine tradeoffs — "
            "flexibility and no commute on one side, isolation and blurred work-life boundaries "
            "on the other. Studies show productivity varies widely by individual and role type."
        ),
    },
]


def run_tests():
    for case in TEST_CASES:
        result = stylometric_signal(case["text"])
        print(f"\n=== {case['name']} ===")
        print(f"Vote:       {result['label']}")
        print(f"Score:      {result['score']}")
        print(f"Metrics:    {result['metrics']}")
        print(f"Normalized: {result['normalized']}")


if __name__ == "__main__":
    run_tests()
