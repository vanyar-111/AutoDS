from datetime import datetime
from html import escape
from pathlib import Path
import pandas as pd

def generate_html_report(
    df,
    filename="dataset.csv",
    profile=None,
    cleaning_summary=None,
    anomaly_results=None,
):
    """Generate a self-contained HTML report for a dataset."""

    rows, columns = df.shape
    missing_total = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    categorical_columns = [
        col for col in df.columns if col not in numeric_columns
    ]

    def make_table(headers, body_rows):
        head_html = "".join(
            f"<th>{escape(str(header))}</th>" for header in headers
        )
        rows_html = ""

        for row in body_rows:
            cells = "".join(
                f"<td>{escape(str(value))}</td>" for value in row
            )
            rows_html += f"<tr>{cells}</tr>"

        return (
            "<div class='table-wrap'><table><thead><tr>"
            + head_html
            + "</tr></thead><tbody>"
            + rows_html
            + "</tbody></table></div>"
        )

    type_rows = [
        (column, str(df[column].dtype), int(df[column].nunique()))
        for column in df.columns
    ]

    missing_rows = [
        (column, int(count), round(count / max(rows, 1) * 100, 2))
        for column, count in df.isna().sum().items()
        if count > 0
    ]

    statistics_html = ""
    if numeric_columns:
        stats = df[numeric_columns].describe().round(3)
        statistics_html = make_table(
            ["Statistic"] + numeric_columns,
            [
                [index] + [stats.loc[index, col] for col in numeric_columns]
                for index in stats.index
            ],
        )

    cleaning_html = "<p>No cleaning operation recorded.</p>"
    if cleaning_summary:
        cleaning_rows = [
            (key.replace("_", " ").title(), value)
            for key, value in cleaning_summary.items()
        ]
        cleaning_html = make_table(
            ["Metric", "Value"], cleaning_rows
        )
        anomaly_html = "<p>Anomaly detection has not been run.</p>"

    if anomaly_results:
        anomaly_rows = [
            ("Rows analyzed", anomaly_results["rows_analyzed"]),
            ("Numeric columns used", ", ".join(
                anomaly_results["numeric_columns_used"]
            )),
            ("Potential anomalies detected",
             anomaly_results["anomalies_detected"]),
            ("Anomaly percentage",
             f'{anomaly_results["anomaly_percentage"]}%'),
        ]

        anomaly_html = make_table(
            ["Metric", "Value"],
            anomaly_rows,
        )

        flagged_rows = anomaly_results.get("anomalies", [])
        if flagged_rows:
            anomaly_columns = list(flagged_rows[0].keys())
            anomaly_html += make_table(
                anomaly_columns,
                [
                    [row.get(column, "") for column in anomaly_columns]
                    for row in flagged_rows
                ],
            )
        else:
            anomaly_html += "<p>No potential anomalies were flagged.</p>"

    missing_html = (
        make_table(
            ["Column", "Missing values", "Missing (%)"],
            missing_rows,
        )
        if missing_rows
        else "<p>No missing values found.</p>"
    )

    generated_at = datetime.now().strftime("%d %b %Y, %H:%M")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AutoDS Report — {escape(filename)}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    max-width: 1100px;
    margin: 35px auto;
    padding: 0 20px;
    color: #202437;
    background: #f4f5fa;
    line-height: 1.5;
}}
h1, h2 {{ color: #4146a5; }}
section, .metric {{
    background: white;
    border: 1px solid #e0e2ec;
    border-radius: 10px;
    padding: 20px;
    margin: 18px 0;
}}
.metrics {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
}}
.metric strong {{ display: block; font-size: 1.6rem; }}
.table-wrap {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{
    text-align: left;
    padding: 10px;
    border-bottom: 1px solid #e5e6ee;
}}
th {{ background: #eeeff8; }}
button {{
    padding: 10px 16px;
    border: 0;
    border-radius: 6px;
    background: #5559c7;
    color: white;
    cursor: pointer;
}}
@media print {{
    body {{ background: white; margin: 0; }}
    button {{ display: none; }}
    section, .metric {{ break-inside: avoid; }}
}}
</style>
</head>
<body>
<button onclick="window.print()">Print / Save as PDF</button>
<h1>AutoDS — Automated Data Science Report</h1>
<p>Dataset: <strong>{escape(str(filename))}</strong></p>
<p>Generated: {generated_at}</p>

<section>
<h2>1. Dataset Overview</h2>
<div class="metrics">
<div class="metric">Rows<strong>{rows}</strong></div>
<div class="metric">Columns<strong>{columns}</strong></div>
<div class="metric">Missing cells<strong>{missing_total}</strong></div>
<div class="metric">Duplicate rows<strong>{duplicates}</strong></div>
</div>
<p>Numeric columns: {len(numeric_columns)}</p>
<p>Categorical columns: {len(categorical_columns)}</p>
</section>

<section>
<h2>2. Column Information</h2>
{make_table(["Column", "Data type", "Unique values"], type_rows)}
</section>

<section>
<h2>3. Missing Value Analysis</h2>
{missing_html}
</section>

<section>
<h2>4. Numeric Summary Statistics</h2>
{statistics_html or "<p>No numeric columns available.</p>"}
</section>

<section>
<h2>5. Cleaning Summary</h2>
{cleaning_html}
</section>

<section>
<h2>6. Anomaly Detection Summary</h2>
{anomaly_html}
<p><em>Anomalies are potential outliers, not necessarily data errors.</em></p>
</section>

<footer>
<p>Generated locally by AutoDS.</p>
</footer>
</body>
</html>"""
