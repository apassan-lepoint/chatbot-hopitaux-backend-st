"""
This module contains functions to format prompts for various tasks in the chatbot application.
"""

from app.utils.query_detection.prompt_instructions import PROMPT_INSTRUCTIONS

def format_sanity_check_medical_pertinence_prompt(prompt: str) -> str:
    return PROMPT_INSTRUCTIONS["sanity_check_medical_pertinence_prompt"].format(prompt=prompt)


def format_sanity_check_chatbot_pertinence_prompt(prompt):
    return PROMPT_INSTRUCTIONS["sanity_check_chatbot_pertinence_prompt"].format(prompt=prompt)


def format_second_detect_specialty_prompt(mapping_words, prompt):
    return PROMPT_INSTRUCTIONS["second_detect_specialty_prompt"].format(mapping_words=mapping_words, prompt=prompt)


def format_detect_city_prompt(prompt):
    return PROMPT_INSTRUCTIONS["detect_city_prompt"].format(prompt=prompt)


def format_second_detect_city_prompt(prompt):
    return PROMPT_INSTRUCTIONS["second_detect_city_prompt"].format(prompt=prompt)


def format_detect_topk_prompt(prompt):
    return PROMPT_INSTRUCTIONS["detect_topk_prompt"].format(prompt=prompt)


def format_detect_institution_type_prompt(prompt, institution_list):
    return PROMPT_INSTRUCTIONS["detect_institution_type_prompt"].format(prompt=prompt, institution_list=institution_list)


def format_second_detect_institution_type_prompt(prompt):
    return PROMPT_INSTRUCTIONS["second_detect_institution_type_prompt"].format(prompt=prompt)


def format_continue_conversation_prompt(prompt, conv_history):
    return PROMPT_INSTRUCTIONS["continue_conversation_prompt"].format(conv_history=conv_history, prompt=prompt)


def format_detect_modification_prompt(prompt, conv_history):
    return PROMPT_INSTRUCTIONS["detect_modification_prompt"].format(conv_history=conv_history, prompt=prompt)


def format_rewrite_query_prompt(last_query, modification):
    return PROMPT_INSTRUCTIONS["rewrite_query_prompt"].format(last_query=last_query, modification=modification)
    