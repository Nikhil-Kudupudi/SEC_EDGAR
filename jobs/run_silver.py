"""python -m jobs.run_silver"""
from sec_edgar.pipeline.silver import build_silver
from sec_edgar.spark import get_spark

if __name__ == "__main__":
    build_silver(get_spark("silver"))
