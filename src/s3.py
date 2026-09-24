import json

import boto3

from src.config import AWS_REGION, S3_BUCKET


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
    )


def upload_json(
    data,
    key: str,
):
    s3 = get_s3_client()

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(
            data,
            indent=2,
        ),
        ContentType="application/json",
    )

    print(
        f"Uploaded: s3://{S3_BUCKET}/{key}"
    )


def upload_file(
    local_path: str,
    key: str,
    content_type: str | None = None,
):
    s3 = get_s3_client()

    extra_args = {}

    if content_type:
        extra_args["ContentType"] = content_type

    s3.upload_file(
        local_path,
        S3_BUCKET,
        key,
        ExtraArgs=extra_args,
    )

    print(
        f"Uploaded: s3://{S3_BUCKET}/{key}"
    )