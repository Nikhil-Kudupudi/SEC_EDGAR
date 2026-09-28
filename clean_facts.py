from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv
import pyspark.sql.functions as sf
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
df = spark.read.parquet("s3a://secedgar-nikhil/raw/company_us_gaap_facts/*.parquet")

#convert end, start to date format from string 
df = df.withColumns({
    "end": sf.to_date('end'),
    "start": sf.to_date("start")
})

print(df.filter((df.unit_type == "USD/shares") | (df.unit_type == "USD/shares_unit")).show(5))

reqd_tags=reqd_tags = [
    "Revenues",
    "NetIncomeLoss",
    "Assets",
    "Liabilities",
    "StockholdersEquity",
    "CashAndCashEquivalentsAtCarryingValue"
]
fin_df = df.filter(df.fact_name.isin(reqd_tags))

fin_df_insigihts = fin_df.groupBy("fact_name", "form").agg(
    sf.sum("val").alias("total_val")
)
print(fin_df_insigihts.show())
print(fin_df.filter(fin_df.fact_name == "Assets").filter(fin_df.form == "10-K") \
    .select("end", "accn", "val", "fy", "form") \
    .distinct().orderBy("end").show(50, truncate=False))