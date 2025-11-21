#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enrichissement des métadonnées avec catégories métier
Ajout du mapping type_document → categories_metier pour le routing du chatbot
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent
METADATA_DIR = BASE_DIR / "_metadata"
DOCS_METADATA_DIR = METADATA_DIR / "documents"
INDEX_FILE = METADATA_DIR / "index_complet.json"

# Mapping des types de documents vers catégories métier
TYPE_TO_CATEGORIES = {
    'circulaire_csn': ['DEONTOLOGIE'],
    'avenant_ccn': ['RH'],
    'accord_branche': ['RH'],
    'fil_info': ['DEONTOLOGIE'],  # Par défaut, sera affiné par analyse
    'guide_pratique': ['DEONTOLOGIE'],  # Par défaut, sera affiné par analyse
    'decret_ordonnance': ['DEONTOLOGIE'],
    'assurance': ['ASSURANCES'],
    'conformite': ['DEONTOLOGIE'],
    'formation': ['DEONTOLOGIE'],  # Par défaut, sera affiné par analyse
}

# Mots-clés pour l'affinage des catégories
KEYWORDS_TO_CATEGORY = {
    'DEONTOLOGIE': [
        'déontologie', 'éthique', 'discipline', 'secret professionnel',
        'rpn', 'code de déontologie', 'obligations professionnelles',
        'serment', 'missions du notaire', 'responsabilité professionnelle',
        'lcb-ft', 'tracfin', 'blanchiment', 'conformité', 'médiation',
        'inspection', 'contrôle', 'normes professionnelles', 'règlement intérieur'
    ],
    'RH': [
        'ccn', 'salaire', 'formation', 'opco', 'clerc', 'emploi',
        'rémunération', 'avenant', 'convention collective', 'idcc',
        'embauche', 'licenciement', 'contrat de travail', 'grille salariale',
        'prévoyance', 'retraite', 'congés', 'classification professionnelle',
        'contrats', 'temps de travail', 'personnel'
    ],
    'ASSURANCES': [
        'assurance', 'rcp', 'cyber', 'prévoyance', 'garantie',
        'responsabilité civile', 'sinistre', 'franchise', 'couverture',
        'police d\'assurance', 'risque professionnel', 'indemnisation',
        'cyber-risques', 'rc professionnelle', 'protection'
    ]
}

# Priorités pour déterminer la catégorie principale
CATEGORY_PRIORITY = {
    'DEONTOLOGIE': 1,
    'RH': 2,
    'ASSURANCES': 3,
}


def normalize_text(text):
    """Normalise le texte pour l'analyse"""
    if not text:
        return ""
    return text.lower().strip()


def detect_categories_from_content(metadata):
    """
    Détecte les catégories métier en analysant le contenu du document
    """
    # Textes à analyser
    titre = normalize_text(metadata.get('metadata', {}).get('titre', ''))
    resume = normalize_text(metadata.get('resume', ''))
    mots_cles = ' '.join(normalize_text(k) for k in metadata.get('mots_cles', []))
    domaines = ' '.join(normalize_text(d) for d in metadata.get('classification', {}).get('domaines_juridiques', []))

    # Combiner tous les textes
    full_text = f"{titre} {resume} {mots_cles} {domaines}"

    # Compter les occurrences de mots-clés par catégorie
    category_scores = defaultdict(int)

    for category, keywords in KEYWORDS_TO_CATEGORY.items():
        for keyword in keywords:
            # Recherche du mot-clé (avec regex pour matcher les mots entiers)
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, full_text))
            category_scores[category] += matches

    # Retourner les catégories avec score > 0, triées par score
    detected = [(cat, score) for cat, score in category_scores.items() if score > 0]
    detected.sort(key=lambda x: x[1], reverse=True)

    return [cat for cat, score in detected]


