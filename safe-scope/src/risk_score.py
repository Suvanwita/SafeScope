import pandas as pd


def normalize_series(series: pd.Series) -> pd.Series:
    """Normalize a numeric series to a 0-1 range."""
    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    minimum = numeric.min()
    maximum = numeric.max()
    if maximum == minimum:
        return pd.Series(0.5, index=series.index)
    return (numeric - minimum) / (maximum - minimum)


def calculate_grid_risk(grid_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate 0-100 historical risk scores for approximate grid cells."""
    if grid_df.empty:
        result = grid_df.copy()
        result["risk_score"] = []
        result["risk_label"] = []
        return result

    scored = grid_df.copy()
    risk = (
        0.40 * normalize_series(scored["incident_count"])
        + 0.25 * normalize_series(scored["avg_severity"])
        + 0.20 * normalize_series(scored["night_ratio"])
    )

    if "recent_activity" in scored.columns:
        risk = risk + 0.15 * normalize_series(scored["recent_activity"])

    scored["risk_score"] = (risk * 100).round(1)
    scored["risk_label"] = pd.cut(
        scored["risk_score"],
        bins=[-1, 30, 60, 100],
        labels=[
            "Lower historical incident pattern",
            "Moderate historical incident pattern",
            "Higher historical incident pattern",
        ],
    ).astype(str)
    return scored.sort_values("risk_score", ascending=False)


def calculate_area_risk(df: pd.DataFrame) -> pd.DataFrame:
    """Score community areas from 0-100 using volume, severity, night, and domestic indicators."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "community_area",
                "incident_count",
                "severity_total",
                "night_incidents",
                "domestic_incidents",
                "risk_score",
                "risk_level",
                "latitude",
                "longitude",
            ]
        )

    grouped = (
        df.groupby("community_area")
        .agg(
            incident_count=("case_number", "count"),
            severity_total=("severity_weight", "sum"),
            night_incidents=("is_night", "sum"),
            domestic_incidents=("domestic", "sum"),
            latitude=("latitude", "mean"),
            longitude=("longitude", "mean"),
        )
        .reset_index()
    )

    def normalize(series: pd.Series) -> pd.Series:
        if series.max() == series.min():
            return pd.Series(50, index=series.index)
        return ((series - series.min()) / (series.max() - series.min())) * 100

    grouped["risk_score"] = (
        normalize(grouped["incident_count"]) * 0.35
        + normalize(grouped["severity_total"]) * 0.35
        + normalize(grouped["night_incidents"]) * 0.20
        + normalize(grouped["domestic_incidents"]) * 0.10
    ).round(1)

    grouped["risk_level"] = pd.cut(
        grouped["risk_score"],
        bins=[-1, 35, 70, 100],
        labels=["Lower", "Moderate", "Higher"],
    ).astype(str)
    return grouped.sort_values("risk_score", ascending=False)


def incident_risk_label(row: pd.Series) -> str:
    """Label individual records for display."""
    score = row.get("severity_weight", 1)
    if row.get("is_night", False):
        score += 1
    if row.get("is_public_space", False):
        score += 1
    if row.get("domestic", False):
        score += 1

    if score >= 6:
        return "Higher attention"
    if score >= 4:
        return "Moderate attention"
    return "Lower attention"
