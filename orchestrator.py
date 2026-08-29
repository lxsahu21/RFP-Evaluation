"""
Orchestrator Agent
==================
Controls the end-to-end workflow in the required order:

  1. Load active criteria from SQLite
  2. For each supplier: extract PDF text -> call Evaluation Agent (LLM) -> Validate
  3. Compute benchmarks, scores, PPI across the whole batch (Ranking Tool)
  4. Apply deterministic tie-breaks and assign ranks
  5. Persist the full run (criteria snapshot + supplier_results) to SQLite

This module contains NO scoring or ranking logic itself -- it only calls the
tools in the correct order and shapes data between them, exactly as the
"Orchestrator Agent" role describes in the brief.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from db.init_db import get_connection
from tools.llm_agent import Criterion, evaluate_supplier
from tools.pdf_tool import extract_text_from_pdf, truncate_for_prompt
from tools.ranking import SupplierInput, SupplierRankResult, rank_suppliers
from tools.validation import validate_and_normalize


@dataclass
class SupplierSubmission:
    supplier_name: str
    submission_date: date
    experience_rating: float
    pdf_bytes: bytes


def load_active_criteria(conn: sqlite3.Connection) -> List[Criterion]:
    rows = conn.execute(
        "SELECT criterion_id, name, description, weight, max_score "
        "FROM evaluation_criteria WHERE is_active = 1 ORDER BY criterion_id"
    ).fetchall()
    if not rows:
        raise ValueError("No active evaluation criteria found. Add/activate criteria first.")
    total_weight = sum(r["weight"] for r in rows)
    if abs(total_weight - 100) > 0.01:
        raise ValueError(
            f"Active criteria weights sum to {total_weight}%, not 100%. Fix weights before evaluating."
        )
    return [
        Criterion(
            criterion_id=r["criterion_id"],
            name=r["name"],
            description=r["description"],
            weight=r["weight"],
            max_score=r["max_score"],
        )
        for r in rows
    ]


def run_batch_evaluation(
    submissions: List[SupplierSubmission],
    backend: str = "mock",
    api_key: Optional[str] = None,
    model: str = "claude-sonnet-4-6",
    db_path: Optional[str] = None,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    Runs the full pipeline for one batch of supplier submissions and persists
    the result under a single rfp_run_id. Returns the complete result dict
    (same shape as what gets written to SQLite / offered for JSON download).
    """
    conn = get_connection(db_path) if db_path else get_connection()
    try:
        criteria = load_active_criteria(conn)
        criteria_snapshot = [asdict(c) for c in criteria]

        rfp_run_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO rfp_runs (rfp_run_id, status, criteria_snapshot) VALUES (?, ?, ?)",
            (rfp_run_id, "in_progress", json.dumps(criteria_snapshot)),
        )
        conn.commit()

        supplier_inputs: List[SupplierInput] = []
        all_warnings: Dict[str, List[str]] = {}

        for i, sub in enumerate(submissions, start=1):
            if progress_callback:
                progress_callback(i, len(submissions), sub.supplier_name)

            # Step: Document Tool
            raw_text = extract_text_from_pdf(sub.pdf_bytes)
            prompt_text = truncate_for_prompt(raw_text)

            # Step: Evaluation Agent (LLM)
            try:
                raw_llm_output = evaluate_supplier(
                    supplier_name=sub.supplier_name,
                    proposal_text=prompt_text,
                    criteria=criteria,
                    backend=backend,
                    api_key=api_key,
                    model=model,
                )
            except Exception as e:
                # Don't let one supplier's LLM failure abort the whole batch.
                # Validation Tool will default every criterion and record this as a warning.
                raw_llm_output = {"supplier_name": sub.supplier_name, "_llm_error": str(e)}

            # Step: Validation Tool
            validated = validate_and_normalize(raw_llm_output, sub.supplier_name, criteria)
            all_warnings[sub.supplier_name] = validated.warnings

            supplier_inputs.append(SupplierInput(
                supplier_name=sub.supplier_name,
                submission_date=sub.submission_date,
                experience_rating=sub.experience_rating,
                validated_result=validated,
            ))

        # Step: Ranking Tool (benchmarks, scores, PPI, tie-breaks, ranks) -- deterministic only
        ranked: List[SupplierRankResult] = rank_suppliers(supplier_inputs)

        # Step: Persist
        for r in ranked:
            result_json = json.dumps(_rank_result_to_dict(r))
            conn.execute(
                """
                INSERT INTO supplier_results
                    (rfp_run_id, supplier_name, submission_date, experience_rating,
                     absolute_score, ppi, final_rank, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rfp_run_id,
                    r.supplier_name,
                    r.submission_date,
                    r.experience_rating,
                    r.absolute_score,
                    r.ppi,
                    r.final_rank,
                    result_json,
                ),
            )
        conn.execute(
            "UPDATE rfp_runs SET status = 'completed' WHERE rfp_run_id = ?",
            (rfp_run_id,),
        )
        conn.commit()

        return {
            "rfp_run_id": rfp_run_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "completed",
            "backend": backend,
            "criteria": criteria_snapshot,
            "tie_break_order": [
                "Higher PPI first",
                "Earlier submission date",
                "Higher historical experience rating",
                "Supplier name ascending",
            ],
            "results": [_rank_result_to_dict(r) for r in ranked],
        }

    except Exception as e:
        conn.execute(
            "UPDATE rfp_runs SET status = 'failed', notes = ? WHERE rfp_run_id = ?",
            (str(e), rfp_run_id if "rfp_run_id" in dir() else "unknown"),
        )
        conn.commit()
        raise
    finally:
        conn.close()


def _rank_result_to_dict(r: SupplierRankResult) -> Dict[str, Any]:
    d = asdict(r)
    return d


def fetch_run(rfp_run_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Reload a persisted run (e.g. for the Run Details screen)."""
    conn = get_connection(db_path) if db_path else get_connection()
    try:
        run_row = conn.execute(
            "SELECT * FROM rfp_runs WHERE rfp_run_id = ?", (rfp_run_id,)
        ).fetchone()
        if not run_row:
            raise ValueError(f"No run found with id {rfp_run_id}")

        result_rows = conn.execute(
            "SELECT * FROM supplier_results WHERE rfp_run_id = ? ORDER BY final_rank",
            (rfp_run_id,),
        ).fetchall()

        return {
            "rfp_run_id": run_row["rfp_run_id"],
            "created_at": run_row["created_at"],
            "status": run_row["status"],
            "criteria": json.loads(run_row["criteria_snapshot"]),
            "results": [json.loads(row["result_json"]) for row in result_rows],
        }
    finally:
        conn.close()


def list_runs(db_path: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection(db_path) if db_path else get_connection()
    try:
        return conn.execute(
            "SELECT rfp_run_id, created_at, status FROM rfp_runs ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
