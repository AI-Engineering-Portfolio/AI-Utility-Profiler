from pathlib import Path
from src.Processing.dq_profiling import profile_folder


def main():
    raw_folder = "data/raw"
    output_folder = Path("data/outputs")
    output_folder.mkdir(parents=True, exist_ok=True)

    profile_df = profile_folder(raw_folder=raw_folder)

    csv_path = output_folder / "dq_profile.csv"
    json_path = output_folder / "dq_profile.json"

    profile_df.to_csv(csv_path, index=False)
    profile_df.to_json(json_path, orient="records")

    print("Profiling complete.")
    print(f"CSV written to: {csv_path}")
    print(f"JSON written to: {json_path}")


if __name__ == "__main__":
    main()
