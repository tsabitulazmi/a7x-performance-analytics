WITH performance AS (

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
        engagement_count,
        engagement_rate,

        LAG(view_count) OVER (
            PARTITION BY song_id
            ORDER BY ingestion_date
        ) AS previous_view_count,

        LAG(like_count) OVER (
            PARTITION BY song_id
            ORDER BY ingestion_date
        ) AS previous_like_count,

        LAG(comment_count) OVER (
            PARTITION BY song_id
            ORDER BY ingestion_date
        ) AS previous_comment_count,

        LAG(ingestion_date) OVER (
            PARTITION BY song_id
            ORDER BY ingestion_date
        ) AS previous_ingestion_date

    FROM {{ ref('fct_music_performance_history') }}

),

growth AS (

    SELECT
        *,
        
        date_diff(
            'day',
            CAST(previous_ingestion_date AS DATE),
            CAST(ingestion_date AS DATE)
        ) AS days_since_previous_snapshot,

        view_count - previous_view_count AS view_growth,

        like_count - previous_like_count AS like_growth,

        comment_count - previous_comment_count AS comment_growth

    FROM performance

)

SELECT
    *,
    
    CASE
        WHEN previous_view_count > 0
        THEN view_growth * 1.0 / previous_view_count
        ELSE NULL
    END AS view_growth_pct,

    CASE
        WHEN days_since_previous_snapshot > 0
        THEN view_growth * 1.0 / days_since_previous_snapshot
        ELSE NULL
    END AS avg_daily_view_growth

FROM growth