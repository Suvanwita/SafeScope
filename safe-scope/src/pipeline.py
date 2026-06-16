import pandas as pd
import streamlit as st

from src.data_loader import load_uploaded_or_sample, normalize_common_columns, validate_required_columns
from src.feature_engineering import add_safety_features
from src.preprocessing import clean_crime_data


def build_crime_pipeline_from_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and feature-engineer an in-memory dataframe, then store it in session state."""
    normalized = normalize_common_columns(raw_df)
    is_valid, missing = validate_required_columns(normalized)
    if not is_valid:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    cleaned_df = clean_crime_data(normalized)
    final_df = add_safety_features(cleaned_df)
    st.session_state["cleaned_df"] = final_df
    return final_df


def build_crime_pipeline(uploaded_file=None) -> pd.DataFrame:
    """Load, clean, engineer features, and store the final dataframe in session state."""
    raw_df = load_uploaded_or_sample(uploaded_file)
    return build_crime_pipeline_from_dataframe(raw_df)


def get_session_or_sample_data() -> pd.DataFrame:
    """Return the shared cleaned dataframe, building it from sample data when needed."""
    if "cleaned_df" not in st.session_state:
        return build_crime_pipeline()
    return st.session_state["cleaned_df"]
