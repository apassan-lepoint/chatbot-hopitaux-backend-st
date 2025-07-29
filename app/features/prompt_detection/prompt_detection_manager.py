from .city.city_service import CityService
from .city.city_validation import CityCheckException
from .institution_name.institution_name_service import InstitutionNameService
from .institution_type.institution_type_service import InstitutionTypeService
from .topk.topk_service import TopKService
from .specialty.specialty_detection import SpecialtyDetector
from app.utility.logging import get_logger

logger = get_logger(__name__)

class PromptDetectionManager:
    def __init__(self, model=None, institution_list=None, llm_handler_service=None):
        logger.info("Initializing PromptDetectionManager")
        self.model = model
        self.city_service = CityService(llm_handler_service, model)
        self.institution_name_service = InstitutionNameService(model, institution_list or "")
        self.institution_type_service = InstitutionTypeService(model, institution_list or "")
        self.specialty_detector = SpecialtyDetector(model)
        self.topk_service = TopKService(model)

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
                'topk': ...
            }
        """
        specialty_result = self.specialty_detector.detect_specialty(text, conv_history)
        specialty = specialty_result.get_primary_specialty() if hasattr(specialty_result, 'get_primary_specialty') else specialty_result
        topk = self.topk_service.process_topk(text, conv_history)

        try:
            city_info = self.city_service.process_city(text, conv_history)
            logger.debug(f"PromptDetectionManager.run_all_detections: city_info={city_info}")
            # Sanity check: city_info must be a dict with 'city' and 'city_detected'
            if not isinstance(city_info, dict) or "city" not in city_info or "city_detected" not in city_info:
                logger.error(f"PromptDetectionManager.run_all_detections: city_info malformed, using fallback: {city_info}")
                city_info = {"city": None, "city_detected": False}
        except CityCheckException as e:
            logger.error(f"PromptDetectionManager.run_all_detections: CityCheckException: {e}")
            city_info = {"city": None, "city_detected": False}
        except Exception as e:
            logger.error(f"PromptDetectionManager.run_all_detections: Unexpected exception: {e}")
            city_info = {"city": None, "city_detected": False}

        institution_name_result = self.institution_name_service.detect_and_validate(text, conv_history)
        institution_type_result = self.institution_type_service.detect_and_validate_type(text, conv_history)
        return {
            "city": city_info["city"],
            "city_detected": city_info["city_detected"],
            "institution_name": institution_name_result.get("institution_name"),
            "institution_type": institution_type_result.get("institution_type"),
            "specialty": specialty,
            "topk": topk
        }
