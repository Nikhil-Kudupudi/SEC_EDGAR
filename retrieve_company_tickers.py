import requests 
import polars as pl
from utils.logger import logger
from utils.file_utils import export_parquet 
def get_company_tickers():
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {
        "User-Agent": "nikhilkudupudi@gmail.com"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to retrieve company tickers. Status code: {response.status_code}")

def tickers_master():
 
    tickers = get_company_tickers()
    rows = []
    for ticker in tickers.values():
        ticker["cik_str"]= str(ticker["cik_str"]).zfill(10)
        rows.append(ticker)
    df = pl.DataFrame(rows)
    logger.info(f"Retrieved {len(df)} company tickers.")
    export_parquet(df, bucket="secedgar-nikhil", prefix="raw", basename_template="company_tickers_master.parquet")
    logger.info("Exported company tickers to S3 as Parquet.")

if __name__ == "__main__":
    # tickers_master()
    df = pl.read_parquet("s3://secedgar-nikhil/raw/company_tickers_master.parquet")
    print(df.head())