"""
Logging utilities for the chatbot backend.
"""

import logging
import os

# Define the path for the log file (app.log in the same directory as this script)
LOG_FILE = os.path.join(os.path.dirname(__file__), "app.log")

# Configure the logging system:
# - Set the logging level to INFO
# - Define the log message format
# - Log messages will be written both to a file and to the console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    return logging.getLogger(name)