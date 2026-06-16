import pandas as pd


REQUIRED_COLUMNS = {
    "date",
    "primary_type",
    "description",
    "location_description",
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
    normalized = normalize_columns(df)
    missing = sorted(REQUIRED_COLUMNS - set(normalized.columns))
    return len(missing) == 0, missing


def clean_crime_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw crime records into a consistent analysis-ready dataframe."""
    cleaned = normalize_columns(df)
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")

    for column in ["primary_type", "description", "location_description"]:
        cleaned[column] = cleaned[column].fillna("UNKNOWN").astype(str).str.upper()

    optional_defaults = {
        "case_number": [f"ROW-{index + 1:05d}" for index in range(len(cleaned))],
        "arrest": False,
        "domestic": False,
        "ward": pd.NA,
        "community_area": pd.NA,
    }
    for column, default in optional_defaults.items():
        if column not in cleaned.columns:
            cleaned[column] = default

    for column in ["arrest", "domestic"]:
        cleaned[column] = cleaned[column].astype(str).str.lower().isin(["true", "1", "yes"])

    numeric_columns = ["ward", "community_area", "latitude", "longitude"]
    for column in numeric_columns:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned["ward"] = cleaned["ward"].fillna(0)
    cleaned["community_area"] = cleaned["community_area"].fillna(0)

    cleaned = cleaned.dropna(subset=["date", "latitude", "longitude"])
    cleaned = cleaned[cleaned["latitude"].between(-90, 90)]
    cleaned = cleaned[cleaned["longitude"].between(-180, 180)]

    cleaned["year"] = cleaned["date"].dt.year
    cleaned["month"] = cleaned["date"].dt.month
    cleaned["day_name"] = cleaned["date"].dt.day_name()
    cleaned["hour"] = cleaned["date"].dt.hour
    cleaned["is_night"] = cleaned["hour"].between(20, 23) | cleaned["hour"].between(0, 5)
    cleaned["weekend"] = cleaned["date"].dt.dayofweek >= 5

    current_year = pd.Timestamp.today().year
    cleaned = cleaned[cleaned["year"].between(1900, current_year + 1)]
    cleaned = cleaned[cleaned["hour"].between(0, 23)]

    cleaned["crime_type"] = cleaned["primary_type"]
    cleaned["primary_type"] = cleaned["crime_type"]
    cleaned["location_description"] = cleaned["location_description"]
    cleaned["is_weekend"] = cleaned["weekend"]
    cleaned["month_number"] = cleaned["month"]
    return cleaned.reset_index(drop=True)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible wrapper for the main preprocessing function."""
    return clean_crime_data(df)


def filter_data(
    df: pd.DataFrame,
    crime_types: list[str] | None = None,
    locations: list[str] | None = None,
    hour_range: tuple[int, int] | None = None,
) -> pd.DataFrame:
    """Apply common sidebar filters."""
    filtered = df.copy()
    if crime_types:
        type_column = "crime_type" if "crime_type" in filtered.columns else "primary_type"
        filtered = filtered[filtered[type_column].isin(crime_types)]
    if locations:
        filtered = filtered[filtered["location_description"].isin(locations)]
    if hour_range:
        start_hour, end_hour = hour_range
        filtered = filtered[filtered["hour"].between(start_hour, end_hour)]
    return filtered
