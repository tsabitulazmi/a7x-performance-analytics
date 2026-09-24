import os

from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-3")
S3_BUCKET = os.getenv(
    "S3_BUCKET",
    "tsabitul-a7x-music-analytic",
)

S3_CATALOG_KEY = "raw/catalog/a7x_catalog.csv"
S3_SPOTIFY_PREFIX = "raw/spotify/"
S3_YOUTUBE_PREFIX = "raw/youtube/"
S3_PROCESSED_PREFIX = "processed/"