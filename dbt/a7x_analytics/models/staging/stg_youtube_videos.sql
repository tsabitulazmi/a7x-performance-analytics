{{ config(
    materialized='view'
) }}

select
    cast(song_id as varchar) as song_id,
    cast(album_id as varchar) as album_id,
    cast(song_name as varchar) as song_name,
    cast(album_name as varchar) as album_name,
    cast(youtube_video_id as varchar) as youtube_video_id,
    cast(youtube_title as varchar) as youtube_title,
    cast(youtube_channel_id as varchar) as youtube_channel_id,
    cast(youtube_channel_title as varchar) as youtube_channel_title,
    cast(published_at as varchar) as published_at,
    cast(youtube_content_type as varchar) as youtube_content_type,
    cast(match_status as varchar) as match_status,
    cast(ingested_at as varchar) as ingested_at,
    cast(view_count as bigint) as view_count,
    cast(like_count as bigint) as like_count,
    cast(comment_count as bigint) as comment_count,
    cast(partition_0 as varchar) as ingestion_date
from {{ source('a7x_music_analytics', 'youtube') }}
