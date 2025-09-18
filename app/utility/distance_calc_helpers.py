"""
Utility functions for distance calculations and geocoding using geopy.
"""

import certifi
from geopy.distance import geodesic 
from geopy.geocoders import Nominatim  
import logging
import pandas as pd
import ssl
from typing import List, Tuple





def multi_radius_search(public_df: pd.DataFrame, private_df: pd.DataFrame,number_institutions: int,city_not_specified: bool,radii: List[int]) -> Tuple[pd.DataFrame, pd.DataFrame, int]:
    """
    Try increasing radii to get enough institutions. Returns filtered public/private dfs and the used radius.
    If city_not_specified is True, returns original dfs and radius 0.
    """
    if city_not_specified:
        return public_df, private_df, 0
    logger = logging.getLogger("multi_radius_search")
    logger.debug(f"[multi_radius_search] Called with radii: {radii}")
    logger.debug(f"[multi_radius_search] Initial public_df shape: {public_df.shape if public_df is not None else 'None'}")
    logger.debug(f"[multi_radius_search] Initial private_df shape: {private_df.shape if private_df is not None else 'None'}")
    for radius in radii:
        logger.debug(f"[multi_radius_search] Trying radius: {radius}")
        pub = public_df[public_df['Distance'] <= radius] if 'Distance' in public_df.columns else public_df
        priv = private_df[private_df['Distance'] <= radius] if 'Distance' in private_df.columns else private_df
        logger.debug(f"[multi_radius_search] pub_filtered shape: {pub.shape if pub is not None else 'None'}")
        logger.debug(f"[multi_radius_search] priv_filtered shape: {priv.shape if priv is not None else 'None'}")
        logger.debug(f"[multi_radius_search] pub_filtered head: {pub.head(5) if pub is not None else 'None'}")
        logger.debug(f"[multi_radius_search] priv_filtered head: {priv.head(5) if priv is not None else 'None'}")
        # Combine and sort by score, return top N
        combined = pd.concat([pub, priv]).drop_duplicates()
        combined_sorted = combined.sort_values(by='Note / 20', ascending=False)
        top_n = combined_sorted.nlargest(number_institutions, 'Note / 20')
        if len(top_n) >= number_institutions:
            logger.debug(f"[multi_radius_search] Returning top {number_institutions} results at radius {radius}")
            # Split back to public/private for downstream formatting
            top_pub = top_n[top_n['Catégorie'] == 'Public']
            top_priv = top_n[top_n['Catégorie'] == 'Privé']
            return top_pub, top_priv, radius
    # If none of the radii yield enough, return the largest radius result
    if 'Distance' in public_df.columns:
        pub = public_df[public_df['Distance'] <= radii[-1]]
    else:
        pub = public_df
    if 'Distance' in private_df.columns:
        priv = private_df[private_df['Distance'] <= radii[-1]]
    else:
        priv = private_df
    combined = pd.concat([pub, priv]).drop_duplicates()
    combined_sorted = combined.sort_values(by='Note / 20', ascending=False)
    top_n = combined_sorted.nlargest(number_institutions, 'Note / 20')
    logger.debug(f"[multi_radius_search] Not enough results, returning top {number_institutions} at max radius {radii[-1]}")
    top_pub = top_n[top_n['Catégorie'] == 'Public']
    top_priv = top_n[top_n['Catégorie'] == 'Privé']
    return top_pub, top_priv, radii[-1]

def exget_coordinates(city_name: str) -> tuple:
    """
    Retrieve the geographic coordinates (latitude, longitude) of a given city using geopy.

    Args:
        city_name (str): Name of the city to geocode.

    Returns:
        tuple: (latitude, longitude) if found, otherwise None.
    """
    try:
        # Create SSL context with certifi's trusted certificates
        ctx = ssl.create_default_context(cafile=certifi.where())
        # Initialize geopy geolocator with SSL context
        geolocator = Nominatim(user_agent="city_distance_calculator", timeout=5, ssl_context=ctx)  # Increased timeout to 5 seconds for reliability
        # Attempt to geocode the city name
        location = geolocator.geocode(city_name)
        if location:
            # Return coordinates if found
            return (location.latitude, location.longitude), False  # geolocation_api_error is False if successful
        else:
            # Return None if city not found
            return None, False  # geolocation_api_error is False if city not found
    except Exception as e:
        return None, True  # geolocation_api_error is True if an error occurs


def get_coordinates(df_with_cities: pd.DataFrame, city_name: str) -> tuple:
    """
    Retrieve the geographic coordinates (latitude, longitude) of a city from 
        the hospitals DataFrame.

    Args:
        city_name (str): Name of the city to look up.

    Returns:
        tuple: (latitude, longitude) if found, otherwise raises an error.
    """
    df=df_with_cities
    # Filter DataFrame for the specified city and extract coordinates
    result = df[df['Ville'] == city_name][['Latitude', 'Longitude']]
    
    # Error handling if city not found
    if result.empty:
        return None
    
    latitude, longitude = result.iloc[0]
    
    return (latitude,longitude)
    
    
def distance_to_query(query_coords: tuple, city: str, df_with_cities: pd.DataFrame, geolocation_api_error: bool) -> float:
    """
    Calculate the geodesic distance in kilometers between a query location and a city.

    Args:
        query_coords (tuple): (latitude, longitude) of the query location.
        city (str): Name of the city to compare.

    Returns:
        float: Distance in kilometers if successful, otherwise None.
    """
    # Get coordinates for the target city
    from app.utility.logging import get_logger
    logger = get_logger(__name__)
    # logger.debug(f"distance_to_query called: query_coords={query_coords}, city={city}")
    city_coords = get_coordinates(df_with_cities, city)
    if city_coords:
        try:
            res = geodesic(query_coords, city_coords).kilometers
            # logger.debug(f"Calculated distance for city '{city}': {res} km (query_coords={query_coords}, city_coords={city_coords})")
            return res
        except Exception as e:
            geolocation_api_error = True
            logger.error(f"Error calculating distance for city '{city}': {e} (query_coords={query_coords}, city_coords={city_coords})")
            return None
    else:
        logger.warning(f"No coordinates found for city '{city}' in DataFrame. Returning None.")
        return None