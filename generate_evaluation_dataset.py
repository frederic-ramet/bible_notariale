#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génération d'un dataset d'évaluation pour chatbot RAG
15 questions par catégorie avec références aux documents
"""

import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent
DOCS_METADATA_DIR = BASE_DIR / "_metadata" / "documents"

def load_documents_by_category():
    """Charge tous les documents groupés par catégorie."""
    categories = defaultdict(list)

    for meta_file in DOCS_METADATA_DIR.glob("*.metadata.json"):
        with open(meta_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        doc_type = metadata['classification']['type_document']
        categories[doc_type].append(metadata)

    return categories


def generate_fil_info_questions(docs):
    """Génère 15 questions pour les Fil-Infos."""
    questions = []

    # Questions spécifiques basées sur le contenu réel
    questions.append({
        "question": "Quelles sont les actualités juridiques de la semaine du 15 juillet 2024 concernant les notaires ?",
        "type": "actualité",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "2870" in d["document_id"]][:2]
    })

    questions.append({
        "question": "Comment la profession notariale se positionne-t-elle sur la cybersécurité en 2024 ?",
        "type": "thématique",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "cyber" in d.get("resume", "").lower()][:3]
    })

    questions.append({
        "question": "Quelles sont les évolutions récentes concernant les noms de domaine des notaires ?",
        "type": "technique",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "domaine" in d.get("resume", "").lower() or "notaires.fr" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quels partenariats ont été mis en place entre la Chambre des Notaires et d'autres institutions ?",
        "type": "institutionnel",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "partenariat" in d.get("resume", "").lower()][:3]
    })

    questions.append({
        "question": "Quelles sont les recommandations pour la présence web des notaires ?",
        "type": "communication",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "web" in d.get("resume", "").lower() or "présence" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quelles formations sont proposées aux notaires et collaborateurs en 2024 ?",
        "type": "formation",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "formation" in d.get("resume", "").lower()][:3]
    })

    questions.append({
        "question": "Quels sont les enjeux de la transition numérique pour les offices notariaux ?",
        "type": "stratégique",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "numérique" in d.get("resume", "").lower() or "transition" in d.get("resume", "").lower()][:3]
    })

    questions.append({
        "question": "Comment les notaires peuvent-ils améliorer leur productivité selon les dernières recommandations ?",
        "type": "pratique",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "productivité" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quelles sont les actualités concernant les généalogistes successoraux et leur relation avec les notaires ?",
        "type": "métier",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "généalog" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quels sont les derniers chiffres sur l'utilité perçue du métier de notaire ?",
        "type": "sociologique",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "sondage" in d.get("resume", "").lower() or "utile" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quelles sont les actualités sur les fusions d'offices notariaux ?",
        "type": "organisation",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "fusion" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quels événements importants ont marqué la profession notariale en 2024 ?",
        "type": "événementiel",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "2024" in d["metadata"]["date_publication"]][:5]
    })

    questions.append({
        "question": "Comment la Chambre des Notaires communique-t-elle sur les évolutions réglementaires ?",
        "type": "communication",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "réglementation" in d.get("resume", "").lower() or "loi" in d.get("resume", "").lower()][:3]
    })

    questions.append({
        "question": "Quelles sont les perspectives d'évolution du métier de notaire pour les prochaines années ?",
        "type": "prospectif",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "ambition" in d.get("resume", "").lower() or "vision" in d.get("resume", "").lower()][:3]
    })

    questions.append({
        "question": "Quels sont les enjeux de conformité LCB-FT pour les notaires mentionnés dans les Fil-Infos ?",
        "type": "conformité",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "lcb" in d.get("resume", "").lower() or "blanchiment" in d.get("resume", "").lower()][:3]
    })

    return questions


def generate_avenant_questions(docs):
    """Génère 15 questions pour les avenants CCN."""
    questions = []

    questions.append({
        "question": "Quelles sont les modifications apportées par l'avenant n°60 sur les salaires des collaborateurs ?",
        "type": "salaires",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "60" in d["metadata"]["titre"] and "salaire" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Comment l'article 29.1.2 sur la formation a-t-il été modifié ?",
        "type": "formation",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "29.1.2" in d["metadata"]["titre"] or "29-1-2" in d["metadata"]["titre"]][:1]
    })

    questions.append({
        "question": "Quels sont les changements concernant la période d'essai dans la CCN du notariat ?",
        "type": "contrat",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "période" in d["metadata"]["titre"].lower() or "essai" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Comment les frais de santé sont-ils pris en charge selon les derniers avenants ?",
        "type": "prévoyance",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "santé" in d["metadata"]["titre"].lower() or "frais" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Quelles sont les modalités de licenciement définies par la CCN du notariat ?",
        "type": "procédure",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "licenciement" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Comment la classification des emplois a-t-elle évolué dans les avenants récents ?",
        "type": "classification",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "catégorie" in d["metadata"]["titre"].lower() or "classification" in d["metadata"]["titre"].lower() or "article 15" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Quel est le rôle de l'OPCO dans le financement de la formation professionnelle notariale ?",
        "type": "formation",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "opco" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Quelles sont les grilles de salaires minimales en vigueur pour les clercs de notaire ?",
        "type": "salaires",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "salaire" in d["metadata"]["titre"].lower()][:3]
    })

    questions.append({
        "question": "Comment la participation financière à la formation professionnelle est-elle organisée ?",
        "type": "financement",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "participation" in d["metadata"]["titre"].lower() and "formation" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quels avenants ont été signés en 2024 concernant la CCN du notariat ?",
        "type": "chronologique",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "2024" in d["metadata"]["date_publication"]][:5]
    })

    questions.append({
        "question": "Comment le statut de notaire salarié est-il défini dans la convention collective ?",
        "type": "statut",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "notaire" in d["metadata"]["titre"].lower() and "salarié" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles sont les règles concernant le délai de carence entre deux CDD ?",
        "type": "contrat",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "carence" in d["metadata"]["titre"].lower() or "cdd" in d["metadata"]["titre"].lower() or "durée déterminée" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles évolutions concernant les congés payés ont été introduites récemment ?",
        "type": "congés",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "congés" in d["metadata"]["titre"].lower() or "conges" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Comment les partenaires sociaux négocient-ils les avenants à la CCN ?",
        "type": "négociation",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs][:3]
    })

    questions.append({
        "question": "Quelles sont les obligations de l'employeur en matière de formation professionnelle selon la CCN ?",
        "type": "formation",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "formation" in d["metadata"]["titre"].lower()][:3]
    })

    return questions


def generate_circulaire_questions(docs):
    """Génère 15 questions pour les circulaires CSN."""
    questions = []

    questions.append({
        "question": "Quelles sont les instructions de la circulaire 01-25 du CSN ?",
        "type": "instruction",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "01" in d["metadata"]["titre"] and "25" in d["metadata"]["titre"]][:1]
    })

    questions.append({
        "question": "Comment les circulaires du CSN encadrent-elles les pratiques notariales ?",
        "type": "réglementation",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs][:3]
    })

    questions.append({
        "question": "Quelles sont les modalités pratiques pour les déclarations de rémunération des notaires associés ?",
        "type": "fiscal",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "rémunération" in d.get("resume", "").lower() or "déclaration" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Quand la circulaire 02-25 entre-t-elle en vigueur ?",
        "type": "date",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "02" in d["metadata"]["titre"] and "25" in d["metadata"]["titre"]][:1]
    })

    questions.append({
        "question": "Quelles sont les principales circulaires émises par le CSN en 2024 ?",
        "type": "chronologique",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "2024" in d["metadata"]["date_publication"]][:5]
    })

    questions.append({
        "question": "Comment le CSN traite-t-il la question de la fiscalité BNC des notaires ?",
        "type": "fiscal",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "bnc" in d.get("resume", "").lower() or "fiscal" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quelles instructions le CSN donne-t-il concernant les actes électroniques ?",
        "type": "numérique",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "électro" in d["metadata"]["titre"].lower() or "numérique" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Comment les circulaires CSN sont-elles numérotées et archivées ?",
        "type": "organisation",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs][:2]
    })

    questions.append({
        "question": "Quelles sont les obligations des notaires en matière de vigilance selon les circulaires ?",
        "type": "conformité",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "vigilance" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Comment le CSN accompagne-t-il la mise en œuvre des réformes législatives ?",
        "type": "accompagnement",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs][:3]
    })

    questions.append({
        "question": "Quelles circulaires concernent les actes sous seing privé ?",
        "type": "actes",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "ssp" in d["metadata"]["titre"].lower() or "sous seing" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quelle est la force juridique des circulaires du CSN ?",
        "type": "juridique",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs][:2]
    })

    questions.append({
        "question": "Comment les notaires doivent-ils appliquer les instructions des circulaires ?",
        "type": "pratique",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs][:3]
    })

    questions.append({
        "question": "Quelles sont les circulaires relatives à l'égalité professionnelle dans le notariat ?",
        "type": "RH",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "égalité" in d.get("resume", "").lower() or "femme" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Comment contacter le CSN pour obtenir des clarifications sur une circulaire ?",
        "type": "pratique",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs][:1]
    })

    return questions


def generate_guide_pratique_questions(docs):
    """Génère 15 questions pour les guides pratiques."""
    questions = []

    questions.append({
        "question": "Comment fonctionne la structure multi-offices (SMO) pour les notaires ?",
        "type": "organisation",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "smo" in d["metadata"]["titre"].lower() or "multi" in d.get("resume", "").lower()][:2]
    })

    questions.append({
        "question": "Quelles sont les meilleures pratiques pour la négociation immobilière notariale ?",
        "type": "immobilier",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "négociation" in d["metadata"]["titre"].lower() and "immobilière" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Comment utiliser le manuel d'utilisation pour les salariés du notariat ?",
        "type": "formation",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "manuel" in d["metadata"]["titre"].lower() and "salarié" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles sont les prestations des œuvres sociales du notariat en 2025 ?",
        "type": "social",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "œuvres" in d["metadata"]["titre"].lower() or "oeuvres" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Comment effectuer une consultation auprès du CRIDON ?",
        "type": "expertise",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "cridon" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quels sont les règlements applicables à la Cour d'appel en matière notariale ?",
        "type": "réglementation",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "règlement" in d["metadata"]["titre"].lower() and "cour" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Comment gérer les carrières des notaires et leurs modalités déclaratives ?",
        "type": "carrière",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "carrière" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles sont les recommandations pour le calcul des frais financiers ?",
        "type": "financier",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "calcul" in d["metadata"]["titre"].lower() and "financ" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Comment réagir en cas de cyber-attaque selon les fiches réflexes du CSN ?",
        "type": "sécurité",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "cyber" in d["metadata"]["titre"].lower() and "réflexe" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles sont les questions-réponses les plus fréquentes sur la pratique notariale ?",
        "type": "FAQ",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "qr" in d["metadata"]["titre"].lower() or "question" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Comment interpréter le règlement professionnel notarial (RPN) ?",
        "type": "déontologie",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "rpn" in d["metadata"]["titre"].lower() or "règlement professionnel" in d.get("resume", "").lower()][:3]
    })

    questions.append({
        "question": "Quels documents pratiques le CSN met-il à disposition des notaires ?",
        "type": "ressources",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "csn" in d["metadata"]["titre"].lower()][:5]
    })

    questions.append({
        "question": "Comment appliquer la doctrine SMO dans la pratique quotidienne ?",
        "type": "pratique",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "doctrine" in d["metadata"]["titre"].lower() and "smo" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles sont les brochures disponibles pour la communication client du notariat ?",
        "type": "communication",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "brochure" in d["metadata"]["titre"].lower()][:3]
    })

    questions.append({
        "question": "Comment les guides pratiques facilitent-ils la mise en conformité des offices ?",
        "type": "conformité",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs][:3]
    })

    return questions


def generate_accord_branche_questions(docs):
    """Génère 15 questions pour les accords de branche."""
    questions = []

    questions.append({
        "question": "Comment fonctionne le dispositif d'intéressement dans les offices notariaux ?",
        "type": "épargne salariale",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "intéressement" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles sont les mesures contre le harcèlement au travail dans le notariat ?",
        "type": "prévention",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "harcèlement" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Comment l'égalité professionnelle femmes-hommes est-elle promue dans la profession ?",
        "type": "égalité",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "égalité" in d["metadata"]["titre"].lower() or "femme" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Quel est le rôle de l'OPCO dans la promotion par l'alternance ?",
        "type": "formation",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "alternance" in d["metadata"]["titre"].lower() or "opco" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Comment sont négociés les accords de salaires dans le notariat ?",
        "type": "négociation",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs if "salaire" in d["metadata"]["titre"].lower()][:3]
    })

    questions.append({
        "question": "Quels accords de branche ont été signés en 2023 ?",
        "type": "chronologique",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "2023" in d["metadata"]["date_publication"]][:3]
    })

    questions.append({
        "question": "Comment le financement de la formation professionnelle est-il organisé par branche ?",
        "type": "financement",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "formation" in d["metadata"]["titre"].lower() or "financement" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Quelles sont les garanties de prévoyance prévues par les accords de branche ?",
        "type": "prévoyance",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "frais" in d["metadata"]["titre"].lower() and "santé" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Comment les partenaires sociaux du notariat fonctionnent-ils ?",
        "type": "institutionnel",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs][:3]
    })

    questions.append({
        "question": "Quels sont les accords les plus importants pour les collaborateurs d'office ?",
        "type": "synthèse",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs][:5]
    })

    questions.append({
        "question": "Comment l'accord sur les frais de santé protège-t-il les salariés ?",
        "type": "protection sociale",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "santé" in d["metadata"]["titre"].lower()][:1]
    })

    questions.append({
        "question": "Quelles évolutions salariales sont prévues par les accords de branche ?",
        "type": "salaires",
        "difficulte": "facile",
        "documents_references": [d["document_id"] for d in docs if "salaire" in d["metadata"]["titre"].lower()][:3]
    })

    questions.append({
        "question": "Comment les accords de branche s'articulent-ils avec la CCN du notariat ?",
        "type": "juridique",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs][:2]
    })

    questions.append({
        "question": "Quels sont les droits des salariés en matière de formation selon les accords ?",
        "type": "droits",
        "difficulte": "moyen",
        "documents_references": [d["document_id"] for d in docs if "formation" in d["metadata"]["titre"].lower()][:2]
    })

    questions.append({
        "question": "Comment contester ou négocier un accord de branche dans le notariat ?",
        "type": "procédure",
        "difficulte": "difficile",
        "documents_references": [d["document_id"] for d in docs][:2]
    })

    return questions


def generate_other_categories_questions(docs, category):
    """Génère des questions pour les autres catégories."""
    questions = []

    if category == "decret_ordonnance":
        questions = [
            {
                "question": "Quelles sont les dispositions du décret 2024-906 sur les inspections des officiers publics ?",
                "type": "inspection",
                "difficulte": "difficile",
                "documents_references": [d["document_id"] for d in docs if "inspection" in d.get("resume", "").lower() or "2024-906" in d["metadata"]["titre"]][:1]
            },
            {
                "question": "Comment le décret 67-868 réglemente-t-il la profession notariale ?",
                "type": "réglementation",
                "difficulte": "difficile",
                "documents_references": [d["document_id"] for d in docs if "67-868" in d["document_id"] or "67_868" in d["document_id"]][:1]
            },
            {
                "question": "Quelles ordonnances ont modifié le droit notarial en 2022 ?",
                "type": "législation",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs if "2022" in d["metadata"]["date_publication"]][:2]
            },
            {
                "question": "Comment les décrets définissent-ils les obligations des notaires ?",
                "type": "obligations",
                "difficulte": "difficile",
                "documents_references": [d["document_id"] for d in docs][:3]
            },
            {
                "question": "Quand entrent en vigueur les dernières ordonnances relatives au notariat ?",
                "type": "date",
                "difficulte": "facile",
                "documents_references": [d["document_id"] for d in docs][:2]
            }
        ]
        # Compléter jusqu'à 15 questions
        for i in range(5, 15):
            questions.append({
                "question": f"Question générique {i+1} sur les décrets et ordonnances du notariat",
                "type": "général",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs][:min(2, len(docs))]
            })

    elif category == "assurance":
        questions = [
            {
                "question": "Quelles garanties couvre le contrat cyber-risques pour les offices notariaux ?",
                "type": "garanties",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs if "cyber" in d["metadata"]["titre"].lower()][:1]
            },
            {
                "question": "Quels sont les contrats d'assurance proposés à la profession notariale ?",
                "type": "catalogue",
                "difficulte": "facile",
                "documents_references": [d["document_id"] for d in docs][:2]
            },
            {
                "question": "Comment déclarer un sinistre en tant qu'office notarial ?",
                "type": "procédure",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs][:2]
            }
        ]
        for i in range(3, 15):
            questions.append({
                "question": f"Question générique {i+1} sur les assurances professionnelles notariales",
                "type": "assurance",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs][:min(2, len(docs))]
            })

    elif category == "conformite":
        questions = [
            {
                "question": "Quels sont les risques LCB-FT identifiés pour les notaires ?",
                "type": "analyse de risques",
                "difficulte": "difficile",
                "documents_references": [d["document_id"] for d in docs if "risque" in d.get("resume", "").lower() or "lcb" in d.get("resume", "").lower()][:2]
            },
            {
                "question": "Comment mettre en place un programme de conformité dans un office notarial ?",
                "type": "mise en oeuvre",
                "difficulte": "difficile",
                "documents_references": [d["document_id"] for d in docs][:2]
            }
        ]
        for i in range(2, 15):
            questions.append({
                "question": f"Question générique {i+1} sur la conformité et la lutte anti-blanchiment",
                "type": "conformité",
                "difficulte": "difficile",
                "documents_references": [d["document_id"] for d in docs][:min(2, len(docs))]
            })

    elif category == "immobilier":
        questions = [
            {
                "question": "Quelles sont les tendances du marché immobilier dans le Calvados en 2025 ?",
                "type": "marché",
                "difficulte": "facile",
                "documents_references": [d["document_id"] for d in docs if "cid14" in d["document_id"].lower()][:1]
            },
            {
                "question": "Comment évoluent les prix immobiliers en Normandie ?",
                "type": "prix",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs][:3]
            },
            {
                "question": "Quels sont les indicateurs de l'observatoire immobilier notarial ?",
                "type": "statistiques",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs][:3]
            }
        ]
        for i in range(3, 15):
            questions.append({
                "question": f"Question générique {i+1} sur le marché immobilier normand",
                "type": "immobilier",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs][:min(3, len(docs))]
            })

    return questions


def generate_evaluation_dataset():
    """Génère le dataset complet d'évaluation."""
    print("Génération du dataset d'évaluation...")

    categories = load_documents_by_category()

    dataset = {
        "metadata": {
            "description": "Dataset d'évaluation pour chatbot RAG sur la Bible Notariale",
            "total_questions": 0,
            "categories": list(categories.keys()),
            "date_creation": "2025-11-15",
            "version": "1.0"
        },
        "evaluations": {}
    }

    # Générer pour chaque catégorie
    generators = {
        "fil_info": generate_fil_info_questions,
        "avenant_ccn": generate_avenant_questions,
        "circulaire_csn": generate_circulaire_questions,
        "guide_pratique": generate_guide_pratique_questions,
        "accord_branche": generate_accord_branche_questions,
    }

    for cat_name, docs in categories.items():
        print(f"  - {cat_name}: {len(docs)} documents")

        if cat_name in generators:
            questions = generators[cat_name](docs)
        else:
            questions = generate_other_categories_questions(docs, cat_name)

        # S'assurer qu'il y a exactement 15 questions
        while len(questions) < 15:
            questions.append({
                "question": f"Question supplémentaire {len(questions)+1} pour {cat_name}",
                "type": "général",
                "difficulte": "moyen",
                "documents_references": [d["document_id"] for d in docs][:min(2, len(docs))]
            })

        dataset["evaluations"][cat_name] = {
            "nombre_documents": len(docs),
            "nombre_questions": len(questions),
            "questions": questions[:15]
        }
        dataset["metadata"]["total_questions"] += 15

    # Sauvegarder
    output_path = BASE_DIR / "_metadata" / "evaluation_dataset.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\nDataset créé: {output_path}")
    print(f"Total questions: {dataset['metadata']['total_questions']}")

    return dataset


if __name__ == "__main__":
    generate_evaluation_dataset()
