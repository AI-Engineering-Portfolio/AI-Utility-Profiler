import pandas as pd
from pathlib import Path
from typing import List
from pandas.api.types import is_numeric_dtype, is_bool_dtype


def list_csv_files(folder: Path) -> List[Path]:
    """Return all CSV files in the given folder (non-recursive)."""
    return sorted(folder.glob("*.csv"))


def profile_dataframe(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Column-level profile for one DataFrame."""
    rows = []
    n_rows = len(df)

    for col in df.columns:
        s = df[col]
        nulls = s.isna().sum()
        null_pct = (nulls / n_rows * 100) if n_rows > 0 else 0
        distinct = s.nunique(dropna=True)

        # Default: no numeric stats
        numeric = {}

        # Only compute numeric stats for real numeric (not boolean) columns
        if is_numeric_dtype(s) and not is_bool_dtype(s):
            numeric_series = s.astype("float64")
            numeric = {
                "min": numeric_series.min(),
                "p25": numeric_series.quantile(0.25),
                "median": numeric_series.median(),
                "p75": numeric_series.quantile(0.75),
                "max": numeric_series.max(),
            }

        rows.append(
            {
                "table": table_name,
                "column": col,
                "rows": n_rows,
                "nulls": nulls,
                "null_pct": round(null_pct, 2),
                "distinct": int(distinct),
                **numeric,
            }
        )

    return pd.DataFrame(rows)


def profile_folder(raw_folder: str = "data/raw") -> pd.DataFrame:
    """
    Profile all CSVs in the given folder and return one combined DataFrame.
    Each file becomes one 'table' in the profile.
    """
    folder_path = Path(raw_folder)
    all_profiles = []

    for path in list_csv_files(folder_path):
        df = pd.read_csv(path)
        table_name = path.stem  # filename without extension
        prof = profile_dataframe(df, table_name)
        all_profiles.append(prof)

    if not all_profiles:
        raise FileNotFoundError(f"No CSV files found in {folder_path}")

    return pd.concat(all_profiles, ignore_index=True)
