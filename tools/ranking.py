"""
Ranking Tool
============
100% deterministic Python. No LLM involvement. Implements the formulas and
tie-break rules from the project brief exactly:

  Absolute weighted score = sum( (criterion_score / max_score) * weight )
  Criterion benchmark      = highest valid score observed for that criterion across all suppliers
  Criterion gap            = supplier_score - benchmark_score  (0 for the leader, else <= 0)
  Relative performance %   = (supplier_score / benchmark_score) * 100   [0 if benchmark is 0]
  PPI                      = weighted average of criterion relative-performance percentages

Tie-break order (applied only after PPI is computed, as a stable sort):
  1) Higher PPI first
  2) Earlier submission date
  3) Higher historical experience rating
  4) Supplier name ascending (A-Z)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from tools.validation import ValidatedSupplierResult


@dataclass
class SupplierInput:
    supplier_name: str
    submission_date: date
    experience_rating: float
    validated_result: ValidatedSupplierResult


@dataclass
class CriterionScoreDetail:
    criterion_id: int
    name: str
    weight: float
    max_score: int
    score: float
    benchmark_score: float
    gap: float
    relative_pct: float
    justification: str
    evidence: str
    was_defaulted: bool


@dataclass
class SupplierRankResult:
    supplier_name: str
    submission_date: str
    experience_rating: float
    absolute_score: float
    ppi: float
    final_rank: int
    criteria_detail: List[CriterionScoreDetail]
    risks: List[str]
    overall_summary: str
    warnings: List[str]


def compute_absolute_score(validated: ValidatedSupplierResult) -> float:
    """Sum of (criterion score / max score) * weight, weights in percent -> result 0-100."""
    total = 0.0
    for cr in validated.criteria_results:
        if cr.max_score > 0:
            total += (cr.score / cr.max_score) * cr.weight
    return round(total, 2)


def compute_benchmarks(suppliers: List[SupplierInput]) -> Dict[int, float]:
    """Highest valid score observed for each criterion, across all suppliers."""
    benchmarks: Dict[int, float] = {}
    for s in suppliers:
        for cr in s.validated_result.criteria_results:
            current = benchmarks.get(cr.criterion_id, float("-inf"))
            if cr.score > current:
                benchmarks[cr.criterion_id] = cr.score
    return benchmarks


def compute_supplier_metrics(
    supplier: SupplierInput,
    benchmarks: Dict[int, float],
) -> tuple[float, float, List[CriterionScoreDetail]]:
    """Returns (absolute_score, ppi, per-criterion detail) for one supplier."""
    absolute_score = compute_absolute_score(supplier.validated_result)

    details: List[CriterionScoreDetail] = []
    weighted_relative_sum = 0.0
    total_weight = 0.0

    for cr in supplier.validated_result.criteria_results:
        benchmark = benchmarks.get(cr.criterion_id, 0.0)
        gap = round(cr.score - benchmark, 2)
        if benchmark > 0:
            relative_pct = round((cr.score / benchmark) * 100, 2)
        else:
            # Safe handling when benchmark is zero: nobody scored on this criterion.
            relative_pct = 0.0

        details.append(CriterionScoreDetail(
            criterion_id=cr.criterion_id,
            name=cr.name,
            weight=cr.weight,
            max_score=cr.max_score,
            score=cr.score,
            benchmark_score=benchmark,
            gap=gap,
            relative_pct=relative_pct,
            justification=cr.justification,
            evidence=cr.evidence,
            was_defaulted=cr.was_defaulted,
        ))

        weighted_relative_sum += relative_pct * cr.weight
        total_weight += cr.weight

    ppi = round(weighted_relative_sum / total_weight, 2) if total_weight > 0 else 0.0
    return absolute_score, ppi, details


def rank_suppliers(suppliers: List[SupplierInput]) -> List[SupplierRankResult]:
    """
    Full deterministic pipeline: benchmark -> per-supplier metrics -> stable
    tie-break sort -> sequential rank assignment.
    """
    if not suppliers:
        return []

    benchmarks = compute_benchmarks(suppliers)

    scored: List[SupplierRankResult] = []
    for s in suppliers:
        absolute_score, ppi, details = compute_supplier_metrics(s, benchmarks)
        scored.append(SupplierRankResult(
            supplier_name=s.supplier_name,
            submission_date=s.submission_date.isoformat(),
            experience_rating=s.experience_rating,
            absolute_score=absolute_score,
            ppi=ppi,
            final_rank=0,  # assigned after sort
            criteria_detail=details,
            risks=s.validated_result.risks,
            overall_summary=s.validated_result.overall_summary,
            warnings=s.validated_result.warnings,
        ))

    # Mandatory tie-break order:
    # 1) Higher PPI first  2) Earlier submission date  3) Higher experience rating
    # 4) Supplier name ascending
    scored.sort(
        key=lambda r: (
            -r.ppi,
            r.submission_date,          # ISO format sorts chronologically as string
            -r.experience_rating,
            r.supplier_name.lower(),
        )
    )

    for i, r in enumerate(scored, start=1):
        r.final_rank = i

    return scored
