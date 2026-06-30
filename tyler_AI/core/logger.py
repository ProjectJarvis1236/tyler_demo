import logging 
import os 

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, "jarvis.log")

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers = [logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler()
                ]
)

def get_logger(name: str):
    return logging.getLogger(name)