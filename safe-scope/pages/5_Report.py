import pandas as pd
import streamlit as st

from src.anomaly_detection import detect_anomalies
from src.recommendations import generate_safety_recommendations
from src.risk_score import calculate_grid_risk
from src.ui import render_disclaimer, render_sidebar, require_cleaned_data
from src.visualizations import create_area_grid


st.set_page_config(page_title="Report | SafeScope", layout="wide")
render_sidebar("Report")
st.title("Report")
st.caption("Build an explainable, downloadable awareness report for a selected grid area.")
render_disclaimer()

df = require_cleaned_data()

if "risk_grid" in st.session_state:
    risk_grid = st.session_state["risk_grid"].copy()
else:
    risk_grid = calculate_grid_risk(create_area_grid(df))
    st.session_state["risk_grid"] = risk_grid

if "anomaly_df" in st.session_state:
    anomaly_df = st.session_state["anomaly_df"].copy()
else:
    anomaly_df = detect_anomalies(df)
    st.session_state["anomaly_df"] = anomaly_df

if risk_grid.empty:
    st.info("No grid summary is available for the current dataset.")
    st.stop()

risk_grid = risk_grid.reset_index(drop=True)
risk_grid["grid_label"] = risk_grid.apply(
    lambda row: f"{row['latitude_center']:.4f}, {row['longitude_center']:.4f} | {row['top_crime_type']}",
    axis=1,
)

selected_label = st.sidebar.selectbox("Area/grid", risk_grid["grid_label"].tolist())
selected_hour = st.sidebar.selectbox("Time/hour", ["All"] + list(range(24)))
day_order = ["All", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
selected_day = st.sidebar.selectbox("Day", day_order)

selected_area = risk_grid[risk_grid["grid_label"] == selected_label].iloc[0]
lat_grid = round(float(selected_area["latitude_center"]), 2)
lon_grid = round(float(selected_area["longitude_center"]), 2)

area_df = df[(df["latitude"].round(2) == lat_grid) & (df["longitude"].round(2) == lon_grid)].copy()
if selected_hour != "All":
    area_df = area_df[area_df["hour"] == selected_hour]
if selected_day != "All":
    area_df = area_df[area_df["day_name"] == selected_day]

if area_df.empty:
    st.info("No incidents match the selected area, hour, and day filters.")
    st.stop()

top_crime_types = area_df["crime_type"].value_counts().head(5).reset_index()
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
area_summary["weekend_ratio"] = float(area_df["weekend"].mean())
area_summary["anomaly_count"] = anomaly_count
area_summary["top_crime_type"] = top_crime_types.iloc[0]["crime_type"] if not top_crime_types.empty else "N/A"

recommendations = generate_safety_recommendations(
    area_summary,
    selected_hour=None if selected_hour == "All" else int(selected_hour),
    selected_day=None if selected_day == "All" else selected_day,
)

risk_score = float(selected_area["risk_score"])
if risk_score >= 61:
    risk_explanation = "Higher historical incident pattern based on density, severity, and time-pattern signals."
elif risk_score >= 31:
    risk_explanation = "Moderate historical incident pattern based on density, severity, and time-pattern signals."
else:
    risk_explanation = "Lower historical incident pattern based on density, severity, and time-pattern signals."

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
metric_col1.metric("Selected incidents", len(area_df))
metric_col2.metric("Risk score", f"{risk_score:.1f}")
metric_col3.metric("Night ratio", f"{float(selected_area['night_ratio']) * 100:.1f}%")
metric_col4.metric("Unusual spikes", anomaly_count)

left, right = st.columns([1, 1])
with left:
    st.subheader("Selected Area Summary")
    summary_table = pd.DataFrame(
        [
            {
                "latitude_center": selected_area["latitude_center"],
                "longitude_center": selected_area["longitude_center"],
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
    st.markdown("**Selected filters**")
    st.markdown(f"- Hour: `{selected_hour}`")
    st.markdown(f"- Day: `{selected_day}`")

table_col1, table_col2 = st.columns(2)
with table_col1:
    st.subheader("Top Crime Types")
    st.dataframe(top_crime_types, use_container_width=True, hide_index=True)
with table_col2:
    st.subheader("Peak Incident Hours")
    st.dataframe(peak_hours.head(8), use_container_width=True, hide_index=True)

st.subheader("Safety Recommendations")
for recommendation in recommendations:
    st.markdown(f"- {recommendation}")

report_rows = []
for recommendation in recommendations:
    row = summary_table.iloc[0].to_dict()
    row["selected_hour"] = selected_hour
    row["selected_day"] = selected_day
    row["risk_explanation"] = risk_explanation
    row["recommendation"] = recommendation
    report_rows.append(row)
report_df = pd.DataFrame(report_rows)

report_text = "\n".join(
    [
        "SafeScope Awareness Report",
        "",
        f"Area/grid: {selected_label}",
        f"Selected hour: {selected_hour}",
        f"Selected day: {selected_day}",
        f"Risk score: {risk_score:.1f}",
        f"Risk explanation: {risk_explanation}",
        f"Incident count in selected filters: {len(area_df)}",
        f"Top crime type: {area_summary['top_crime_type']}",
        f"Unusual spikes: {anomaly_count}",
        "",
        "Top crime types:",
        *[f"- {row.crime_type}: {row.incident_count}" for row in top_crime_types.itertuples()],
        "",
        "Peak incident hours:",
        *[f"- {int(row.hour)}:00 | {row.incident_count} incidents" for row in peak_hours.head(8).itertuples()],
        "",
        "Recommendations:",
        *[f"- {item}" for item in recommendations],
        "",
        "Ethical note: This report summarizes historical public incident patterns for awareness and planning only.",
    ]
)

download_col1, download_col2 = st.columns(2)
with download_col1:
    st.download_button(
        "Download CSV report",
        data=report_df.to_csv(index=False),
        file_name="safescope_area_report.csv",
        mime="text/csv",
    )
with download_col2:
    st.download_button(
        "Download text report",
        data=report_text,
        file_name="safescope_area_report.txt",
        mime="text/plain",
    )
