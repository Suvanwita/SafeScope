import pandas as pd
import streamlit as st

from src.anomaly_detection import detect_anomalies
from src.pipeline import build_crime_pipeline
from src.recommendations import generate_safety_recommendations
from src.risk_score import calculate_grid_risk
from src.ui import render_disclaimer, render_sidebar
from src.visualizations import create_area_grid


st.set_page_config(page_title="Report | SafeScope", layout="wide")
render_sidebar("Report")
st.title("Report")
st.caption("Enter a location and time to get recommendations based on historical trained patterns.")
render_disclaimer()

uploaded_file = st.sidebar.file_uploader("Upload historical CSV", type=["csv"])
try:
    if uploaded_file is not None:
        df = build_crime_pipeline(uploaded_file)
        st.success("Historical data loaded. Recommendations will use models and scores from this dataset.")
    elif "cleaned_df" in st.session_state:
        df = st.session_state["cleaned_df"]
    else:
        df = build_crime_pipeline()
        st.session_state["active_data_source"] = "Sample data"
except Exception as error:
    st.error(f"Unable to prepare historical data for recommendations: {error}")
    st.stop()

if df.empty:
    st.info("No valid historical records remain after preprocessing.")
    st.stop()

with st.spinner("Training/scoring historical patterns..."):
    risk_grid = calculate_grid_risk(create_area_grid(df))
    anomaly_df = detect_anomalies(df)
    st.session_state["risk_grid"] = risk_grid
    st.session_state["anomaly_df"] = anomaly_df

if risk_grid.empty:
    st.info("No grid summary is available for the current historical dataset.")
    st.stop()

st.subheader("User Query")
st.write("Enter the location and time you want to ask about. This input is not used for training.")

default_lat = float(df["latitude"].mean())
default_lon = float(df["longitude"].mean())
with st.form("user_query_form"):
    query_col1, query_col2, query_col3, query_col4 = st.columns(4)
    query_latitude = query_col1.number_input("Latitude", min_value=-90.0, max_value=90.0, value=default_lat, format="%.6f")
    query_longitude = query_col2.number_input("Longitude", min_value=-180.0, max_value=180.0, value=default_lon, format="%.6f")
    selected_hour = query_col3.selectbox("Hour", list(range(24)), index=20)
    selected_day = query_col4.selectbox(
        "Day",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    )
    submitted = st.form_submit_button("Generate recommendations")

if not submitted and "last_query" in st.session_state:
    query_latitude, query_longitude, selected_hour, selected_day = st.session_state["last_query"]
else:
    st.session_state["last_query"] = (query_latitude, query_longitude, selected_hour, selected_day)

risk_grid = risk_grid.copy()
risk_grid["distance_to_query"] = (
    (risk_grid["latitude_center"] - query_latitude) ** 2
    + (risk_grid["longitude_center"] - query_longitude) ** 2
) ** 0.5
selected_area = risk_grid.sort_values("distance_to_query").iloc[0]

lat_grid = round(float(selected_area["latitude_center"]), 2)
lon_grid = round(float(selected_area["longitude_center"]), 2)
area_df = df[(df["latitude"].round(2) == lat_grid) & (df["longitude"].round(2) == lon_grid)].copy()
time_matched_df = area_df[(area_df["hour"] == selected_hour) & (area_df["day_name"] == selected_day)]
context_df = time_matched_df if not time_matched_df.empty else area_df

top_crime_types = context_df["crime_type"].value_counts().head(5).reset_index()
top_crime_types.columns = ["crime_type", "incident_count"]
peak_hours = area_df.groupby("hour").size().reset_index(name="incident_count").sort_values("incident_count", ascending=False)

anomaly_count = 0
if not anomaly_df.empty and {"latitude_grid", "longitude_grid", "anomaly_label"}.issubset(anomaly_df.columns):
    anomaly_count = int(
        anomaly_df[
            (anomaly_df["latitude_grid"] == lat_grid)
            & (anomaly_df["longitude_grid"] == lon_grid)
            & (anomaly_df["anomaly_label"] == "unusual spike")
        ].shape[0]
    )

area_summary = selected_area.to_dict()
area_summary["weekend_ratio"] = float(area_df["weekend"].mean()) if not area_df.empty else 0
area_summary["anomaly_count"] = anomaly_count
area_summary["top_crime_type"] = top_crime_types.iloc[0]["crime_type"] if not top_crime_types.empty else selected_area["top_crime_type"]

