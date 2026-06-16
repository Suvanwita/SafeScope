import streamlit as st

from src.feature_engineering import summary_metrics
from src.pipeline import build_crime_pipeline, get_session_or_sample_data
from src.recommendations import generate_recommendations
from src.risk_score import calculate_area_risk
from src.visualizations import hourly_chart, risk_score_chart


st.set_page_config(page_title="Report | SafeScope", layout="wide")
st.title("Report")
st.caption("Generate a concise awareness report from the current dataset.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
try:
    df = build_crime_pipeline(uploaded_file) if uploaded_file else get_session_or_sample_data()
except ValueError as error:
    st.error(str(error))
    st.stop()

area_risk = calculate_area_risk(df)
metrics = summary_metrics(df)
recommendations = generate_recommendations(df, area_risk)

st.warning(
    "SafeScope uses historical public incident data for awareness and planning only. It does not predict real-time danger, "
    "guarantee safety, replace emergency services, or make legal/policing decisions."
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Incidents", metrics["total_incidents"])
col2.metric("Night share", f"{metrics['night_share']}%")
col3.metric("Domestic share", f"{metrics['domestic_share']}%")
col4.metric("Top type", metrics["top_type"])

left, right = st.columns(2)
with left:
    st.plotly_chart(risk_score_chart(area_risk), use_container_width=True)
with right:
    st.plotly_chart(hourly_chart(df), use_container_width=True)

st.subheader("Key Findings")
if not area_risk.empty:
    top = area_risk.iloc[0]
    st.markdown(
        f"- Highest sample risk score: community area **{int(top['community_area'])}** "
        f"with score **{top['risk_score']}** and **{int(top['incident_count'])}** incidents."
    )
st.markdown(f"- Most common incident type: **{metrics['top_type']}**.")
st.markdown(f"- Night-time records make up **{metrics['night_share']}%** of the current dataset.")

st.subheader("Recommendations")
for item in recommendations:
    st.markdown(f"- {item}")

report_text = "\n".join(
    [
        "SafeScope Awareness Report",
        "",
        f"Total incidents: {metrics['total_incidents']}",
        f"Night-time share: {metrics['night_share']}%",
        f"Domestic share: {metrics['domestic_share']}%",
        f"Most common type: {metrics['top_type']}",
        "",
        "Recommendations:",
        *[f"- {item}" for item in recommendations],
    ]
)

st.download_button(
    "Download report text",
    data=report_text,
    file_name="safescope_report.txt",
    mime="text/plain",
)
