"""
Agentic RFP Evaluation & Supplier Ranking -- Streamlit app.

Run with:
    streamlit run app.py
"""
import json
import os
from datetime import date

import pandas as pd
import streamlit as st

from db.init_db import DB_PATH, get_connection, init_db
from orchestrator import SupplierSubmission, fetch_run, list_runs, run_batch_evaluation

st.set_page_config(page_title="Agentic RFP Evaluation", layout="wide")

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
if not os.path.exists(DB_PATH):
    init_db()

if "last_run_result" not in st.session_state:
    st.session_state.last_run_result = None

st.title("📋 Agentic RFP Evaluation & Supplier Ranking")
st.caption(
    "Orchestrator -> Document Tool -> Evaluation Agent (LLM) -> Validation Tool -> "
    "Ranking Tool (deterministic) -> SQLite -> UI"
)

# ---------------------------------------------------------------------------
# Sidebar: LLM backend configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ LLM Configuration")
    backend = st.radio(
        "Evaluation backend",
        options=["mock", "groq", "anthropic"],
        format_func=lambda x: {
            "mock": "Mock (offline heuristic, no API key needed)",
            "groq": "Groq (real LLM, free tier available)",
            "anthropic": "Anthropic Claude (real LLM, paid)",
        }[x],
    )
    api_key = None
    if backend == "anthropic":
        model = "claude-sonnet-4-6"
        api_key = st.text_input("Anthropic API key", type="password")
        model = st.text_input("Model", value=model)
        st.caption("Requires `pip install anthropic`. Get a key (paid, no free tier) at console.anthropic.com.")
    elif backend == "groq":
        model = "openai/gpt-oss-120b"
        api_key = st.text_input("Groq API key", type="password")
        model = st.text_input("Model", value=model)
        st.caption(
            "Requires `pip install groq`. Get a free key at console.groq.com -> API Keys. "
            "Default model is openai/gpt-oss-120b (Groq's current recommended general-purpose model)."
        )
    else:
        model = "claude-sonnet-4-6"
        st.info(
            "Mock mode scores proposals with a transparent keyword-density heuristic. "
            "Use this for demos without API billing; switch to Groq or Anthropic for real LLM reasoning."
        )

    st.divider()
    st.header("🗄️ Database")
    if st.button("Reset database (re-seed criteria)"):
        init_db(reseed=True)
        st.success("Database reset and criteria re-seeded.")
        st.rerun()

tab_criteria, tab_input, tab_leaderboard, tab_scorecards, tab_run_details = st.tabs(
    ["1. Criteria", "2. Supplier Input & Evaluate", "3. Leaderboard", "4. Detailed Scorecards", "5. Run Details"]
)

# ---------------------------------------------------------------------------
# Screen 1: Criteria
# ---------------------------------------------------------------------------
with tab_criteria:
    st.subheader("Active Evaluation Criteria")
    conn = get_connection()
    criteria_df = pd.read_sql_query(
        "SELECT criterion_id, name, description, weight, max_score, is_active FROM evaluation_criteria ORDER BY criterion_id",
        conn,
    )
    conn.close()

    active_df = criteria_df[criteria_df["is_active"] == 1]
    total_weight = active_df["weight"].sum()

    st.dataframe(
        criteria_df.rename(columns={
            "criterion_id": "ID", "name": "Name", "description": "Description",
            "weight": "Weight %", "max_score": "Max Score", "is_active": "Active",
        }),
        use_container_width=True,
        hide_index=True,
    )

    if abs(total_weight - 100) > 0.01:
        st.error(f"⚠️ Active criteria weights sum to {total_weight}%, not 100%. Evaluation will be blocked until fixed.")
    else:
        st.success(f"✅ Active criteria weights sum to {total_weight}%.")

    with st.expander("Edit criteria weights / activation"):
        st.caption("Edit values below, then click Save. Weight changes only take effect for new runs.")
        edited = st.data_editor(
            criteria_df,
            column_config={
                "is_active": st.column_config.CheckboxColumn("Active"),
                "weight": st.column_config.NumberColumn("Weight %", min_value=0, max_value=100, step=1),
                "max_score": st.column_config.NumberColumn("Max Score", min_value=1, step=1),
            },
            disabled=["criterion_id", "name", "description"],
            hide_index=True,
            use_container_width=True,
            key="criteria_editor",
        )
        if st.button("Save criteria changes"):
            conn = get_connection()
            for _, row in edited.iterrows():
                conn.execute(
                    "UPDATE evaluation_criteria SET weight = ?, max_score = ?, is_active = ? WHERE criterion_id = ?",
                    (float(row["weight"]), int(row["max_score"]), int(bool(row["is_active"])), int(row["criterion_id"])),
                )
            conn.commit()
            conn.close()
            st.success("Saved. Reload the Criteria tab to confirm.")
            st.rerun()

