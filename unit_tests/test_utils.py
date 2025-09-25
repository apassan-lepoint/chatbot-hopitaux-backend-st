import pytest
import pandas as pd
import numpy as np
from app.utility.functions.data_processor_service_helpers import haversine, add_distance_column
from app.utility.functions.formatting_helpers import normalize_text, format_links
from app.utility.functions.llm_helpers import parse_llm_response
from app.utility.functions.pipeline_orchestrator_helpers import format_rows, generate_web_link, get_institution_type_for_url, handle_variable_selection, _sum_keys_with_substring       


class TestUtils:
    def test_normalize_text(self):
        """
        Test normalize_text for typical, edge, and invalid inputs.
        Covers: accents, articles, spaces, non-string, empty, punctuation.
        """
        # Typical French string
        assert normalize_text("L'hôpital de la Santé", mode="string_matching") == "hopital sante"
        assert normalize_text("Cancer de la Vessie", mode="web_link") == "cancer-de-la-vessie"
        # Non-string
        assert normalize_text(None) == ""
        assert normalize_text(123) == ""
        assert normalize_text(["a", "b"]) == ""
        # Only accents/punctuation
        assert normalize_text("!!!", mode="string_matching") == ""
        assert normalize_text("éàè", mode="string_matching") == "eae"
        # Only articles
        assert normalize_text("de la le les", mode="string_matching") == ""
        # Multiple spaces
        assert normalize_text("  Santé   ", mode="string_matching") == "sante"
        # Empty string
        assert normalize_text("", mode="string_matching") == ""


    def test_format_links(self):
        """
        Test format_links for appending links, empty links, and empty result.
        """
        # Appends links
        result = format_links("Classement:", ["http://example.com", "http://test.com"])
        assert "🔗Page du classement" in result
        assert "http://example.com" in result and "http://test.com" in result
        # Empty links
        assert format_links("Classement:", []) == "Classement:"
        # Empty result
        assert format_links("", ["http://example.com"]) == "<br>[🔗Page du classement](http://example.com)"


    def test_haversine(self):
        """
        Test haversine for known cities, same coordinates, invalid and negative values.
        """
        # Paris-Lyon
        dist = haversine(48.8566, 2.3522, 45.7640, 4.8357)
        assert np.isclose(dist, 392, atol=1)
        # Same coordinates
        assert np.isclose(haversine(0, 0, 0, 0), 0, atol=0.1)
        # Invalid coordinates
        result = haversine(np.nan, 2.3522, 45.7640, 4.8357)
        assert np.isnan(result)


    def test_add_distance_column(self):
        """
        Test add_distance_column for correct output, empty df, missing columns, NaN values.
        """
        # Correct output
        df = pd.DataFrame({
            "ETABLISSEMENT_LATITUDE": [48.8566, 45.7640],
            "ETABLISSEMENT_LONGITUDE": [2.3522, 4.8357]
        })
        loc_lat, loc_lon = 48.8566, 2.3522
        df_out = add_distance_column(df, loc_lat, loc_lon)
        assert "distance_km" in df_out.columns
        assert np.isclose(df_out.iloc[0]["distance_km"], 0, atol=0.1)
        assert np.isclose(df_out.iloc[1]["distance_km"], 392, atol=1)
        # Empty DataFrame
        empty_df = pd.DataFrame()
        out_df = add_distance_column(empty_df, 48.8566, 2.3522)
        assert out_df.empty
        # Missing columns
        df_missing = pd.DataFrame({"LAT": [48.8566], "LON": [2.3522]})
        with pytest.raises(KeyError):
            add_distance_column(df_missing, 48.8566, 2.3522)
        # NaN values
        df_nan = pd.DataFrame({
            "ETABLISSEMENT_LATITUDE": [np.nan, 45.7640],
            "ETABLISSEMENT_LONGITUDE": [2.3522, np.nan]
        })
        out_df_nan = add_distance_column(df_nan, 48.8566, 2.3522)
        assert np.isnan(out_df_nan.iloc[0]["distance_km"]) or np.isnan(out_df_nan.iloc[1]["distance_km"])


    def test_format_rows(self):
        """
        Test format_rows for normal, empty, missing columns, location specified/not specified.
        """
        df = pd.DataFrame({
            "ETABLISSEMENT_NOM": ["A", "B"],
            "ETABLISSEMENT_TYPE": ["Public", "Privé"],
            "CLASSEMENT_NOTE": [18, 17],
            "distance_km": [10, 20]
        })
        msg = format_rows(df, "public", 2, False)
        assert "A" in msg and "B" in msg and "10 km" in msg
        # Empty DataFrame
        assert "Aucun établissement" in format_rows(pd.DataFrame(), "public", 2, False)
        # Missing columns
        df_missing = pd.DataFrame({"X": [1]})
        msg_missing = format_rows(df_missing, "public", 1, False)
        assert "Nom inconnu" in msg_missing
        # Location not specified
        msg_no_loc = format_rows(df, "public", 2, True)
        assert "situé à" not in msg_no_loc


    def test_generate_web_link(self):
        """
        Test generate_web_link for normal, empty, unknown type.
        """
        link = generate_web_link("Audition", "Public")
        assert "audition-public" in link
        # Empty specialty
        link_empty = generate_web_link("", "Privé")
        assert "-prive" in link_empty
        # Unknown type
        link_unknown = generate_web_link("Cancer", "UnknownType")
        assert "unknowntype" in link_unknown


    def test_get_institution_type_for_url(self):
        """
        Test get_institution_type_for_url for known and unknown types.
        """
        assert get_institution_type_for_url("Public") == "public"
        assert get_institution_type_for_url("Privé") == "prive"
        assert get_institution_type_for_url("UnknownType") == "unknowntype"


    def test_handle_variable_selection(self):
        """
        Test handle_variable_selection for single, multiple, none, user-selected.
        """        
        # User selected
        success, val = handle_variable_selection("specialty", "cardiologie interventionnelle", {})
        assert success and val == "cardiologie interventionnelle"
        # None detected
        success, val = handle_variable_selection("specialty", None, {})
        assert success and val is None
        # Single detected
        success, val = handle_variable_selection("specialty", None, {"specialty": ["Cancer de la vessie"]})
        assert success and val == {"specialty": "Cancer de la vessie"}
        # Multiple detected
        success, val = handle_variable_selection("specialty", None, {"specialty": ["Cardio", "Neuro"]})
        assert not success and "multiple_specialty" in val


    def test_sum_keys_with_substring(self):
        """
        Test _sum_keys_with_substring for normal, no match, non-numeric.
        """
        d = {"cost1": 1.5, "cost2": 2.5, "tokens": 10, "other": "x"}
        assert _sum_keys_with_substring(d, "cost") == 4.0
        assert _sum_keys_with_substring(d, "tokens") == 10
        assert _sum_keys_with_substring({}, "cost") == 0.0
        assert _sum_keys_with_substring({"cost": "abc"}, "cost") == 0.0


    def test_parse_llm_response(self):
        """
        Test parse_llm_response for boolean, numeric, location, modification, institution_type, specialty, fallback.
        """
        # Boolean
        assert parse_llm_response("1", "boolean") is True
        assert parse_llm_response("0", "boolean") is False
        # Numeric
        assert parse_llm_response("42", "numeric") == 42
        # Location
        assert parse_llm_response("1", "location") == 1
        # Modification
        assert parse_llm_response("1", "modification") == 1
        # Institution type
        assert parse_llm_response("2", "institution_type") == "private"
        # Specialty
        assert parse_llm_response("2", "specialty") is not None
        # Fallback
        assert parse_llm_response("not-a-number", "numeric", default=99) == 99

