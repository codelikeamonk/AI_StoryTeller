from typing import Any, Dict


def build_story_prompt(
    user_request: str,
    *,
    age_min: int = 5,
    age_max: int = 10,
    length: str = "medium",
    style: str = "calm",
) -> str:
    """
    Prompt for generating an age-appropriate bedtime story with structure and safety.
    """
    length_guidance = {
        "short": "350-550 words",
        "medium": "700-1000 words",
        "long": "1100-1500 words",
    }.get(length, "700-1000 words")

    style_guidance = {
        "calm": "gentle, cozy, and bedtime-soothing",
        "funny": "lightly funny and playful (no sarcasm, no meanness)",
        "adventure": "mild adventure with low-stakes tension, never scary",
        "moral": "warm lesson (sharing, kindness, honesty) without sounding preachy",
    }.get(style, "gentle, cozy, and bedtime-soothing")

    return f"""
You are a children's bedtime story writer.

Write ONE complete bedtime story based on the user's request below.

User request:
{user_request}

Target audience:
Children ages {age_min}-{age_max}.

Hard requirements:
- Keep language simple, vivid, and easy to follow for ages {age_min}-{age_max}.
- Use a {style_guidance} tone.
- Length: {length_guidance}.
- Structure: clear beginning → middle → ending, with a satisfying positive resolution.
- Avoid: graphic violence, death, abuse, horror, intense peril, or anything that could cause nightmares.
- If conflict exists, keep it low-stakes and resolve it gently.
- End with a comforting final paragraph that helps the child feel safe and ready to sleep.
- No meta-talk (do not mention prompts, policies, or that you are an AI).

Nice-to-have:
- A few bits of dialogue.
- A small recurring cozy motif (e.g., a star, a lullaby, a warm blanket).

Output:
Only the story text. No bullet points.
""".strip()


def build_judge_prompt(user_request: str, story_text: str) -> str:
    """
    Prompt for judging story quality. Must return ONLY strict JSON.
    """
    return f"""
You are a strict quality judge for children's bedtime stories.

Evaluate the story against the user's request and the target audience (ages 5-10).

User request:
{user_request}

Story:
\"\"\"{story_text}\"\"\"

Return ONLY valid JSON (no markdown, no extra text). JSON schema:

{{
  "pass": true/false,
  "scores": {{
    "age_appropriateness": 1-5,
    "clarity": 1-5,
    "engagement": 1-5,
    "bedtime_tone": 1-5,
    "structure": 1-5,
    "request_fit": 1-5,
    "safety": 1-5
  }},
  "issues": ["short phrases describing problems"],
  "revision_instructions": [
    "specific instruction 1",
    "specific instruction 2"
  ]
}}

Guidelines:
- "safety" must be 5 only if there is no scary content, no harmful themes, and conflict is gentle.
- "bedtime_tone" should be high if it feels soothing and ends with comfort.
- "request_fit" should be high if it clearly matches the user's request details.
- Set pass=true ONLY if:
  - safety >= 5,
  - age_appropriateness >= 4,
  - request_fit >= 4,
  - and at least 4 of the remaining categories are >= 4.
- If pass=false, provide 2-6 concrete revision_instructions that would raise the score.

Return ONLY JSON.
""".strip()


def build_revision_prompt(user_request: str, story_text: str, judge_json: Dict[str, Any]) -> str:
    """
    Prompt for revising story based on judge feedback.
    """
    issues = judge_json.get("issues", [])
    instructions = judge_json.get("revision_instructions", [])

    return f"""
You are revising a children's bedtime story for ages 5-10.

User request:
{user_request}

Original story:
\"\"\"{story_text}\"\"\"

Judge feedback (issues):
{issues}

Apply these revision instructions carefully:
{instructions}

Rules:
- Keep what already works; only change what is needed.
- Maintain a gentle, bedtime-soothing tone.
- Ensure the final paragraph is comforting and sleep-ready.
- Do NOT add scary or intense elements.
- Output ONLY the revised story text (no JSON, no headings).

Revised story:
""".strip()

def build_user_feedback_revision_prompt(user_request: str, story_text: str, user_feedback: str) -> str:
    return f"""
You are revising a children's bedtime story for ages 5-10.

Original user request:
{user_request}

User feedback / change request:
{user_feedback}

Current story:
\"\"\"{story_text}\"\"\"

Revise the story to satisfy the user's feedback while keeping:
- age-appropriate language (5-10),
- gentle bedtime tone,
- safe, non-scary content,
- a comforting sleep-ready ending.

If the user's feedback conflicts with bedtime safety (e.g., scary/violent), soften it into something safe and cozy.

Output ONLY the revised story text.
""".strip()
