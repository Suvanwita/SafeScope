import folium
import pandas as pd
import plotly.express as px
from folium.plugins import HeatMap, MarkerCluster


RISK_COLORS = {
    "Lower": "#2a9d8f",
    "Moderate": "#e9c46a",
    "Higher": "#e76f51",
}


def crime_type_bar(df: pd.DataFrame):
    counts = df["primary_type"].value_counts().reset_index()
    counts.columns = ["primary_type", "incidents"]
    return px.bar(
        counts,
        x="incidents",
        y="primary_type",
        orientation="h",
        color="incidents",
        color_continuous_scale="Tealrose",
        title="Incidents by Type",
    )


def hourly_chart(df: pd.DataFrame):
    hourly = df.groupby("hour").size().reset_index(name="incidents")
    return px.line(hourly, x="hour", y="incidents", markers=True, title="Incidents by Hour")


def weekday_chart(df: pd.DataFrame):
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = df["day_name"].value_counts().reindex(order, fill_value=0).reset_index()
    weekday.columns = ["day_name", "incidents"]
    return px.bar(weekday, x="day_name", y="incidents", title="Incidents by Day of Week")


def monthly_chart(df: pd.DataFrame):
    monthly = (
        df.groupby(["month_number", "month"])
        .size()
        .reset_index(name="incidents")
        .sort_values("month_number")
    )
    return px.area(monthly, x="month", y="incidents", title="Incidents by Month")


def risk_score_chart(area_risk: pd.DataFrame):
    return px.bar(
        area_risk.head(12),
        x="community_area",
        y="risk_score",
        color="risk_level",
        color_discrete_map=RISK_COLORS,
        title="Top Community Areas by Sample Risk Score",
    )


def cluster_scatter(clustered_df: pd.DataFrame):
    return px.scatter_mapbox(
        clustered_df,
        lat="latitude",
        lon="longitude",
        color="cluster",
        hover_name="primary_type",
        hover_data=["date", "location_description", "hour"],
        zoom=10,
        height=520,
        mapbox_style="open-street-map",
        title="Incident Clusters",
    )


def anomaly_scatter(anomaly_df: pd.DataFrame):
    return px.scatter(
        anomaly_df,
        x="hour",
        y="severity_weight",
        color="is_anomaly",
        hover_data=["primary_type", "location_description", "community_area"],
        title="Anomaly Detection: Hour vs Severity",
    )


def _coordinate_columns(df: pd.DataFrame) -> tuple[str, str]:
    """Return latitude and longitude column names for cleaned or raw-style data."""
    lat_col = "latitude" if "latitude" in df.columns else "Latitude"
    lon_col = "longitude" if "longitude" in df.columns else "Longitude"
    return lat_col, lon_col


def create_incident_map(df: pd.DataFrame, max_points: int = 1000) -> folium.Map:
    """Create a clustered incident marker map, sampling markers for performance."""
    lat_col, lon_col = _coordinate_columns(df)
    map_df = df.dropna(subset=[lat_col, lon_col]).copy()
    center = [map_df[lat_col].mean(), map_df[lon_col].mean()] if not map_df.empty else [41.8781, -87.6298]
    incident_map = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

    if map_df.empty:
        return incident_map

    if len(map_df) > max_points:
        map_df = map_df.sample(max_points, random_state=42)

    marker_cluster = MarkerCluster(name="Incident markers").add_to(incident_map)
    for _, row in map_df.iterrows():
        crime_type = row.get("crime_type", row.get("primary_type", "Incident"))
        popup = (
            f"<b>{crime_type}</b><br>"
            f"{row.get('date', 'Unknown date')}<br>"
            f"{row.get('location_description', 'Unknown location')}<br>"
            f"Severity: {row.get('severity_score', 'N/A')}"
        )
        folium.CircleMarker(
            location=[row[lat_col], row[lon_col]],
            radius=6,
            popup=folium.Popup(popup, max_width=280),
            color="#457b9d",
            fill=True,
            fill_opacity=0.75,
        ).add_to(marker_cluster)

    return incident_map


def create_heatmap(df: pd.DataFrame) -> folium.Map:
    """Create a heatmap weighted by severity when available."""
    lat_col, lon_col = _coordinate_columns(df)
    heat_df = df.dropna(subset=[lat_col, lon_col]).copy()
    center = [heat_df[lat_col].mean(), heat_df[lon_col].mean()] if not heat_df.empty else [41.8781, -87.6298]
    heat_map = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

    if heat_df.empty:
        return heat_map

    weight_col = "severity_score" if "severity_score" in heat_df.columns else None
    heat_data = (
        heat_df[[lat_col, lon_col, weight_col]].values.tolist()
        if weight_col
        else heat_df[[lat_col, lon_col]].values.tolist()
    )
    HeatMap(heat_data, radius=18, blur=24, min_opacity=0.25).add_to(heat_map)
    return heat_map


def create_area_grid(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate incidents into approximate 0.01-degree grid cells."""
    if df.empty:
        return pd.DataFrame(
            columns=[
                "latitude_grid",
                "longitude_grid",
                "incident_count",
                "avg_severity",
                "night_ratio",
                "top_crime_type",
                "latitude_center",
                "longitude_center",
            ]
        )

    lat_col, lon_col = _coordinate_columns(df)
    grid_df = df.dropna(subset=[lat_col, lon_col]).copy()
    grid_df["latitude_grid"] = grid_df[lat_col].round(2)
    grid_df["longitude_grid"] = grid_df[lon_col].round(2)

    severity_col = "severity_score" if "severity_score" in grid_df.columns else None
    if severity_col is None:
        grid_df["severity_score"] = 1
        severity_col = "severity_score"

    crime_col = "crime_type" if "crime_type" in grid_df.columns else "primary_type"

    grouped = (
        grid_df.groupby(["latitude_grid", "longitude_grid"])
        .agg(
            incident_count=(crime_col, "count"),
            avg_severity=(severity_col, "mean"),
            night_ratio=("is_night", "mean"),
            top_crime_type=(crime_col, lambda values: values.mode().iat[0] if not values.mode().empty else "N/A"),
            latitude_center=(lat_col, "mean"),
            longitude_center=(lon_col, "mean"),
        )
        .reset_index()
    )

    if "recency_score" in grid_df.columns:
        recent = (
            grid_df.groupby(["latitude_grid", "longitude_grid"])["recency_score"]
            .mean()
            .reset_index(name="recent_activity")
        )
        grouped = grouped.merge(recent, on=["latitude_grid", "longitude_grid"], how="left")

    grouped["avg_severity"] = grouped["avg_severity"].round(2)
    grouped["night_ratio"] = grouped["night_ratio"].round(3)
    return grouped.sort_values("incident_count", ascending=False)
