import boto3
import pandas as pd
from pyathena import connect


AWS_REGION = "ap-southeast-1"
ATHENA_DATABASE = "a7x_analytics"
ATHENA_S3_OUTPUT = "s3://tsabitul-a7x-music-analytic/athena-results/"


def get_connection():
    return connect(
        region_name=AWS_REGION,
        schema_name=ATHENA_DATABASE,
        s3_staging_dir=ATHENA_S3_OUTPUT,
    )


def run_query(query: str) -> pd.DataFrame:
    conn = get_connection()

    try:
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def get_overview():
    query = """
    SELECT
        COUNT(DISTINCT song_id) AS total_songs,
        COUNT(DISTINCT album_id) AS total_albums,
        SUM(view_count) AS total_views,
        SUM(like_count) AS total_likes,
        SUM(comment_count) AS total_comments,
        SUM(engagement_count) AS total_engagement
    FROM fct_song_performance_summary
    """

    return run_query(query)


def get_album_performance():
    query = """
    SELECT
        album_id,
        album_name,
        song_count,
        total_views,
        total_likes,
        total_comments,
        total_engagement,
        engagement_rate,
        avg_views_per_song,
        avg_song_engagement_rate
    FROM fct_album_performance_summary
    ORDER BY total_views DESC
    """

    return run_query(query)


def get_song_performance():
    query = """
    SELECT
        song_id,
        album_id,
        song_name,
        album_name,
        spotify_track_id,
        youtube_video_id,
        youtube_content_type,
        view_count,
        like_count,
        comment_count,
        engagement_count,
        engagement_rate,
        spotify_match_status,
        youtube_match_status,
        spotify_ingestion_date,
        youtube_ingestion_date
    FROM fct_song_performance_summary
    """

    return run_query(query)


def get_content_type_distribution():
    query = """
    SELECT
        youtube_content_type,
        COUNT(*) AS song_count,
        SUM(view_count) AS total_views
    FROM fct_song_performance_summary
    GROUP BY youtube_content_type
    ORDER BY total_views DESC
    """

    return run_query(query)


def get_data_quality():
    query = """
    SELECT
        COUNT(*) AS total_songs,

        SUM(
            CASE
                WHEN spotify_match_status = 'MATCHED'
                THEN 1
                ELSE 0
            END
        ) AS spotify_matched,

        SUM(
            CASE
                WHEN youtube_match_status = 'MATCHED'
                THEN 1
                ELSE 0
            END
        ) AS youtube_matched,

        MAX(spotify_ingestion_date) AS latest_spotify_ingestion,
        MAX(youtube_ingestion_date) AS latest_youtube_ingestion

    FROM fct_song_performance_summary
    """

    return run_query(query)

def get_song_growth():
    query = """
        SELECT
            song_id,
            album_id,
            song_name,
            album_name,
            ingestion_date,
            view_count,
            previous_view_count,
            view_growth,
            view_growth_pct,
            days_since_previous_snapshot,
            avg_daily_view_growth
        FROM fct_song_growth
        ORDER BY ingestion_date, view_growth DESC
    """

    return run_query(query)

def get_growth_trend():
    query = """
        SELECT
            ingestion_date,
            SUM(view_count) AS total_views
        FROM fct_music_performance_history
        GROUP BY ingestion_date
        ORDER BY ingestion_date
    """

    return run_query(query)

def get_latest_growth():
    query = """
        SELECT
            song_id,
            song_name,
            album_name,
            ingestion_date,
            view_growth,
            view_growth_pct,
            days_since_previous_snapshot,
            avg_daily_view_growth
        FROM fct_song_growth
        WHERE ingestion_date = (
            SELECT MAX(ingestion_date)
            FROM fct_song_growth
        )
        AND previous_view_count IS NOT NULL
        ORDER BY avg_daily_view_growth DESC
    """

    return run_query(query)