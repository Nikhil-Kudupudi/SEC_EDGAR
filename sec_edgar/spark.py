"""The one place a SparkSession is built. Jobs call get_spark()."""
import os
import sys

from pyspark.sql import SparkSession

from sec_edgar.config import settings


def get_spark(app_name: str = "sec_edgar", s3: bool = True) -> SparkSession:
    """s3=False gives a plain local session (no AWS jars) for local runs and tests."""
    # Python workers must run the same interpreter as the driver (venv), not system Python.
    os.environ["PYSPARK_PYTHON"] = sys.executable
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.session.timeZone", "UTC")
        # overwrite only the partitions present in the DataFrame, not the whole table
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
    )
    if not s3:
        builder = builder.config("spark.sql.shuffle.partitions", "8")  # small local data
    if s3:
        packages = f"org.apache.hadoop:hadoop-aws:{settings.hadoop_version},{settings.aws_sdk_package}"
        builder = (
            builder.config("spark.jars.packages", packages)
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3a.access.key", settings.aws_access_key)
            .config("spark.hadoop.fs.s3a.secret.key", settings.aws_secret_key)
        )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark
