from .city.city_analyst import CityAnalyst
from .city.city_validation import CityCheckException
from .institution_name.institution_name_analyst import InstitutionNameAnalyst
from .institution_type.institution_type_analyst import InstitutionTypeAnalyst
from .number_institutions.number_institutions_analyst import NumberInstitutionsAnalyst
from .specialty.specialty_analyst import SpecialtyAnalyst
from app.utility.specialty_dicts_lists import specialty_categories_dict
from app.utility.logging import get_logger

logger = get_logger(__name__)

class QueryAnalyst:
    """
    QueryAnalyst consolidates various detection services to analyze queries for city, institution name,
    institution type, specialty, and number of institutions.
    It provides a unified interface to run all detections and returns the results in a structured format.

    Attributes:
        model: The model used for processing queries.
        institution_list: Optional list of institutions for validation.
        llm_handler_service: Optional service for handling large language model interactions.
    Methods:
        run_all_detections(text, conv_history="", institution_list=None):
            Analyzes the provided text and conversation history to detect city, institution name,
            institution type, specialty, and number of institutions.    
    """
    def __init__(self, model=None, institution_list=None, llm_handler_service=None):
        logger.info("Initializing QueryAnalyst")
        self.model = model
        self.city_service = CityAnalyst(llm_handler_service, model)
        self.institution_name_service = InstitutionNameAnalyst(model, institution_list or "")
        self.institution_type_service = InstitutionTypeAnalyst(model, institution_list or "")
        # Use SpecialtyAnalyst instead of SpecialtyDetector
        # You may want to pass a specialty_list from config or data, here we use all specialties from the dict
        all_specialties = [s for specs in specialty_categories_dict.values() for s in specs]
        self.specialty_analyst = SpecialtyAnalyst(model, all_specialties, specialty_categories_dict)
        self.number_institutions_service = NumberInstitutionsAnalyst(model)


    def run_all_detections(self, text, conv_history="", institution_list=None):
        logger.debug(f"run_all_detections called: text={text}, conv_history={conv_history}, institution_list={institution_list}")
        """
        Consolidate results from all prompt detection classes into a dictionary.
        Returns:
            dict: {
                'city': ...,
                'institution_name': ...,
                'institution_type': ...,
                'specialty': ...,
                'number_institutions': ...
            }
        """
        specialty_result = self.specialty_analyst.detect_and_validate_specialty(text, conv_history)
        number_institutions = self.number_institutions_service.process_number_institutions(text, conv_history)

        try:
            city_info = self.city_service.process_city(text, conv_history)
            logger.debug(f"QueryAnalyst.run_all_detections: city_info={city_info}")
            # Sanity check: city_info must be a dict with 'city' and 'city_detected'
            if not isinstance(city_info, dict) or "city" not in city_info or "city_detected" not in city_info:
                logger.error(f"QueryAnalyst.run_all_detections: city_info malformed, using fallback: {city_info}")
                city_info = {"city": None, "city_detected": False}
        except CityCheckException as e:
            logger.error(f"QueryAnalyst.run_all_detections: CityCheckException: {e}")
            city_info = {"city": None, "city_detected": False}
        except Exception as e:
            logger.error(f"QueryAnalyst.run_all_detections: Unexpected exception: {e}")
            city_info = {"city": None, "city_detected": False}

        institution_name_result = self.institution_name_service.detect_and_validate(text, conv_history)
        institution_type_result = self.institution_type_service.detect_and_validate_type(text, conv_history)
        return {
            "city": city_info["city"],
            "city_detected": city_info["city_detected"],
            "institution_name": institution_name_result.get("institution_name"),
            "institution_type": institution_type_result.get("institution_type"),
            "specialty": specialty_result,  # returns full dict from SpecialtyAnalyst
            "number_institutions": number_institutions
        }
