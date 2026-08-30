"""
Evaluation Agent
================
Builds a grounded prompt from the active criteria + extracted proposal text,
calls the LLM, and returns the RAW parsed JSON (unvalidated). All arithmetic,
benchmarking, tie-breaks, and ranking happen later in deterministic Python
(tools/ranking.py) -- the LLM never decides those.

Two backends are supported:
  - "Groq": real call to Groq via the groq API (requires GROQ_API_KEY)
  - "mock": deterministic offline heuristic scorer, used for local testing/demo
            when no API key is available (e.g. classroom demo without billing).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


SYSTEM_PROMPT = """You are a procurement evaluation assistant. You score ONE supplier's \
RFP proposal against a fixed set of evaluation criteria.

Rules you MUST follow:
1. Use ONLY evidence present in the supplied proposal text. Do not invent facts.
2. Return exactly one score object for EVERY criterion listed, even if the proposal \
does not address it (in that case, score it low and say so in the justification).
3. Every score must be an integer between 0 and the criterion's max_score (inclusive).
4. Output JSON ONLY. No markdown fences, no commentary, no text before or after the JSON.
5. You do not calculate weighted totals, rankings, or comparisons to other suppliers. \
That is handled outside of you.
"""

USER_PROMPT_TEMPLATE = """Supplier name: {supplier_name}

Active evaluation criteria (id, name, description, max_score):
{criteria_block}

Proposal text extracted from the supplier's PDF:
\"\"\"
{proposal_text}
\"\"\"

Return JSON matching exactly this schema. Keep "justification" and "evidence" \
to ONE short sentence each (under 25 words) so the full response stays compact:
{{
  "supplier_name": "{supplier_name}",
  "criteria": [
    {{
      "criterion_id": <int>,
      "score": <int, 0 to max_score>,
      "justification": "<one short sentence>",
      "evidence": "<one short quote or paraphrase>"
    }}
  ],
  "risks": ["<short risk 1>", "..."],
  "overall_summary": "<2-3 sentence summary>"
}}
"""


@dataclass
class Criterion:
    criterion_id: int
    name: str
    description: str
    weight: float
    max_score: int


def build_criteria_block(criteria: List[Criterion]) -> str:
    lines = []
    for c in criteria:
        lines.append(f"- id={c.criterion_id} | {c.name} (max_score={c.max_score}): {c.description}")
    return "\n".join(lines)


def build_user_prompt(supplier_name: str, proposal_text: str, criteria: List[Criterion]) -> str:
    return USER_PROMPT_TEMPLATE.format(
        supplier_name=supplier_name,
        criteria_block=build_criteria_block(criteria),
        proposal_text=proposal_text,
    )


def _extract_json(raw: str) -> Dict[str, Any]:
    """Best-effort extraction of a JSON object from an LLM response."""
    raw = raw.strip()
    # Strip markdown fences if the model added them despite instructions
    raw = re.sub(r"^```(json)?", "", raw.strip(), flags=re.IGNORECASE).strip()
    raw = re.sub(r"```$", "", raw.strip()).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fall back to grabbing the first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def call_anthropic(
    supplier_name: str,
    proposal_text: str,
    criteria: List[Criterion],
    api_key: str,
    model: str = "claude-sonnet-4-6",
) -> Dict[str, Any]:
    """Real LLM call. Requires `pip install anthropic` and a valid API key."""
    import anthropic  # imported lazily so the app runs without the package for mock mode

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = build_user_prompt(supplier_name, proposal_text, criteria)

    response = client.messages.create(
        model=model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw_text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    return _extract_json(raw_text)


def call_groq(
    supplier_name: str,
    proposal_text: str,
    criteria: List[Criterion],
    api_key: str,
    model: str = "openai/gpt-oss-120b",
) -> Dict[str, Any]:
    """
    Real LLM call via Groq's OpenAI-compatible API. Requires `pip install groq`
    and a free API key from console.groq.com.

    Note: we intentionally do NOT use Groq's strict response_format=json_object
    mode. That mode makes Groq itself reject the request with a hard 400 error
    ("json_validate_failed") if the model's output doesn't parse as strict JSON
    -- which happens more often on longer, detail-rich responses. Instead we
    rely on clear prompt instructions plus our own lenient `_extract_json`
    parser, matching how the Anthropic backend works. Any parsing failure is
    caught by the Orchestrator and surfaces as a validation warning instead of
    crashing the batch.
    """
    from groq import Groq  # imported lazily so the app runs without the package for mock mode

    client = Groq(api_key=api_key)
    user_prompt = build_user_prompt(supplier_name, proposal_text, criteria)

    response = client.chat.completions.create(
        model=model,
        max_tokens=4096,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw_text = response.choices[0].message.content
    return _extract_json(raw_text)


# ---------------------------------------------------------------------------
# Mock backend: deterministic offline heuristic, used when no API key is set.
# This lets the app (and the automated grading demo) run end-to-end without
# network access or billing, while keeping the same JSON contract as the
# real LLM call. It is intentionally simple and clearly labeled as a mock.
# ---------------------------------------------------------------------------
_KEYWORDS = {
    "Technical Capability": ["architecture", "integration", "scalab", "api", "microservice", "technical", "cloud"],
    "Implementation Plan": ["timeline", "milestone", "staffing", "risk plan", "week", "month", "team structure", "phase"],
    "Commercial Value": ["price", "pricing", "cost", "$", "assumption", "fee", "budget"],
    "Security & Compliance": ["security", "compliance", "certification", "iso", "gdpr", "audit", "privacy", "encrypt"],
    "Support & Experience": ["support", "reference", "similar project", "experience", "sla", "helpdesk", "case stud"],
}


def call_mock(supplier_name: str, proposal_text: str, criteria: List[Criterion]) -> Dict[str, Any]:
    text_lower = proposal_text.lower()
    results = []
    for c in criteria:
        keywords = _KEYWORDS.get(c.name, [c.name.lower()])
        hits = sum(text_lower.count(k) for k in keywords)
        # Heuristic: base score scaled by keyword density, capped at max_score
        density_score = min(c.max_score, 4 + hits)
        results.append({
            "criterion_id": c.criterion_id,
            "score": int(density_score),
            "justification": f"Mock heuristic: found {hits} references to '{c.name}' related terms.",
            "evidence": f"Keyword-based match count={hits} in proposal text." if hits else "No direct evidence found in proposal text.",
        })
    return {
        "supplier_name": supplier_name,
        "criteria": results,
        "risks": ["Mock evaluation: risks not analyzed by a real LLM."],
        "overall_summary": f"[MOCK MODE] Heuristic keyword-based evaluation for {supplier_name}. "
                            f"Replace with a real Anthropic API key for genuine LLM reasoning.",
    }


def evaluate_supplier(
    supplier_name: str,
    proposal_text: str,
    criteria: List[Criterion],
    backend: str = "mock",
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-6",
) -> Dict[str, Any]:
    """
    Single entry point used by the orchestrator. Returns raw (unvalidated) LLM JSON.
    """
    if backend == "anthropic":
        if not api_key:
            raise ValueError("Anthropic backend selected but no API key was provided.")
        return call_anthropic(supplier_name, proposal_text, criteria, api_key=api_key, model=model)
    if backend == "groq":
        if not api_key:
            raise ValueError("Groq backend selected but no API key was provided.")
        return call_groq(supplier_name, proposal_text, criteria, api_key=api_key, model=model)
    return call_mock(supplier_name, proposal_text, criteria)
