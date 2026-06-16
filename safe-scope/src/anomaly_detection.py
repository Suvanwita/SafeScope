import pandas as pd
from sklearn.ensemble import IsolationForest


def _coordinate_columns(df: pd.DataFrame) -> tuple[str, str]:
    lat_col = "latitude" if "latitude" in df.columns else "Latitude"
    lon_col = "longitude" if "longitude" in df.columns else "Longitude"
    return lat_col, lon_col


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.08) -> pd.DataFrame:
    """Flag unusual daily grid-cell incident spikes with Isolation Forest."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "latitude_grid",
                "longitude_grid",
                "incident_count",
                "avg_severity",
                "night_ratio",
                "anomaly_score",
                "anomaly_label",
            ]
        )

    lat_col, lon_col = _coordinate_columns(df)
    working = df.dropna(subset=["date", lat_col, lon_col]).copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce").dt.date
    working = working.dropna(subset=["date"])
    working["latitude_grid"] = working[lat_col].round(2)
    working["longitude_grid"] = working[lon_col].round(2)

    severity_col = "severity_score" if "severity_score" in working.columns else "severity_weight"
    if severity_col not in working.columns:
        working["severity_score"] = 1
        severity_col = "severity_score"

    aggregated = (
        working.groupby(["date", "latitude_grid", "longitude_grid"])
        .agg(
            incident_count=(severity_col, "count"),
            avg_severity=(severity_col, "mean"),
            night_ratio=("is_night", "mean"),
        )
        .reset_index()
    )

    if len(aggregated) < 5:
        aggregated["anomaly_score"] = 0.0
        aggregated["anomaly_label"] = "normal"
        aggregated["is_anomaly"] = False
        return aggregated

    features = aggregated[["incident_count", "avg_severity", "night_ratio"]].copy()
    model = IsolationForest(contamination=contamination, random_state=42)
    flags = model.fit_predict(features)

    aggregated["anomaly_score"] = model.decision_function(features).round(4)
    aggregated["anomaly_label"] = ["unusual spike" if flag == -1 else "normal" for flag in flags]
    aggregated["is_anomaly"] = aggregated["anomaly_label"].eq("unusual spike")
    aggregated["avg_severity"] = aggregated["avg_severity"].round(2)
    aggregated["night_ratio"] = aggregated["night_ratio"].round(3)
    return aggregated.sort_values(["date", "anomaly_label"]).reset_index(drop=True)


def anomaly_summary(anomaly_df: pd.DataFrame) -> pd.DataFrame:
    """Return the most unusual incidents first."""
    if anomaly_df.empty or "anomaly_label" not in anomaly_df.columns:
        return pd.DataFrame()

    return anomaly_df[anomaly_df["anomaly_label"].eq("unusual spike")].sort_values("anomaly_score")
