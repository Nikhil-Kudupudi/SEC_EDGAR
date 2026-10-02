"""All settings in one place. Values come from environment variables (.env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bucket: str = os.getenv("S3_BUCKET", "secedgar-nikhil")
    # SEC requires a User-Agent that identifies you: "Name email"
    sec_user_agent: str = os.getenv("SEC_USER_AGENT", "nikhilkudupudi@gmail.com")
    # boto3 standard names first, fall back to the names used so far in .env
    aws_access_key: str | None = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY")
    aws_secret_key: str | None = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET")

    # S3 layout: raw (untouched JSON) -> bronze (flattened) -> silver (cleaned) -> gold (metrics)
    raw_prefix: str = "raw"
    bronze_prefix: str = "bronze"
    silver_prefix: str = "silver"
    gold_prefix: str = "gold"

    # Spark
    hadoop_version: str = "3.5.0"  # must match the hadoop jars bundled with pyspark
    aws_sdk_package: str = "com.amazonaws:aws-java-sdk-bundle:1.12.262"

    def s3a(self, prefix: str) -> str:
        """Path Spark uses to read/write a prefix in the bucket."""
        return f"s3a://{self.bucket}/{prefix}"


settings = Settings()
