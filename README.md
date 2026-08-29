# Agentic RFP Evaluation & Supplier Ranking

An AI-assisted app that reads supplier RFP PDFs, scores them against
configurable criteria using an LLM, benchmarks suppliers against their peers
with **deterministic Python only**, and produces an explainable leaderboard.

## Folder structure

```
rfp_eval/
├── app.py                     # Streamlit UI (5 screens)
├── orchestrator.py            # Orchestrator Agent: runs the workflow in order
├── db/
│   ├── schema.sql              # SQLite table definitions
│   └── init_db.py              # DB creation + criteria seed script
├── tools/
│   ├── pdf_tool.py              # Document Tool: PDF text extraction
│   ├── llm_agent.py             # Evaluation Agent: prompt + LLM call (Anthropic or mock)
│   ├── validation.py            # Validation Tool: schema checks & normalization
│   └── ranking.py               # Ranking Tool: scoring, benchmarks, PPI, tie-breaks
├── generate_sample_rfps.py    # Builds 4 synthetic supplier PDFs
├── data/
│   ├── sample_rfps/             # 4 generated supplier PDFs
│   └── sample_output/           # sample_run.json (one completed run)
├── requirements.txt
└── README.md
```

## Setup

```bash
cd rfp_eval
pip install -r requirements.txt

# 1. Create + seed the database
python db/init_db.py

# 2. Generate the 4 synthetic supplier PDFs (already included, re-run if needed)
python generate_sample_rfps.py

# 3. Launch the app
streamlit run app.py
```

Open the sidebar and choose an evaluation backend:
- **Mock** (default): a transparent, offline keyword-density heuristic. No API
  key required — useful for demos and grading without LLM billing.
- **Groq**: paste a free API key (console.groq.com -> API Keys, no credit card
  needed) to get real LLM-generated scores using Llama 3.3 70B with forced
  JSON mode. Requires `pip install groq` (included in requirements.txt).
- **Anthropic**: paste an API key to get real Claude-generated scores,
  justifications, and evidence. Requires a paid account (console.anthropic.com)
  and `pip install anthropic` (included in requirements.txt).

To deploy on Streamlit Community Cloud: push this folder to a GitHub repo,
create a new app pointing at `app.py`, and optionally add `GROQ_API_KEY` and/or
`ANTHROPIC_API_KEY` as Streamlit secrets if you want a backend available by
default (the app also accepts a key typed into the sidebar at runtime).

## Agentic architecture

| Component | Responsibility | Where |
|---|---|---|
| Orchestrator Agent | Calls each tool in the required order for a batch | `orchestrator.py` |
| Document Tool | Extracts text from each uploaded PDF | `tools/pdf_tool.py` (pypdf) |
| Evaluation Agent | Builds a grounded prompt, asks the LLM for one JSON scorecard per supplier | `tools/llm_agent.py` |
| Validation Tool | Checks schema, fills missing criteria, clips out-of-range scores, records warnings | `tools/validation.py` |
| Ranking Tool | Weighted scores, peer benchmarks, gaps, relative %, PPI, tie-breaks, ranks | `tools/ranking.py` (pure Python, no LLM) |

**Important separation of concerns:** the LLM only judges proposal content
(per-criterion score, justification, evidence). All arithmetic, benchmarking,
tie-breaks, and final ranking are computed in `tools/ranking.py` with plain
Python — deterministic and reproducible given the same validated inputs.

### Data flow (per the brief)
Setup → Input → Batch → Evaluate → Validate → Score → Benchmark → Rank → Persist → Present.
This is implemented end-to-end in `orchestrator.run_batch_evaluation()`.

## SQLite design

- `evaluation_criteria`: criterion_id, name, description, weight, max_score, is_active
- `rfp_runs`: rfp_run_id (UUID), created_at, status, criteria_snapshot (JSON), notes
- `supplier_results`: rfp_run_id, supplier_name, submission_date, experience_rating,
  absolute_score, ppi, final_rank, result_json (full per-criterion breakdown)

Every run stores a **snapshot** of the criteria used, so historical runs stay
reproducible even if weights are changed later.

## Formulas

- **Absolute weighted score** = Σ (criterion_score / max_score) × weight — weights in %, result 0–100.
- **Criterion benchmark** = highest valid score observed for that criterion across all suppliers in the batch.
- **Criterion gap** = supplier_score − benchmark (0 for the leader, ≤ 0 otherwise).
- **Relative performance %** = (supplier_score / benchmark) × 100. If the benchmark is 0 (nobody scored on that criterion), relative % is defined as 0 to avoid a division-by-zero.
- **Peer Performance Index (PPI)** = weighted average of each criterion's relative performance %, using the same criteria weights.

### Tie-break order (mandatory, applied as a single stable sort)
1. Higher PPI first
2. Earlier submission date
3. Higher historical experience rating
4. Supplier name, ascending

Ranks 1, 2, 3… are assigned only after this sort — see `tools/ranking.py::rank_suppliers`.

## Validation rules

- Missing criterion in the LLM's JSON → defaulted to score 0, warning recorded.
- Non-numeric / unparseable score → defaulted to 0, warning recorded.
- Score below 0 or above `max_score` → clipped to the valid range, warning recorded.
- Missing/empty `justification` or `overall_summary` → replaced with a placeholder, warning recorded.
- Non-list `risks` → replaced with an empty list.
- All warnings are stored per-supplier in the run and shown in the "Run Details" screen.

## Assumptions

- Historical experience rating is entered manually per supplier (0–10) at upload time, as the brief does not specify an automated source for it.
- Active criteria weights must sum to exactly 100%; the Orchestrator refuses to start a batch otherwise (surfaced as an error in the Criteria tab and blocked in the Evaluate tab).
- Proposal text is truncated (with head+tail retained) before prompting if a single PDF's extracted text exceeds ~12,000 characters, to keep prompt size predictable.
- The mock backend is a keyword-density heuristic for offline demo/testing only; it is clearly labeled as `[MOCK MODE]` in its output and is not a substitute for real LLM judgment.

## Sample data

- `data/sample_rfps/` contains 4 synthetic supplier proposals for the same fictional procurement (a customer-support ticketing platform migration): **Apex Systems** (strong technical/security, higher price), **BrightPath Tech** (lowest price, fastest timeline, weak compliance detail), **NexaWorks** (balanced, strongest implementation plan/support), **Orbit Digital** (strong experience/references, vague integration plan).
- `data/sample_output/sample_run.json` is a complete sample run (mock backend) showing the full leaderboard, per-criterion breakdown, benchmarks, PPI, and tie-break metadata for these 4 suppliers.

## Demonstration script (for submission video)

1. Show the **Criteria** tab — active criteria and weights summing to 100%.
2. Upload the 4 sample PDFs in **Supplier Input & Evaluate**, fill in metadata, click Evaluate (mock or real backend).
3. Show the **Leaderboard**, then drill into a **Detailed Scorecard** for one supplier (evidence, gap, relative %).
4. Show **Run Details**: RFP_RUN_ID, tie-break order, and download the JSON.
5. For the required error case: re-run with a deliberately malformed LLM response (see `tools/validation.py` test in this README, or temporarily break a PDF) and show the resulting warnings surfaced in Run Details.

## Reproducibility

Given the same validated per-criterion scores, `tools/ranking.py` always
produces the same absolute scores, benchmarks, PPI, and final order — it
contains no randomness and no LLM calls, satisfying the success condition
that identical inputs produce identical formulas and ordering.
