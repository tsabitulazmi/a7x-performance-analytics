import base64
import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1"


def get_access_token() -> str:
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        raise ValueError(
            "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET "
            "must be configured in .env"
        )

    credentials = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "client_credentials"
    }

    response = requests.post(
        TOKEN_URL,
        headers=headers,
        data=data,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["access_token"]


def search_track(
    track_name: str,
    album_name: str,
    access_token: str,
) -> dict[str, Any]:

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "q": (
            f'track:"{track_name}" '
            f'album:"{album_name}" '
            f'artist:"Avenged Sevenfold"'
        ),
        "type": "track",
        "limit": 5,
    }

    response = requests.get(
        f"{API_BASE_URL}/search",
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def transform_spotify_result(
    row: pd.Series,
    response: dict[str, Any],
    ingested_at: str,
) -> dict[str, Any]:

    items = response.get(
        "tracks",
        {}
    ).get(
        "items",
        []
    )

    if not items:
        return {
            "song_id": row["song_id"],
            "album_id": row["album_id"],
            "song_name": row["song_name"],
            "album_name": row["album_name"],
            "spotify_track_id": None,
            "spotify_album_id": None,
            "spotify_track_uri": None,
            "spotify_url": None,
            "spotify_track_name": None,
            "spotify_album_name": None,
            "duration_ms": None,
            "explicit": None,
            "track_number": None,
            "match_status": "NOT_FOUND",
            "ingested_at": ingested_at,
        }

    track = items[0]

    return {
        "song_id": row["song_id"],
        "album_id": row["album_id"],
        "song_name": row["song_name"],
        "album_name": row["album_name"],
        "spotify_track_id": track["id"],
        "spotify_album_id": track["album"]["id"],
        "spotify_track_uri": track["uri"],
        "spotify_url": track["external_urls"].get("spotify"),
        "spotify_track_name": track["name"],
        "spotify_album_name": track["album"]["name"],
        "duration_ms": track["duration_ms"],
        "explicit": track["explicit"],
        "track_number": track["track_number"],
        "match_status": "MATCHED",
        "ingested_at": ingested_at,
    }


def ingest_catalog(
    catalog_path: str,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:

    catalog = pd.read_csv(catalog_path)

    access_token = get_access_token()

    processed_records = []
    raw_records = []

    for _, row in catalog.iterrows():
        ingested_at = datetime.now(timezone.utc).isoformat()

        # ONE Spotify API call
        response = search_track(
            track_name=row["song_name"],
            album_name=row["album_name"],
            access_token=access_token,
        )

        # ---------------------------------------------
        # Raw layer
        # ---------------------------------------------

        raw_records.append(
            {
                "ingested_at": ingested_at,
                "song_id": row["song_id"],
                "album_id": row["album_id"],
                "song_name": row["song_name"],
                "album_name": row["album_name"],
                "search_response": response,
            }
        )

        # ---------------------------------------------
        # Processed layer
        # ---------------------------------------------

        processed_record = transform_spotify_result(
            row=row,
            response=response,
            ingested_at=ingested_at,
        )

        processed_records.append(
            processed_record
        )

    processed_df = pd.DataFrame(
        processed_records
    )

    return processed_df, raw_records