def enrich_metadata_file(filepath):
    """
    Enrichit un fichier metadata.json avec les catégories métier
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Type de document (sources_document dans la nouvelle structure)
    type_doc = metadata.get('classification', {}).get('sources_document', '')

    # Catégories de base selon le type
    base_categories = TYPE_TO_CATEGORIES.get(type_doc, ['DEONTOLOGIE'])

    # Affinage pour fil_info et guide_pratique
    if type_doc in ['fil_info', 'guide_pratique']:
        detected_categories = detect_categories_from_content(metadata)
        if detected_categories:
            # Remplacer les catégories par défaut par celles détectées
            base_categories = detected_categories[:3]  # Max 3 catégories

    # Dédupliquer tout en préservant l'ordre
    categories_metier = []
    seen = set()
    for cat in base_categories:
        if cat not in seen:
            categories_metier.append(cat)
            seen.add(cat)

    # Déterminer la catégorie principale (première de la liste, ou selon priorité)
    if categories_metier:
        # Trier par priorité si plusieurs
        sorted_cats = sorted(categories_metier, key=lambda x: CATEGORY_PRIORITY.get(x, 999))
        categorie_principale = sorted_cats[0]
    else:
        categories_metier = ['DEONTOLOGIE']
        categorie_principale = 'DEONTOLOGIE'

    # Ajouter les nouveaux champs
    if 'classification' not in metadata:
        metadata['classification'] = {}

    metadata['classification']['domaines_metier'] = categories_metier
    metadata['classification']['domaine_metier_principal'] = categorie_principale

    # Sauvegarder
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        'document_id': metadata.get('document_id', ''),
        'sources_document': type_doc,
        'domaines_metier': categories_metier,
        'domaine_principal': categorie_principale
    }


def generate_report(enrichment_results):
    """
    Génère un rapport sur l'enrichissement
    """
    print("\n" + "="*80)
    print("RAPPORT D'ENRICHISSEMENT DES CATÉGORIES MÉTIER")
    print("="*80 + "\n")

    # Stats globales
    total_docs = len(enrichment_results)
    print(f"📊 Total de documents enrichis : {total_docs}\n")

    # Répartition par domaine principal
    print("📈 RÉPARTITION PAR DOMAINE PRINCIPAL")
    print("-" * 80)
    dom_principale_count = Counter(r['domaine_principal'] for r in enrichment_results)
    for dom, count in sorted(dom_principale_count.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_docs) * 100
        print(f"  {dom:25s} : {count:3d} documents ({pct:5.1f}%)")

    # Répartition multi-domaines
    print(f"\n📊 RÉPARTITION MULTI-DOMAINES")
    print("-" * 80)
    all_domains = []
    for r in enrichment_results:
        all_domains.extend(r['domaines_metier'])
    dom_all_count = Counter(all_domains)
    for dom, count in sorted(dom_all_count.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_docs) * 100
        print(f"  {dom:25s} : {count:3d} occurrences ({pct:5.1f}%)")

    # Répartition par source de document
    print(f"\n📋 RÉPARTITION PAR SOURCE DE DOCUMENT")
    print("-" * 80)
    source_doc_count = Counter(r['sources_document'] for r in enrichment_results)
    for source_doc, count in sorted(source_doc_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source_doc:25s} : {count:3d} documents")

    # Documents avec plusieurs domaines
    multi_dom_docs = [r for r in enrichment_results if len(r['domaines_metier']) > 1]
    print(f"\n🔀 Documents multi-domaines : {len(multi_dom_docs)}")

    # Exemples par domaine principal
    print(f"\n📚 EXEMPLES PAR DOMAINE PRINCIPAL")
    print("-" * 80)
    for dom in sorted(CATEGORY_PRIORITY.keys(), key=lambda x: CATEGORY_PRIORITY[x]):
        examples = [r for r in enrichment_results if r['domaine_principal'] == dom]
        if examples:
            print(f"\n  {dom} ({len(examples)} documents):")
            for ex in examples[:3]:  # 3 premiers exemples
                doms_str = ', '.join(ex['domaines_metier'])
                print(f"    - {ex['document_id'][:60]:60s} [{doms_str}]")

    print("\n" + "="*80)
    print(f"✅ Enrichissement terminé avec succès")
    print("="*80 + "\n")


def main():
    """
    Fonction principale
    """
    print(f"\n🚀 Démarrage de l'enrichissement des catégories métier...")
    print(f"📁 Répertoire metadata : {DOCS_METADATA_DIR}")

    # Lister tous les fichiers metadata.json
    metadata_files = list(DOCS_METADATA_DIR.glob("*.metadata.json"))
    print(f"📄 {len(metadata_files)} fichiers metadata trouvés\n")

    # Enrichir tous les fichiers
    enrichment_results = []
    for i, filepath in enumerate(metadata_files, 1):
        if i % 50 == 0:
            print(f"  Traitement en cours : {i}/{len(metadata_files)}...")

        result = enrich_metadata_file(filepath)
        enrichment_results.append(result)

    print(f"\n✅ {len(enrichment_results)} fichiers enrichis")

    # Générer le rapport
    generate_report(enrichment_results)

    # Mettre à jour l'index complet
    print(f"🔄 Mise à jour de l'index complet...")
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        # Mettre à jour chaque document dans l'index
        for doc in index_data.get('documents', []):
            doc_id = doc.get('document_id', '')
            # Trouver le résultat correspondant
            matching_result = next((r for r in enrichment_results if r['document_id'] == doc_id), None)
            if matching_result:
                if 'classification' not in doc:
                    doc['classification'] = {}
                doc['classification']['domaines_metier'] = matching_result['domaines_metier']
                doc['classification']['domaine_metier_principal'] = matching_result['domaine_principal']

        # Sauvegarder l'index mis à jour
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Index complet mis à jour : {INDEX_FILE}")

    # Sauvegarder le rapport en JSON
    report_file = METADATA_DIR / "domaines_metier_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'total_documents': len(enrichment_results),
            'documents': [
                {
                    'document_id': r['document_id'],
                    'classification': {
                        'sources_document': r['sources_document'],
                        'domaines_metier': r['domaines_metier'],
                        'domaine_principal': r['domaine_principal']
                    }
                }
                for r in enrichment_results
            ],
            'statistics': {
                'by_main_domain': dict(Counter(r['domaine_principal'] for r in enrichment_results)),
                'by_source': dict(Counter(r['sources_document'] for r in enrichment_results)),
                'multi_domain_count': len([r for r in enrichment_results if len(r['domaines_metier']) > 1])
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"📊 Rapport JSON sauvegardé : {report_file}")
    print(f"\n🎉 Enrichissement terminé avec succès !\n")


if __name__ == '__main__':
    main()
