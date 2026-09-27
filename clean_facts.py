from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

from company_facts import get_us_gaap_facts
from utils.file_utils import export_parquet

load_dotenv()
AWS_ACESSS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET")

HADOOP_VERSION = "3.5.0"
spark = SparkSession.builder \
    .appName("Clean Facts") \
    .config("spark.jars.packages", f"org.apache.hadoop:hadoop-aws:{HADOOP_VERSION},com.amazonaws:aws-java-sdk-bundle:1.12.262") \
    .config("spark.hadoop.fs.s3a.access.key", AWS_ACESSS_KEY)\
    .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET_KEY)\
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

spark.sparkContext.setLogLevel("OFF")

cik = "0000881695"
df = spark.createDataFrame(get_us_gaap_facts(cik=cik))

export_parquet(
    df,
    bucket="secedgar-nikhil",
    prefix="raw/company_us_gaap_facts",
    basename_template=f"{cik}_us_gaap_facts.parquet",
)
