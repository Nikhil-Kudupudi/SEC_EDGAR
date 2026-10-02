"""python -m jobs.run_bronze [CIK ...]"""
import sys

from sec_edgar.pipeline.bronze import build_bronze

if __name__ == "__main__":
    build_bronze(sys.argv[1:] or ["0000881695"])  # default: sample company
