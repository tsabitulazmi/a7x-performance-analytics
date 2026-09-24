{{ config(
    materialized='table'
) }}

select
    f.song_id,
    d.album_id,
    d.song_name,
    d.album_name,

    f.spotify_track_id,
    f.youtube_video_id,
    f.youtube_content_type,

    f.view_count,
    f.like_count,
    f.comment_count,
    f.engagement_count,
    f.engagement_rate,

    f.spotify_match_status,
    f.youtube_match_status,

    f.spotify_ingestion_date,
    f.youtube_ingestion_date

from {{ ref('fact_music_performance') }} f

left join {{ ref('dim_song') }} d
    on f.song_id = d.song_id