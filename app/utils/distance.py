"""
Utility functions for geolocation and distance calculations.

This file provides helpers to compute distances between cities and hospitals,
    and to retrieve geographic coordinates for use in ranking/filtering.
"""

import pandas as pd
from geopy.geocoders import Nominatim  
from geopy.distance import geodesic 

def exget_coordinates(city_name: str) -> tuple:
    """
    Retrieve the geographic coordinates (latitude, longitude) of a given city using geopy.

    Args:
        city_name (str): Name of the city to geocode.

    Returns:
        tuple: (latitude, longitude) if found, otherwise None.
    """
    
    try:
        # Initialize geopy geolocator
        geolocator = Nominatim(user_agent="city_distance_calculator")
        # Attempt to geocode the city name
        location = geolocator.geocode(city_name)
        if location:
            # Return coordinates if found
            return (location.latitude, location.longitude), False  # geopy_problem is False if successful
        else:
            # Return None if city not found
            return None, False  # geopy_problem is False if city not found
    except Exception as e:
        return None, True  # geopy_problem is True if an error occurs
    
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
    result = df[df['City'] == city_name][['Latitude', 'Longitude']]
    
    # Error handling if city not found
    if result.empty:
        return None
    
    latitude, longitude = result.iloc[0]
    return (latitude,longitude)
    
def distance_to_query(query_coords: tuple, city: str, df_with_cities: pd.DataFrame, geopy_problem: bool) -> float:
    """
    Calculate the geodesic distance in kilometers between a query location and a city.

    Args:
        query_coords (tuple): (latitude, longitude) of the query location.
        city (str): Name of the city to compare.

    Returns:
        float: Distance in kilometers if successful, otherwise None.
    """
    
    # Get coordinates for the target city
    city_coords = get_coordinates(df_with_cities, city)
    if city_coords:
        try: 
            # Calculate geodesic distance between the two coordinate pairs
            res=geodesic(query_coords, city_coords).kilometers
            return res
        except Exception as e:
            # Set geopy_problem flag to True if an error occurs
            geopy_problem=True
            return None
    else:
        # Return None if city coordinates not found
        return None