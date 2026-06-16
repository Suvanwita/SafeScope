import streamlit as st

from src.data_loader import get_data
from src.feature_engineering import prepare_features, summary_metrics
from src.preprocessing import clean_data, filter_data, normalize_columns, validate_columns
from src.visualizations import crime_type_bar


st.set_page_config(page_title="Data Explorer | SafeScope", layout="wide")
st.title("Data Explorer")
st.caption("Review, filter, and understand the incident dataset.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
raw_df = get_data(uploaded_file)
raw_df = normalize_columns(raw_df)
is_valid, missing = validate_columns(raw_df)

if not is_valid:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

df = prepare_features(clean_data(raw_df))

crime_types = st.sidebar.multiselect("Crime types", sorted(df["primary_type"].unique()))
locations = st.sidebar.multiselect("Location descriptions", sorted(df["location_description"].unique()))
hour_range = st.sidebar.slider("Hour range", 0, 23, (0, 23))
filtered = filter_data(df, crime_types, locations, hour_range)

metrics = summary_metrics(filtered)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Incidents", metrics["total_incidents"])
col2.metric("Night share", f"{metrics['night_share']}%")
col3.metric("Domestic share", f"{metrics['domestic_share']}%")
col4.metric("Top type", metrics["top_type"])

left, right = st.columns([1, 1])
with left:
    st.subheader("Filtered Records")
    st.dataframe(
        filtered[
            [
                "case_number",
                "date",
                "primary_type",
                "location_description",
                "community_area",
                "hour",
                "domestic",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
with right:
    if filtered.empty:
        st.info("No records match the current filters.")
    else:
        st.plotly_chart(crime_type_bar(filtered), use_container_width=True)

st.download_button(
    "Download filtered CSV",
    data=filtered.to_csv(index=False),
    file_name="safescope_filtered_incidents.csv",
    mime="text/csv",
)
