import streamlit as st

from src.anomaly_detection import anomaly_summary, detect_anomalies
from src.clustering import cluster_incidents, cluster_summary
from src.data_loader import get_data
from src.feature_engineering import prepare_features
from src.preprocessing import clean_data, normalize_columns, validate_columns
from src.visualizations import anomaly_scatter, cluster_scatter


st.set_page_config(page_title="ML Insights | SafeScope", layout="wide")
st.title("ML Insights")
st.caption("Beginner-friendly clustering and anomaly detection for pattern exploration.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
raw_df = get_data(uploaded_file)
raw_df = normalize_columns(raw_df)
is_valid, missing = validate_columns(raw_df)

if not is_valid:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

df = prepare_features(clean_data(raw_df))

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
