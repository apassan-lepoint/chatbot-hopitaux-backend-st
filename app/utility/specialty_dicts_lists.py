# Dictionary mapping main specialties to their sub-specialties or procedures
specialty_categories_dict = {
        "Maternités": ["Accouchements normaux", "Accouchements à risques"],
        "Cardiologie": ["Angioplastie coronaire", "Cardiologie interventionnelle", "Chirurgie cardiaque adulte", "Chirurgie cardiaque pédiatrique", "Infarctus du myocarde", "Insuffisance cardiaque", "Rythmologie"],
        "Veines et artères": ["Ablation des varices", "Chirurgie des artères", "Chirurgie des carotides", "Hypertension artérielle", "Médecine vasculaire"],
        "Orthopédie": ["Arthrose de la main", "Chirurgie de l'épaule", "Chirurgie de la cheville", "Chirurgie du canal carpien", "Chirurgie du dos de l'adulte", "Chirurgie du dos de l'enfant et de l’adolescent", "Chirurgie du pied", "Ligaments du genou", "Prothèse de genou", "Prothèse de hanche"],
        "Ophtalmologie": ["Cataracte", "Chirurgie de la cornée", "Chirurgie de la rétine", "Glaucome", "Strabisme"],
        "Gynécologie et cancers de la femme": ["Cancer de l'ovaire", "Cancer de l'utérus", "Cancer du sein", "Endométriose", "Fibrome utérin"],
        "Appareil digestif": ["Appendicite", "Cancer de l'estomac ou de l'œsophage", "Cancer du côlon ou de l'intestin", "Cancer du foie", "Cancer du pancréas", "Chirurgie de l'obésité", "Chirurgie du rectum", "Hernies de l'abdomen", "Maladies inflammatoires chroniques de l'intestin (MICI)", "Proctologie"],
        "Psychiatrie": ["Dépression", "Schizophrénie"],
        "Urologie": ["Adénome de la prostate", "Calculs urinaires", "Cancer de la prostate", "Cancer de la vessie", "Cancer du rein", "Chirurgie des testicules de l’adulte", "Chirurgie des testicules de l’enfant et de l’adolescent"],
        "Tête et cou": ["Amygdales et végétations", "Audition", "Cancer ORL", "Chirurgie dentaire et orale de l’adulte", "Chirurgie dentaire et orale de l’enfant et de l’adolescent", "Chirurgie du nez et des sinus", "Chirurgie maxillo-faciale", "Glandes salivaires"],
        "Neurologie": ["Accidents vasculaires cérébraux", "Epilepsie de l’adulte", "Epilepsie de l’enfant et de l’adolescent", "Maladie de Parkinson"],
        "Cancerologie": ["Cancer de la thyroïde", "Cancer des os de l’enfant et de l’adolescent", "Cancer du poumon", "Cancers de la peau", "Chirurgie des cancers osseux de l'adulte", "Chirurgie des sarcomes des tissus mous", "Leucémie de l'adulte", "Leucémie de l'enfant et de l’adolescent", "Lymphome-myélome de l’adulte", "Tumeurs du cerveau de l'adulte"],
        "Diabète": ["Diabète de l'adulte", "Diabète de l'enfant et de l’adolescent"]
    }

category_variations = {
            "maternités": ["maternité", "maternités", "accouchement", "accouchements", "grossesse", "enceinte", "bébé", "nouveau-né"],
            "gynécologie et cancers de la femme": ["gynécologie", "gynéco", "femme", "femmes", "utérus", "ovaires", "sein", "seins", "gynécologique"],
            "ophtalmologie": ["ophtalmologie", "ophtalmologique", "yeux", "œil", "oeil", "vision", "vue", "regard", "ophtalmo"],
            "appareil digestif": ["digestif", "digestion", "intestin", "intestins", "estomac", "ventre", "abdomen", "abdominal", "gastro"],
            "tête et cou": ["tête", "cou", "orl", "oreille", "nez", "gorge", "bouche", "dents", "dentaire", "maxillo"],
            "veines et artères": ["veines", "artères", "vasculaire", "circulation", "sang", "vaisseaux", "cardio-vasculaire"],
            "orthopédie": ["orthopédie", "orthopédique", "os", "articulation", "articulations", "squelette", "fracture", "prothèse", "prothèses"],
            "cardiologie": ["cardiologie", "cardiaque", "cardiaques", "cœur", "coeur", "cardio", "circulation", "tension", "artérielle"],
            "urologie": ["urologie", "urologique", "urine", "vessie", "rein", "reins", "prostate", "urinaire"],
            "psychiatrie": ["psychiatrie", "psychiatrique", "mental", "mentale", "psychologique", "dépression", "anxiété", "stress"],
            "cancerologie": ["cancérologie", "cancero", "oncologie", "oncologique", "tumeur", "tumeurs", "métastase", "chimiothérapie"],
            "neurologie": ["neurologie", "neurologique", "neuro", "cerveau", "système nerveux", "parkinson", "alzheimer", "avc"],
            "diabète": ["diabète", "diabétique", "sucre", "glycémie", "insuline", "endocrinologie"]
        }

general_cancer_terms = [
        "cancer",
        "cancers", 
        "le cancer",
        "les cancers",
        "du cancer",
        "des cancers",
        "pour cancer",
        "pour le cancer",
        "pour les cancers",
        "concernant le cancer",
        "concernant les cancers",
        "sur le cancer",
        "sur les cancers",
        "au niveau du cancer",
        "au niveau des cancers",
        "question cancer",
        "question cancers"
    ]