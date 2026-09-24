{{ config(
    materialized='table'
) }}

select
    song_id,
    album_id,
    song_name,
    album_name,
    track_number,
    duration_ms,
    explicit,
    spotify_track_id,
    spotify_album_id,
    youtube_video_id,
    youtube_title,
    youtube_content_type

from {{ ref('int_song_performance') }}
