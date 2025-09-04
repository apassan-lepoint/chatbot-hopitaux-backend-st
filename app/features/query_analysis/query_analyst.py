from .city.city_analyst import CityAnalyst
from .city.city_validation import CityCheckException
from .institution_names.institution_names_analyst import InstitutionNamesAnalyst
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
        self.institution_names_service = InstitutionNamesAnalyst(model, institution_list or "")
        self.institution_type_service = InstitutionTypeAnalyst(model, institution_list or "")
        all_specialties = [s for specs in specialty_categories_dict.values() for s in specs]
        self.specialty_analyst = SpecialtyAnalyst(model, all_specialties, specialty_categories_dict)
        self.number_institutions_service = NumberInstitutionsAnalyst(model)


    def run_all_detections(self, text, conv_history="", institution_list=None):
        """
        Consolidate results from all prompt detection classes into a dictionary.
        """
        logger.info(f"QueryAnalyst running all detections for text: {text}, conv_history: {conv_history}")

        specialty_result = self.specialty_analyst.detect_and_validate_specialty(text, conv_history)
        number_institutions_result = self.number_institutions_service.process_number_institutions(text, conv_history)

        try:
            city_result = self.city_service.detect_and_validate_city(text, conv_history)
            if not isinstance(city_result, dict) or "city" not in city_result or "city_detected" not in city_result:
                logger.error(f"QueryAnalyst.run_all_detections: city_result malformed, using fallback: {city_result}")
                city_result = {"city": None, "city_detected": False, "detection_method": None, "cost": 0.0}
        except CityCheckException as e:
            logger.error(f"QueryAnalyst.run_all_detections: CityCheckException: {e}")
            city_result = {"city": None, "city_detected": False, "detection_method": None, "cost": 0.0}
        except Exception as e:
            logger.error(f"QueryAnalyst.run_all_detections: Unexpected exception: {e}")
            city_result = {"city": None, "city_detected": False, "detection_method": None, "cost": 0.0}

        institution_names_result = self.institution_names_service.detect_and_validate_institution_names(text, conv_history)
        institution_type_result = self.institution_type_service.detect_and_validate_institution_type(text, conv_history)

        total_cost = (
            city_result.get("cost", 0.0)
            + institution_names_result.get("cost", 0.0)
            + institution_type_result.get("cost", 0.0)
            + specialty_result.get("cost", 0.0)
            + number_institutions_result.get("cost", 0.0)
        )
        total_token_usage = (
            city_result.get("token_usage", 0)
            + institution_names_result.get("token_usage", 0)
            + institution_type_result.get("token_usage", 0)
            + specialty_result.get("token_usage", 0)
            + number_institutions_result.get("token_usage", 0)
        )
        results =  {
            "city": city_result["city"],
            "city_detected": city_result["city_detected"],
            "city_detection_method": city_result.get("detection_method"),
            "city_cost": city_result.get("cost", 0.0),
            "city_token_usage": city_result.get("token_usage", 0),
            "institution_names_with_types": institution_names_result.get("institutions"),  # list of {name,type}
            "institution_names_detection_method": institution_names_result.get("detection_method"),
            "institution_names_cost": institution_names_result.get("cost", 0.0),
            "institution_names_token_usage": institution_names_result.get("token_usage", 0),
            "institution_names_intent": institution_names_result.get("intent"),
            "institution_type": institution_type_result.get("institution_type"),
            "institution_type_detection_method": institution_type_result.get("detection_method"),
            "institution_type_cost": institution_type_result.get("cost", 0.0),
            "institution_type_token_usage": institution_type_result.get("token_usage", 0),
            "specialty": specialty_result.get("specialty"),
            "specialty_detection_method": specialty_result.get("detection_method"),
            "specialty_cost": specialty_result.get("cost", 0.0),
            "specialty_token_usage": specialty_result.get("token_usage", 0),
            "number_institutions": number_institutions_result.get("number_institutions"),
            "number_institutions_detection_method": number_institutions_result.get("detection_method"),
            "number_institutions_cost": number_institutions_result.get("cost", 0.0),
            "number_institutions_token_usage": number_institutions_result.get("token_usage", 0),
            "total_cost": total_cost,
            "total_token_usage": total_token_usage
        }

        logger.info(f"QueryAnalyst detected: specialty={specialty_result.get('specialty')}, city={city_result.get('city')}, institution_names={institution_names_result.get('institution_names')}, institution_type={institution_type_result.get('institution_type')}, number_institutions={number_institutions_result.get('number_institutions')}")
        logger.info(f"QueryAnalyst costs/tokens: specialty_cost={specialty_result.get('cost')}, city_cost={city_result.get('cost')}, institution_names_cost={institution_names_result.get('cost')}, institution_type_cost={institution_type_result.get('cost')}, number_institutions_cost={number_institutions_result.get('cost')}")
        logger.info(f"QueryAnalyst tokens: specialty_tokens={specialty_result.get('token_usage')}, city_tokens={city_result.get('token_usage')}, institution_names_tokens={institution_names_result.get('token_usage')}, institution_type_tokens={institution_type_result.get('token_usage')}, number_institutions_tokens={number_institutions_result.get('token_usage')}")

        return results
    

    #  # Logging for debugging and analysis
    # logger.info(
    #     f"Institution names detected: {results['institution_names_with_types']}, "
    #     f"intent={results['institution_names_intent']}, "
    #     f"detection method={results['institution_names_detection_method']}"
    # )
    # logger.info(
    #     f"Costs/tokens: cost={results['institution_names_cost']}, "
    #     f"tokens={results['institution_names_token_usage']}"
    # )
