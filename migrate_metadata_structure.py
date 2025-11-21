#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration de la structure des métadonnées
Transforme l'ancienne structure vers la nouvelle :
- type_document → sources_document
- Ajout type_document (catégorie business)
- categories_metier → domaines_metier
- categorie_metier_principale → domaine_metier_principal
- Extraction thematiques du vocabulaire_specifique
- Suppression IMMOBILIER, PROCEDURE, FISCAL_SUCCESSION
"""

import os
import json
from pathlib import Path
from collections import Counter

# Configuration
BASE_DIR = Path(__file__).parent
METADATA_DIR = BASE_DIR / "_metadata"
DOCS_METADATA_DIR = METADATA_DIR / "documents"
INDEX_FILE = METADATA_DIR / "index_complet.json"

# Mapping sources_document → type_document
SOURCE_TO_TYPE_MAPPING = {
    'circulaire_csn': 'Directives CSN',
    'guide_pratique': 'Directives CSN',
    'avenant_ccn': 'Convention collectives Notariat',
    'accord_branche': 'Convention collectives Notariat',
    'fil_info': 'Actualités',
    'decret_ordonnance': 'Lois et règlements',
    'assurance': 'Assurances',
    'conformite': 'Directives CSN',  # Par défaut
    'formation': 'Actualités',  # Par défaut
}

# Domaines valides (nouveaux)
VALID_DOMAINS = {'RH', 'DEONTOLOGIE', 'ASSURANCES'}

# Domaines supprimés
REMOVED_DOMAINS = {'IMMOBILIER', 'PROCEDURE', 'FISCAL_SUCCESSION'}


def extract_thematiques(metadata):
    """
    Extrait les thématiques du vocabulaire_specifique
    """
    thematiques = []
    vocab = metadata.get('vocabulaire_specifique', [])

    for item in vocab:
        terme = item.get('terme', '')
        if terme:
            # Nettoyer et ajouter le terme
            terme_clean = terme.strip().lower()
            if terme_clean and terme_clean not in thematiques:
                thematiques.append(terme_clean)

    return thematiques[:10]  # Max 10 thématiques


def migrate_metadata_file(filepath):
    """
    Migre un fichier metadata.json vers la nouvelle structure
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    classification = metadata.get('classification', {})

    # 1. Sauvegarder l'ancien type_document comme sources_document
    old_type = classification.get('type_document', '')
    classification['sources_document'] = old_type

    # 2. Définir le nouveau type_document (catégorie business)
    new_type = SOURCE_TO_TYPE_MAPPING.get(old_type, 'Actualités')
    classification['type_document'] = new_type

    # 3. Migrer categories_metier → domaines_metier
    old_categories = classification.get('categories_metier', [])

    # Filtrer les domaines supprimés et ne garder que les valides
    new_domains = [cat for cat in old_categories if cat in VALID_DOMAINS]

    # Si plus aucun domaine, mettre DEONTOLOGIE par défaut
    if not new_domains:
        new_domains = ['DEONTOLOGIE']

    classification['domaines_metier'] = new_domains

    # 4. Migrer categorie_metier_principale → domaine_metier_principal
    old_principale = classification.get('categorie_metier_principale', '')

    # Si l'ancienne principale est supprimée, prendre le premier domaine valide
    if old_principale in REMOVED_DOMAINS:
        new_principale = new_domains[0]
    elif old_principale in VALID_DOMAINS:
        new_principale = old_principale
    else:
        new_principale = new_domains[0]

    classification['domaine_metier_principal'] = new_principale

    # 5. Extraire les thématiques
    thematiques = extract_thematiques(metadata)
    if thematiques:
        classification['thematiques'] = thematiques

    # 6. Supprimer les anciens champs
    classification.pop('categories_metier', None)
    classification.pop('categorie_metier_principale', None)

    # Sauvegarder
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        'document_id': metadata.get('document_id', ''),
        'old_type': old_type,
        'new_type': new_type,
        'sources': old_type,
        'old_domains': old_categories,
        'new_domains': new_domains,
        'domain_principal': new_principale,
        'thematiques_count': len(thematiques)
    }


def migrate_index_complet():
    """
    Migre l'index complet
    """
    if not INDEX_FILE.exists():
        print(f"⚠️  Index complet non trouvé : {INDEX_FILE}")
        return

    print(f"\n📄 Migration de l'index complet...")

    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    documents = index_data.get('documents', [])
    migrated_count = 0

    for doc in documents:
        classification = doc.get('classification', {})

        # 1. Sauvegarder l'ancien type_document comme sources_document
        old_type = classification.get('type_document', '')
        classification['sources_document'] = old_type

        # 2. Définir le nouveau type_document
        new_type = SOURCE_TO_TYPE_MAPPING.get(old_type, 'Actualités')
        classification['type_document'] = new_type

        # 3. Migrer categories_metier → domaines_metier
        old_categories = classification.get('categories_metier', [])
        new_domains = [cat for cat in old_categories if cat in VALID_DOMAINS]

        if not new_domains:
            new_domains = ['DEONTOLOGIE']

        classification['domaines_metier'] = new_domains

        # 4. Migrer categorie_metier_principale → domaine_metier_principal
        old_principale = classification.get('categorie_metier_principale', '')

        if old_principale in REMOVED_DOMAINS:
            new_principale = new_domains[0]
        elif old_principale in VALID_DOMAINS:
            new_principale = old_principale
        else:
            new_principale = new_domains[0]

        classification['domaine_metier_principal'] = new_principale

        # 5. Extraire thématiques
        thematiques = extract_thematiques(doc)
        if thematiques:
            classification['thematiques'] = thematiques

        # 6. Supprimer les anciens champs
        classification.pop('categories_metier', None)
        classification.pop('categorie_metier_principale', None)

        migrated_count += 1

    # Sauvegarder l'index mis à jour
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Index complet migré : {migrated_count} documents")


def generate_migration_report(results):
    """
    Génère un rapport de migration
    """
    print("\n" + "="*80)
    print("RAPPORT DE MIGRATION DES MÉTADONNÉES")
    print("="*80 + "\n")

    total = len(results)
    print(f"📊 Total de documents migrés : {total}\n")

    # Répartition par type_document (nouveau)
    print("📈 RÉPARTITION PAR TYPE DE DOCUMENT (nouveau)")
    print("-" * 80)
    type_count = Counter(r['new_type'] for r in results)
    for type_doc, count in sorted(type_count.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total) * 100
        print(f"  {type_doc:40s} : {count:3d} documents ({pct:5.1f}%)")

    # Répartition par sources_document
    print(f"\n📋 RÉPARTITION PAR SOURCES_DOCUMENT")
    print("-" * 80)
    source_count = Counter(r['sources'] for r in results)
    for source, count in sorted(source_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source:40s} : {count:3d} documents")

    # Répartition par domaine principal
    print(f"\n🏷️  RÉPARTITION PAR DOMAINE MÉTIER PRINCIPAL")
    print("-" * 80)
    domain_count = Counter(r['domain_principal'] for r in results)
    for domain, count in sorted(domain_count.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total) * 100
        print(f"  {domain:40s} : {count:3d} documents ({pct:5.1f}%)")

    # Documents avec domaines supprimés
    docs_with_removed = [r for r in results if any(d in REMOVED_DOMAINS for d in r['old_domains'])]
    print(f"\n🗑️  Documents ayant perdu des domaines supprimés : {len(docs_with_removed)}")

    if docs_with_removed:
        for r in docs_with_removed[:10]:  # Premiers 10
            old = ', '.join(r['old_domains'])
            new = ', '.join(r['new_domains'])
            print(f"  - {r['document_id'][:50]:50s}")
            print(f"    Avant: [{old}] → Après: [{new}]")

    # Statistiques thématiques
    with_themes = [r for r in results if r['thematiques_count'] > 0]
    print(f"\n🏷️  Documents avec thématiques : {len(with_themes)}/{total}")

    print("\n" + "="*80)
    print(f"✅ Migration terminée avec succès")
    print("="*80 + "\n")


def main():
    """
    Fonction principale
    """
    print(f"\n🚀 Démarrage de la migration des métadonnées...")
    print(f"📁 Répertoire metadata : {DOCS_METADATA_DIR}")

    # Lister tous les fichiers metadata.json
    metadata_files = list(DOCS_METADATA_DIR.glob("*.metadata.json"))
    print(f"📄 {len(metadata_files)} fichiers metadata trouvés\n")

    # Migrer tous les fichiers
    results = []
    for i, filepath in enumerate(metadata_files, 1):
        if i % 50 == 0:
            print(f"  Traitement en cours : {i}/{len(metadata_files)}...")

        result = migrate_metadata_file(filepath)
        results.append(result)

    print(f"\n✅ {len(results)} fichiers migrés")

    # Migrer l'index complet
    migrate_index_complet()

    # Générer le rapport
    generate_migration_report(results)

    # Sauvegarder le rapport en JSON
    report_file = METADATA_DIR / "migration_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'migration_date': str(Path(__file__).stat().st_mtime),
            'total_documents': len(results),
            'results': results,
            'statistics': {
                'by_new_type': dict(Counter(r['new_type'] for r in results)),
                'by_source': dict(Counter(r['sources'] for r in results)),
                'by_domain': dict(Counter(r['domain_principal'] for r in results)),
                'removed_domains_count': len([r for r in results if any(d in REMOVED_DOMAINS for d in r['old_domains'])])
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"📊 Rapport de migration sauvegardé : {report_file}")
    print(f"\n🎉 Migration terminée avec succès !\n")


if __name__ == '__main__':
    main()
