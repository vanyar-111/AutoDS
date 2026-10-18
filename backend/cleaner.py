import pandas as pd
def clean_dataset(
    df,
    missing_strategy="auto",
    remove_duplicates=True
):
    cleaned_df = df.copy()

    allowed_strategies = {
        "auto", "mean", "median", "mode", "none"
    }
    if missing_strategy not in allowed_strategies:
        raise ValueError(
            f"Strategy must be one of {sorted(allowed_strategies)}"
        )

    rows_before = len(cleaned_df)
    missing_before = int(cleaned_df.isna().sum().sum())
    duplicates_before = int(cleaned_df.duplicated().sum())

    if remove_duplicates:
        cleaned_df = cleaned_df.drop_duplicates().copy()

    if missing_strategy != "none":
        for column in cleaned_df.columns:
            if not cleaned_df[column].isna().any():
                continue

            series = cleaned_df[column]

            if missing_strategy == "mean":
                if not pd.api.types.is_numeric_dtype(series):
                    raise ValueError(
                        f"Mean imputation requires numeric column: {column}"
                    )
                fill_value = series.mean()

            elif missing_strategy == "median":
                if not pd.api.types.is_numeric_dtype(series):
                    raise ValueError(
                        f"Median imputation requires numeric column: {column}"
                    )
                fill_value = series.median()

            elif missing_strategy == "mode":
                mode = series.mode(dropna=True)
                fill_value = mode.iloc[0] if not mode.empty else None

            else:  # auto
                if pd.api.types.is_numeric_dtype(series):
                    fill_value = series.median()
                else:
                    mode = series.mode(dropna=True)
                    fill_value = (
                        mode.iloc[0] if not mode.empty else None
                    )

            if fill_value is not None:
                cleaned_df[column] = series.fillna(fill_value)

    summary = {
        "rows_before": int(rows_before),
        "rows_after": int(len(cleaned_df)),
        "duplicates_found": int(duplicates_before),
        "duplicates_removed": int(
            duplicates_before if remove_duplicates else 0
        ),
        "missing_before": missing_before,
        "missing_after": int(cleaned_df.isna().sum().sum()),
        "missing_strategy": missing_strategy,
    }

    return cleaned_df, summary
