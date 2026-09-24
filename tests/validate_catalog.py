import pandas as pd
from pathlib import Path


CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "catalog"
    / "a7x_catalog.csv"
)


EXPECTED_TRACKS = {
    "A7X-01": 13,
    "A7X-02": 12,
    "A7X-03": 11,
    "A7X-04": 10,
    "A7X-05": 11,
    "A7X-06": 10,
    "A7X-07": 11,
    "A7X-08": 11,
}


def validate_catalog():
    print(f"Reading catalog: {CATALOG_PATH}")

    df = pd.read_csv(CATALOG_PATH)

    # ---------------------------------------------------------
    # 1. Basic row count
    # ---------------------------------------------------------

    assert len(df) == 89, (
        f"Expected 89 songs, found {len(df)}"
    )

    # ---------------------------------------------------------
    # 2. Album count
    # ---------------------------------------------------------

    assert df["album_id"].nunique() == 8, (
        f"Expected 8 albums, found {df['album_id'].nunique()}"
    )

    # ---------------------------------------------------------
    # 3. Required columns
    # ---------------------------------------------------------

    required_columns = {
        "song_id",
        "album_id",
        "artist_name",
        "album_name",
        "song_name",
        "track_number",
        "release_date",
        "version_type",
        "is_primary_version",
    }

    missing_columns = required_columns - set(df.columns)

    assert not missing_columns, (
        f"Missing columns: {missing_columns}"
    )

    # ---------------------------------------------------------
    # 4. NULL checks
    # ---------------------------------------------------------

    required_non_null = [
        "song_id",
        "album_id",
        "artist_name",
        "album_name",
        "song_name",
        "track_number",
        "release_date",
        "version_type",
    ]

    for column in required_non_null:
        assert df[column].notna().all(), (
            f"NULL values found in {column}"
        )

    # ---------------------------------------------------------
    # 5. song_id uniqueness
    # ---------------------------------------------------------

    assert df["song_id"].is_unique, (
        "song_id contains duplicates"
    )

    # ---------------------------------------------------------
    # 6. Album + track number uniqueness
    # ---------------------------------------------------------

    duplicate_tracks = df.duplicated(
        subset=["album_id", "track_number"]
    )

    assert not duplicate_tracks.any(), (
        "Duplicate album_id + track_number combinations found"
    )

    # ---------------------------------------------------------
    # 7. Artist validation
    # ---------------------------------------------------------

    assert (
        df["artist_name"] == "Avenged Sevenfold"
    ).all(), (
        "Unexpected artist found in catalog"
    )

    # ---------------------------------------------------------
    # 8. Version validation
    # ---------------------------------------------------------

    assert (
        df["version_type"] == "studio_album"
    ).all(), (
        "Unexpected version_type found"
    )

    assert (
        df["is_primary_version"] == True
    ).all(), (
        "Non-primary version found"
    )

    # ---------------------------------------------------------
    # 9. Track count per album
    # ---------------------------------------------------------

    actual_tracks = (
        df.groupby("album_id")
        .size()
        .to_dict()
    )

    assert actual_tracks == EXPECTED_TRACKS, (
        f"Unexpected track counts:\n"
        f"Expected: {EXPECTED_TRACKS}\n"
        f"Actual: {actual_tracks}"
    )

    print()
    print("=" * 50)
    print("CATALOG VALIDATION PASSED")
    print("=" * 50)
    print(f"Songs  : {len(df)}")
    print(f"Albums : {df['album_id'].nunique()}")
    print(f"Artist : {df['artist_name'].unique().tolist()}")
    print("=" * 50)


if __name__ == "__main__":
    validate_catalog()