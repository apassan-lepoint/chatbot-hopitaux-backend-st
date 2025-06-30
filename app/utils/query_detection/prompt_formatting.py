"""
This module contains functions to format prompts for various tasks in the chatbot application.
"""

from app.utils.query_detection.prompt_instructions import prompt_instructions

def format_check_medical_pertinence_prompt(prompt: str) -> str:
    return prompt_instructions["check_medical_pertinence_prompt"].format(prompt=prompt)


def format_check_chatbot_pertinence_prompt(prompt):
    return prompt_instructions["check_chatbot_pertinence_prompt"].format(prompt=prompt)


def format_detect_specialty_prompt(specialty_list, prompt):
    return prompt_instructions["detect_speciality_prompt"].format(specialty_list=specialty_list, prompt=prompt)


def format_second_detect_specialty_prompt(mapping_words, prompt):
    return prompt_instructions["second_detect_speciality_prompt"].format(mapping_words=mapping_words, prompt=prompt)

def format_detect_city_prompt(prompt):
    return prompt_instructions["detect_city_prompt"].format(prompt=prompt)


def format_second_detect_city_prompt(prompt):
    return prompt_instructions["second_detect_city_prompt"].format(prompt=prompt)


def format_detect_topk_prompt(prompt):
    return prompt_instructions["detect_topk_prompt"].format(prompt=prompt)


def format_detect_institution_type_prompt(prompt, institution_list):
    return prompt_instructions["detect_institution_type_prompt"].format(prompt=prompt, institution_list=institution_list)


def format_second_detect_institution_type_prompt(prompt):
    return prompt_instructions["second_detect_institution_type_prompt"].format(prompt=prompt)


def format_continue_conversation_prompt(prompt, conv_history):
    return prompt_instructions["continue_conversation_prompt"].format(conv_history=conv_history, prompt=prompt)


def format_detect_modification_prompt(prompt, conv_history):
    return prompt_instructions["detect_modification_prompt"].format(conv_history=conv_history, prompt=prompt)


def format_rewrite_query_prompt(last_query, modification):
    return prompt_instructions["rewrite_query_prompt"].format(last_query=last_query, modification=modification)
    