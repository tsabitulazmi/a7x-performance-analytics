{{ config(
    materialized='table'
) }}

select distinct
    album_id,
    album_name

from {{ ref('int_song_performance') }}
