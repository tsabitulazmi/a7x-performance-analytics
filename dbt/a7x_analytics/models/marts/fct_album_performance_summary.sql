{{ config(
    materialized='table'
) }}

select
    album_id,
    album_name,

    count(distinct song_id) as song_count,

    sum(view_count) as total_views,
    sum(like_count) as total_likes,
    sum(comment_count) as total_comments,
    sum(engagement_count) as total_engagement,

    case
        when sum(view_count) > 0 then
            (
                sum(like_count)
                + sum(comment_count)
            ) * 1.0 / sum(view_count)
        else 0
    end as engagement_rate,

    avg(view_count) as avg_views_per_song,
    avg(engagement_rate) as avg_song_engagement_rate

from {{ ref('fct_song_performance_summary') }}

group by
    album_id,
    album_name