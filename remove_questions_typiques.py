#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suppression des questions_typiques génériques des métadonnées
Les questions génériques ne sont pas assez discriminantes pour le matching RAG
"""

import os
import json
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent
METADATA_DIR = BASE_DIR / "_metadata"
DOCS_METADATA_DIR = METADATA_DIR / "documents"
INDEX_FILE = METADATA_DIR / "index_complet.json"


def remove_questions_from_metadata_file(filepath):
    """
    Supprime le champ questions_typiques d'un fichier metadata.json
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Supprimer le champ questions_typiques s'il existe
    if 'questions_typiques' in metadata:
        del metadata['questions_typiques']

        # Sauvegarder
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return True

    return False


def main():
    """
    Fonction principale
    """
    print(f"\n🚀 Suppression des questions_typiques génériques...")
    print(f"📁 Répertoire metadata : {DOCS_METADATA_DIR}")

    # Lister tous les fichiers metadata.json
    metadata_files = list(DOCS_METADATA_DIR.glob("*.metadata.json"))
    print(f"📄 {len(metadata_files)} fichiers metadata trouvés\n")

    # Supprimer questions_typiques de tous les fichiers
    removed_count = 0
    for i, filepath in enumerate(metadata_files, 1):
        if i % 50 == 0:
            print(f"  Traitement en cours : {i}/{len(metadata_files)}...")

        if remove_questions_from_metadata_file(filepath):
            removed_count += 1

    print(f"\n✅ {removed_count} fichiers modifiés (champ questions_typiques supprimé)")

    # Mettre à jour l'index complet
    print(f"\n🔄 Mise à jour de l'index complet...")
    if INDEX_FILE.exists():
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        # Supprimer questions_typiques de chaque document dans l'index
        modified_index_count = 0
        for doc in index_data.get('documents', []):
            if 'questions_typiques' in doc:
                del doc['questions_typiques']
                modified_index_count += 1

        # Sauvegarder l'index mis à jour
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Index complet mis à jour : {modified_index_count} documents modifiés")
        print(f"   Fichier : {INDEX_FILE}")

    print(f"\n🎉 Suppression terminée avec succès !")
    print(f"\n📊 Résumé :")
    print(f"   - Fichiers metadata modifiés : {removed_count}")
    print(f"   - Documents dans l'index modifiés : {modified_index_count}")
    print(f"\n💡 Les questions_typiques génériques ont été supprimées.")
    print(f"   → Amélioration du matching RAG en retirant le bruit générique\n")


if __name__ == '__main__':
    main()
