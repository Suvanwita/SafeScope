import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def _coordinate_columns(df: pd.DataFrame) -> tuple[str, str]:
    lat_col = "latitude" if "latitude" in df.columns else "Latitude"
    lon_col = "longitude" if "longitude" in df.columns else "Longitude"
    return lat_col, lon_col


def run_dbscan_clustering(
    df: pd.DataFrame,
    eps: float = 0.01,
    min_samples: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Find dense geographic hotspot clusters with DBSCAN."""
    clustered = df.copy()
    lat_col, lon_col = _coordinate_columns(clustered)
    clustered = clustered.dropna(subset=[lat_col, lon_col]).copy()

    if clustered.empty:
        clustered["cluster_id"] = []
        return clustered, _empty_dbscan_summary()

    if len(clustered) < min_samples:
        clustered["cluster_id"] = -1
        return clustered, _dbscan_summary(clustered, lat_col, lon_col)

    coordinates = clustered[[lat_col, lon_col]].copy()
    model = DBSCAN(eps=eps, min_samples=min_samples)
    clustered["cluster_id"] = model.fit_predict(coordinates)
    return clustered, _dbscan_summary(clustered, lat_col, lon_col)


def _empty_dbscan_summary() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "cluster_id",
            "incident_count",
            "avg_latitude",
            "avg_longitude",
            "avg_severity",
            "night_ratio",
            "top_crime_type",
        ]
    )


def _dbscan_summary(clustered_df: pd.DataFrame, lat_col: str, lon_col: str) -> pd.DataFrame:
    if clustered_df.empty:
        return _empty_dbscan_summary()

    severity_col = "severity_score" if "severity_score" in clustered_df.columns else "severity_weight"
    if severity_col not in clustered_df.columns:
        clustered_df = clustered_df.copy()
        clustered_df["severity_score"] = 1
        severity_col = "severity_score"

    crime_col = "crime_type" if "crime_type" in clustered_df.columns else "primary_type"

    summary = (
        clustered_df.groupby("cluster_id")
        .agg(
            incident_count=(crime_col, "count"),
            avg_latitude=(lat_col, "mean"),
            avg_longitude=(lon_col, "mean"),
            avg_severity=(severity_col, "mean"),
            night_ratio=("is_night", "mean"),
            top_crime_type=(crime_col, lambda values: values.mode().iat[0] if not values.mode().empty else "N/A"),
        )
        .reset_index()
        .sort_values(["cluster_id", "incident_count"], ascending=[True, False])
    )

    summary["avg_latitude"] = summary["avg_latitude"].round(5)
    summary["avg_longitude"] = summary["avg_longitude"].round(5)
    summary["avg_severity"] = summary["avg_severity"].round(2)
    summary["night_ratio"] = summary["night_ratio"].round(3)
    return summary


def cluster_incidents(df: pd.DataFrame, n_clusters: int = 4) -> pd.DataFrame:
    """Cluster incidents by location, hour, and severity."""
    if len(df) < n_clusters:
        clustered = df.copy()
        clustered["cluster"] = 0
        return clustered

    features = df[["latitude", "longitude", "hour", "severity_weight"]].copy()
    scaled = StandardScaler().fit_transform(features)
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)

    clustered = df.copy()
    clustered["cluster"] = model.fit_predict(scaled)
    return clustered


def cluster_summary(clustered_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize cluster behavior for human interpretation."""
    if "cluster" not in clustered_df.columns or clustered_df.empty:
        return pd.DataFrame()

    return (
        clustered_df.groupby("cluster")
        .agg(
            incidents=("case_number", "count"),
            avg_hour=("hour", "mean"),
            avg_severity=("severity_weight", "mean"),
            night_share=("is_night", "mean"),
            top_type=("primary_type", lambda values: values.mode().iat[0] if not values.mode().empty else "N/A"),
        )
        .assign(
            avg_hour=lambda frame: frame["avg_hour"].round(1),
            avg_severity=lambda frame: frame["avg_severity"].round(2),
            night_share=lambda frame: (frame["night_share"] * 100).round(1),
        )
        .reset_index()
    )
