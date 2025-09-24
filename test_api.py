import requests

API_URL = "http://localhost:8000"

# Test /ask endpoint
def test_ask():
    payload = {
        # "prompt": "Quel est le meilleur hôpital entre Clinique Belledonne et Nouvelle clinique de Tours ? ",
        # "prompt": "Quel est le classement de CH de Vannes pour la cancer au sein ?",
        # "prompt": "Donnes-moi le meilleur hôpital à Paris pour la cardiologie",
        "prompt": "Quel est le meilleur hôpital entre Clinique Belledonne, Clinique Jean Causse, et Polyclinique de Kerio pour les problèmes auditifs ?"
        # "prompt": "Quels sont les meilleurs hôpitaux à Paris pour la cancer du vessie ?",
        # "prompt": "Quels sont les meilleurs hôpitaux à Paris pour la cancer de la vessie ?"
        #   pour les problèmes auditifs
    }
    response = requests.post(f"{API_URL}/ask", json=payload)
    print("/ask response:", response.status_code, response.json())

# Test /chat endpoint - only for multi-turn conversations
def test_chat():
    payload = {
        "prompt": "Et à Lyon?",
        "conversation": [["Quels sont les meilleurs hôpitaux à Paris?", "Voici la liste..."]]
    }
    response = requests.post(f"{API_URL}/chat", json=payload)
    print("/chat response:", response.status_code, response.json())

if __name__ == "__main__":
    test_ask()
    #test_chat()