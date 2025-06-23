import pandas as pd

def format_mapping_words_csv(
    self, 
    file_path: str #fichier Excel des mots associés à chaque spécialité
    ) -> str:
    # Convertit le fichier Excel des mots associés à chaque spécialité en un format pour injection dans un prompt.
    df = pd.read_csv(file_path)
    colonne = df['Valeurs'].dropna()  # Nettoyage de base
    resultat = colonne.astype(str).str.cat(sep="\n")
    return resultat

def format_correspondance_list(self,
    liste_spe
        ):
       # Si on a plusieurs correspondances, on créer un texte avec la liste des corréspondances, en supprimant les doublons
        options_string = liste_spe.removeprefix("plusieurs correspondances:").strip()
        options_list = options_string.split(',')
        options_list = [element.replace('.', '') for element in options_list]
        options_list = [element.strip() for element in options_list]
        resultat = [element for element in options_list if element in liste_spe]
        self.specialty="plusieurs correspondances:"+",".join(resultat)
        return self.specialty
    
def enlever_accents(self,
    chaine: str#chaîne pour laquelle on veut enlever les accents
    )-> str:
        chaine_normalisee = unicodedata.normalize('NFD', chaine)
        chaine_sans_accents = ''.join(c for c in chaine_normalisee if unicodedata.category(c) != 'Mn')
        chaine_sans_accents = chaine_sans_accents.replace("'", '-')
        return chaine_sans_accents
    
def tableau_en_texte(self,
    df: pd.DataFrame,#Tableau des résultats correspondant à la question
    ):
        #convertit le tableau des résultats en une réponse sous forme de texte
        descriptions = []
        if self.no_city:
            for index, row in df.iterrows():
                description = (
                    f"{row['Etablissement']}:"
                    f"Un établissement {row['Catégorie']}. "
                    f"avec une note de {row['Note / 20']}"
                )
                descriptions.append(description)
            
            # Joindre toutes les descriptions avec des sauts de ligne
            texte_final = "<br>\n".join(descriptions)
            
            return texte_final
        else:  
            for index, row in df.iterrows():
                description = (
                    f"{row['Etablissement']}:"
                    f"Un établissement {row['Catégorie']} situé à {int(row['Distance'])} km. "
                    f"avec une note de {row['Note / 20']}"
                )
                descriptions.append(description)
            
            # Joindre toutes les descriptions avec des sauts de ligne
            texte_final = "<br>\n".join(descriptions)
            
            return texte_final