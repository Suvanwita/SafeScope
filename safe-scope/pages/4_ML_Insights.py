import streamlit as st

from src.anomaly_detection import anomaly_summary, detect_anomalies
from src.clustering import cluster_incidents, cluster_summary
from src.pipeline import build_crime_pipeline, get_session_or_sample_data
from src.visualizations import anomaly_scatter, cluster_scatter


st.set_page_config(page_title="ML Insights | SafeScope", layout="wide")
st.title("ML Insights")
st.caption("Beginner-friendly clustering and anomaly detection for pattern exploration.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
try:
    df = build_crime_pipeline(uploaded_file) if uploaded_file else get_session_or_sample_data()
except ValueError as error:
    st.error(str(error))
    st.stop()

n_clusters = st.sidebar.slider("Number of clusters", 2, 6, 4)
contamination = st.sidebar.slider("Anomaly sensitivity", 0.02, 0.20, 0.08, 0.01)

clustered = cluster_incidents(df, n_clusters=n_clusters)
anomalies = detect_anomalies(df, contamination=contamination)

tab1, tab2 = st.tabs(["Clusters", "Anomalies"])
with tab1:
    st.plotly_chart(cluster_scatter(clustered), use_container_width=True)
    st.dataframe(cluster_summary(clustered), use_container_width=True, hide_index=True)
with tab2:
    st.plotly_chart(anomaly_scatter(anomalies), use_container_width=True)
    st.dataframe(anomaly_summary(anomalies), use_container_width=True, hide_index=True)

st.info(
    "These models are exploratory. Clusters group similar records; anomalies flag unusual combinations of time, "
    "location, and severity in the sample."
)
