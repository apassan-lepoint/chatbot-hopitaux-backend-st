import pandas as pd
from app.utils.config import PATHS
from app.utils.logging import get_logger
logger = get_logger(__name__)


# Attempt to read the hospital coordinates from the Excel file
try:
    institution_coordinates_df = pd.read_excel(PATHS["hospital_coordinates_path"])
except Exception as e:
    logger.error(f"Failed to load hospital coordinates Excel: {e}")
    raise


def get_institution_list(institution_coordinates_df):
    """
    Returns a formatted, deduplicated list of institutions present in the rankings.
    Cleans names to avoid duplicates or matching errors.
    """
    
    column_1 = institution_coordinates_df.iloc[:, 0]
    institution_list = [element.split(",")[0] for element in column_1] # Remove location details after commas for better matching
    institution_list = list(set(institution_list))
    institution_list = [element for element in institution_list if element not in ("CHU", "CH")] # Remove generic names that could cause false matches
    institution_list = ", ".join(map(str, institution_list))
    logger.debug(f"Institution list: {institution_list}")
    return institution_list

institution_list = get_institution_list(institution_coordinates_df)