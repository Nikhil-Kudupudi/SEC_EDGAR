from datetime import date

import requests
from retrieve_company_tickers import get_company_tickers
from utils.logger import logger
from utils.file_utils import export_parquet
import polars as pl

def retrieve_company_facts(cik: str):
    """
    Retrieves company facts from the SEC EDGAR API for a given CIK.

    Args:
        cik (str): The Central Index Key (CIK) of the company.
    """
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {
        "User-Agent": "nikhilkudupudi@gmail.com"
    }

    logger.info(f"Requesting company facts for CIK {cik} from {url}")
    company_facts = requests.get(url, headers=headers)
    logger.info(f"Received response for CIK {cik} with status code {company_facts.status_code}")
    company_facts.raise_for_status()

    # with open(f"CIK{cik}.json", "w") as f:
    #     f.write(company_facts.text)
    return company_facts.json()


def get_us_gaap_facts(cik: str):
    """
    Retrieves US GAAP facts from the SEC EDGAR API for a given CIK.

    Args:
        cik (str): The Central Index Key (CIK) of the company.
    """
    company_facts = retrieve_company_facts(cik)
    us_gaap_facts = company_facts.get("facts", {}).get("us-gaap", {})
    logger.info(f"Found {len(us_gaap_facts)} us-gaap facts for CIK {cik}")
    fact_data= []
    for fact_name, fact in us_gaap_facts.items():
        fact_dict={"cik": cik, "fact_name": fact_name, "label": fact["label"]}
        for unit_type in fact["units"]:
            for unit in fact["units"][unit_type]:
                fact_data.append({ **fact_dict,"unit_type": unit_type, **unit,
          "val": float(unit["val"]),
         }) 
    
    return fact_data


if __name__ == "__main__":
    # tickers = get_company_tickers()
    # for entry in list(tickers.values())[:10]:
    #     cik = str(entry["cik_str"]).zfill(10)
    #     facts = retrieve_company_facts(cik=cik)
    #     print(entry["ticker"], cik, list(facts["facts"].keys()), list(facts["facts"].get("us-gaap", {}).keys() ))
    get_us_gaap_facts(cik="0000881695")