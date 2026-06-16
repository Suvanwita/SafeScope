import pandas as pd


def _value(area_summary, key: str, default=None):
    if area_summary is None:
        return default
    if isinstance(area_summary, pd.Series):
        return area_summary.get(key, default)
    if isinstance(area_summary, dict):
        return area_summary.get(key, default)
    return getattr(area_summary, key, default)


def generate_safety_recommendations(
    area_summary,
    selected_hour: int | None = None,
    selected_day: str | None = None,
) -> list[str]:
    """Create rule-based awareness recommendations from selected area signals."""
    recommendations = [
        "Use this summary for awareness and planning, alongside official local information.",
        "Prefer well-lit and crowded routes when possible.",
        "Share trip details with trusted contacts.",
        "Check official local advisories for real-time updates.",
    ]

    risk_score = float(_value(area_summary, "risk_score", 0) or 0)
    night_ratio = float(_value(area_summary, "night_ratio", 0) or 0)
    top_crime_type = _value(area_summary, "top_crime_type", _value(area_summary, "common_incident_type", "incidents"))
    weekend_ratio = float(_value(area_summary, "weekend_ratio", 0) or 0)
    anomaly_count = int(_value(area_summary, "anomaly_count", 0) or 0)

    if risk_score >= 61:
        recommendations.append("This area shows higher historical incident density during late evening hours.")
    elif risk_score >= 31:
        recommendations.append("This area shows a moderate historical incident pattern; review timing and location context before planning.")
    else:
        recommendations.append("This area shows a lower historical incident pattern in the selected dataset.")

    if night_ratio >= 0.40:
        recommendations.append("Night-time records are prominent here; consider earlier travel windows when practical.")

    if top_crime_type and str(top_crime_type).upper() != "N/A":
        recommendations.append(f"The most common incident type in this selection is {top_crime_type}; review nearby context and timing.")

    if weekend_ratio >= 0.40 or (selected_day in {"Saturday", "Sunday"}):
        recommendations.append("Weekend patterns are visible; plan around crowd levels, transport options, and event schedules.")

    if anomaly_count > 0:
        recommendations.append("Recent unusual spikes were flagged in this area; compare with official updates and local context.")

    if selected_hour is not None and (selected_hour >= 20 or selected_hour <= 5):
        recommendations.append("The selected hour falls in a late-night window; keep check-ins and transport options ready.")

    return recommendations


def generate_recommendations(df: pd.DataFrame, area_risk: pd.DataFrame) -> list[str]:
    """Create awareness-oriented recommendations from observed patterns."""
    recommendations = [
        "Use these findings for planning, awareness, and resource conversations, not as real-time alerts.",
        "Pair map patterns with local context such as lighting, transport availability, events, and community feedback.",
    ]

    if df.empty:
        return recommendations

    night_share = df["is_night"].mean()
    transit_share = df["is_transit_related"].mean()
    public_share = df["is_public_space"].mean()

    if night_share >= 0.35:
        recommendations.append("Night-time incidents are prominent; prioritize well-lit routes, check-in plans, and late-hour transport options.")
    if transit_share >= 0.20:
        recommendations.append("Transit-linked records are visible; review station, platform, bus, and train waiting-area patterns.")
    if public_share >= 0.50:
        recommendations.append("Many incidents occur in public spaces; planning should consider street lighting, crowd flow, and staffed waiting points.")
    if area_risk is not None and not area_risk.empty:
        top_area = int(area_risk.iloc[0]["community_area"])
        recommendations.append(f"Community area {top_area} has the highest sample risk score; inspect its incident mix before drawing conclusions.")

    return recommendations


def page_notes() -> dict[str, str]:
    """Short navigation blurbs for the home page."""
    return {
        "Data Explorer": "Review the dataset, filter incidents, and inspect summary metrics.",
        "Risk Map": "View incident locations and community-area risk scores on an interactive map.",
        "Time Analysis": "Explore hourly, weekly, and monthly incident patterns.",
        "ML Insights": "Run beginner-friendly clustering and anomaly detection on the sample records.",
        "Report": "Generate a concise awareness report with risk summaries and recommendations.",
    }
