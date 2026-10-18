import pandas as pd
from backend.anomalydet import detect_anomalies

df = pd.read_csv("testdata.csv")

try:
    result = detect_anomalies(df)
    print("Rows analyzed:", result["rows_analyzed"])
    print("Numeric columns:", result["numeric_columns_used"])
    print("Potential anomalies:", result["anomalies_detected"])
    print("Anomaly percentage:", result["anomaly_percentage"])
    print(pd.DataFrame(result["anomalies"]))
except ValueError as error:
    print("Cannot run anomaly detection:", error)