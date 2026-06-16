from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_chicago_crimes.csv"


@st.cache_data
def load_sample_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Load the bundled sample dataset."""
    return pd.read_csv(path)


def load_uploaded_data(uploaded_file) -> pd.DataFrame | None:
    """Load a user-uploaded CSV when present."""
    if uploaded_file is None:
        return None
    return pd.read_csv(uploaded_file)


def get_data(uploaded_file=None) -> pd.DataFrame:
    """Return uploaded data when supplied, otherwise the sample data."""
    uploaded = load_uploaded_data(uploaded_file)
    if uploaded is not None:
        return uploaded
    return load_sample_data()
