"""
AutoDS -- Flask Backend
Serves the frontend and exposes API endpoints for the ML pipeline.
"""

import os
import json
import traceback
from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import numpy as np

from backend.profiler import profile_dataset, get_missing_summary, get_type_summary

app = Flask(__name__)
app.secret_key = os.urandom(24)

# In-memory store (single-user, dev mode)
store = {
    "df": None,
    "profile": None,
    "filename": None,
}


# ── Helper: make numpy types JSON-serializable ──
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        return super().default(obj)


app.json_encoder = NumpyEncoder


# ── Pages ──

@app.route("/")
def index():
    return render_template("index.html")


# ── API: Upload CSV ──

@app.route("/api/upload", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only .csv files are supported"}), 400

    try:
        df = pd.read_csv(file)
        store["df"] = df
        store["filename"] = file.filename
        store["profile"] = None

        return jsonify({
            "filename": file.filename,
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024**2, 2),
            "column_names": df.columns.tolist(),
            "preview": df.head(10).fillna("").to_dict(orient="records"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Run Profiler ──

@app.route("/api/profile", methods=["POST"])
def run_profiler():
    if store["df"] is None:
        return jsonify({"error": "No dataset loaded. Upload a CSV first."}), 400

    data = request.get_json(silent=True) or {}
    target_col = data.get("target_column", None)

    try:
        df = store["df"]
        report = profile_dataset(df, target_col=target_col)
        store["profile"] = report

        # Build correlation matrix as nested list for the frontend
        corr_data = None
        if report.correlation_matrix is not None:
            corr_data = {
                "columns": report.correlation_matrix.columns.tolist(),
                "values": report.correlation_matrix.values.tolist(),
            }

        # Highly correlated pairs
        corr_pairs = []
        if report.correlation_matrix is not None:
            corr = report.correlation_matrix
            for i in range(len(corr.columns)):
                for j in range(i + 1, len(corr.columns)):
                    val = corr.iloc[i, j]
                    if abs(val) > 0.7:
                        corr_pairs.append({
                            "a": corr.columns[i],
                            "b": corr.columns[j],
                            "r": round(float(val), 3),
                        })

        return jsonify({
            "rows": report.n_rows,
            "columns": report.n_cols,
            "numeric_count": len(report.numeric_columns),
            "categorical_count": len(report.categorical_columns),
            "duplicate_rows": report.duplicate_rows,
            "total_missing": report.total_missing,
            "target_column": report.target_column,
            "task_type": report.task_type,
            "missing": get_missing_summary(report),
            "types": get_type_summary(report),
            "numeric_stats": report.numeric_stats.to_dict(orient="index") if report.numeric_stats is not None else None,
            "skewness": report.skewness,
            "kurtosis": report.kurtosis,
            "correlation": corr_data,
            "corr_pairs": corr_pairs,
            "class_balance": report.class_balance,
            "constant_columns": report.constant_columns,
            "high_cardinality": report.high_cardinality_columns,
            "numeric_columns": report.numeric_columns,
            "categorical_columns": report.categorical_columns,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── API: Get distribution data for a single column ──

@app.route("/api/distribution/<column>", methods=["GET"])
def get_distribution(column):
    if store["df"] is None:
        return jsonify({"error": "No dataset loaded"}), 400

    df = store["df"]
    if column not in df.columns:
        return jsonify({"error": f"Column '{column}' not found"}), 404

    try:
        series = df[column].dropna()
        hist, bin_edges = np.histogram(series, bins=30)
        return jsonify({
            "column": column,
            "bins": [round(float(b), 4) for b in bin_edges],
            "counts": [int(c) for c in hist],
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std": round(float(series.std()), 4),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    os.makedirs("datasets", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    app.run(debug=True, port=5000)
