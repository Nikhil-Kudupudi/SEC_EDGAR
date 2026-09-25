import polars as  pl

df = pl.read_ndjson("s3://secedgar-nikhil/raw/companyfacts/CIK0000001750.json")

print(df)


#  fsspec s3fs adlfs gcsfs