import logging 



logger = logging.getLogger(__name__)
FORMAT = "%(asctime)s -%(name)s - %(levelname)s - %(message)s"

logging.basicConfig(level=logging.INFO, format=FORMAT)