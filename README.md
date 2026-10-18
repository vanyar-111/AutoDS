# AutoDS — Automated Data Science Pipeline

AutoDS is a Flask-based web application that simplifies exploratory data analysis and dataset preparation. Users can upload a CSV file, inspect dataset characteristics, clean missing values and duplicate records, detect potential anomalies using machine learning, and generate a downloadable HTML report.

## Features

- **CSV Upload:** Upload tabular datasets and preview their contents.
- **Automated Dataset Profiling:** Inspect data types, missing values, descriptive statistics, distributions, skewness, kurtosis, and correlations.
- **Data Cleaning:** Handle missing values using automatic, mean, median, mode, or no-imputation strategies. Optionally remove duplicate records.
- **Anomaly Detection:** Use the Isolation Forest algorithm to identify potentially anomalous records in numeric data.
- **HTML Report Generation:** Generate a standalone report containing dataset statistics, data-quality information, cleaning summaries, and anomaly-detection results.
- **Interactive Web Interface:** Access the workflow through a browser-based interface built with HTML, CSS, and JavaScript.

## Technology Stack

| Component | Technologies |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn, Isolation Forest |
| Data Visualization and Analysis | Dataset statistics, distributions, and correlation analysis |
| Report Generation | Python-generated HTML reports |
| Development Environment | Python virtual environment |

## Application Workflow

```text
CSV Upload
    ↓
Dataset Preview
    ↓
Automated Dataset Profiling
    ↓
Data Cleaning
    ↓
Anomaly Detection
    ↓
HTML Report Generation
    ↓
Download Report
```

## Project Structure

```text
AutoDS/
├── app.py
├── backend/
│   ├── __init__.py
│   ├── profiler.py
│   ├── utils.py
│   ├── cleaner.py
│   ├── reportgen.py
│   └── anomaly_detector.py
├── datasets/
├── images/
├── models/
├── reports/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── templates/
│   └── index.html
├── requirements.txt
├── testdata.csv
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or a compatible Python version
- pip
- Git (optional, for cloning the repository)

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AutoDS
```

Alternatively, download the repository as a ZIP file and extract it.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

Open the local URL printed by Flask, typically:

```text
http://127.0.0.1:5000
```

## Anomaly Detection

AutoDS uses **Isolation Forest**, an unsupervised machine-learning algorithm, to identify observations that differ from the broader patterns in numeric data.

The implementation handles missing numeric values through median imputation and excludes numeric columns that contain no usable values or have no variation.

The contamination parameter controls the expected proportion of anomalies. Detected records should be interpreted as potential anomalies rather than confirmed errors or fraudulent observations.

## Data Cleaning

The cleaning pipeline supports the following strategies for missing values:

- **Auto:** Median imputation for numeric columns and mode imputation for categorical columns.
- **Mean:** Mean imputation for numeric columns.
- **Median:** Median imputation for numeric columns.
- **Mode:** Most-frequent-value imputation.
- **None:** Do not impute missing values.

Duplicate records can also be removed. The application provides a cleaning summary so users can inspect changes made to their datasets.

## Report Generation

The generated HTML report summarizes the analyzed dataset and can include:

- Dataset dimensions and column information
- Missing-value and duplicate statistics
- Descriptive statistics for numeric columns
- Data-cleaning results
- Anomaly-detection summaries and flagged records

The report can be opened in a browser and downloaded for later reference.

## Limitations

- The current application is designed primarily for interactive, single-user demonstrations.
- Anomaly detection requires sufficient rows and at least one numeric column with varying values.
- Isolation Forest results depend on the dataset and selected contamination setting.
- Uploaded datasets and intermediate results are maintained in application memory. The
