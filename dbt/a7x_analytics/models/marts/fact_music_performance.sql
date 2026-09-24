{{ config(
    materialized='table'
) }}

select
    song_id,
    album_id,

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

from {{ ref('int_song_performance') }}
