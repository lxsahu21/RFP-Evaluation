"""
Validation Tool
================
Checks the LLM's raw JSON against the active criteria, fills in missing
criteria, clips out-of-range scores, and records human-readable warnings.

Implemented with plain Python (dataclasses) rather than Pydantic to keep
the app dependency-light; the validation rules are identical to what a
Pydantic model + validator would enforce.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from tools.llm_agent import Criterion


@dataclass
class CriterionResult:
    criterion_id: int
    name: str
    weight: float
    max_score: int
    score: float
    justification: str
    evidence: str
    was_defaulted: bool = False  # True if this row had to be synthesized/clipped


@dataclass
class ValidatedSupplierResult:
    supplier_name: str
    criteria_results: List[CriterionResult]
    risks: List[str]
    overall_summary: str
    warnings: List[str] = field(default_factory=list)


def validate_and_normalize(
    raw_llm_output: Dict[str, Any],
    supplier_name: str,
    criteria: List[Criterion],
) -> ValidatedSupplierResult:
    warnings: List[str] = []

    if not isinstance(raw_llm_output, dict):
        warnings.append("LLM output was not a JSON object; using fully defaulted result.")
        raw_llm_output = {}

    if raw_llm_output.get("_llm_error"):
        warnings.append(f"LLM call failed for this supplier: {raw_llm_output['_llm_error']}. All criteria defaulted.")
        raw_llm_output = {}

    raw_name = raw_llm_output.get("supplier_name")
    if raw_name and raw_name != supplier_name:
        warnings.append(f"LLM returned supplier_name '{raw_name}', overridden with '{supplier_name}'.")

    raw_criteria_list = raw_llm_output.get("criteria")
    if not isinstance(raw_criteria_list, list):
        warnings.append("Missing or malformed 'criteria' array in LLM output; all criteria defaulted.")
        raw_criteria_list = []

    raw_by_id = {}
    for item in raw_criteria_list:
        if isinstance(item, dict) and "criterion_id" in item:
            try:
                cid = int(item["criterion_id"])
                raw_by_id[cid] = item
            except (TypeError, ValueError):
                warnings.append(f"Skipped a criterion entry with invalid criterion_id: {item.get('criterion_id')!r}")

    results: List[CriterionResult] = []
    for c in criteria:
        item = raw_by_id.get(c.criterion_id)
        if item is None:
            warnings.append(
                f"Criterion '{c.name}' (id={c.criterion_id}) missing from LLM output; defaulted to score 0."
            )
            results.append(CriterionResult(
                criterion_id=c.criterion_id,
                name=c.name,
                weight=c.weight,
                max_score=c.max_score,
                score=0,
                justification="No LLM result returned for this criterion.",
                evidence="",
                was_defaulted=True,
            ))
            continue

        was_defaulted = False
        score = item.get("score")
        try:
            score = float(score)
        except (TypeError, ValueError):
            warnings.append(
                f"Criterion '{c.name}': non-numeric score '{item.get('score')!r}' defaulted to 0."
            )
            score = 0.0
            was_defaulted = True

        if score < 0:
            warnings.append(f"Criterion '{c.name}': negative score {score} clipped to 0.")
            score = 0.0
            was_defaulted = True
        elif score > c.max_score:
            warnings.append(
                f"Criterion '{c.name}': score {score} exceeds max_score {c.max_score}; clipped."
            )
            score = float(c.max_score)
            was_defaulted = True

        justification = item.get("justification")
        if not isinstance(justification, str) or not justification.strip():
            justification = "No justification provided."
            was_defaulted = True

        evidence = item.get("evidence")
        if not isinstance(evidence, str):
            evidence = ""

        results.append(CriterionResult(
            criterion_id=c.criterion_id,
            name=c.name,
            weight=c.weight,
            max_score=c.max_score,
            score=score,
            justification=justification,
            evidence=evidence,
            was_defaulted=was_defaulted,
        ))

    risks = raw_llm_output.get("risks")
    if not isinstance(risks, list):
        risks = []
    risks = [str(r) for r in risks if isinstance(r, (str, int, float))]

    overall_summary = raw_llm_output.get("overall_summary")
    if not isinstance(overall_summary, str) or not overall_summary.strip():
        overall_summary = "No summary provided by the LLM."
        warnings.append("Missing or empty 'overall_summary'; defaulted.")

    return ValidatedSupplierResult(
        supplier_name=supplier_name,
        criteria_results=results,
        risks=risks,
        overall_summary=overall_summary,
        warnings=warnings,
    )
