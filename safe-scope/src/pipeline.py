import pandas as pd
import streamlit as st

from src.data_loader import load_uploaded_or_sample
from src.feature_engineering import add_safety_features
from src.preprocessing import clean_crime_data


def build_crime_pipeline(uploaded_file=None) -> pd.DataFrame:
    """Load, clean, engineer features, and store the final dataframe in session state."""
    raw_df = load_uploaded_or_sample(uploaded_file)
    cleaned_df = clean_crime_data(raw_df)
    final_df = add_safety_features(cleaned_df)
    st.session_state["cleaned_df"] = final_df
    return final_df


def get_session_or_sample_data() -> pd.DataFrame:
    """Return the shared cleaned dataframe, building it from sample data when needed."""
    if "cleaned_df" not in st.session_state:
        return build_crime_pipeline()
    return st.session_state["cleaned_df"]
