import pandas as pd


REQUIRED_COLUMNS = {
    "case_number",
    "date",
    "primary_type",
    "description",
    "location_description",
    "arrest",
    "domestic",
    "ward",
    "community_area",
    "latitude",
    "longitude",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column names to lower snake_case."""
    cleaned = df.copy()
    cleaned.columns = (
        cleaned.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return cleaned


def validate_columns(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """Check whether the dataset has the columns used by the app."""
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    return len(missing) == 0, missing


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean types, fill labels, and remove records without coordinates."""
    cleaned = normalize_columns(df)
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")

    for column in ["primary_type", "description", "location_description"]:
        cleaned[column] = cleaned[column].fillna("UNKNOWN").astype(str).str.upper()

    for column in ["arrest", "domestic"]:
        cleaned[column] = cleaned[column].astype(str).str.lower().isin(["true", "1", "yes"])

    numeric_columns = ["ward", "community_area", "latitude", "longitude"]
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned = cleaned.dropna(subset=["date", "latitude", "longitude"])
    return cleaned.reset_index(drop=True)


def filter_data(
    df: pd.DataFrame,
    crime_types: list[str] | None = None,
    locations: list[str] | None = None,
    hour_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Apply common sidebar filters."""
    filtered = df.copy()
    if crime_types:
        filtered = filtered[filtered["primary_type"].isin(crime_types)]
    if locations:
        filtered = filtered[filtered["location_description"].isin(locations)]
    if hour_range:
        start_hour, end_hour = hour_range
        filtered = filtered[filtered["hour"].between(start_hour, end_hour)]
    return filtered
