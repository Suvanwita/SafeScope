import streamlit as st

from src.pipeline import build_crime_pipeline, get_session_or_sample_data
from src.visualizations import hourly_chart, monthly_chart, weekday_chart


st.set_page_config(page_title="Time Analysis | SafeScope", layout="wide")
st.title("Time Analysis")
st.caption("Explore when incidents appear most often in the historical sample.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
try:
    df = build_crime_pipeline(uploaded_file) if uploaded_file else get_session_or_sample_data()
except ValueError as error:
    st.error(str(error))
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("Peak hour", int(df.groupby("hour").size().idxmax()))
col2.metric("Weekend incidents", int(df["weekend"].sum()))
col3.metric("Night incidents", int(df["is_night"].sum()))

tab1, tab2, tab3 = st.tabs(["Hourly", "Weekday", "Monthly"])
with tab1:
    st.plotly_chart(hourly_chart(df), use_container_width=True)
with tab2:
    st.plotly_chart(weekday_chart(df), use_container_width=True)
with tab3:
    st.plotly_chart(monthly_chart(df), use_container_width=True)

st.subheader("Time Pattern Table")
time_summary = (
    df.groupby(["day_name", "hour"])
    .size()
    .reset_index(name="incidents")
    .sort_values("incidents", ascending=False)
)
st.dataframe(time_summary, use_container_width=True, hide_index=True)
