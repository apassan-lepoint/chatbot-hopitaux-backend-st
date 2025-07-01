README

# Description
The hospital ranking assistant allows interaction with Le Point's hospital rankings and exploration of its content. It enables users to ask questions to query one of the rankings and continue the conversation based on the results of the initial question. It is currently accessible through a simple Streamlit application, serving as a user interface for testing and in production mode via FastAPI (in development).

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
│   ├── db/
│   │   ├── query.py
│   │   └── snowflake_connector.py
│   ├── models/
│   │   ├── query_model.py
│   │   └── response_model.py
│   ├── services/
│   │   ├── query_extraction_service.py
│   │   ├── conversation_service.py
│   │   ├── llm_service.py
│   │   ├── pipeline_service.py
│   │   └── processing_service.py
│   └── ui/
│       ├── streamlit_app.py
│   └── utils/
│       ├── query_detection/
│       │   ├── institutions.py
│       │   ├── prompt_formatting.py
│       │   ├── prompt_instructions.py
│       │   └── specialties.py
│       ├── sanity_checks/
│       │   ├── core_logic_sanity_checks.py
│       │   ├── fast_api_sanity_checks.py
│       │   └── streamlit_sanity_checks.py
│       ├── config.py
│       ├── distance.py
│       ├── formatting.py
│       └── logging.py
├── data/
├── history/
├── tests/



# Installation
If you want to launch the Streamlit app, you should create a python environnement named 'chop_venv' with the package from the "requirement.txt" file. 
You should as well get an API Key from Open AI and paste it in the '.env' file  to use our model: "gpt-4o-mini".

# Usage - EDIT 
Here are the commands to launch the Streamlit app from the terminal anaconda for example: 
- input "conda activate chop_venv"
Copy the path of the Front folder
- input "cd 'paste the path here'"
- input "streamlit run app/ui/streamlit_app.py"

Then you could ask your question.

# Code organization
UPDATE!!!! - give high level overview of how code works

# Contact
Anuradha (Annie) Passan - apassan@ext.lepoint.fr, apassan@eulidia.com
Maxime Kermagoet - mkermagoet@ext.lepoint.fr, mkermagoet@eulidia.com
Benjamin L'Hyver - blhyver@eulidia.com


