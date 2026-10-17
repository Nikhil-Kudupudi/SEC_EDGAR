"""python -m jobs.run_gold"""
from sec_edgar.pipeline.gold import build_gold
from sec_edgar.spark import get_spark

if __name__ == "__main__":
    build_gold(get_spark("gold"))
