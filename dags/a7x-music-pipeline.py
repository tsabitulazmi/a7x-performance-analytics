from datetime import datetime
import time

import boto3

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


PROJECT_DIR = "/opt/airflow/a7x_performance_analytics"

AWS_REGION = "ap-southeast-1"
GLUE_CRAWLER_NAME = "a7x-processed-crawler"


def start_glue_crawler():
    glue = boto3.client(
        "glue",
        region_name=AWS_REGION,
    )

    crawler = glue.get_crawler(
        Name=GLUE_CRAWLER_NAME
    )["Crawler"]

    state = crawler["State"]

    if state == "READY":
        glue.start_crawler(
            Name=GLUE_CRAWLER_NAME
        )
        print(f"Started Glue crawler: {GLUE_CRAWLER_NAME}")

    elif state == "RUNNING":
        print(f"Glue crawler already running: {GLUE_CRAWLER_NAME}")

    else:
        raise RuntimeError(
            f"Glue crawler is in unexpected state: {state}"
        )


def wait_for_glue_crawler():
    glue = boto3.client(
        "glue",
        region_name=AWS_REGION,
    )

    while True:
        crawler = glue.get_crawler(
            Name=GLUE_CRAWLER_NAME
        )["Crawler"]

        state = crawler["State"]

        print(f"Glue crawler state: {state}")

        if state == "READY":
            print("Glue crawler finished successfully.")
            break

        time.sleep(10)


with DAG(
    dag_id="a7x_music_pipeline",
    description="A7X music performance analytics pipeline",
    start_date=datetime(2026, 9, 22),
    schedule=None,
    catchup=False,
    tags=["a7x", "music", "data-engineering"],
) as dag:

    ingest_spotify = BashOperator(
        task_id="ingest_spotify",
        bash_command=(
            f"cd '{PROJECT_DIR}' && "
            "python -m src.run_spotify_ingestion"
        ),
    )

    ingest_youtube = BashOperator(
        task_id="ingest_youtube",
        bash_command=(
            f"cd '{PROJECT_DIR}' && "
            "python -m src.run_youtube_ingestion"
        ),
    )

    start_glue_crawler = PythonOperator(
        task_id="start_glue_crawler",
        python_callable=start_glue_crawler,
    )

    wait_for_glue_crawler = PythonOperator(
        task_id="wait_for_glue_crawler",
        python_callable=wait_for_glue_crawler,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"cd '{PROJECT_DIR}/dbt/a7x_analytics' && "
            "dbt run"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd '{PROJECT_DIR}/dbt/a7x_analytics' && "
            "dbt test"
        ),
    )

    [
        ingest_spotify,
        ingest_youtube,
    ] >> start_glue_crawler

    start_glue_crawler >> wait_for_glue_crawler

    wait_for_glue_crawler >> dbt_run

    dbt_run >> dbt_test