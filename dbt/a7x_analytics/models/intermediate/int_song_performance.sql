{{ config(
    materialized='view'
) }}

with spotify_ranked as (

    select
        song_id,
        album_id,
        song_name,
        album_name,
        spotify_track_id,
        spotify_album_id,
        duration_ms,
        explicit,
        track_number,
        match_status as spotify_match_status,
        ingestion_date as spotify_ingestion_date,

        row_number() over (
            partition by song_id
            order by ingestion_date desc
        ) as rn

    from {{ ref('stg_spotify_tracks') }}

),

spotify as (

    select
        song_id,
        album_id,
        song_name,
        album_name,
        spotify_track_id,
        spotify_album_id,
        duration_ms,
        explicit,
        track_number,
        spotify_match_status,
        spotify_ingestion_date
    from spotify_ranked
    where rn = 1

),

youtube_ranked as (

    select
        song_id,
        youtube_video_id,
        youtube_title,
        youtube_channel_id,
        youtube_channel_title,
        published_at,
        youtube_content_type,
        match_status as youtube_match_status,
        view_count,
        like_count,
        comment_count,
        ingestion_date as youtube_ingestion_date,

        row_number() over (
            partition by song_id
            order by ingestion_date desc
        ) as rn

    from {{ ref('stg_youtube_videos') }}

),

youtube as (

    select
        song_id,
        youtube_video_id,
        youtube_title,
        youtube_channel_id,
        youtube_channel_title,
        published_at,
        youtube_content_type,
        youtube_match_status,
        view_count,
        like_count,
        comment_count,
        youtube_ingestion_date
    from youtube_ranked
    where rn = 1

)

select
    s.song_id,
    s.album_id,
    s.song_name,
    s.album_name,
    s.spotify_track_id,
    s.spotify_album_id,
    s.duration_ms,
    s.explicit,
    s.track_number,
    s.spotify_match_status,
    s.spotify_ingestion_date,
    y.youtube_video_id,
    y.youtube_title,
    y.youtube_channel_id,
    y.youtube_channel_title,
    y.published_at,
    y.youtube_content_type,
    y.youtube_match_status,
    y.view_count,
    y.like_count,
    y.comment_count,
    coalesce(y.like_count, 0) + coalesce(y.comment_count, 0)
        as engagement_count,
    case
        when coalesce(y.view_count, 0) > 0 then
            (
                coalesce(y.like_count, 0)
                + coalesce(y.comment_count, 0)
            ) * 1.0 / y.view_count
        else 0
    end as engagement_rate,
    y.youtube_ingestion_date

from spotify s

left join youtube y
    on s.song_id = y.song_id