"""
safety_layer.py

Deterministic (non-LLM) safety layer for the Wellness RAG Bot.

Design principle: this layer prioritizes RECALL over PRECISION.
A false negative (missing a genuine crisis message) is a severe harm.
A false positive (showing a helpline to someone who wasn't in crisis)
is a mild inconvenience. When in doubt, this layer triggers the safety
response. This is a deliberate design decision - document it in your
Responsible AI section.

This module has two independent checks, run in this order:
  1. check_crisis()                  -> highest priority, always wins
  2. check_eating_disorder_numeric()  -> restricts numeric ED content

Both run BEFORE retrieval/generation. Neither depends on the LLM.
"""

import re

# ---------------------------------------------------------------------
# 1. CRISIS DETECTION
# ---------------------------------------------------------------------
# Patterns use \b word boundaries and cover common verb inflections
# (kill/killing, want/wanted) so simple substring matching doesn't miss
# obvious variants. Intentionally does NOT try to detect negation
# ("I don't want to kill myself") - a deterministic layer cannot
# reliably parse negation, and treating a negated crisis phrase as
# non-crisis risks a false negative, which is the worse failure mode.
CRISIS_PATTERNS = [
    r"\bsuicid(e|al)\b",
    r"\bkill(ing)?\s+myself\b",
    r"\bend(ing)?\s+(it all|my life)\b",
    r"\bwant(ed|s)?\s+to\s+die\b",
    r"\bnot\s+worth\s+living\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bno\s+point\s+in\s+living\b",
    r"\bbetter\s+off\s+dead\b",
    r"\bhurt(ing)?\s+myself\b",
    r"\bself[\s-]?harm(ing)?\b",
    r"\bcutting\s+myself\b",
    r"\bcan'?t\s+go\s+on\b",
    r"\btake\s+my\s+(own\s+)?life\b",
    r"\bdon'?t\s+want\s+to\s+(be\s+alive|live)\s+anymore\b",
    r"\bwish\s+i\s+(was|were)n'?t\s+alive\b",
    r"\boverdose\s+on\s+purpose\b",
    r"\bbetter\s+off\s+(if\s+i\s+(wasn'?t|weren'?t)\s+(here|around)|without\s+me)\b",
]
_CRISIS_REGEX = re.compile("|".join(CRISIS_PATTERNS), re.IGNORECASE)

CRISIS_RESPONSE = (
    "It sounds like you might be going through something really difficult. "
    "Please reach out to Tele MANAS — India's 24/7 mental health helpline — "
    "at 14416 or 1-800-891-4416. You can also contact KIRAN at 1800-599-0019. "
    "You don't have to go through this alone, and support is available right now."
)


def check_crisis(user_input: str) -> bool:
    """Returns True if the input matches a crisis pattern. Deterministic,
    no LLM call, runs first and always wins over other routing."""
    return bool(_CRISIS_REGEX.search(user_input))


# ---------------------------------------------------------------------
# 2. EATING-DISORDER NUMERIC REQUEST DETECTION
# ---------------------------------------------------------------------
# Fires when the message combines eating-disorder-adjacent context with
# a request for a specific number (calories, weight, meal plan). Per
# the project brief, the bot must never generate specific numeric
# guidance here - only awareness-level content and a redirect.
_ED_CONTEXT_PATTERNS = [
    r"\bcalories?\b", r"\bbinge\b", r"\bpurg(e|ing)\b", r"\brestrict(ing)?\s+(food|eating)\b",
    r"\banorexi", r"\bbulimi", r"\beating\s+disorder\b", r"\bweight\s+loss\b", r"\blose\s+weight\b",
    r"\bskip(ping)?\s+meals\b", r"\bfast(ing)?\s+for\b",
]
# These phrasings are specific and risky enough (a request for an exact
# calorie/weight number, or a bounded meal plan) to trigger the
# restricted route on their own, without also requiring a separate
# ED-context keyword in the same message.
_NUMERIC_ASK_PATTERNS = [
    r"\bhow\s+many\s+calories\b", r"\bhow\s+much\s+should\s+i\s+(eat|weigh)\b",
    r"\btarget\s+weight\b", r"\bmeal\s+plan\b", r"\bcalorie\s+(count|target|limit|goal)\b",
    r"\bideal\s+weight\b", r"\bhow\s+little\s+can\s+i\s+eat\b",
]
_ED_CONTEXT_REGEX = re.compile("|".join(_ED_CONTEXT_PATTERNS), re.IGNORECASE)
_NUMERIC_ASK_REGEX = re.compile("|".join(_NUMERIC_ASK_PATTERNS), re.IGNORECASE)
_HAS_DIGIT_REGEX = re.compile(r"\d")

EATING_DISORDER_RESTRICTED_RESPONSE = (
    "I'm not able to give specific numbers around food, weight, or calories — "
    "that kind of guidance can do real harm, especially if you're already "
    "struggling with this. Eating disorders are treatable, and they're not "
    "about willpower or a lifestyle choice. If this is something you're "
    "dealing with, please consider reaching out to a doctor or counselor, "
    "or Tele MANAS at 14416 for support."
)


def check_eating_disorder_numeric(user_input: str) -> bool:
    """Returns True if the message either:
      (a) matches a specific numeric-ask phrase directly (e.g. "how many
          calories", "meal plan", "ideal weight") - these are risky
          enough to trigger on their own, or
      (b) combines general ED-adjacent context with an actual digit in
          the message (e.g. "restricting food, only eating 300 a day").
    """
    if _NUMERIC_ASK_REGEX.search(user_input):
        return True
    if _ED_CONTEXT_REGEX.search(user_input) and _HAS_DIGIT_REGEX.search(user_input):
        return True
    return False


# ---------------------------------------------------------------------
# 3. ROUTER
# ---------------------------------------------------------------------
def route_query(user_input: str) -> dict:
    """
    Runs the deterministic safety checks in priority order and returns
    a routing decision. This should be called BEFORE any retrieval or
    LLM generation step.

    Returns:
        {
            "route": "crisis" | "eating_disorder_restricted" | "normal",
            "response": str or None   # pre-written response if not "normal"
        }
    """
    if check_crisis(user_input):
        return {"route": "crisis", "response": CRISIS_RESPONSE}

    if check_eating_disorder_numeric(user_input):
        return {"route": "eating_disorder_restricted", "response": EATING_DISORDER_RESTRICTED_RESPONSE}

    return {"route": "normal", "response": None}


if __name__ == "__main__":
    # quick manual smoke test
    samples = [
        "I want to kill myself",
        "How can I manage stress before exams?",
        "How many calories should I eat to lose weight fast?",
        "This workload is killing me",
    ]
    for s in samples:
        print(f"{s!r} -> {route_query(s)}")