SELECT
    song_id,
    album_id,
    song_name,
    album_name,
    youtube_video_id,
    youtube_content_type,
    ingestion_date,

    view_count,
    like_count,
    comment_count,

    -- Derived engagement metrics
    like_count + comment_count AS engagement_count,

    CASE
        WHEN view_count > 0
        THEN (like_count + comment_count) * 1.0 / view_count
        ELSE NULL
    END AS engagement_rate

FROM {{ ref('stg_youtube_videos') }}