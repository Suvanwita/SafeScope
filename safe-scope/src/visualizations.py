import folium
import pandas as pd
import plotly.express as px


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


def create_incident_map(df: pd.DataFrame, area_risk: pd.DataFrame | None = None) -> folium.Map:
    center = [df["latitude"].mean(), df["longitude"].mean()] if not df.empty else [41.8781, -87.6298]
    incident_map = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

    risk_lookup = {}
    if area_risk is not None and not area_risk.empty:
        risk_lookup = area_risk.set_index("community_area")[["risk_score", "risk_level"]].to_dict("index")

    for _, row in df.iterrows():
        risk = risk_lookup.get(row["community_area"], {"risk_score": "N/A", "risk_level": "Lower"})
        color = RISK_COLORS.get(risk["risk_level"], "#457b9d")
        popup = (
            f"<b>{row['primary_type']}</b><br>"
            f"{row['date']}<br>"
            f"{row['location_description']}<br>"
            f"Community area: {int(row['community_area']) if pd.notna(row['community_area']) else 'N/A'}<br>"
            f"Risk score: {risk['risk_score']}"
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=6,
            popup=folium.Popup(popup, max_width=280),
            color=color,
            fill=True,
            fill_opacity=0.75,
        ).add_to(incident_map)

    return incident_map
