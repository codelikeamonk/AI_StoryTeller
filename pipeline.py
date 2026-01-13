import json
import re
from typing import Any, Dict, List, Tuple
from prompts import (
    build_story_prompt,
    build_judge_prompt,
    build_revision_prompt,
    build_user_feedback_revision_prompt,
)
from llm import call_model
from prompts import build_story_prompt, build_judge_prompt, build_revision_prompt


def _extract_json_loose(text: str) -> Dict[str, Any]:
    """
    Parse JSON from a model response, even if it includes accidental extra text.
    """
    t = text.strip()

    # Try direct JSON parse
    try:
        return json.loads(t)
    except Exception:
        pass

    # Try to locate a JSON object within the text
    match = re.search(r"\{.*\}", t, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("Could not parse judge JSON.")


def _score_summary(j: Dict[str, Any]) -> str:
    scores = j.get("scores", {})
    if not isinstance(scores, dict):
        return ""
    return ", ".join([f"{k}={v}" for k, v in scores.items()])


def generate_story_with_judge(
    user_request: str,
    *,
    max_rounds: int = 3,
    length: str = "medium",
    style: str = "calm",
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate → judge → revise loop.
    Returns: (final_story, judge_history)
    """
    judge_history: List[Dict[str, Any]] = []

    # 1) Draft
    story_prompt = build_story_prompt(user_request, length=length, style=style)
    story = call_model(story_prompt, max_tokens=1400, temperature=0.8)

    # 2) Judge + revise loop
    for _ in range(max_rounds):
        judge_prompt = build_judge_prompt(user_request, story)
        judge_raw = call_model(judge_prompt, max_tokens=600, temperature=0.0)

        try:
            judge = _extract_json_loose(judge_raw)
        except Exception:
            # Fallback: if JSON judge fails, do a conservative generic revision
            story = call_model(
                f"""
                Revise this bedtime story for ages 5-10 to better match the user's request, improve clarity,
                increase bedtime calmness, and ensure gentle safety. Keep a comforting sleep-ready ending.

                User request:
                {user_request}

                Story:
                \"\"\"{story}\"\"\"

                Output ONLY the revised story.
                """.strip(),
                max_tokens=1400,
                temperature=0.7,
            )
            continue

        judge_history.append(judge)

        if bool(judge.get("pass", False)):
            return story, judge_history

        # Revise using judge feedback
        revision_prompt = build_revision_prompt(user_request, story, judge)
        story = call_model(revision_prompt, max_tokens=1400, temperature=0.7)

    # Best-effort return
    return story, judge_history

def revise_story_with_user_feedback(
    user_request: str,
    story: str,
    user_feedback: str,
    *,
    max_rounds: int = 2,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Apply user feedback, then run judge+revise loop to maintain quality/safety.
    """
    judge_history: List[Dict[str, Any]] = []

    # First: apply user feedback directly
    fb_prompt = build_user_feedback_revision_prompt(user_request, story, user_feedback)
    story = call_model(fb_prompt, max_tokens=1400, temperature=0.7)

    # Then: judge+revise for quality/safety
    for _ in range(max_rounds):
        judge_prompt = build_judge_prompt(user_request, story)
        judge_raw = call_model(judge_prompt, max_tokens=600, temperature=0.0)

        try:
            judge = _extract_json_loose(judge_raw)
        except Exception:
            # fallback: one generic calming revision
            story = call_model(
                f"""
                Revise this bedtime story for ages 5-10 to improve clarity, bedtime calmness,
                and ensure gentle safety. Keep a comforting sleep-ready ending.

                User request:
                {user_request}

                Story:
                \"\"\"{story}\"\"\"

                Output ONLY the revised story.
                """.strip(),
                max_tokens=1400,
                temperature=0.7,
            )
            continue

        judge_history.append(judge)
        if bool(judge.get("pass", False)):
            return story, judge_history

        revision_prompt = build_revision_prompt(user_request, story, judge)
        story = call_model(revision_prompt, max_tokens=1400, temperature=0.7)

    return story, judge_history

def format_judge_debug(judge_history: List[Dict[str, Any]]) -> str:
    """
    Helper to print a short debug summary.
    """
    if not judge_history:
        return "No judge history."
    last = judge_history[-1]
    return f"pass={last.get('pass')} | scores: {_score_summary(last)} | issues: {last.get('issues', [])}"
