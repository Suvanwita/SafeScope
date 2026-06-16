import streamlit as st
from streamlit_folium import st_folium

from src.data_loader import get_data
from src.feature_engineering import prepare_features
from src.preprocessing import clean_data, filter_data, normalize_columns, validate_columns
from src.risk_score import calculate_area_risk
from src.visualizations import create_incident_map, risk_score_chart


st.set_page_config(page_title="Risk Map | SafeScope", layout="wide")
st.title("Risk Map")
st.caption("Map historical incidents and community-area sample risk scores.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
raw_df = get_data(uploaded_file)
raw_df = normalize_columns(raw_df)
is_valid, missing = validate_columns(raw_df)

if not is_valid:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

df = prepare_features(clean_data(raw_df))
crime_types = st.sidebar.multiselect("Crime types", sorted(df["primary_type"].unique()))
hour_range = st.sidebar.slider("Hour range", 0, 23, (0, 23))
filtered = filter_data(df, crime_types=crime_types, hour_range=hour_range)
area_risk = calculate_area_risk(filtered)

if filtered.empty:
    st.info("No records match the current filters.")
    st.stop()

col1, col2 = st.columns([1.3, 0.7])
with col1:
    incident_map = create_incident_map(filtered, area_risk)
    st_folium(incident_map, width=None, height=560)
with col2:
    st.subheader("Area Risk Table")
    st.dataframe(area_risk, use_container_width=True, hide_index=True)

st.plotly_chart(risk_score_chart(area_risk), use_container_width=True)
