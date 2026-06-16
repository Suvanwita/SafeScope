import streamlit as st


DISCLAIMER = (
    "SafeScope uses historical public incident data for awareness and planning only. "
    "It does not predict real-time danger, guarantee safety, replace emergency services, "
    "or make legal/policing decisions."
)


def render_sidebar(current_page: str) -> None:
    """Render a consistent SafeScope sidebar."""
    with st.sidebar:
        st.title("SafeScope")
        st.caption("Women Safety Pattern Analyzer")
        st.markdown(f"**Current page:** {current_page}")
        st.info("Use Data Explorer first to load or refresh the cleaned dataset.")
        st.markdown("**Workflow**")
        st.markdown("- Data Explorer\n- Risk Map\n- Time Analysis\n- ML Insights\n- Report")


def render_disclaimer() -> None:
    """Render the project ethical disclaimer."""
    st.info(DISCLAIMER)


def require_cleaned_data():
    """Return cleaned data from session state or stop with a clear instruction."""
    if "cleaned_df" not in st.session_state:
        st.warning("Please go to Data Explorer first to load and preprocess the dataset.")
        st.stop()

    df = st.session_state["cleaned_df"]
    if df.empty:
        st.info("The cleaned dataset is empty. Please load a valid CSV in Data Explorer.")
        st.stop()
    return df
