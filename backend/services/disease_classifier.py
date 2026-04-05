"""
Disease Classifier – categorises AI diagnosis output as
spreadable (flu-like / other) or non-spreadable so that only
contagious cases appear on the community outbreak map.

Migrated from hackathon_project1.
"""


class DiseaseClassifier:
    # Spreadable diseases (flu-like) – RED on map
    FLU_LIKE_DISEASES = [
        "influenza", "flu", "covid", "covid-19", "sars-cov-2",
        "common cold", "cold", "respiratory infection", "bronchitis",
        "pneumonia", "whooping cough", "rsv", "throat infection",
        "breathing issues", "body aches", "fever", "cough", "sore throat",
        "runny nose", "congestion", "sinus infection", "flu-like",
    ]

    # Other spreadable diseases – ORANGE on map
    OTHER_SPREADABLE = [
        "strep throat", "staphylococcus", "e. coli", "salmonella",
        "hepatitis", "tuberculosis", "measles", "chickenpox",
        "meningitis", "conjunctivitis", "pink eye", "norovirus",
        "skin infection", "rash", "fungal infection", "bacterial infection",
        "stomach flu", "gastroenteritis", "food poisoning",
    ]

    # Non-spreadable conditions – NOT shown on map
    NON_SPREADABLE = [
        "allergy", "allergies", "migraine", "headache", "asthma",
        "diabetes", "hypertension", "arthritis", "back pain",
        "anxiety", "depression", "insomnia", "constipation",
        "indigestion", "acidity", "dehydration", "fatigue",
        "acne", "skin roughness", "dryness", "swelling", "eczema",
        "psoriasis", "dermatitis", "hair loss", "dandruff",
    ]

    @classmethod
    def classify_disease(cls, ai_response: str | None) -> dict:
        """Return category, spreadable flag, marker colour, and disease type."""
        if not ai_response:
            return {
                "category": "unknown",
                "spreadable": False,
                "marker_color": "gray",
                "disease_type": "unknown",
            }

        lower = ai_response.lower()

        for disease in cls.FLU_LIKE_DISEASES:
            if disease in lower:
                return {
                    "category": "flu_like",
                    "spreadable": True,
                    "marker_color": "red",
                    "disease_type": "flu-like spreadable",
                }

        for disease in cls.OTHER_SPREADABLE:
            if disease in lower:
                return {
                    "category": "other_spreadable",
                    "spreadable": True,
                    "marker_color": "orange",
                    "disease_type": "other spreadable",
                }

        for condition in cls.NON_SPREADABLE:
            if condition in lower:
                return {
                    "category": "non_spreadable",
                    "spreadable": False,
                    "marker_color": "green",
                    "disease_type": "non-spreadable",
                }

        return {
            "category": "unknown",
            "spreadable": False,
            "marker_color": "gray",
            "disease_type": "unknown",
        }
