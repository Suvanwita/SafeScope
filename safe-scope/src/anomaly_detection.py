import pandas as pd
from sklearn.ensemble import IsolationForest


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.08) -> pd.DataFrame:
    """Find records with unusual time, place, or severity patterns."""
    if len(df) < 10:
        result = df.copy()
        result["is_anomaly"] = False
        result["anomaly_score"] = 0.0
        return result

    features = df[["latitude", "longitude", "hour", "severity_weight"]].copy()
    model = IsolationForest(contamination=contamination, random_state=42)

    result = df.copy()
    result["anomaly_flag"] = model.fit_predict(features)
    result["anomaly_score"] = model.decision_function(features).round(4)
    result["is_anomaly"] = result["anomaly_flag"].eq(-1)
    return result.drop(columns=["anomaly_flag"])


def anomaly_summary(anomaly_df: pd.DataFrame) -> pd.DataFrame:
    """Return the most unusual incidents first."""
    if anomaly_df.empty or "is_anomaly" not in anomaly_df.columns:
        return pd.DataFrame()

    columns = [
        "date",
        "primary_type",
        "location_description",
        "community_area",
        "hour",
        "anomaly_score",
    ]
    return anomaly_df[anomaly_df["is_anomaly"]].sort_values("anomaly_score")[columns]
