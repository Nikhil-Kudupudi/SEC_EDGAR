from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Clean Facts") \
    .config("fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
df = spark.read.parquet("s3a://secedgar-nikhil/raw/company_us_gaap_facts/*.parquet")

print(df.show())