"""
AutoDS — Dataset Profiler
Comprehensive automated profiling for uploaded datasets.
Computes shape, types, missing values, duplicates, correlations,
class balance, and generates profile summaries.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from backend.utils import detect_task_type, get_numeric_columns, get_categorical_columns


@dataclass
class ProfileReport:
    """Container for all profiling results."""

    # Shape
    n_rows: int = 0
    n_cols: int = 0

    # Columns
    column_names: list[str] = field(default_factory=list)
    dtypes: dict[str, str] = field(default_factory=dict)

    # Missing values
    missing_counts: dict[str, int] = field(default_factory=dict)
    missing_pcts: dict[str, float] = field(default_factory=dict)
    total_missing: int = 0

    # Duplicates
    duplicate_rows: int = 0

    # Column categories
    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)

    # Statistics
    numeric_stats: pd.DataFrame | None = None  # describe() output
    correlation_matrix: pd.DataFrame | None = None

    # Target info
    target_column: str | None = None
    task_type: str | None = None  # Classification / Regression
    class_balance: dict | None = None  # value counts for classification targets

    # Skewness & Kurtosis
    skewness: dict[str, float] = field(default_factory=dict)
    kurtosis: dict[str, float] = field(default_factory=dict)

    # Unique value counts
    unique_counts: dict[str, int] = field(default_factory=dict)

    # Constant / quasi-constant columns
    constant_columns: list[str] = field(default_factory=list)

    # High cardinality categorical columns (>50 unique)
    high_cardinality_columns: list[str] = field(default_factory=list)


def profile_dataset(df: pd.DataFrame, target_col: str | None = None) -> ProfileReport:
    """
    Run full profiling on a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The uploaded dataset.
    target_col : str, optional
        Name of the target / label column. If None, the last column is assumed.

    Returns
    -------
    ProfileReport
        Dataclass containing all profiling results.
    """
    report = ProfileReport()

    # --- Shape ---
    report.n_rows, report.n_cols = df.shape

    # --- Columns & types ---
    report.column_names = df.columns.tolist()
    report.dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # --- Missing values ---
    missing = df.isnull().sum()
    report.missing_counts = missing[missing > 0].to_dict()
    report.missing_pcts = {
        col: round(count / report.n_rows * 100, 2)
        for col, count in report.missing_counts.items()
    }
    report.total_missing = int(missing.sum())

    # --- Duplicates ---
    report.duplicate_rows = int(df.duplicated().sum())

    # --- Column categories ---
    report.numeric_columns = get_numeric_columns(df)
    report.categorical_columns = get_categorical_columns(df)

    # --- Numeric statistics ---
    if report.numeric_columns:
        report.numeric_stats = df[report.numeric_columns].describe().round(2)

    # --- Correlation matrix (numeric only) ---
    if len(report.numeric_columns) >= 2:
        report.correlation_matrix = df[report.numeric_columns].corr().round(3)

    # --- Unique counts ---
    report.unique_counts = {col: int(df[col].nunique()) for col in df.columns}

    # --- Constant columns (only 1 unique value) ---
    report.constant_columns = [
        col for col, n in report.unique_counts.items() if n <= 1
    ]

    # --- High cardinality categoricals ---
    report.high_cardinality_columns = [
        col
        for col in report.categorical_columns
        if report.unique_counts.get(col, 0) > 50
    ]

    # --- Skewness & Kurtosis ---
    for col in report.numeric_columns:
        try:
            report.skewness[col] = round(float(df[col].skew()), 3)
            report.kurtosis[col] = round(float(df[col].kurtosis()), 3)
        except Exception:
            pass

    # --- Target column ---
    if target_col and target_col in df.columns:
        report.target_column = target_col
    else:
        # Default to the last column
        report.target_column = df.columns[-1]

    # --- Task type ---
    report.task_type = detect_task_type(df, report.target_column)

    # --- Class balance (classification only) ---
    if report.task_type == "Classification":
        vc = df[report.target_column].value_counts()
        report.class_balance = {str(k): int(v) for k, v in vc.items()}

    return report


def get_missing_summary(report: ProfileReport) -> list[dict]:
    """
    Return a list of dicts for display:
    [{"Column": ..., "Missing": ..., "Percent": ...}, ...]
    """
    rows = []
    for col, count in report.missing_counts.items():
        rows.append(
            {
                "Column": col,
                "Missing": count,
                "Percent (%)": report.missing_pcts[col],
            }
        )
    # Sort by missing count descending
    rows.sort(key=lambda r: r["Missing"], reverse=True)
    return rows


def get_type_summary(report: ProfileReport) -> list[dict]:
    """
    Return a list of dicts for data type display:
    [{"Column": ..., "Type": ..., "Unique": ...}, ...]
    """
    rows = []
    for col in report.column_names:
        rows.append(
            {
                "Column": col,
                "Type": report.dtypes[col],
                "Unique Values": report.unique_counts.get(col, "—"),
            }
        )
    return rows
