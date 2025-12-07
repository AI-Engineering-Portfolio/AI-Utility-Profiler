from pathlib import Path
import pandas as pd
from src.Processing.dq_profiling import profile_folder


def main():
    # 1) Choose input folder and output folder
    raw_folder = "data/raw"
    output_folder = Path("data/outputs")
    output_folder.mkdir(parents=True, exist_ok=True)

    # 2) Run profiling
    profile_df = profile_folder(raw_folder=raw_folder)

    # 3) Save as CSV
    csv_path = output_folder / "dq_profile.csv"
    profile_df.to_csv(csv_path, index=False)

    # 4) Save as JSON (records orientation for easy consumption by APIs)
    json_path = output_folder / "dq_profile.json"
    profile_df.to_json(json_path, orient="records")

    print("Profiling complete.")
    print(f"CSV written to:  {csv_path}")
    print(f"JSON written to: {json_path}")


if __name__ == "__main__":
    main()
