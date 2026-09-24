import os
import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_ARTIST_CHANNEL_ID = os.getenv(
    "YOUTUBE_ARTIST_CHANNEL_ID"
)

YOUTUBE_TOPIC_CHANNEL_ID = os.getenv(
    "YOUTUBE_TOPIC_CHANNEL_ID"
)

API_BASE_URL = "https://www.googleapis.com/youtube/v3"


def search_videos(
    song_name: str,
) -> dict[str, Any]:

    if not YOUTUBE_API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY must be configured in .env"
        )

    if not YOUTUBE_OFFICIAL_CHANNEL_ID:
        raise ValueError(
            "YOUTUBE_OFFICIAL_CHANNEL_ID must be configured "
            "in .env"
        )

    params = {
        "part": "snippet",
        "channelId": YOUTUBE_OFFICIAL_CHANNEL_ID,
        "q": song_name,
        "type": "video",
        "maxResults": 10,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(
        f"{API_BASE_URL}/search",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def normalize_text(text: str) -> str:
    """
    Normalize text for song-title matching.
    """

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def title_matches_song(
    title: str,
    song_name: str,
) -> bool:
    """
    Determine whether a YouTube title contains
    the catalog song name.
    """

    normalized_title = normalize_text(title)
    normalized_song = normalize_text(song_name)

    return normalized_song in normalized_title


def select_official_video(
    search_response: dict[str, Any],
    song_name: str,
) -> dict[str, Any] | None:

    items = search_response.get(
        "items",
        []
    )

    if not items:
        return None

    matching_videos = []

    for video in items:

        snippet = video["snippet"]

        title = snippet["title"]

        if title_matches_song(
            title=title,
            song_name=song_name,
        ):
            matching_videos.append(video)

    if not matching_videos:
        return None

    # --------------------------------------------------
    # Prefer official music video over official audio
    # --------------------------------------------------

    def video_priority(video: dict[str, Any]) -> int:

        title = normalize_text(
            video["snippet"]["title"]
        )

        if "official music video" in title:
            return 1

        if "official video" in title:
            return 2

        if "official audio" in title:
            return 3

        if "music video" in title:
            return 4

        return 5

    matching_videos.sort(
        key=video_priority
    )

    return matching_videos[0]


def get_video_statistics(
    video_ids: list[str],
) -> dict[str, Any]:

    if not video_ids:
        return {
            "items": []
        }

    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(
        f"{API_BASE_URL}/videos",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()

def get_video_statistics_batch(
    video_ids: list[str],
) -> list[dict[str, Any]]:
    results = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]

        response = get_video_statistics(batch)

        results.extend(response.get("items", []))

    return results

def get_uploads_playlist_id(channel_id: str) -> str:
    if not YOUTUBE_API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY must be configured in .env"
        )

    params = {
        "part": "contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(
        f"{API_BASE_URL}/channels",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    items = response.json().get("items", [])

    if not items:
        raise ValueError(
            f"YouTube channel not found: {channel_id}"
        )

    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_channel_uploads(
    channel_id: str,
    channel_type: str,
) -> list[dict[str, Any]]:

    playlist_id = get_uploads_playlist_id(channel_id)

    videos = []
    next_page_token = None

    while True:
        params = {
            "part": "snippet,contentDetails",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": YOUTUBE_API_KEY,
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(
            f"{API_BASE_URL}/playlistItems",
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        for video in data.get("items", []):
            video["source_channel_type"] = channel_type
            videos.append(video)

        next_page_token = data.get("nextPageToken")

        if not next_page_token:
            break

    return videos


def transform_youtube_result(
    row: pd.Series,
    video: dict[str, Any] | None,
    statistics: dict[str, Any] | None,
    ingested_at: str,
) -> dict[str, Any]:

    if video is None:
        return {
            "song_id": row["song_id"],
            "album_id": row["album_id"],
            "song_name": row["song_name"],
            "album_name": row["album_name"],
            "youtube_video_id": None,
            "youtube_title": None,
            "youtube_channel_id": None,
            "youtube_channel_title": None,
            "published_at": None,
            "youtube_content_type": None,
            "view_count": None,
            "like_count": None,
            "comment_count": None,
            "match_status": "NOT_FOUND",
            "ingested_at": ingested_at,
        }

    snippet = video["snippet"]

    video_id = video["id"]["videoId"]

    video_stats = {}

    if statistics:
        video_stats = statistics

    title = normalize_text(
        snippet["title"]
    )

    if "official music video" in title:
        content_type = "OFFICIAL_MUSIC_VIDEO"
    elif "official audio" in title:
        content_type = "OFFICIAL_AUDIO"
    elif "music video" in title:
        content_type = "MUSIC_VIDEO"
    else:
        content_type = "OFFICIAL_UPLOAD"

    return {
        "song_id": row["song_id"],
        "album_id": row["album_id"],
        "song_name": row["song_name"],
        "album_name": row["album_name"],
        "youtube_video_id": video_id,
        "youtube_title": snippet["title"],
        "youtube_channel_id": snippet["channelId"],
        "youtube_channel_title": snippet["channelTitle"],
        "published_at": snippet["publishedAt"],
        "youtube_content_type": content_type,
        "view_count": video_stats.get("viewCount"),
        "like_count": video_stats.get("likeCount"),
        "comment_count": video_stats.get("commentCount"),
        "match_status": "MATCHED",
        "ingested_at": ingested_at,
    }


def ingest_catalog(
    catalog_path: str,
) -> tuple[
    pd.DataFrame,
    list[dict[str, Any]],
]:

    catalog = pd.read_csv(
        catalog_path
    )

    processed_records = []
    raw_records = []

    # --------------------------------------------------
    # Step 1: Search official A7X channel
    # --------------------------------------------------

    for index, row in catalog.iterrows():

        print(
            f"[{index + 1}/{len(catalog)}] "
            f"{row['album_name']} - "
            f"{row['song_name']}"
        )

        ingested_at = datetime.now(
            timezone.utc
        ).isoformat()

        search_response = search_videos(
            song_name=row["song_name"]
        )

        selected_video = select_official_video(
            search_response=search_response,
            song_name=row["song_name"],
        )

        # --------------------------------------------------
        # Raw search response
        # --------------------------------------------------

        raw_records.append(
            {
                "ingested_at": ingested_at,
                "song_id": row["song_id"],
                "album_id": row["album_id"],
                "song_name": row["song_name"],
                "album_name": row["album_name"],
                "search_response": search_response,
            }
        )

        # --------------------------------------------------
        # Temporarily store selected video
        # Statistics will be fetched in batch later.
        # --------------------------------------------------

        if selected_video is None:

            processed_records.append(
                transform_youtube_result(
                    row=row,
                    video=None,
                    statistics=None,
                    ingested_at=ingested_at,
                )
            )

        else:

            processed_records.append(
                {
                    "_row": row,
                    "_video": selected_video,
                    "_ingested_at": ingested_at,
                }
            )

    # --------------------------------------------------
    # Step 2: Batch video statistics
    # --------------------------------------------------

    selected_video_ids = [
        record["_video"]["id"]["videoId"]
        for record in processed_records
        if "_video" in record
    ]

    statistics_response = get_video_statistics(
        video_ids=selected_video_ids
    )

    statistics_by_id = {
        item["id"]: item.get("statistics", {})
        for item in statistics_response.get(
            "items",
            []
        )
    }

    # --------------------------------------------------
    # Step 3: Build final processed records
    # --------------------------------------------------

    final_records = []

    for record in processed_records:

        if "_video" not in record:
            final_records.append(record)
            continue

        row = record["_row"]
        video = record["_video"]
        ingested_at = record["_ingested_at"]

        video_id = video["id"]["videoId"]

        statistics = statistics_by_id.get(
            video_id,
            {}
        )

        final_records.append(
            transform_youtube_result(
                row=row,
                video=video,
                statistics=statistics,
                ingested_at=ingested_at,
            )
        )

    return (
        pd.DataFrame(final_records),
        raw_records,
    )

def match_catalog_to_uploads(
    catalog_path: str,
    uploads: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    import pandas as pd
    from datetime import datetime, timezone

    catalog = pd.read_csv(catalog_path)

    results = []

    for _, row in catalog.iterrows():

        song_name = row["song_name"]

        candidates = []

        for video in uploads:

            snippet = video["snippet"]

            title = snippet["title"]

            if not title_matches_song(
                title,
                song_name,
            ):
                continue

            normalized_title = normalize_text(title)

            # Ignore videos that are unlikely to be
            # the actual song upload.
            excluded_words = [
                "teaser",
                "breakdown",
                "interview",
                "behind the scenes",
                "behind the scene",
                "tour",
                "extras",
                "in the studio",
                "trax podcast",
            ]

            if any(
                word in normalized_title
                for word in excluded_words
            ):
                continue

            candidates.append(video)

        selected_video = None

        if candidates:

            def video_priority(video):

                title = normalize_text(
                    video["snippet"]["title"]
                )

                if "official music video" in title:
                    return 1

                if "official video" in title:
                    return 2

                if "official audio" in title:
                    return 3

                if "music video" in title:
                    return 4

                return 5

            candidates.sort(
                key=video_priority
            )

            selected_video = candidates[0]

        ingested_at = datetime.now(
            timezone.utc
        ).isoformat()

        if selected_video:

            snippet = selected_video["snippet"]

            results.append(
                {
                    "song_id": row["song_id"],
                    "album_id": row["album_id"],
                    "song_name": song_name,
                    "album_name": row["album_name"],
                    "youtube_video_id": (
                        selected_video["contentDetails"]["videoId"]
                        if "contentDetails" in selected_video
                        else selected_video["id"]
                    ),
                    "youtube_title": snippet["title"],
                    "youtube_channel_id": (
                        snippet["channelId"]
                    ),
                    "youtube_channel_title": (
                        snippet["channelTitle"]
                    ),
                    "published_at": (
                        snippet["publishedAt"]
                    ),
                    "youtube_content_type": classify_youtube_content(
                        snippet["title"]
                    ),
                    "match_status": "MATCHED",
                    "ingested_at": ingested_at,
                }
            )

        else:

            results.append(
                {
                    "song_id": row["song_id"],
                    "album_id": row["album_id"],
                    "song_name": song_name,
                    "album_name": row["album_name"],
                    "youtube_video_id": None,
                    "youtube_title": None,
                    "youtube_channel_id": None,
                    "youtube_channel_title": None,
                    "published_at": None,
                    "youtube_content_type": None,
                    "match_status": "NOT_FOUND",
                    "ingested_at": ingested_at,
                }
            )

    return results


def get_all_a7x_uploads() -> list[dict[str, Any]]:
    artist_videos = get_channel_uploads(
        channel_id=YOUTUBE_ARTIST_CHANNEL_ID,
        channel_type="ARTIST_CHANNEL",
    )

    topic_videos = get_channel_uploads(
        channel_id=YOUTUBE_TOPIC_CHANNEL_ID,
        channel_type="TOPIC_CHANNEL",
    )

    videos = artist_videos + topic_videos

    unique_videos = {}

    for video in videos:
        video_id = video["contentDetails"]["videoId"]
        unique_videos[video_id] = video

    return list(unique_videos.values())

def classify_youtube_content(title: str) -> str:
    normalized_title = normalize_text(title)

    if "official music video" in normalized_title:
        return "OFFICIAL_MUSIC_VIDEO"

    if "official lyrics video" in normalized_title:
        return "OFFICIAL_LYRICS_VIDEO"

    if "official audio" in normalized_title:
        return "OFFICIAL_AUDIO"

    if "lyric video" in normalized_title:
        return "LYRICS_VIDEO"

    if "music video" in normalized_title:
        return "MUSIC_VIDEO"

    return "OTHER"

def build_youtube_processed_data(
    matches: list[dict[str, Any]],
    stats: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    stats_by_video_id = {
        item["id"]: item
        for item in stats
    }

    processed = []

    for row in matches:

        video_id = row["youtube_video_id"]
        video_stats = stats_by_video_id.get(video_id)

        record = row.copy()

        if video_stats:
            statistics = video_stats.get("statistics", {})

            record["view_count"] = int(
                statistics.get("viewCount", 0)
            )

            record["like_count"] = int(
                statistics.get("likeCount", 0)
            )

            record["comment_count"] = int(
                statistics.get("commentCount", 0)
            )

        else:
            record["view_count"] = None
            record["like_count"] = None
            record["comment_count"] = None

        processed.append(record)

    return processed

def build_youtube_raw_snapshot(
    uploads: list[dict[str, Any]],
    stats: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "uploads": uploads,
        "statistics": stats,
    }