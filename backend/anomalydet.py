import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
def detect_anomalies(df, contamination=0.05):
    """
    Detect potentially anomalous rows using Isolation Forest.

    Returns summary metrics and flagged rows.
    """
    if df is None or df.empty:
        raise ValueError("The dataset is empty.")

    if not isinstance(contamination, (int, float)) or isinstance(
        contamination, bool
    ) or not np.isfinite(contamination) or not 0 < contamination <= 0.5:
        raise ValueError(
            "Contamination must be a number greater than 0 and at most 0.5."
        )

    if len(df) < 5:
        raise ValueError(
            "At least 5 rows are required for anomaly detection."
        )

    # Select numeric columns.
    numeric_df = df.select_dtypes(include="number").copy()

    # Treat infinite values as missing.
    numeric_df = numeric_df.replace([np.inf, -np.inf], np.nan)

    # Exclude entirely missing and constant columns.
    usable_columns = [
        col for col in numeric_df.columns
        if numeric_df[col].notna().any()
        and numeric_df[col].nunique(dropna=True) > 1
    ]
    numeric_df = numeric_df[usable_columns]

    if numeric_df.empty:
        raise ValueError(
            "Anomaly detection requires at least one numeric "
            "column with varying values."
        )

    # Impute missing numeric values.
    imputer = SimpleImputer(strategy="median")
    X = imputer.fit_transform(numeric_df)

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42
    )

    predictions = model.fit_predict(X)
    scores = model.decision_function(X)

    results = df.copy()
    results.insert(0, "Row Number", range(1, len(df) + 1))
    results["Anomaly Score"] = scores
    results["Anomaly"] = np.where(
        predictions == -1,
        "Potential Anomaly",
        "Normal"
    )

    flagged = results[
        results["Anomaly"] == "Potential Anomaly"
    ].copy()

    # Make missing and non-finite values JSON-friendly.
    def records_for_json(frame):
        safe_frame = frame.astype(object)
        safe_frame = safe_frame.where(pd.notna(safe_frame), None)
        safe_frame = safe_frame.replace(
            [np.inf, -np.inf], None
        )
        return safe_frame.to_dict(orient="records")

    return {
        "rows_analyzed": int(len(df)),
        "numeric_columns_used": list(usable_columns),
        "anomalies_detected": int(len(flagged)),
        "anomaly_percentage": round(
            len(flagged) / len(df) * 100, 2
        ),
        "anomalies": records_for_json(flagged),
        "all_results": records_for_json(results),
    }
