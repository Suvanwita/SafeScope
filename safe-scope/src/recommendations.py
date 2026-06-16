import pandas as pd


def generate_recommendations(df: pd.DataFrame, area_risk: pd.DataFrame) -> list[str]:
    """Create awareness-oriented recommendations from observed patterns."""
    recommendations = [
        "Use these findings for planning, awareness, and resource conversations, not as real-time safety predictions.",
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
        recommendations.append("Many incidents occur in public spaces; planning should consider street lighting, crowd flow, and safe waiting points.")
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
