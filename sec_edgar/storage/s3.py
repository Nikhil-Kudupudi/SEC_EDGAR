import boto3


def get_s3_client():
    return boto3.client("s3")


def list_keys(bucket_name: str, prefix: str):
    """Yield every object key under the prefix."""
    paginator = get_s3_client().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj["Key"]


def get_file(bucket_name: str, key: str) -> str:
    return get_s3_client().get_object(Bucket=bucket_name, Key=key)["Body"].read().decode("utf-8")


def delete_keys(bucket_name: str, keys: list[str]) -> None:
    """Delete objects (S3 allows 1000 per request)."""
    client = get_s3_client()
    for i in range(0, len(keys), 1000):
        client.delete_objects(Bucket=bucket_name,
                              Delete={"Objects": [{"Key": k} for k in keys[i:i + 1000]]})


def delete_prefix(bucket_name: str, prefix: str) -> None:
    delete_keys(bucket_name, list(list_keys(bucket_name, prefix)))


def delete_files_starting_with(bucket_name: str, prefix: str, file_prefix: str) -> int:
    """Delete files anywhere under `prefix` whose file NAME starts with `file_prefix`
    (e.g. every file of one company, across all fy=/form= partitions)."""
    keys = [k for k in list_keys(bucket_name, prefix) if k.rsplit("/", 1)[-1].startswith(file_prefix)]
    delete_keys(bucket_name, keys)
    return len(keys)
