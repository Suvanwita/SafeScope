import streamlit as st
import plotly.express as px

from src.feature_engineering import summary_metrics
from src.pipeline import build_crime_pipeline, get_session_or_sample_data
from src.ui import render_disclaimer, render_sidebar


st.set_page_config(page_title="Data Explorer | SafeScope", layout="wide")
render_sidebar("Data Explorer")
st.title("Data Explorer")
st.caption("Review, filter, and understand the incident dataset.")
render_disclaimer()

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
try:
    df = build_crime_pipeline(uploaded_file) if uploaded_file else get_session_or_sample_data()
except Exception as error:
    st.error(f"Unable to load this dataset: {error}")
    st.stop()

st.session_state["cleaned_df"] = df
if df.empty:
    st.info("No valid rows remain after preprocessing. Check date and coordinate columns in the uploaded CSV.")
    st.stop()

st.subheader("Dataset Overview")
shape_col, start_col, end_col = st.columns(3)
shape_col.metric("Rows x columns", f"{df.shape[0]} x {df.shape[1]}")
start_col.metric("Start date", df["date"].min().date())
end_col.metric("End date", df["date"].max().date())

preview_tab, missing_tab, types_tab = st.tabs(["Preview", "Missing Values", "Top Crime Types"])
with preview_tab:
    st.dataframe(df.head(20), use_container_width=True, hide_index=True)
with missing_tab:
    missing_values = df.isna().sum().reset_index()
    missing_values.columns = ["column", "missing_values"]
    st.dataframe(missing_values, use_container_width=True, hide_index=True)
with types_tab:
    top_types = df["crime_type"].value_counts().head(10).reset_index()
    top_types.columns = ["crime_type", "incidents"]
    st.dataframe(top_types, use_container_width=True, hide_index=True)

years = st.sidebar.multiselect("Year", sorted(df["year"].dropna().unique()), default=sorted(df["year"].dropna().unique()))
crime_types = st.sidebar.multiselect("Crime type", sorted(df["crime_type"].unique()), default=sorted(df["crime_type"].unique()))
hour_range = st.sidebar.slider("Hour range", 0, 23, (0, 23))
days = st.sidebar.multiselect("Day", sorted(df["day_name"].unique()), default=sorted(df["day_name"].unique()))

filtered = df[
    df["year"].isin(years)
    & df["crime_type"].isin(crime_types)
    & df["hour"].between(hour_range[0], hour_range[1])
    & df["day_name"].isin(days)
]

metrics = summary_metrics(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Incidents", metrics["total_incidents"])
col2.metric("Night share", f"{metrics['night_share']}%")
col3.metric("Domestic share", f"{metrics['domestic_share']}%")
col4.metric("Top type", metrics["top_type"])

st.subheader("Filtered Records")
if filtered.empty:
    st.info("No records match the current filters.")
else:
    st.dataframe(filtered, use_container_width=True, hide_index=True)

st.subheader("Charts")
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    crime_counts = filtered["crime_type"].value_counts().reset_index()
    crime_counts.columns = ["crime_type", "incidents"]
    st.plotly_chart(
        px.bar(crime_counts, x="incidents", y="crime_type", orientation="h", title="Crime Type Count"),
        use_container_width=True,
    )
with chart_col2:
    yearly = filtered.groupby("year").size().reset_index(name="incidents")
    st.plotly_chart(px.bar(yearly, x="year", y="incidents", title="Incidents by Year"), use_container_width=True)

chart_col3, chart_col4 = st.columns(2)
with chart_col3:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day = filtered["day_name"].value_counts().reindex(day_order, fill_value=0).reset_index()
    by_day.columns = ["day_name", "incidents"]
    st.plotly_chart(px.bar(by_day, x="day_name", y="incidents", title="Incidents by Day of Week"), use_container_width=True)
with chart_col4:
    by_hour = filtered.groupby("hour").size().reset_index(name="incidents")
    st.plotly_chart(px.line(by_hour, x="hour", y="incidents", markers=True, title="Incidents by Hour"), use_container_width=True)

st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False),
    file_name="safescope_filtered_incidents.csv",
    mime="text/csv",
)
