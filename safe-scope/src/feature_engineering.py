import numpy as np
import pandas as pd


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
    featured["hour"] = featured["date"].dt.hour
    featured["day_name"] = featured["date"].dt.day_name()
    featured["month"] = featured["date"].dt.month_name()
    featured["month_number"] = featured["date"].dt.month
    featured["is_weekend"] = featured["date"].dt.dayofweek >= 5
    featured["is_night"] = featured["hour"].between(20, 23) | featured["hour"].between(0, 5)
    return featured


def add_safety_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add simple flags used by risk scoring and recommendations."""
    featured = df.copy()
    featured["is_severe_type"] = featured["primary_type"].isin(SEVERE_TYPES)
    featured["is_transit_related"] = featured["location_description"].str.contains("CTA|TRAIN|BUS|STATION", regex=True)
    featured["is_public_space"] = featured["location_description"].str.contains(
        "STREET|SIDEWALK|ALLEY|PARK|BEACH|PLATFORM|STATION|BUS|TRAIN",
        regex=True,
    )
    featured["severity_weight"] = np.select(
        [
            featured["primary_type"].eq("CRIMINAL SEXUAL ASSAULT"),
            featured["primary_type"].isin(["KIDNAPPING", "ROBBERY"]),
            featured["primary_type"].isin(["ASSAULT", "BATTERY", "STALKING"]),
        ],
        [5, 4, 3],
        default=1,
    )
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
        "top_type": df["primary_type"].mode().iat[0],
    }
