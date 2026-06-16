import numpy as np
import pandas as pd


SEVERITY_MAPPING = {
    "CRIMINAL SEXUAL ASSAULT": 5,
    "KIDNAPPING": 5,
    "ROBBERY": 5,
    "ASSAULT": 4,
    "BATTERY": 4,
    "STALKING": 4,
    "HARASSMENT": 3,
    "CRIMINAL DAMAGE": 3,
    "THEFT": 2,
    "BURGLARY": 2,
    "MOTOR VEHICLE THEFT": 2,
}

SEVERE_TYPES = {
    "CRIMINAL SEXUAL ASSAULT",
    "KIDNAPPING",
    "ROBBERY",
    "ASSAULT",
    "BATTERY",
    "STALKING",
    "OFFENSE INVOLVING CHILDREN",
}


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add readable time columns for analysis and filtering."""
    featured = df.copy()
    if "hour" not in featured.columns:
        featured["hour"] = featured["date"].dt.hour
    if "day_name" not in featured.columns:
        featured["day_name"] = featured["date"].dt.day_name()
    if "month" not in featured.columns:
        featured["month"] = featured["date"].dt.month
    if "month_number" not in featured.columns:
        featured["month_number"] = featured["date"].dt.month
    if "weekend" not in featured.columns:
        featured["weekend"] = featured["date"].dt.dayofweek >= 5
    featured["is_weekend"] = featured["weekend"]
    featured["is_night"] = featured["hour"].between(20, 23) | featured["hour"].between(0, 5)
    return featured


def add_safety_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add severity, recency, and time-risk features for safety analysis."""
    featured = df.copy()
    if "crime_type" not in featured.columns and "primary_type" in featured.columns:
        featured["crime_type"] = featured["primary_type"]
    if "primary_type" not in featured.columns and "crime_type" in featured.columns:
        featured["primary_type"] = featured["crime_type"]
    if "weekend" not in featured.columns:
        featured["weekend"] = featured["date"].dt.dayofweek >= 5
    if "is_night" not in featured.columns:
        featured["is_night"] = featured["hour"].between(20, 23) | featured["hour"].between(0, 5)

    featured["crime_type"] = featured["crime_type"].fillna("UNKNOWN").astype(str).str.upper()
    featured["primary_type"] = featured["crime_type"]
    featured["is_severe_type"] = featured["crime_type"].isin(SEVERE_TYPES)
    featured["is_transit_related"] = featured["location_description"].str.contains("CTA|TRAIN|BUS|STATION", regex=True)
    featured["is_public_space"] = featured["location_description"].str.contains(
        "STREET|SIDEWALK|ALLEY|PARK|BEACH|PLATFORM|STATION|BUS|TRAIN",
        regex=True,
    )
    featured["severity_score"] = featured["crime_type"].map(SEVERITY_MAPPING).fillna(1).astype(int)

    latest_date = featured["date"].max()
    days_old = (latest_date - featured["date"]).dt.days.clip(lower=0)
    max_days = max(int(days_old.max()), 1)
    featured["recency_score"] = (1 + (1 - days_old / max_days) * 4).round(2)

    featured["time_risk_score"] = np.select(
        [featured["is_night"] & featured["weekend"], featured["is_night"], featured["weekend"]],
        [3, 2, 1.5],
        default=1,
    )
    featured["severity_weight"] = featured["severity_score"]
    featured["is_weekend"] = featured["weekend"]
    return featured


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Run all feature creation steps."""
    return add_safety_features(add_time_features(df))


def summary_metrics(df: pd.DataFrame) -> dict[str, float | int | str]:
    """Return headline numbers for dashboard cards."""
    if df.empty:
        return {
            "total_incidents": 0,
            "night_share": 0.0,
            "domestic_share": 0.0,
            "top_type": "N/A",
        }

    return {
        "total_incidents": len(df),
        "night_share": round(df["is_night"].mean() * 100, 1),
        "domestic_share": round(df["domestic"].mean() * 100, 1),
        "top_type": df["crime_type"].mode().iat[0] if "crime_type" in df.columns else df["primary_type"].mode().iat[0],
    }
