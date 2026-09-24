from datetime import datetime, timezone
from pathlib import Path

from src.s3 import upload_file, upload_json
from src.spotify import ingest_catalog


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = PROJECT_ROOT / "catalog" / "a7x_catalog.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "spotify_track_mapping.parquet"


def main():
    print("Starting Spotify ingestion...")
    print(f"Catalog: {CATALOG_PATH}")

    print("\n[1/5] Retrieving Spotify track data...")
    result, raw_data = ingest_catalog(
        catalog_path=str(CATALOG_PATH)
    )

    print("\n[2/5] Building datasets...")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    result.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Processed records: {len(result)}")

    print("\n[3/5] Validating match results...")

    matched_count = (
        result["match_status"] == "MATCHED"
    ).sum()

    print(
        f"Matched songs: "
        f"{matched_count}/{len(result)}"
    )

    if matched_count != len(result):
        print("WARNING: Some catalog songs were not matched.")

    print("\n[4/5] Preparing S3 paths...")

    ingestion_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    raw_key = (
        f"raw/spotify/"
        f"{ingestion_date}/"
        f"spotify_tracks.json"
    )

    processed_key = (
        f"processed/spotify/"
        f"{ingestion_date}/"
        f"spotify_track_mapping.parquet"
    )

    print("\n[5/5] Uploading data to S3...")

    upload_json(
        data=raw_data,
        key=raw_key,
    )

    upload_file(
        local_path=str(OUTPUT_PATH),
        key=processed_key,
        content_type="application/octet-stream",
    )

    print("\nSpotify ingestion completed successfully.")
    print(f"Records: {len(result)}")
    print(f"Raw S3 key: {raw_key}")
    print(f"Processed S3 key: {processed_key}")


if __name__ == "__main__":
    main()