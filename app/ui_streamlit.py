import os
import sys
import json
import pandas as pd
import streamlit as st
import uuid


# This ensure project root is on PYTHONPATH
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.pdf_router import route_pdf
from app.orchestrator_text import run_text_pipeline, summarize_report
from app.orchestrator_vision import run_vision_pipeline



def save_uploaded_file(uploaded_file) -> str:
    os.makedirs("artifacts", exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{uploaded_file.name}"
    out_path = os.path.join("artifacts", safe_name)

    with open(out_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return out_path


def main():
    st.title("Agentic AI Workflow for Data Extraction From Bank Statements")
    st.info(
    "🧪 **UI Sample Only**\n\n"
    "This public demo showcases the **agentic workflow and UI behavior**.\n\n"
    "❗ Running extraction requires a valid OpenAI API key, which is **not configured** "
    "in this hosted environment.\n\n"
    "To run the full system, clone the repository and configure your `.env` file locally.",
    icon="ℹ️",
    )

    uploaded = st.file_uploader("Upload a bank statement PDF", type=["pdf"])
    bank_choice = st.selectbox(
        "Please, select a bank",
        ["Commerce Bank", "SAMPLE"],
    )

    if uploaded is None:
        st.info("Upload a PDF to begin.")
        return

    pdf_path = save_uploaded_file(uploaded)
    st.write("Saved file:", pdf_path)

    router_result = route_pdf(pdf_path)
    st.subheader("Router decision")
    st.json(router_result)

    if st.button("Extract and Validate"):
        with st.spinner("Running extraction + validation..."):

            if router_result.get("route") == "TEXT":
                pipeline = run_text_pipeline
            else:
                pipeline = run_vision_pipeline

            final_table, final_report, meta = pipeline(
                pdf_path,
                max_rounds=2,
                min_pass_rate=0.90,
                configured_bank_name=bank_choice,
            )

        summary = summarize_report(final_report)

        st.subheader("Final table")
        st.dataframe(pd.DataFrame([final_table]))

        st.subheader("Validation summary")
        st.json(summary)

        st.subheader("Validation report (per field)")
        st.dataframe(pd.DataFrame(final_report))

        st.subheader("Raw JSON output")
        st.code(json.dumps(final_table, indent=2), language="json")

        st.subheader("Run metadata")
        st.json(meta)


if __name__ == "__main__":
    main()
