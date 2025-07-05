
"""
This module provides the Processing class which handles the processing of hospital ranking data.
"""

import os
import pandas as pd
import csv
from datetime import datetime
import unicodedata
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

from app.utils.query_detection.institutions import institution_coordinates_df
from app.utils.config import PATHS
from app.services.llm_service import LLMService
from app.utils.formatting import remove_accents
from app.utils.distance import exget_coordinates, get_coordinates, distance_to_query
from app.utils.logging import get_logger
logger = get_logger(__name__)

class Processing:
    def __init__(self):
        self.ranking_df = None
        self.llm_service = LLMService()
        self.specialty_df = None
        self.institution_name = None
        self.specialty_ranking_unavailable = False
        self.web_ranking_link = None
        self.geolocation_api_error = False

        self.weblinks = {
            "public": "https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-public.php",
            "privé": "https://www.lepoint.fr/hopitaux/classements/tableau-d-honneur-prive.php"
        }
        self.specialty = None
        self.institution_type = None
        self.city = None
        self.df_with_cities = None
        self.institution_mentioned = None
        self.paths = PATHS
        self.institution_coordinates_df = institution_coordinates_df

    def get_infos(self, prompt: str) -> None:
        # Extracts specialty, city, and institution type from the prompt using LLMService
        if self.specialty is None:
            self.specialty = self.llm_service.detect_specialty(prompt)
            self.ranking_df = pd.read_excel(self.paths["ranking_file_path"], sheet_name="Palmarès")
        self.ranking_df = pd.read_excel(self.paths["ranking_file_path"], sheet_name="Palmarès")
        self.city = self.llm_service.detect_city(prompt)
        self.institution_type = self.llm_service.detect_institution_type(prompt)
        self.institution_mentioned = self.llm_service.institution_mentioned
        self.institution_name = self.llm_service.institution_name
        return None

    def enlever_accents(self, chaine: str) -> str:
        return remove_accents(chaine)

    def _generate_lien_classement(self, matching_rows: pd.DataFrame = None) -> list:
        self.web_ranking_link = []
        if self.specialty == 'aucune correspondance':
            if self.institution_type == 'Public':
                self.web_ranking_link = [self.weblinks["public"]]
            elif self.institution_type == 'Privé':
                self.web_ranking_link = [self.weblinks["privé"]]
            else:
                self.web_ranking_link = [self.weblinks["public"], self.weblinks["privé"]]
            return None
        etat = self.institution_type
        if self.specialty_ranking_unavailable:
            if self.institution_type == 'Public':
                etat = 'prive'
            if self.institution_type == 'Privé':
                etat = 'public'
            web_ranking_link = self.specialty.replace(' ', '-')
            web_ranking_link = f'https://www.lepoint.fr/hopitaux/classements/{web_ranking_link}-{etat}.php'
            web_ranking_link = web_ranking_link.lower()
            web_ranking_link = self.enlever_accents(web_ranking_link)
            self.web_ranking_link.append(web_ranking_link)
            return self.web_ranking_link

        for _, row in matching_rows.iterrows():
            web_ranking_link = row["Spécialité"].replace(' ', '-')
            web_ranking_link = f'https://www.lepoint.fr/hopitaux/classements/{web_ranking_link}-{row["Catégorie"]}.php'
            web_ranking_link = web_ranking_link.lower()
            web_ranking_link = self.enlever_accents(web_ranking_link)
            self.web_ranking_link.append(web_ranking_link)
        return self.web_ranking_link

    def _load_and_transform_for_no_specialty(self, category: str) -> pd.DataFrame:
        if category == 'aucune correspondance':
            dfs = []
            df_private = pd.read_csv(self.paths["ranking_overall_private_path"])
            df_private['Catégorie'] = 'Privé'
            dfs.append(df_private)
            df_public = pd.read_csv(self.paths["ranking_overall_public_path"])
            df_public['Catégorie'] = 'Public'
            dfs.append(df_public)
            df = pd.concat(dfs, join="inner", ignore_index=True)
        elif category == 'Public':
            csv_path = self.paths["ranking_overall_public_path"]
            df = pd.read_csv(csv_path)
            df['Catégorie'] = category
        elif category == 'Privé':
            csv_path = self.paths["ranking_overall_private_path"]
            df = pd.read_csv(csv_path)
            df['Catégorie'] = category
        else:
            raise ValueError(f"Unknown category: {category}")
        df = df.rename(columns={'Score final': 'Note / 20', 'Nom Print': 'Etablissement'})
        return df

    def load_excel_sheets(self, matching_rows: pd.DataFrame) -> pd.DataFrame:
        excel_path = self.paths["ranking_file_path"]
        dfs = []
        for _, row in matching_rows.iterrows():
            sheet_name = row.iloc[2]
            category = row["Catégorie"]
            df_sheet = pd.read_excel(self.paths["ranking_file_path"], sheet_name=sheet_name)
            df_sheet["Catégorie"] = category
            dfs.append(df_sheet)
        if dfs:
            return pd.concat(dfs, join="inner", ignore_index=True)
        else:
            if self.specialty != 'aucune correspondance' and self.institution_type != 'aucune correspondance':
                res = []
                res.append("Nous n'avons pas d'établissement de ce type pour cette pathologie")
                self.specialty_ranking_unavailable = True
                return res

    def find_excel_sheet_with_specialty(self, prompt: str) -> pd.DataFrame:
        matching_rows = self.ranking_df[self.ranking_df["Spécialité"].str.contains(self.specialty, case=False, na=False)]
        self.web_ranking_link = []
        self._generate_lien_classement(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        return self.specialty_df

    def find_excel_sheet_with_privacy(self, prompt: str, detected_specialty) -> pd.DataFrame:
        self.get_infos(prompt)
        specialty = detected_specialty
        if specialty == 'aucune correspondance':
            self._generate_lien_classement()
            self.specialty_df = self._load_and_transform_for_no_specialty(category=self.institution_type)
            return self.specialty_df
        if self.institution_type == 'aucune correspondance':
            return self.find_excel_sheet_with_specialty(prompt)
        matching_rows = self.ranking_df[self.ranking_df["Spécialité"].str.contains(specialty, case=False, na=False)]
        matching_rows = matching_rows[matching_rows["Catégorie"].str.contains(self.institution_type, case=False, na=False)]
        self._generate_lien_classement(matching_rows)
        self.specialty_df = self.load_excel_sheets(matching_rows)
        return self.specialty_df

    def extract_loca_hospitals(self, df: pd.DataFrame = None) -> pd.DataFrame:
        coordonnees_df = self.institution_coordinates_df.dropna()
        notes_df = self.specialty_df
        coordonnees_df = coordonnees_df[["Etablissement", "Ville", "Latitude", "Longitude"]]
        notes_df = notes_df[["Etablissement", "Catégorie", "Note / 20"]]
        self.df_with_cities = pd.merge(coordonnees_df, notes_df, on="Etablissement", how="inner")
        self.df_with_cities.rename(columns={"Ville": "City"}, inplace=True)
        return self.df_with_cities

    def exget_coordinates(self, city_name: str) -> tuple:
        try:
            geolocator = Nominatim(user_agent="city_distance_calculator")
            location = geolocator.geocode(city_name)
            if location:
                return (location.latitude, location.longitude)
            else:
                return None
        except Exception as e:
            self.geolocation_api_error = True
            return None

    def get_coordinates(self, city_name: str) -> tuple:
        df = self.df_with_cities
        result = df[df['City'] == city_name][['Latitude', 'Longitude']]
        latitude, longitude = result.iloc[0]
        return (latitude, longitude)

    def get_df_with_distances(self) -> pd.DataFrame:
        query_coords = self.exget_coordinates(self.city)
        if self.geolocation_api_error:
            return None
        self.df_with_cities = self.df_with_cities.dropna(subset=['City'])

        def distance_to_query(city):
            city_coords = self.get_coordinates(city)
            if city_coords:
                try:
                    res = geodesic(query_coords, city_coords).kilometers
                    return res
                except Exception as e:
                    self.geolocation_api_error = True
                    return None
            else:
                return None

        self.df_with_cities['Distance'] = self.df_with_cities['City'].apply(distance_to_query)
        self.df_with_distances = self.df_with_cities
        return self.df_with_distances

    def create_csv(self, question: str, reponse: str):
        file_name = self.paths["history_path"]
        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question,
            "ville": self.city,
            "type": self.institution_type,
            "spécialité": self.specialty,
            "résultat": reponse,
        }
        file_exists = os.path.exists(file_name)
        with open(file_name, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
        return None