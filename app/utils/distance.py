"""
Utility functions for geolocation and distance calculations.

This file provides helpers to compute distances between cities and hospitals,
    and to retrieve geographic coordinates for use in ranking/filtering.
"""

from geopy.geocoders import Nominatim  
from geopy.distance import geodesic 

def exget_coordinates(self, city_name: str) -> tuple:
    """
    Retrieve the geographic coordinates (latitude, longitude) of a given city using geopy.

    Args:
        city_name (str): Name of the city to geocode.

    Returns:
        tuple: (latitude, longitude) if found, otherwise None.
    """
    
    try:
        geolocator = Nominatim(user_agent="city_distance_calculator")
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            return None
    except Exception as e:
        self.geopy_problem=True
        return None
    
def get_coordinates(self, city_name: str) -> tuple:
    """
    Retrieve the geographic coordinates (latitude, longitude) of a city from 
        the hospitals DataFrame.

    Args:
        city_name (str): Name of the city to look up.

    Returns:
        tuple: (latitude, longitude) if found, otherwise raises an error.
    """
    df=self.df_with_cities
    result = df[df['City'] == city_name][['Latitude', 'Longitude']]
    latitude, longitude = result.iloc[0]
    return (latitude,longitude)
    
def distance_to_query(city):
    """
    Calculate the geodesic distance in kilometers between a query location and a city.

    Args:
        city (str): Name of the city to compare.
        query_coords (tuple): (latitude, longitude) of the query location.

    Returns:
        float: Distance in kilometers if successful, otherwise None.
    """
    
    city_coords = self.get_coordinates(city)
    if city_coords:
        try: 
            res=geodesic(query_coords, city_coords).kilometers
            return res
        except Exception as e:
            self.geopy_problem=True
            return None
    else:
        return None