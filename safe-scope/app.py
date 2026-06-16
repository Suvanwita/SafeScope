import streamlit as st

from src.ui import render_disclaimer, render_sidebar


st.set_page_config(page_title="SafeScope", layout="wide", initial_sidebar_state="expanded")


def main() -> None:
    render_sidebar("App")

    st.title("SafeScope")
    st.subheader("Women Safety Pattern Analyzer")

    render_disclaimer()

    st.markdown(
        "Think of this as a planning buddy before you step out. You can check what past public incident records "
        "suggest around a place and time, then use that context to make more thoughtful choices about routes, "
        "timing, check-ins, and transport."
    )
    st.markdown(
        "It is not here to scare you or tell you what to do. It is here to give you a clearer picture, so you can "
        "plan with a little more confidence and a little less guesswork."
    )

    st.markdown("## Quick Guide")
    guide_col1, guide_col2 = st.columns(2)
    with guide_col1:
        st.container(border=True).markdown(
            "**1. Load the records**\n\n"
            "Open **Data Explorer** and use the sample records or upload a historical incident CSV."
        )
        st.container(border=True).markdown(
            "**2. Look at the patterns**\n\n"
            "Use **Risk Map**, **Time Analysis**, and **ML Insights** to see where and when incidents appear more often."
        )
    with guide_col2:
        st.container(border=True).markdown(
            "**3. Ask about your plan**\n\n"
            "Open **Report**, enter a latitude, longitude, day, and hour, then generate recommendations."
        )
        st.container(border=True).markdown(
            "**4. Use it alongside real-world care**\n\n"
            "Check official updates, share trip details with someone you trust, and choose well-lit, active routes when possible."
        )


if __name__ == "__main__":
    main()
