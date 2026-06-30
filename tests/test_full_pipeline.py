"""
End-to-end test: runs BOTH signals + the confidence scorer on the four
spec test inputs. Requires GROQ_API_KEY (signal 1 calls Groq for real;
signal 2 is pure Python and always works).

Usage:
    python test_full_pipeline.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from llm_classification_signal import llm_classification_signal
from stylometric_signal import stylometric_signal
from scoring import combine_signals

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
        print(f"\n=== {case['name']} ===")
        try:
            llm_result = llm_classification_signal(case["text"])
        except Exception as e:
            print(f"  LLM signal failed: {e}")
            continue

        stylo_result = stylometric_signal(case["text"])
        combined = combine_signals(llm_result, stylo_result)

        print(f"  LLM vote:         {llm_result['label']} (confidence {llm_result['confidence']})")
        print(f"  Stylometric vote: {stylo_result['label']} (score {stylo_result['score']})")
        print(f"  => confidence:    {combined['confidence']}")
        print(f"  => label:         {combined['label']}")


if __name__ == "__main__":
    run_tests()
