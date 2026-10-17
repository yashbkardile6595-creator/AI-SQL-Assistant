"""Streamlit UI for the local AI SQL Assistant."""
import os
import streamlit as st
import pandas as pd
from sql_assistant import SQLAssistant, OLLAMA_MODEL

st.set_page_config(page_title="AI SQL Assistant", page_icon="📊", layout="wide")
st.title("📊 AI SQL Assistant")
st.caption("Ask questions about your sales database in plain English. SQL is generated locally with Ollama.")

with st.sidebar:
    st.header("Configuration")
    st.write(f"**Model:** `{OLLAMA_MODEL}`")
    st.write("**Database:** `data/sales.db`")
    st.info("Review the generated SQL before running it. This starter allows read-only SELECT queries.")
    st.markdown("**Try asking**")
    st.markdown("- Which product generated the highest revenue?")
    st.markdown("- Show total revenue by product.")
    st.markdown("- Which products have fewer than 20 units in stock?")

@st.cache_resource
def get_assistant():
    return SQLAssistant()

try:
    assistant = get_assistant()
except Exception as exc:
    st.error(f"Could not initialize the assistant: {exc}")
    st.info("Check that you ran `python setup_database.py`, Ollama is running, and the selected model is installed.")
    st.stop()

question = st.text_area(
    "What would you like to know?",
    placeholder="e.g. Which product generated the highest revenue?",
    height=90
)

if st.button("Generate SQL", type="primary", disabled=not question.strip()):
    try:
        with st.spinner("Reading schema and generating SQL with your local model..."):
            sql = assistant.generate_sql(question)
        st.session_state["pending_sql"] = sql
        st.session_state["pending_question"] = question
        st.session_state.pop("query_result", None)
    except Exception as exc:
        st.error(f"Could not generate a safe query: {exc}")

if st.session_state.get("pending_sql"):
    st.subheader("Review generated SQL")
    st.code(st.session_state["pending_sql"], language="sql")
    st.warning("Check the query before execution. Clicking Run query confirms that you want to execute this read-only SELECT.")
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Run query", type="primary"):
            try:
                with st.spinner("Executing query in read-only mode..."):
                    rows = assistant.execute_sql(st.session_state["pending_sql"])
                st.session_state["query_result"] = rows
            except Exception as exc:
                st.error(f"Query failed: {exc}")
    with col2:
        if st.button("Discard query"):
            st.session_state.pop("pending_sql", None)
            st.session_state.pop("pending_question", None)
            st.session_state.pop("query_result", None)
            st.rerun()

if "query_result" in st.session_state:
    st.subheader("Results")
    rows = st.session_state["query_result"]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(f"Returned {len(rows)} row(s), maximum 100.")
    else:
        st.info("The query ran successfully but returned no rows.")
