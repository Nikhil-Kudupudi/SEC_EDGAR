"""The one place a SparkSession is built. Jobs call get_spark()."""
from pyspark.sql import SparkSession

from sec_edgar.config import settings


def get_spark(app_name: str = "sec_edgar") -> SparkSession:
    packages = f"org.apache.hadoop:hadoop-aws:{settings.hadoop_version},{settings.aws_sdk_package}"
    spark = (
        SparkSession.builder.appName(app_name)
        .config("spark.jars.packages", packages)
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.access.key", settings.aws_access_key)
        .config("spark.hadoop.fs.s3a.secret.key", settings.aws_secret_key)
        # overwrite only the partitions present in the DataFrame, not the whole table
        .config("spark.sql.sources.partitionOverwriteMode", "dynamic")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    return spark
