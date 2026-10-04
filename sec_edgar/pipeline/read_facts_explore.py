from pyspark.sql import functions as F 
from spark import get_spark

spark= get_spark("bronze")
df = spark.read.parquet("s3://secedgar_nikhil/bronze/fy=2011")
df = df.select("").count