"""
Utility functions for geolocation and distance calculations.

This file provides helpers to compute distances between cities and hospitals,
    and to retrieve geographic coordinates for use in ranking/filtering.
"""

from geopy.geocoders import Nominatim  
from geopy.distance import geodesic 

def exget_coordinates(self, 
    city_name: str #Ville de la question
    ) -> tuple:
    # Obtient les coordonnées géographiques de la ville de la question.

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
    
def get_coordinates(self, 
    city_name: str #Ville de la liste d'hôpital
    ) -> tuple:
    # Obtient les coordonnées géographiques d'une ville de la liste des hôpitaux depuis ma feuille Hôpitaux
        df=self.df_with_cities
        result = df[df['City'] == city_name][['Latitude', 'Longitude']]
        latitude, longitude = result.iloc[0]
        return (latitude,longitude)
    
def distance_to_query(city):
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