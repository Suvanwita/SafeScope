from pathlib import Path

import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_chicago_crimes.csv"
REQUIRED_COLUMNS = [
    "Date",
    "Primary Type",
    "Description",
    "Location Description",
    "Latitude",
    "Longitude",
]

COLUMN_ALIASES = {
    "date/time": "Date",
    "datetime": "Date",
    "timestamp": "Date",
    "date": "Date",
    "primary type": "Primary Type",
    "primary_type": "Primary Type",
    "crime_type": "Primary Type",
    "crime type": "Primary Type",
    "category": "Primary Type",
    "description": "Description",
    "location description": "Location Description",
    "location_description": "Location Description",
    "location": "Location Description",
    "latitude": "Latitude",
    "lat": "Latitude",
    "longitude": "Longitude",
    "lon": "Longitude",
    "lng": "Longitude",
}


def _column_key(column_name: str) -> str:
    return column_name.strip().lower().replace("-", " ").replace("_", " ")


def normalize_common_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize common dataset column alternatives to the app's display schema."""
    normalized = df.copy()
    rename_map = {}

    for column in normalized.columns:
        stripped = column.strip()
        key = _column_key(stripped)
        alias = COLUMN_ALIASES.get(key) or COLUMN_ALIASES.get(stripped.strip().lower())
        if alias:
            rename_map[column] = alias

    normalized = normalized.rename(columns=rename_map)
    return normalized


def validate_required_columns(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Validate the minimum columns needed for the SafeScope data pipeline."""
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    return len(missing) == 0, missing


@st.cache_data
def load_sample_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Load the bundled sample dataset."""
    return normalize_common_columns(pd.read_csv(path))


def load_uploaded_data(uploaded_file) -> pd.DataFrame | None:
    """Load a user-uploaded CSV when present."""
    if uploaded_file is None:
        return None
    return normalize_common_columns(pd.read_csv(uploaded_file))


def load_uploaded_or_sample(uploaded_file=None) -> pd.DataFrame:
    """Load an uploaded CSV or the bundled sample, then validate required columns."""
    df = load_uploaded_data(uploaded_file)
    if df is None:
        df = load_sample_data()

    df = normalize_common_columns(df)
    is_valid, missing = validate_required_columns(df)
    if not is_valid:
        missing_text = ", ".join(missing)
        raise ValueError(f"Missing required columns: {missing_text}")
    return df


def get_data(uploaded_file=None) -> pd.DataFrame:
    """Return uploaded data when supplied, otherwise the sample data."""
    return load_uploaded_or_sample(uploaded_file)