recommendations = generate_safety_recommendations(
    area_summary,
    selected_hour=int(selected_hour),
    selected_day=selected_day,
)

risk_score = float(selected_area["risk_score"])
if risk_score >= 61:
    risk_explanation = "Higher historical incident pattern near the queried location based on density, severity, and time-pattern signals."
elif risk_score >= 31:
    risk_explanation = "Moderate historical incident pattern near the queried location based on density, severity, and time-pattern signals."
else:
    risk_explanation = "Lower historical incident pattern near the queried location based on density, severity, and time-pattern signals."

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("Nearest grid incidents", int(selected_area["incident_count"]))
metric_col2.metric("Risk score", f"{risk_score:.1f}")
metric_col3.metric("Night ratio", f"{float(selected_area['night_ratio']) * 100:.1f}%")
metric_col4.metric("Unusual spikes", anomaly_count)

left, right = st.columns([1, 1])
with left:
    st.subheader("Nearest Historical Area Summary")
    summary_table = pd.DataFrame(
        [
            {
                "query_latitude": query_latitude,
                "query_longitude": query_longitude,
                "nearest_latitude_center": selected_area["latitude_center"],
                "nearest_longitude_center": selected_area["longitude_center"],
                "selected_hour": selected_hour,
                "selected_day": selected_day,
                "incident_count": int(selected_area["incident_count"]),
                "avg_severity": selected_area["avg_severity"],
                "night_ratio": selected_area["night_ratio"],
                "weekend_ratio": round(area_summary["weekend_ratio"], 3),
                "top_crime_type": area_summary["top_crime_type"],
                "risk_score": risk_score,
                "risk_label": selected_area["risk_label"],
            }
        ]
    )
    st.dataframe(summary_table, use_container_width=True, hide_index=True)

with right:
    st.subheader("Risk Explanation")
    st.info(risk_explanation)
    if time_matched_df.empty:
        st.warning("No exact historical records matched the selected day and hour in the nearest grid. Showing nearest-area context instead.")
    st.markdown("**User query**")
    st.markdown(f"- Latitude: `{query_latitude:.6f}`")
    st.markdown(f"- Longitude: `{query_longitude:.6f}`")
    st.markdown(f"- Hour: `{selected_hour}`")
    st.markdown(f"- Day: `{selected_day}`")

table_col1, table_col2 = st.columns(2)
with table_col1:
    st.subheader("Top Incident Types Near Query")
    st.dataframe(top_crime_types, use_container_width=True, hide_index=True)
with table_col2:
    st.subheader("Peak Historical Hours Near Query")
    st.dataframe(peak_hours.head(8), use_container_width=True, hide_index=True)

st.subheader("Recommendations")
for recommendation in recommendations:
    st.markdown(f"- {recommendation}")

report_rows = []
for recommendation in recommendations:
    row = summary_table.iloc[0].to_dict()
    row["risk_explanation"] = risk_explanation
    row["recommendation"] = recommendation
    report_rows.append(row)
report_df = pd.DataFrame(report_rows)

report_text = "\n".join(
    [
        "SafeScope Query Report",
        "",
        f"Query latitude: {query_latitude:.6f}",
        f"Query longitude: {query_longitude:.6f}",
        f"Query hour: {selected_hour}",
        f"Query day: {selected_day}",
        f"Nearest grid center: {selected_area['latitude_center']:.6f}, {selected_area['longitude_center']:.6f}",
        f"Risk score: {risk_score:.1f}",
        f"Risk explanation: {risk_explanation}",
        f"Top incident type: {area_summary['top_crime_type']}",
        f"Unusual spikes near grid: {anomaly_count}",
        "",
        "Top incident types near query:",
        *[f"- {row.crime_type}: {row.incident_count}" for row in top_crime_types.itertuples()],
        "",
        "Peak historical hours near query:",
        *[f"- {int(row.hour)}:00 | {row.incident_count} incidents" for row in peak_hours.head(8).itertuples()],
        "",
        "Recommendations:",
        *[f"- {item}" for item in recommendations],
        "",
        "Ethical note: This report uses historical public incident patterns for awareness and planning only.",
    ]
)

download_col1, download_col2 = st.columns(2)
with download_col1:
    st.download_button(
        "Download CSV report",
        data=report_df.to_csv(index=False),
        file_name="safescope_query_report.csv",
        mime="text/csv",
    )
with download_col2:
    st.download_button(
        "Download text report",
        data=report_text,
        file_name="safescope_query_report.txt",
        mime="text/plain",
    )
