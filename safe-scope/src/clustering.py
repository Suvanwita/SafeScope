import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


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
