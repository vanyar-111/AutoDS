# AutoDS — Automated Data Science Pipeline

**End-to-end automated ML pipeline**: upload a CSV and get profiling, cleaning, feature engineering, model training, hyperparameter tuning, SHAP explainability, and a downloadable report — all from a single Streamlit dashboard.

---

## 🗺️ Pipeline

```
CSV Upload → Dataset Profiler → Cleaning → Feature Engineering
    → Model Training → Hyperparameter Tuning → Model Comparison
    → SHAP Explainability → HTML/PDF Report → Streamlit Dashboard
```

## 🛠️ Tech Stack

| Purpose               | Library                         |
| --------------------- | ------------------------------- |
| Frontend              | Streamlit                       |
| Data Processing       | Pandas, NumPy                   |
| Visualization         | Matplotlib, Plotly, Seaborn     |
| ML Models             | Scikit-learn, XGBoost, LightGBM |
| Hyperparameter Tuning | Optuna                          |
| Explainability        | SHAP                            |
| Report Generation     | Jinja2 + WeasyPrint             |
| Model Saving          | Joblib                          |

## 🚀 Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

## 📁 Project Structure

```
AutoDS/
├── app.py                    # Streamlit dashboard
├── backend/
│   ├── profiler.py           # Dataset profiling
│   ├── cleaner.py            # Data cleaning pipeline
│   ├── feature_engineering.py# Feature creation & ranking
│   ├── trainer.py            # Model training engine
│   ├── tuner.py              # Optuna hyperparameter tuning
│   ├── explainer.py          # SHAP explainability
│   ├── report.py             # HTML/PDF report generation
│   └── utils.py              # Shared utilities
├── datasets/                 # Sample datasets
├── reports/                  # Generated reports
├── models/                   # Saved trained models
├── images/                   # SHAP plots & visualizations
├── requirements.txt
└── README.md
```

## 📌 Status

- [x] CSV Upload
- [x] Dataset Profiling
- [ ] Cleaning Pipeline
- [ ] Feature Engineering
- [ ] Model Training
- [ ] Hyperparameter Tuning
- [ ] Model Comparison
- [ ] SHAP Explainability
- [ ] Report Generation

