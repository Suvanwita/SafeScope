# SafeScope: Women Safety Pattern Analyzer

SafeScope is a Streamlit multipage analytics app for exploring historical public incident data through maps, time patterns, explainable risk scoring, and machine learning summaries.

## Problem Statement

Women and community planners often need a simple way to understand historical incident patterns by place and time. Raw public datasets can be difficult to inspect quickly, especially during hackathons, civic planning discussions, or awareness workshops. SafeScope turns a CSV dataset into a clean, visual, explainable dashboard for awareness and planning conversations.

## Features

- CSV upload with sample Chicago-style incident data
- Column normalization for common alternatives such as `date/time`, `crime_type`, `lat`, and `lng`
- Data cleaning, coordinate validation, and time feature generation
- Interactive Data Explorer with filters and Plotly charts
- Folium heatmap and marker-cluster incident map
- Approximate grid-cell risk scoring
- Time analysis by hour, weekday, and month
- ML Insights page with DBSCAN and Isolation Forest
- Rule-based recommendations
- Downloadable CSV and text reports
- Streamlit session-state workflow across pages

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Scikit-learn
- Plotly
- Folium
- streamlit-folium
- Matplotlib

## ML Models Used

### DBSCAN

DBSCAN finds dense geographic regions of historical incidents. SafeScope uses it to identify hotspot clusters and noise points without requiring a fixed number of clusters.

### Isolation Forest

Isolation Forest flags unusual date-and-grid incident spikes compared with normal historical patterns in the uploaded dataset.

### Explainable Risk Scoring

Grid risk scores combine:

- Historical incident density
- Average severity
- Night-time ratio
- Recent activity when available

The score is explainable and designed for awareness, not real-time prediction.

## Dataset Instructions

Use the bundled sample file:

```text
data/sample_chicago_crimes.csv
```

You can also upload a CSV with these required fields:

- `Date`
- `Primary Type`
- `Description`
- `Location Description`
- `Latitude`
- `Longitude`

Common alternatives are normalized automatically:

- `date/time` -> `Date`
- `crime_type` or `category` -> `Primary Type`
- `lat` -> `Latitude`
- `lon` or `lng` -> `Longitude`

Optional fields such as `case_number`, `domestic`, `ward`, and `community_area` improve the dashboard but are not required.

## How To Run

```bash
cd safe-scope
pip install -r requirements.txt
streamlit run app.py
```

For an isolated local setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Ethical Disclaimer

SafeScope uses historical public incident data for awareness and planning only. It does not predict real-time danger, guarantee safety, replace emergency services, or make legal/policing decisions.

## Future Improvements

- Real-time official alerts
- Route comparison
- Multilingual support
- Emergency contact integration
- India city-level dataset support

## Project Structure

```text
safe-scope/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   └── sample_chicago_crimes.csv
├── src/
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── feature_engineering.py
│   ├── visualizations.py
│   ├── risk_score.py
│   ├── clustering.py
│   ├── anomaly_detection.py
│   ├── recommendations.py
│   ├── pipeline.py
│   └── ui.py
├── pages/
│   ├── 1_Data_Explorer.py
│   ├── 2_Risk_Map.py
│   ├── 3_Time_Analysis.py
│   ├── 4_ML_Insights.py
│   └── 5_Report.py
└── assets/
```

No paid APIs are used.