# ---------------------------------------------------------------------------
# Screen 2: Supplier Input & Evaluate
# ---------------------------------------------------------------------------
with tab_input:
    st.subheader("Upload Supplier RFP Responses")
    st.caption("Upload one PDF per supplier and provide the required metadata for each.")

    uploaded_files = st.file_uploader(
        "Supplier RFP PDFs (multiple allowed)", type=["pdf"], accept_multiple_files=True
    )

    submissions_meta = []
    validation_errors = []

    if uploaded_files:
        st.markdown("#### Supplier metadata")
        for f in uploaded_files:
            with st.container(border=True):
                cols = st.columns([2, 2, 2, 3])
                default_name = os.path.splitext(f.name)[0]
                supplier_name = cols[0].text_input("Supplier name", value=default_name, key=f"name_{f.name}")
                submission_date = cols[1].date_input("Submission date", value=date.today(), key=f"date_{f.name}")
                experience_rating = cols[2].number_input(
                    "Historical experience rating (0-10)", min_value=0.0, max_value=10.0,
                    value=5.0, step=0.5, key=f"exp_{f.name}",
                )
                cols[3].write(f"📄 `{f.name}` ({f.size / 1024:.1f} KB)")

                if not supplier_name.strip():
                    validation_errors.append(f"Missing supplier name for file {f.name}")

                submissions_meta.append({
                    "file": f,
                    "supplier_name": supplier_name.strip(),
                    "submission_date": submission_date,
                    "experience_rating": experience_rating,
                })

        names = [s["supplier_name"] for s in submissions_meta]
        if len(names) != len(set(names)):
            validation_errors.append("Duplicate supplier names detected -- names must be unique within a batch.")

    if validation_errors:
        for e in validation_errors:
            st.error(e)

    can_evaluate = bool(uploaded_files) and not validation_errors
    if backend == "anthropic" and not api_key:
        can_evaluate = False
        st.warning("Enter an Anthropic API key in the sidebar, or switch to Mock mode, to run evaluation.")

    if st.button("🚀 Create batch & Evaluate", disabled=not can_evaluate, type="primary"):
        submissions = [
            SupplierSubmission(
                supplier_name=s["supplier_name"],
                submission_date=s["submission_date"],
                experience_rating=s["experience_rating"],
                pdf_bytes=s["file"].getvalue(),
            )
            for s in submissions_meta
        ]

        progress_bar = st.progress(0.0, text="Starting evaluation...")

        def _progress(i, total, name):
            progress_bar.progress(i / total, text=f"Evaluating {name} ({i}/{total})...")

        try:
            result = run_batch_evaluation(
                submissions=submissions,
                backend=backend,
                api_key=api_key,
                model=model,
                progress_callback=_progress,
            )
            st.session_state.last_run_result = result
            progress_bar.progress(1.0, text="Done.")
            st.success(f"Batch evaluated. RFP_RUN_ID = `{result['rfp_run_id']}`. See the Leaderboard tab.")
        except Exception as e:
            st.error(f"Evaluation failed: {e}")

