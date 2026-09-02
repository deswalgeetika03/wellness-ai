import streamlit as st

from query_pipeline import get_vector_db, answer_query


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Wellness RAG Bot",
    page_icon="🧠",
    layout="centered"
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🧠 Wellness RAG Bot")
st.write(
    "An AI-powered wellness information assistant using "
    "Retrieval-Augmented Generation (RAG), IBM Granite, "
    "and a deterministic safety layer."
)

st.divider()


# ---------------------------------------------------------
# LOAD VECTOR DATABASE
# ---------------------------------------------------------

@st.cache_resource
def load_vector_db():
    return get_vector_db()


try:
    vector_db = load_vector_db()
except Exception as error:
    st.error(
        f"Unable to load the wellness knowledge base.\n\n"
        f"{type(error).__name__}: {error}"
    )
    st.stop()


# ---------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------

question = st.text_area(
    "Ask a wellness-related question:",
    placeholder="Example: What are common symptoms of anxiety?",
    height=100
)


# ---------------------------------------------------------
# GENERATE ANSWER
# ---------------------------------------------------------

if st.button("Get Answer", type="primary"):

    if not question.strip():
        st.warning("Please enter a question first.")
        st.stop()

    with st.spinner("Processing your question..."):
        try:
            result = answer_query(vector_db, question.strip())

        except Exception as error:
            st.error(
                f"An error occurred while processing your question.\n\n"
                f"{type(error).__name__}: {error}"
            )
            st.stop()

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    st.subheader("Response")

    st.write(result.get("answer", ""))


    # -----------------------------------------------------
    # ROUTE
    # -----------------------------------------------------

    route = result.get("route", "unknown")

    with st.expander("Pipeline information"):

        st.write(f"**Route:** `{route}`")

        sources = result.get("sources", [])

        if sources:
            st.write("**Sources used:**")

            for source in sources:
                organization = source.get("organization", "Unknown")
                title = source.get("title", "Unknown")

                st.write(
                    f"- **{organization}** — {title}"
                )

        else:
            st.write("No retrieval sources were used for this response.")


# ---------------------------------------------------------
# RESPONSIBLE AI NOTICE
# ---------------------------------------------------------

st.divider()

st.caption(
    "This prototype provides educational wellness information and "
    "is not a substitute for professional medical advice. "
    "Safety-sensitive requests are handled by a deterministic "
    "safety layer before retrieval and generation."
)