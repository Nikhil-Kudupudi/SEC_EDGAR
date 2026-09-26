import requests 

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

    company_facts = requests.get(url, headers=headers)

    # with open(f"CIK{cik}.json", "w") as f:
    #     f.write(company_facts.text)
    return company_facts.json()

if __name__ == "__main__":
    facts = retrieve_company_facts(cik= "0001045810")
    print(facts["facts"].keys())