import streamlit as st

from src.data_loader import get_data
from src.feature_engineering import prepare_features
from src.preprocessing import clean_data, normalize_columns, validate_columns
from src.visualizations import hourly_chart, monthly_chart, weekday_chart


st.set_page_config(page_title="Time Analysis | SafeScope", layout="wide")
st.title("Time Analysis")
st.caption("Explore when incidents appear most often in the historical sample.")

uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
raw_df = get_data(uploaded_file)
raw_df = normalize_columns(raw_df)
is_valid, missing = validate_columns(raw_df)

if not is_valid:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

df = prepare_features(clean_data(raw_df))

col1, col2, col3 = st.columns(3)
col1.metric("Peak hour", int(df.groupby("hour").size().idxmax()))
col2.metric("Weekend incidents", int(df["is_weekend"].sum()))
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
