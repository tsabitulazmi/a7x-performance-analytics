from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.s3 import upload_file, upload_json
from src.youtube import (
    get_all_a7x_uploads,
    match_catalog_to_uploads,
    get_video_statistics_batch,
    build_youtube_processed_data,
    build_youtube_raw_snapshot,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CATALOG_PATH = (
    PROJECT_ROOT
    / "catalog"
    / "a7x_catalog.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "youtube_video_mapping.parquet"
)


def main():
    print("Starting YouTube ingestion...")
    print(f"Catalog: {CATALOG_PATH}")

    # --------------------------------------------------
    # 1. Extract YouTube channel uploads
    # --------------------------------------------------

    print(
        "\n[1/5] Retrieving A7X channel uploads..."
    )

    videos = get_all_a7x_uploads()

    print(
        f"Total uploads retrieved: {len(videos)}"
    )

    # --------------------------------------------------
    # 2. Match catalog songs to YouTube videos
    # --------------------------------------------------

    print(
        "\n[2/5] Matching catalog songs..."
    )

    matches = match_catalog_to_uploads(
        catalog_path=str(CATALOG_PATH),
        uploads=videos,
    )

    matched_count = sum(
        row["match_status"] == "MATCHED"
        for row in matches
    )

    print(
        f"Matched songs: "
        f"{matched_count}/{len(matches)}"
    )

    if matched_count != len(matches):
        print(
            "WARNING: Some catalog songs "
            "were not matched."
        )

    # --------------------------------------------------
    # 3. Retrieve YouTube statistics
    # --------------------------------------------------

    print(
        "\n[3/5] Retrieving YouTube statistics..."
    )

    video_ids = [
        row["youtube_video_id"]
        for row in matches
        if row["match_status"] == "MATCHED"
    ]

    stats = get_video_statistics_batch(
        video_ids
    )

    print(
        f"Statistics retrieved: {len(stats)}"
    )

    # --------------------------------------------------
    # 4. Build raw + processed datasets
    # --------------------------------------------------

    print(
        "\n[4/5] Building datasets..."
    )

    raw_snapshot = build_youtube_raw_snapshot(
        uploads=videos,
        stats=stats,
    )

    processed = build_youtube_processed_data(
        matches=matches,
        stats=stats,
    )

    df = pd.DataFrame(processed)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    ingestion_date = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d")

    print(
        f"Processed records: {len(df)}"
    )

    # --------------------------------------------------
    # 5. Upload to S3
    # --------------------------------------------------

    print(
        "\n[5/5] Uploading data to S3..."
    )

    raw_key = (
        f"raw/youtube/"
        f"{ingestion_date}/"
        f"youtube_videos.json"
    )

    upload_json(
        data=raw_snapshot,
        key=raw_key,
    )

    processed_key = (
        f"processed/youtube/"
        f"{ingestion_date}/"
        f"youtube_video_mapping.parquet"
    )

    upload_file(
        local_path=str(OUTPUT_PATH),
        key=processed_key,
        content_type="application/octet-stream",
    )

    # --------------------------------------------------
    # Done
    # --------------------------------------------------

    print(
        "\nYouTube ingestion completed successfully."
    )

    print(
        f"Records: {len(df)}"
    )

    print(
        f"Raw S3 key: {raw_key}"
    )

    print(
        f"Processed S3 key: {processed_key}"
    )


if __name__ == "__main__":
    main()