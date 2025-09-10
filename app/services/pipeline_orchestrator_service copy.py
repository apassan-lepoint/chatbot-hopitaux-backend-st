def generate_response(self, prompt: str, max_radius_km: int = 5,
                      detected_specialty: str = None, conversation=None, conv_history=None):
    """
    Main entry point: processes the user question and returns a formatted answer with ranking and links.
    """
    logger.info(f"Starting pipeline processing - prompt: {prompt}")

    # Reset attributes and set specialty
    self.reset_attributes()
    self.specialty = detected_specialty or "no specialty match"
    self.data_processor.specialty = self.specialty

    conversation = conversation or []
    conv_history = conv_history or ""

    # ------------------- Sanity Checks ------------------- #
    error_msg = self._run_sanity_checks(prompt, conversation, conv_history)
    if error_msg:
        return error_msg, None

    # ------------------- Specialty Detection ------------------- #
    specialty_list = self._handle_specialty_detection(prompt, detected_specialty, conv_history)
    if specialty_list and len(specialty_list) > 1:
        logger.info("Multiple specialty matches detected")
        formatted_response = NON_ERROR_MESSAGES['multiple_specialties'] + "\n- " + "\n- ".join(specialty_list)
        return {"message": formatted_response, "multiple_specialties": specialty_list}, None

    # ------------------- Build Ranking DataFrame ------------------- #
    df = self._build_ranking_df(prompt, self.ranking_file_path, detected_specialty)
    if df is None:
        return ERROR_MESSAGES['general_ranking_error'], None
    if self.data_processor.geolocation_api_error:
        return ERROR_MESSAGES['geopy_error'], None

    # ------------------- Handle Fallback for Unavailable Specialty ------------------- #
    fallback_response = self._handle_fallback_if_unavailable()
    if fallback_response:
        return fallback_response

    # ------------------- Institution-specific Query ------------------- #
    if self.institution_name_mentioned:
        try:
            res = self.get_filtered_and_sorted_df(df, max_radius_km, self.number_institutions, prompt)
            return res, self.data_processor.web_ranking_link
        except Exception as e:
            logger.exception(f"Exception in get_filtered_and_sorted_df: {e}")
            return ERROR_MESSAGES['general_error'], self.data_processor.web_ranking_link

    # ------------------- City-specific Ranking ------------------- #
    if self.data_processor.city_detected and "Ville" in df.columns:
        return self._handle_city_ranking(df, prompt, max_radius_km)

    # ------------------- General Ranking (no city) ------------------- #
    return self._handle_general_ranking(prompt)

# ------------------- Helper Methods ------------------- #

def _run_sanity_checks(self, prompt, conversation, conv_history):
    try:
        result = self.sanity_checks_analyst_results.run_checks(prompt, conversation, conv_history)
        self.sanity_checks_analyst_result = result
        if isinstance(result, dict) and not result.get("passed", True):
            error_msg = result.get("error", ERROR_MESSAGES['general_error'])
            self._log_result_to_csv(prompt, error_msg)
            return error_msg
        return None
    except Exception as exc:
        error_msg = str(exc)
        self._log_result_to_csv(prompt, error_msg)
        return error_msg

def _handle_specialty_detection(self, prompt, detected_specialty, conv_history):
    detections = self.extract_query_parameters(prompt, detected_specialty, conv_history)
    specialty_list = []

    if detections:
        if "multiple_specialties" in detections and detections["multiple_specialties"]:
            specialty_list = detections["multiple_specialties"]
        elif isinstance(detections.get("specialty"), list) and len(detections["specialty"]) > 1:
            specialty_list = detections["specialty"]
        elif isinstance(detections.get("specialty"), str):
            spec_str = detections["specialty"].lower().replace(" ", "")
            if spec_str.startswith("multiplematches:"):
                matches_str = detections["specialty"].split(":", 1)[1].strip()
                specialty_list = [s.strip() for s in matches_str.split(",") if s.strip()]
    return specialty_list

def _build_ranking_df(self, prompt, file_path, detected_specialty):
    try:
        return self.build_ranking_dataframe_with_distances(prompt, file_path, detected_specialty)
    except Exception as e:
        logger.exception(f"Exception in build_ranking_dataframe_with_distances: {e}")
        return None

