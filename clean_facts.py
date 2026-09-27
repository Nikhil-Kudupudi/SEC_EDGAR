from pyspark.sql import SparkSession

HADOOP_VERSION = "3.5.0"
spark = SparkSession.builder \
    .appName("Clean Facts") \
    .config("spark.jars.packages", f"org.apache.hadoop:hadoop-aws:{HADOOP_VERSION},com.amazonaws:aws-java-sdk-bundle:1.12.262") \
    .config("spark.hadoop.fs.s3a.access.key", "")\
    .config("spark.hadoop.fs.s3a.secret.key", "")\
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
df = spark.read.parquet("s3a://secedgar-nikhil/raw/company_us_gaap_facts/*.parquet")

print(df.show())