# ---------------------------------------------------------------------------
# Screen 3: Leaderboard
# ---------------------------------------------------------------------------
with tab_leaderboard:
    st.subheader("Leaderboard")

    runs = list_runs()
    run_options = {f"{r['rfp_run_id']} ({r['created_at']}, {r['status']})": r["rfp_run_id"] for r in runs}

    selected_label = st.selectbox(
        "Select an RFP run",
        options=list(run_options.keys()),
        index=0 if run_options else None,
        placeholder="No runs yet -- evaluate a batch first",
    ) if run_options else None

    result = None
    if selected_label:
        rfp_run_id = run_options[selected_label]
        result = fetch_run(rfp_run_id)
    elif st.session_state.last_run_result:
        result = st.session_state.last_run_result

    if result and result.get("results"):
        rows = []
        for r in result["results"]:
            rows.append({
                "Rank": r["final_rank"],
                "Supplier": r["supplier_name"],
                "Absolute Score": r["absolute_score"],
                "PPI": r["ppi"],
                "Submission Date": r["submission_date"],
                "Experience Rating": r["experience_rating"],
            })
        df = pd.DataFrame(rows).sort_values("Rank")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.bar_chart(df.set_index("Supplier")[["Absolute Score", "PPI"]])
    elif result:
        st.warning("This run has no completed supplier results (it may have failed before finishing). Try running a new batch.")
    else:
        st.info("No evaluation run yet. Go to the 'Supplier Input & Evaluate' tab.")

# ---------------------------------------------------------------------------
# Screen 4: Detailed Scorecards
# ---------------------------------------------------------------------------
with tab_scorecards:
    st.subheader("Detailed Supplier Scorecards")

    if result and result.get("results"):
        supplier_names = [r["supplier_name"] for r in result["results"]]
        chosen = st.selectbox("Select supplier", supplier_names)
        supplier_result = next(r for r in result["results"] if r["supplier_name"] == chosen)

        c1, c2, c3 = st.columns(3)
        c1.metric("Final Rank", supplier_result["final_rank"])
        c2.metric("Absolute Score", supplier_result["absolute_score"])
        c3.metric("Peer Performance Index (PPI)", supplier_result["ppi"])

        st.markdown("##### Criterion breakdown")
        crit_rows = []
        for c in supplier_result["criteria_detail"]:
            crit_rows.append({
                "Criterion": c["name"],
                "Weight %": c["weight"],
                "Score": c["score"],
                "Max": c["max_score"],
                "Benchmark": c["benchmark_score"],
                "Gap": c["gap"],
                "Relative %": c["relative_pct"],
                "Defaulted?": "⚠️" if c["was_defaulted"] else "",
            })
        st.dataframe(pd.DataFrame(crit_rows), use_container_width=True, hide_index=True)

        with st.expander("Evidence & justification per criterion"):
            for c in supplier_result["criteria_detail"]:
                st.markdown(f"**{c['name']}** — score {c['score']}/{c['max_score']}")
                st.write(f"Justification: {c['justification']}")
                st.write(f"Evidence: {c['evidence']}")
                st.divider()

        st.markdown("##### Risks identified")
        for risk in supplier_result["risks"]:
            st.write(f"- {risk}")

        st.markdown("##### Overall summary")
        st.info(supplier_result["overall_summary"])

        if supplier_result["warnings"]:
            st.markdown("##### Validation warnings")
            for w in supplier_result["warnings"]:
                st.warning(w)
    else:
        st.info("No evaluation run yet.")

# ---------------------------------------------------------------------------
# Screen 5: Run Details
# ---------------------------------------------------------------------------
with tab_run_details:
    st.subheader("Run Details")

    if result and result.get("results"):
        st.markdown(f"**RFP_RUN_ID:** `{result['rfp_run_id']}`")
        st.markdown(f"**Created at:** {result['created_at']}")
        st.markdown(f"**Status:** {result['status']}")

        st.markdown("##### Tie-break rule order")
        for i, rule in enumerate(result.get("tie_break_order", []), start=1):
            st.write(f"{i}. {rule}")

        st.markdown("##### Criteria snapshot used for this run")
        st.dataframe(pd.DataFrame(result["criteria"]), use_container_width=True, hide_index=True)

        all_warnings = {r["supplier_name"]: r["warnings"] for r in result["results"] if r["warnings"]}
        if all_warnings:
            st.markdown("##### Validation / error cases")
            for supplier, warns in all_warnings.items():
                with st.expander(f"{supplier} ({len(warns)} warning(s))"):
                    for w in warns:
                        st.warning(w)
        else:
            st.success("No validation warnings for this run.")

        st.markdown("##### Download complete result")
        st.download_button(
            "⬇️ Download run as JSON",
            data=json.dumps(result, indent=2),
            file_name=f"rfp_run_{result['rfp_run_id']}.json",
            mime="application/json",
        )
    else:
        st.info("No evaluation run yet.")
