import logging

import pyarrow as pa
import pyarrow.parquet as pq
import polars as  pl

from utils.aws_utils import delete_prefix

logger = logging.getLogger(__name__)


def export_parquet(df:pl.DataFrame, bucket:str, prefix:str, basename_template:str, partition_cols: list[str] = None)-> None:
    """
    Writes a polars DataFrame to a parquet file in S3.

    Args:
        df (pl.DataFrame): The polars DataFrame to write.
        bucket (str): The name of the S3 bucket.
        prefix (str): The prefix (path) in the S3 bucket where the file will be stored.
        basename_template (str): The template for the basename of the parquet file to be created.
        partition_cols (list[str], optional): Columns to partition the parquet output by.
    """
    if df is None or df.is_empty():
        raise ValueError("The DataFrame is empty. Cannot write to Parquet.")
    if not isinstance(df, pl.DataFrame):
        raise TypeError("The provided data is not a polars DataFrame.")

    prefix = prefix.lstrip("/")
    s3_root = f"s3://{bucket}/{prefix}"

    try:
        arrow_table = df.to_arrow()

        if partition_cols:
            # clear only the leaf-level partitions this write touches (e.g. state=X/city=Y),
            # leaving sibling city= folders under the same state untouched
            partitions = df.select(partition_cols).unique()
            for row in partitions.iter_rows(named=True):
                partition_path = "/".join(f"{col}={row[col]}" for col in partition_cols)
                delete_prefix(bucket_name=bucket, prefix=f"{prefix}/{partition_path}")

            pq.write_to_dataset(
                arrow_table,
                root_path=s3_root,
                partition_cols=partition_cols,
                compression="snappy",
                row_group_size=100000,
                basename_template=f"{basename_template}",
            )
        else:
            delete_prefix(bucket_name=bucket, prefix=f"{prefix}/{basename_template}")
            pq.write_table(arrow_table, f"{s3_root}/{basename_template}", compression="snappy")
    except Exception:
        logger.exception("Failed to export parquet to %s", s3_root)
        raise
