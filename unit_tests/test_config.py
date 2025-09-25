import os
import pytest
from app.config import features_config, file_paths_config

def test_openai_model_name():
    """
    Test that the OpenAI model name is set and is a string.
    """
    assert isinstance(features_config.OPENAI_MODEL, str)
    assert features_config.OPENAI_MODEL.startswith("gpt-")

def test_pricing_settings():
    """
    Test that pricing settings are floats and within reasonable bounds.
    """
    assert isinstance(features_config.INPUT_PROMPT_PRICE_PER_TOKEN, float)
    assert isinstance(features_config.OUTPUT_COMPLETION_PRICE_PER_TOKEN, float)
    assert features_config.INPUT_PROMPT_PRICE_PER_TOKEN > 0
    assert features_config.OUTPUT_COMPLETION_PRICE_PER_TOKEN > 0

def test_url_and_mapping():
    """
    Test that ranking URLs and institution type mapping are present and correct.
    """
    assert features_config.PUBLIC_RANKING_URL.startswith("http")
    assert features_config.PRIVATE_RANKING_URL.startswith("http")
    assert "Public" in features_config.INSTITUTION_TYPE_URL_MAPPING
    assert features_config.INSTITUTION_TYPE_URL_MAPPING["Public"] == "public"

def test_non_error_messages():
    """
    Test that NON_ERROR_MESSAGES contains expected keys and values are strings.
    """
    for key, value in features_config.NON_ERROR_MESSAGES.items():
        assert isinstance(key, str)
        assert isinstance(value, str)

def test_error_messages():
    """
    Test that ERROR_MESSAGES contains expected keys and values are strings.
    """
    for key, value in features_config.ERROR_MESSAGES.items():
        assert isinstance(key, str)
        assert isinstance(value, str)

def test_file_paths_exist():
    """
    Test that file paths in PATHS are strings and point to expected directories or files.
    """
    for key, path in file_paths_config.PATHS.items():
        assert isinstance(path, str)
        assert path.startswith(str(file_paths_config.REPO_ROOT))

def test_data_and_history_dirs():
    """
    Test that DATA_DIR and HISTORY_DIR are subdirectories of REPO_ROOT.
    """
    assert file_paths_config.DATA_DIR.startswith(str(file_paths_config.REPO_ROOT))
    assert file_paths_config.HISTORY_DIR.startswith(str(file_paths_config.REPO_ROOT))

def test_missing_path_key():
    """
    Test edge case: accessing a missing key in PATHS raises KeyError.
    """
    with pytest.raises(KeyError):
        _ = file_paths_config.PATHS["nonexistent_key"]

def test_methodology_link():
    """
    Test that the methodology web link is a valid URL string.
    """
    assert isinstance(features_config.METHODOLOGY_WEB_LINK, str)
    assert features_config.METHODOLOGY_WEB_LINK.startswith("http")

