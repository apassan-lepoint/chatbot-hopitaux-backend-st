README

# Description
The hospital ranking assistant allows interaction with Le Point's hospital rankings and exploration of its content. It enables users to ask questions to query the rankings. It is currently accessible through a Streamlit application, serving as a user interface for testing and in production mode via FastAPI (in development).

# Project Structure

BackendChatbotHopitaux/
├── .env
├── .gitignore
├── Dockerfile
├── README.md
├── requirements.txt
├── main.py
├── app/
│   ├── api/
│   │   ├── dependencies.py 
│   │   └── routes.py
│   ├── config/
│   │   ├── features_config.py
│   │   └── file_paths_config.py
│   ├── features/
│   │   ├── conversation/
│   │   │  ├── conversation_analyst.py
│   │   │  ├── llm_responder.py
│   │   │  └── multi_turn.py
│   │   ├── query_analysis/
│   │   │  ├── city/
│   │   │  │   ├── city_analyst.py
│   │   │  │   ├── city_detection.py
│   │   │  │   └── city_validation.py
│   │   │  ├── institution_name/
│   │   │  │   ├── institution_name_analyst.py
│   │   │  │   ├── institution_name_detection.py
│   │   │  │   └── institution_name_validation.py
│   │   │  ├── institution_type/
│   │   │  │   ├── institution_type_analyst.py
│   │   │  │   ├── institution_type_detection.py
│   │   │  │   └── institution_type_validation.py
│   │   │  ├── number_institutions/
│   │   │  │   ├── number_institutions_analyst.py
│   │   │  │   ├── number_institutions_detection.py
│   │   │  │   └── number_institutions_validation.py
│   │   │  └── specialty/
│   │   │  │   ├── specialty_analyst.py - IN DEV
│   │   │  │   ├── specialty_detection.py - IN DEV
│   │   │  │   └── specialty_validation.py - IN DEV
│   │   │  └── query_analyst.py
│   │   └── sanity_checks/
│   │      ├── conversation_limit_check.py
│   │      ├── message_length_check.py
│   │      ├── message_pertinence_check.py
│   │      └── sanity_checks_analyst.py
│   ├── pydantic_models/
│   │   ├── query_model.py
│   │   └── response_model.py
│   ├── services/
│   │   ├── data_processing_service.py
│   │   ├── llm_handler_service.py
│   │   └── pipeline_orchestrator_service.py
│   ├── snowflake_db/
│   │   ├── query.py
│   │   └── snowflake_connector.py
│   └── utils/
│       ├── distance_calc_helpers.py
│       │── formatting_helpers.py
│       │── llm_helpers.py
│       │── logging.py
│       │── prompt_formatting_helpers.py
│       │── prompt_instructions.py
│       │── specialty_dicts_lists.py
│       └── wrappers.py
├── streamlit/
│   ├── st_app.py
│   ├── st_config.py
│   ├── st_message_handler.py
│   ├── st_specialty_handler.py
│   ├── st_ui_components.py
│   └── st_utility.py
├── data/
├── history/
└── tests/



# Installation (in dev)
If you want to launch the Streamlit app, you should create a python environnement with the packages from the "requirement.txt" file and then run the main.py file. 
Additionally, you will need an API Key from Open AI and paste it in the '.env' file  to use our model: "gpt-4o-mini".

# Code organization
UPDATE!!!! - give high level overview of how code works

# Contact
Anuradha (Annie) Passan - apassan@ext.lepoint.fr, apassan@eulidia.com
Benjamin L'Hyver - blhyver@eulidia.com
