""" 
data_processor_service_helpers.py
--------------------------
This module contains helper functions for the DataProcessorService class.
"""

import pandas as pd
import numpy as np
from app.config.file_paths_config import PATHS
from app.config.features_config import SEARCH_RADIUS_KM
from app.utility.functions.logging import get_logger

logger = get_logger(__name__)


def upload_coordinate_csvs():
    
    """
    Upload CSV files containing coordinates for institutions.
    """
    # Load public and private institution coordinates from CSV files
    region_coords_df = pd.read_csv(PATHS["france_regions"])
    department_coords_df = pd.read_csv(PATHS["france_departments"])
    commune_coords_df = pd.read_csv(PATHS["france_communes"])

    # Rename columns for consistency
    commune_coords_df = commune_coords_df.rename(columns={
        "latitude_centre": "LATITUDE_DECIMAL",
        "longitude_centre": "LONGITUDE_DECIMAL",
    })

    return commune_coords_df, department_coords_df, region_coords_df


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth (in km).
    """
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


def add_distance_column(df, loc_lat, loc_lon):
        df = df.copy()
        df["distance_km"] = df.apply(
            lambda row: haversine(
                row["ETABLISSEMENT_LATITUDE"], row["ETABLISSEMENT_LONGITUDE"], loc_lat, loc_lon
            ),
            axis=1
        )
        return df


def process_other_query_with_coordinates_fallback(ranking_df, specialty: str, location_final: str, location_level_final: str, institution_type: str, number_institutions: int):
    """
    Fallback processing for other queries using coordinates.
    """
    # Filter by specialty
    logger.debug("Filtering ranking_df by specialty")
    ranking_df = ranking_df[ranking_df["CLASSEMENT_TYPE_NORM"] == specialty]
    logger.debug(f"ranking_df after specialty filter: {ranking_df}")

    # Filter by Institution type
    logger.debug("Filtering ranking_df by institution type")
    if institution_type in ["Public", "Privé"]:
        ranking_df = ranking_df[ranking_df["ETABLISSEMENT_TYPE"] == institution_type]
        ranking_df_public = ranking_df if institution_type == "Public" else None
        ranking_df_private = ranking_df if institution_type == "Privé" else None
    else:
        ranking_df_public = ranking_df[ranking_df["ETABLISSEMENT_TYPE"] == "Public"]
        ranking_df_private = ranking_df[ranking_df["ETABLISSEMENT_TYPE"] == "Privé"]

    # Load coordinate CSVs
    logger
    commune_coords_df, department_coords_df, region_coords_df = upload_coordinate_csvs()

    # Get coordinates for location_final
    coords_lookup = {
        "postal_code": ("ETABLISSEMENT_CODE_POSTAL", commune_coords_df, "codes_postaux"),
        "city_commune": ("ETABLISSEMENT_VILLE", commune_coords_df, "nom_standard_normalized"),
        "department": ("ETABLISSEMENT_DEPARTEMENT", department_coords_df, "DEPARTEMENT_NORMALIZED"),
        "region": ("ETABLISSEMENT_REGION", region_coords_df, "REGION_NORMALIZED")
    }

    _, coords_df, lookup_col = coords_lookup[location_level_final]
    location_row = coords_df[coords_df[lookup_col] == location_final[0]]
    logger.debug(f"Location row found: {location_row}") 
    
    if location_row.empty:
        # Could not find coordinates for location_final
        logger.warning(f"Could not find coordinates for {location_level_final}: {location_final}")
        return pd.DataFrame(), pd.DataFrame()
    
    # Extract latitude and longitude, with fallback for city_commune
    logger.debug("Extracting latitude and longitude from location_row")
    loc_lat = location_row.iloc[0]["LATITUDE_DECIMAL"]
    loc_lon = location_row.iloc[0]["LONGITUDE_DECIMAL"]
    if location_level_final == "city_commune" and (pd.isna(loc_lat) or pd.isna(loc_lon)):
        logger.warning("LATITUDE_DECIMAL/LONGITUDE_DECIMAL is NaN for city_commune, trying latitude_mairie/longitude_mairie")
        if "latitude_mairie" in location_row.columns and "longitude_mairie" in location_row.columns:
            loc_lat = location_row.iloc[0]["latitude_mairie"]
            loc_lon = location_row.iloc[0]["longitude_mairie"]
            logger.debug(f"Fallback coordinates: lat={{loc_lat}}, lon={{loc_lon}}")
        else:
            logger.error("No mairie coordinates available for city_commune fallback.")
    logger.debug(f"Extracted coordinates: lat={loc_lat}, lon={loc_lon}")

    # Add distance column
    logger.debug("Adding distance column to ranking DataFrames")
    ranking_df_public = add_distance_column(ranking_df_public, loc_lat, loc_lon) if ranking_df_public is not None else pd.DataFrame()
    ranking_df_private = add_distance_column(ranking_df_private, loc_lat, loc_lon) if ranking_df_private is not None else pd.DataFrame()

    # Try each search radius
    for radius in SEARCH_RADIUS_KM:
        # Filter by distance
        logger.debug(f"Filtering institutions within {radius} km")
        public_within = ranking_df_public[ranking_df_public["distance_km"] <= radius] if not ranking_df_public.empty else pd.DataFrame()
        private_within = ranking_df_private[ranking_df_private["distance_km"] <= radius] if not ranking_df_private.empty else pd.DataFrame()
        logger.debug(f"Found {len(public_within)} public and {len(private_within)} private institutions within {radius} km")  

        # Sort by score descending
        logger.debug("Sorting institutions by score")
        public_sorted = public_within.sort_values(by="CLASSEMENT_NOTE", ascending=False) if not public_within.empty and "CLASSEMENT_NOTE" in public_within.columns else pd.DataFrame()
        private_sorted = private_within.sort_values(by="CLASSEMENT_NOTE", ascending=False) if not private_within.empty and "CLASSEMENT_NOTE" in private_within.columns else pd.DataFrame()

        # Select top N
        logger.debug(f"Selecting top {number_institutions} institutions")
        logger.debug(f"Public institutions found: {len(public_sorted)}, Private institutions found: {len(private_sorted)}")
        if len(public_sorted) >= number_institutions and len(private_sorted) >= number_institutions:
            ranking_df_public_final = public_sorted.head(number_institutions)
            ranking_df_private_final = private_sorted.head(number_institutions)
            return ranking_df_public_final, ranking_df_private_final
        
    # If no radius yielded enough results, return whatever is available
    logger.debug("No radius yielded enough results; returning available institutions")
    ranking_df_public_final = public_sorted.head(number_institutions) if not public_sorted.empty else pd.DataFrame()
    ranking_df_private_final = private_sorted.head(number_institutions) if not private_sorted.empty else pd.DataFrame()
    return ranking_df_public_final, ranking_df_private_final