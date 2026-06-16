import streamlit as st
from streamlit_folium import st_folium

from src.risk_score import calculate_grid_risk
from src.visualizations import create_area_grid, create_heatmap, create_incident_map


st.set_page_config(page_title="Risk Map | SafeScope", layout="wide")
st.title("Risk Map")
st.caption("Geospatial view of historical incident density, severity, and time patterns.")

if "cleaned_df" not in st.session_state:
    st.warning("Please go to Data Explorer first to load and preprocess the dataset.")
    st.stop()

df = st.session_state["cleaned_df"]

if df.empty:
    st.info("The cleaned dataset is empty. Please load a valid CSV in Data Explorer.")
    st.stop()

st.info(
    "Risk score is based on historical incident density, severity, and time patterns. "
    "It should be used only for awareness."
)

crime_types = st.sidebar.multiselect(
    "Crime type",
    sorted(df["crime_type"].dropna().unique()),
    default=sorted(df["crime_type"].dropna().unique()),
)
years = st.sidebar.multiselect(
    "Year",
    sorted(df["year"].dropna().unique()),
    default=sorted(df["year"].dropna().unique()),
)
hour_range = st.sidebar.slider("Hour range", 0, 23, (0, 23))
max_points = st.sidebar.slider("Max marker points", 100, 3000, 1000, step=100)

filtered = df[
    df["crime_type"].isin(crime_types)
    & df["year"].isin(years)
    & df["hour"].between(hour_range[0], hour_range[1])
].copy()

if filtered.empty:
    st.info("No incidents match the current filters.")
    st.stop()

grid_df = create_area_grid(filtered)
risk_grid = calculate_grid_risk(grid_df)

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric("Filtered incidents", len(filtered))
metric_col2.metric("Grid cells", len(risk_grid))
metric_col3.metric("Markers shown", min(len(filtered), max_points))

tab1, tab2 = st.tabs(["Heatmap", "Incident Markers"])
with tab1:
    st_folium(create_heatmap(filtered), width=None, height=560)
with tab2:
    st_folium(create_incident_map(filtered, max_points=max_points), width=None, height=560)

top_columns = [
    "latitude_center",
    "longitude_center",
    "incident_count",
    "avg_severity",
    "night_ratio",
    "top_crime_type",
    "risk_score",
    "risk_label",
]
if "recent_activity" in risk_grid.columns:
    top_columns.insert(5, "recent_activity")

st.subheader("Top 10 Higher-Risk Grid Cells")
st.dataframe(risk_grid.head(10)[top_columns], use_container_width=True, hide_index=True)

st.subheader("Area-Wise Risk Score Table")
st.dataframe(risk_grid[top_columns], use_container_width=True, hide_index=True)