def _handle_fallback_if_unavailable(self):
    if not self.data_processor.specialty_ranking_unavailable:
        return None
    try:
        fallback_type = 'Public' if self.data_processor.institution_type == 'Privé' else 'Privé'
        self.data_processor.institution_type = fallback_type
        self.institution_type = fallback_type
        self.data_processor.specialty_ranking_unavailable = False
        fallback_df = self.data_processor.generate_data_response()
        if fallback_df is None or fallback_df.empty:
            return f"Aucun établissement ({fallback_type}) n'est disponible pour votre query.", self.data_processor.web_ranking_link
        # Format response for fallback
        filtered_df = fallback_df[fallback_df["Catégorie"] == fallback_type]
        if fallback_type == 'Public':
            res_str = format_response(filtered_df, None, self.number_institutions, not self.data_processor.city_detected)
            message = self._format_response_with_specialty(NON_ERROR_MESSAGES['no_private_institutions'], self.number_institutions, None, self.city)
        else:
            res_str = format_response(None, filtered_df, self.number_institutions, not self.data_processor.city_detected)
            message = self._format_response_with_specialty(NON_ERROR_MESSAGES['no_public_institutions'], self.number_institutions, None, self.city)
        return self._create_response_and_log(message, res_str, None, METHODOLOGY_WEB_LINK), self.data_processor.web_ranking_link
    except Exception as e:
        logger.exception(f"Exception in fallback handling: {e}")
        return "Aucun établissement n'est disponible pour votre query.", self.data_processor.web_ranking_link

def _handle_city_ranking(self, df, prompt, max_radius_km):
    query_city = self.data_processor.city
    query_coords = getattr(self.data_processor, 'get_city_coordinates', lambda x: None)(query_city)
    selected_df, used_radius = self.data_processor.select_hospitals(df, query_city, self.number_institutions, query_coords, SEARCH_RADIUS_KM)
    if selected_df is None or selected_df.empty:
        return NON_ERROR_MESSAGES['no_results_found_in_location'], self.data_processor.web_ranking_link

    public_df = selected_df[selected_df["Catégorie"] == "Public"]
    private_df = selected_df[selected_df["Catégorie"] == "Privé"]

    if self.institution_type == 'Public':
        res_str = format_response(public_df, None, self.number_institutions, not self.data_processor.city_detected)
    elif self.institution_type == 'Privé':
        res_str = format_response(None, private_df, self.number_institutions, not self.data_processor.city_detected)
    else:
        res_str = format_response(public_df, private_df, self.number_institutions, not self.data_processor.city_detected)

    message = self._format_response_with_specialty(f"Voici les meilleurs établissements (rayon utilisé : {used_radius} km)", self.number_institutions, used_radius, self.city)
    return self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK), self.data_processor.web_ranking_link

def _handle_general_ranking(self, prompt):
    try:
        if 'Distance' in self.df_gen.columns:
            self.df_gen = self.df_gen.drop(columns=['Distance'])
        public_df = self.df_gen[self.df_gen["Catégorie"] == "Public"].nlargest(self.number_institutions, "Note / 20")
        private_df = self.df_gen[self.df_gen["Catégorie"] == "Privé"].nlargest(self.number_institutions, "Note / 20")
        res_str = format_response(public_df, private_df, self.number_institutions, not self.data_processor.city_detected)
        base_msg = "Voici le meilleur établissement" if self.number_institutions == 1 else f"Voici les {self.number_institutions} meilleurs établissements"
        display_specialty, is_no_match = self._normalize_specialty_for_display(self.specialty)
        message = f"{base_msg} pour la pathologie {display_specialty}<br> \n" if not is_no_match else f"{base_msg}:<br> \n"
        return self._create_response_and_log(message, res_str, prompt, METHODOLOGY_WEB_LINK), self.data_processor.web_ranking_link
    except Exception as e:
        logger.exception(f"Exception in general ranking response: {e}")
        return ERROR_MESSAGES['general_ranking_error'], self.data_processor.web_ranking_link