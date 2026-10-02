import polars as pl
import pyarrow.parquet as pq

from sec_edgar.storage.s3 import delete_files_starting_with
from sec_edgar.utils.logger import logger


def export_parquet(df: pl.DataFrame, bucket: str, prefix: str, file_prefix: str,
                   partition_cols: list[str] | None = None) -> None:
    """Replace one owner's data (e.g. one company) in S3 with `df`: delete, then write.

    Files are named `{file_prefix}_<n>.parquet`. Before writing, every existing file
    starting with `file_prefix` under `prefix` is deleted (in all partitions), so old
    files with another schema or stale partitions never mix with the new ones.
    Other owners' files in the same partitions are untouched.
    """
    if not isinstance(df, pl.DataFrame):
        raise TypeError("export_parquet takes a polars DataFrame")
    if df.is_empty():
        raise ValueError("The DataFrame is empty. Cannot write to Parquet.")

    prefix = prefix.strip("/")
    deleted = delete_files_starting_with(bucket, prefix, file_prefix)
    logger.info(f"Deleted {deleted} old files for {file_prefix} under {prefix}")

    pq.write_to_dataset(
        df.to_arrow(),
        root_path=f"s3://{bucket}/{prefix}",
        partition_cols=partition_cols,
        basename_template=f"{file_prefix}_{{i}}.parquet",
        compression="snappy",
    )
    logger.info(f"Wrote {len(df)} rows to s3://{bucket}/{prefix}")
