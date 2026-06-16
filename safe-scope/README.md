# SafeScope: Women Safety Pattern Analyzer

SafeScope is a complete beginner-friendly Streamlit multipage project for exploring historical public incident data. It is built for awareness, planning, and learning data analysis workflows.

## Ethical Disclaimer

SafeScope uses historical public incident data for awareness and planning only. It does not predict real-time danger, guarantee safety, replace emergency services, or make legal/policing decisions.

## Features

- Streamlit multipage dashboard
- Sample Chicago-style crime incident dataset
- Data cleaning and feature engineering modules
- Interactive data explorer with filters
- Folium risk map with community-area risk scoring
- Hourly, weekday, and monthly time analysis
- KMeans clustering and Isolation Forest anomaly detection
- Awareness-oriented report and recommendations

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
│   └── recommendations.py
├── pages/
│   ├── 1_Data_Explorer.py
│   ├── 2_Risk_Map.py
│   ├── 3_Time_Analysis.py
│   ├── 4_ML_Insights.py
│   └── 5_Report.py
└── assets/
```

## Setup

```bash
cd safe-scope
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data

The bundled CSV is a compact educational sample inspired by columns found in public Chicago crime datasets. For real analysis, replace `data/sample_chicago_crimes.csv` with official open data that uses the same columns:

- `case_number`
- `date`
- `primary_type`
- `description`
- `location_description`
- `arrest`
- `domestic`
- `ward`
- `community_area`
- `latitude`
- `longitude`

## Notes for Learners

The app keeps logic in small modules under `src/`:

- `data_loader.py` reads sample or uploaded CSV files.
- `preprocessing.py` cleans and validates records.
- `feature_engineering.py` creates time, safety, and severity features.
- `risk_score.py` calculates transparent area-level risk scores.
- `clustering.py` groups similar incidents.
- `anomaly_detection.py` flags unusual records.
- `recommendations.py` writes awareness-oriented guidance.
- `visualizations.py` centralizes Plotly and Folium charts.

No paid APIs are used.
