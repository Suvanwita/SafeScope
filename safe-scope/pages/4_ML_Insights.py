import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from src.anomaly_detection import anomaly_summary, detect_anomalies
from src.clustering import run_dbscan_clustering


st.set_page_config(page_title="ML Insights | SafeScope", layout="wide")
st.title("ML Insights")
st.caption("Explainable clustering and anomaly detection for historical incident patterns.")

if "cleaned_df" not in st.session_state:
    st.warning("Please go to Data Explorer first to load and preprocess the dataset.")
    st.stop()

df = st.session_state["cleaned_df"]
if df.empty:
    st.info("The cleaned dataset is empty. Please load a valid CSV in Data Explorer.")
    st.stop()

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

st.sidebar.markdown("### DBSCAN")
eps = st.sidebar.slider("DBSCAN eps", 0.001, 0.050, 0.010, 0.001, format="%.3f")
min_samples = st.sidebar.slider("DBSCAN min_samples", 2, 50, 10)

st.sidebar.markdown("### Isolation Forest")
contamination = st.sidebar.slider("Contamination", 0.01, 0.30, 0.08, 0.01)

filtered = df[
    df["crime_type"].isin(crime_types)
    & df["year"].isin(years)
    & df["hour"].between(hour_range[0], hour_range[1])
].copy()

if filtered.empty:
    st.info("No incidents match the current filters.")
    st.stop()

clustered_df, cluster_summary = run_dbscan_clustering(filtered, eps=eps, min_samples=min_samples)
cluster_rows = cluster_summary[cluster_summary["cluster_id"] != -1]
noise_count = int((clustered_df["cluster_id"] == -1).sum()) if "cluster_id" in clustered_df.columns else 0

anomaly_df = detect_anomalies(filtered, contamination=contamination)
unusual_df = anomaly_summary(anomaly_df)


def cluster_center_map(summary_df: pd.DataFrame) -> folium.Map:
    """Render DBSCAN cluster centers as proportional circle markers."""
    if summary_df.empty:
        center = [filtered["latitude"].mean(), filtered["longitude"].mean()]
        return folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

    center = [summary_df["avg_latitude"].mean(), summary_df["avg_longitude"].mean()]
    cluster_map = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

    for _, row in summary_df.iterrows():
        popup = (
            f"<b>Cluster {int(row['cluster_id'])}</b><br>"
            f"Incidents: {int(row['incident_count'])}<br>"
            f"Avg severity: {row['avg_severity']}<br>"
            f"Night ratio: {row['night_ratio']}<br>"
            f"Top type: {row['top_crime_type']}"
        )
        folium.CircleMarker(
            location=[row["avg_latitude"], row["avg_longitude"]],
            radius=max(7, min(24, row["incident_count"] * 2)),
            color="#d95f02",
            fill=True,
            fill_opacity=0.75,
            popup=folium.Popup(popup, max_width=260),
        ).add_to(cluster_map)

    return cluster_map


def anomaly_time_chart(anomalies: pd.DataFrame) -> go.Figure:
    """Show incident counts over time with unusual spikes highlighted."""
    daily = (
        anomalies.groupby("date")
        .agg(
            incident_count=("incident_count", "sum"),
            unusual_spikes=("is_anomaly", "sum"),
        )
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"])
    spike_days = daily[daily["unusual_spikes"] > 0]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["incident_count"],
            mode="lines+markers",
            name="Daily incidents",
            line={"color": "#457b9d"},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=spike_days["date"],
            y=spike_days["incident_count"],
            mode="markers",
            name="Unusual spike",
            marker={"color": "#e76f51", "size": 12, "symbol": "diamond"},
        )
    )
    figure.update_layout(
        title="Incident Count Over Time with Anomalies Highlighted",
        xaxis_title="Date",
        yaxis_title="Incident count",
        legend_title="Pattern",
    )
    return figure


tab1, tab2 = st.tabs(["DBSCAN Hotspots", "Isolation Forest Anomalies"])

with tab1:
    st.info("DBSCAN finds dense geographic regions of incidents.")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Hotspot clusters", len(cluster_rows))
    metric_col2.metric("Noise points", noise_count)
    metric_col3.metric("Clustered incidents", len(clustered_df) - noise_count)

    st.subheader("Largest Clusters")
    if cluster_rows.empty:
        st.info("No hotspot clusters found with the current DBSCAN settings. Try increasing eps or lowering min_samples.")
    else:
        largest_clusters = cluster_rows.sort_values("incident_count", ascending=False).head(5)
        st.dataframe(largest_clusters, use_container_width=True, hide_index=True)

    st.subheader("Cluster Summary")
    st.dataframe(cluster_summary, use_container_width=True, hide_index=True)

    st.subheader("Cluster Center Map")
    st_folium(cluster_center_map(cluster_rows), width=None, height=520)

with tab2:
    st.info("Isolation Forest flags unusual spikes compared with normal incident patterns.")

    metric_col1, metric_col2 = st.columns(2)
    metric_col1.metric("Unusual incident spikes", len(unusual_df))
    metric_col2.metric("Date-grid records analyzed", len(anomaly_df))

    st.plotly_chart(anomaly_time_chart(anomaly_df), use_container_width=True)

    st.subheader("Date-Wise Anomaly Table")
    st.dataframe(anomaly_df, use_container_width=True, hide_index=True)

    st.subheader("Unusual Incident Spikes")
    if unusual_df.empty:
        st.info("No unusual spikes were flagged with the current contamination setting.")
    else:
        st.dataframe(unusual_df, use_container_width=True, hide_index=True)

st.caption(
    "These ML views summarize historical patterns only. They do not predict danger or replace emergency, legal, "
    "or public safety decisions."
)
