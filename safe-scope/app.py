import streamlit as st

from src.data_loader import get_data
from src.feature_engineering import prepare_features, summary_metrics
from src.preprocessing import clean_data, normalize_columns, validate_columns
from src.recommendations import page_notes
from src.risk_score import calculate_area_risk


st.set_page_config(
    page_title="SafeScope",
    layout="wide",
    initial_sidebar_state="expanded",
)


DISCLAIMER = (
    "SafeScope uses historical public incident data for awareness and planning only. "
    "It does not predict real-time danger, guarantee safety, replace emergency services, "
    "or make legal/policing decisions."
)


def render_metric_cards(metrics: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sample incidents", metrics["total_incidents"])
    col2.metric("Night-time share", f"{metrics['night_share']}%")
    col3.metric("Domestic share", f"{metrics['domestic_share']}%")
    col4.metric("Most common type", metrics["top_type"])


def render_page_cards() -> None:
    notes = page_notes()
    rows = [st.columns(2), st.columns(2), st.columns(1)]
    page_items = list(notes.items())
    for index, (name, note) in enumerate(page_items):
        row = rows[0] if index < 2 else rows[1] if index < 4 else rows[2]
        with row[index % len(row)]:
            st.container(border=True).markdown(f"**{name}**\n\n{note}")


def main() -> None:
    with st.sidebar:
        st.title("SafeScope")
        st.caption("Women Safety Pattern Analyzer")
        st.info("Start with the sample data or upload a Chicago crime style CSV from any page.")
        st.markdown("**Pages**")
        st.markdown("- Data Explorer\n- Risk Map\n- Time Analysis\n- ML Insights\n- Report")

    raw_df = normalize_columns(get_data())
    is_valid, missing = validate_columns(raw_df)
    if not is_valid:
        st.error(f"The bundled dataset is missing columns: {', '.join(missing)}")
        st.stop()

    df = prepare_features(clean_data(raw_df))
    metrics = summary_metrics(df)
    area_risk = calculate_area_risk(df)

    st.title("SafeScope")
    st.subheader("Women Safety Pattern Analyzer")
    st.write(
        "SafeScope is a beginner-friendly Streamlit application for exploring historical incident patterns. "
        "It combines data exploration, time analysis, maps, simple machine learning, and a printable-style report "
        "to support awareness and planning conversations."
    )

    st.warning(DISCLAIMER)
    render_metric_cards(metrics)

    left, right = st.columns([1.2, 0.8])
    with left:
        st.container(border=True).markdown(
            "### What this project does\n"
            "SafeScope cleans incident records, creates time and location features, scores community areas from "
            "sample-level patterns, and highlights clusters or unusual records using transparent machine learning methods."
        )
        st.container(border=True).markdown(
            "### How to navigate\n"
            "Use the left sidebar page menu to move through the app. Each page reuses the same modular Python helpers "
            "from `src/`, so it is easy to study or extend the code."
        )
    with right:
        st.container(border=True).markdown(
            f"### Highest sample risk area\n"
            f"Community area **{int(area_risk.iloc[0]['community_area'])}** currently has the highest sample risk score "
            f"at **{area_risk.iloc[0]['risk_score']}**."
        )
        st.container(border=True).markdown(
            "### Data note\n"
            "The bundled CSV is a compact educational sample inspired by public Chicago crime data fields. "
            "Replace it with official open data for real analysis."
        )

    st.markdown("## Page Guide")
    render_page_cards()


if __name__ == "__main__":
    main()
