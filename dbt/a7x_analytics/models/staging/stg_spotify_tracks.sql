{{ config(
    materialized='view'
) }}

select
    cast(song_id as varchar) as song_id,
    cast(album_id as varchar) as album_id,
    cast(song_name as varchar) as song_name,
    cast(album_name as varchar) as album_name,
    cast(spotify_track_id as varchar) as spotify_track_id,
    cast(spotify_album_id as varchar) as spotify_album_id,
    cast(spotify_track_uri as varchar) as spotify_track_uri,
    cast(spotify_url as varchar) as spotify_url,
    cast(spotify_track_name as varchar) as spotify_track_name,
    cast(spotify_album_name as varchar) as spotify_album_name,
    cast(duration_ms as bigint) as duration_ms,
    cast(explicit as boolean) as explicit,
    cast(track_number as bigint) as track_number,
    cast(match_status as varchar) as match_status,
    cast(ingested_at as varchar) as ingested_at,
    cast(partition_0 as varchar) as ingestion_date
from {{ source('a7x_music_analytics', 'spotify') }}
