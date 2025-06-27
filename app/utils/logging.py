"""
Logging utilities for the chatbot backend.

This file configures and provides logging functions for tracking events,
    errors, and usage throughout the application.
    
NOT YET DEVELOPED
"""

import logging
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    return logging.getLogger(name)