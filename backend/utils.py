"""
AutoDS — Utility Functions
Shared helpers used across backend modules.
"""

import pandas as pd
import numpy as np


def detect_task_type(df: pd.DataFrame, target_col: str) -> str:
    """
    Detect whether the task is Classification or Regression
    based on the target column's characteristics.

    Heuristic:
      - If dtype is object/category/bool → Classification
      - If dtype is numeric with ≤ 20 unique values → Classification
      - Otherwise → Regression
    """
    series = df[target_col]

    if series.dtype == "bool" or pd.api.types.is_categorical_dtype(series):
        return "Classification"

    if pd.api.types.is_object_dtype(series):
        return "Classification"

    n_unique = series.nunique()
    if n_unique <= 20:
        return "Classification"

    return "Regression"


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Return list of numeric column names."""
    return df.select_dtypes(include=[np.number]).columns.tolist()


def get_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Return list of categorical / object column names."""
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()


def abbreviate_number(n: int | float) -> str:
    """Human-friendly number abbreviation (e.g. 1200 → '1.2K')."""
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Division that returns *default* when divisor is zero."""
    return a / b if b != 0 else default
