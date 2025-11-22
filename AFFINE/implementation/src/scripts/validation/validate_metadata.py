#!/usr/bin/env python3
"""
Validation des métadonnées enrichies

Ce script valide la structure et le contenu de l'index_complet.json
avant export vers Neo4j.

Usage:
    python3 validate_metadata.py --source ../../../../_metadata/index_complet.json

Validations effectuées :
    1. Structure JSON valide
    2. Tous les champs requis présents
    3. Classification 5 niveaux cohérente
    4. Vocabulaire spécifique bien formé
    5. Pas de valeurs nulles ou vides dans champs critiques
    6. Domaines métier valides (RH, DEONTOLOGIE, ASSURANCES uniquement)
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


class MetadataValidator:
    """
    Valide les métadonnées enrichies
    """

    # Valeurs autorisées
    VALID_DOMAINS = ['RH', 'DEONTOLOGIE', 'ASSURANCES']

    VALID_TYPES = [
        'Directives CSN',
        'Convention collectives Notariat',
        'Actualités',
        'Lois et règlements',
        'Assurances'
    ]

    VALID_SOURCES = [
        'circulaire_csn',
        'guide_pratique',
        'avenant_ccn',
        'accord_branche',
        'fil_info',
        'decret_ordonnance',
        'assurance',
        'conformite',
        'formation'
    ]

    def __init__(self, strict: bool = True):
        """
        Args:
            strict: Mode strict (erreur si warning) ou non
        """
        self.strict = strict
        self.errors = []
        self.warnings = []

    def validate(self, index_path: str) -> Tuple[bool, List[str], List[str]]:
        """
        Valide un fichier index_complet.json

        Returns:
            (success, errors, warnings)
        """

        self.errors = []
        self.warnings = []

        # 1. Charger JSON
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"❌ JSON invalide : {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"❌ Fichier introuvable : {index_path}")
            return False, self.errors, self.warnings

        # 2. Vérifier structure globale
        if 'documents' not in index:
            self.errors.append("❌ Clé 'documents' manquante dans l'index")
            return False, self.errors, self.warnings

        documents = index['documents']

        print(f"\n🔍 Validation de {len(documents)} documents...")

        # 3. Valider chaque document
        for i, doc in enumerate(documents):
            doc_id = doc.get('document_id', f'document_{i}')
            self._validate_document(doc, doc_id)

        # 4. Résumé
        success = len(self.errors) == 0

        if not success or (self.strict and len(self.warnings) > 0):
            success = False

        return success, self.errors, self.warnings

    def _validate_document(self, doc: Dict, doc_id: str):
        """
        Valide un document
        """

        # Champs requis
        required_fields = ['document_id', 'fichier', 'classification']

        for field in required_fields:
            if field not in doc:
                self.errors.append(f"❌ {doc_id} : Champ requis manquant : {field}")

        # Valider classification
        if 'classification' in doc:
            self._validate_classification(doc['classification'], doc_id)

        # Valider vocabulaire
        if 'vocabulaire_specifique' in doc:
            self._validate_vocabulaire(doc['vocabulaire_specifique'], doc_id)

    def _validate_classification(self, classification: Dict, doc_id: str):
        """
        Valide la classification 5 niveaux
        """

        # 1. Type de document
        type_doc = classification.get('type_document')
        if not type_doc:
            self.warnings.append(f"⚠️  {doc_id} : type_document vide")
        elif type_doc not in self.VALID_TYPES:
            self.errors.append(f"❌ {doc_id} : type_document invalide : {type_doc}")

        # 2. Source document
        source_doc = classification.get('sources_document')
        if not source_doc:
            self.warnings.append(f"⚠️  {doc_id} : sources_document vide")
        elif source_doc not in self.VALID_SOURCES:
            self.warnings.append(f"⚠️  {doc_id} : sources_document inconnue : {source_doc}")

        # 3. Domaines métier
        domaines = classification.get('domaines_metier', [])
        if not domaines:
            self.errors.append(f"❌ {doc_id} : domaines_metier vide (au moins 1 requis)")
        else:
            for domaine in domaines:
                if domaine not in self.VALID_DOMAINS:
                    self.errors.append(f"❌ {doc_id} : domaine invalide : {domaine}")

        # 4. Domaine principal
        domaine_principal = classification.get('domaine_metier_principal')
        if not domaine_principal:
            self.warnings.append(f"⚠️  {doc_id} : domaine_metier_principal vide")
        elif domaine_principal not in self.VALID_DOMAINS:
            self.errors.append(f"❌ {doc_id} : domaine_metier_principal invalide : {domaine_principal}")
        elif domaine_principal not in domaines:
            self.errors.append(f"❌ {doc_id} : domaine_metier_principal ({domaine_principal}) pas dans domaines_metier")

        # 5. Thématiques
        thematiques = classification.get('thematiques', [])
        if not thematiques:
            self.warnings.append(f"⚠️  {doc_id} : thematiques vide")

    def _validate_vocabulaire(self, vocabulaire: List, doc_id: str):
        """
        Valide le vocabulaire spécifique
        """

        if not isinstance(vocabulaire, list):
            self.errors.append(f"❌ {doc_id} : vocabulaire_specifique doit être une liste")
            return

        for i, vocab_item in enumerate(vocabulaire):
            if not isinstance(vocab_item, dict):
                self.errors.append(f"❌ {doc_id} : vocabulaire[{i}] doit être un objet")
                continue

            # Vérifier structure
            if 'terme' not in vocab_item:
                self.errors.append(f"❌ {doc_id} : vocabulaire[{i}] : clé 'terme' manquante")

            if 'synonymes' not in vocab_item:
                self.warnings.append(f"⚠️  {doc_id} : vocabulaire[{i}] : clé 'synonymes' manquante")

            # Vérifier que terme n'est pas vide
            terme = vocab_item.get('terme', '').strip()
            if not terme:
                self.errors.append(f"❌ {doc_id} : vocabulaire[{i}] : terme vide")

    def print_report(self):
        """
        Affiche le rapport de validation
        """

        print("\n" + "="*60)
        print("📋 RAPPORT DE VALIDATION")
        print("="*60)

        if self.errors:
            print(f"\n❌ ERREURS ({len(self.errors)}) :\n")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}) :\n")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ AUCUNE ERREUR - Métadonnées valides !\n")

        print("="*60 + "\n")


def main():
    """
    Point d'entrée principal
    """

    parser = argparse.ArgumentParser(description='Valide les métadonnées enrichies')
    parser.add_argument('--source', required=True, help='Chemin vers index_complet.json')
    parser.add_argument('--strict', action='store_true', help='Mode strict (warnings = erreurs)')

    args = parser.parse_args()

    # Vérifier fichier source
    if not Path(args.source).exists():
        print(f"❌ Erreur : Fichier source introuvable : {args.source}")
        return 1

    # Valider
    validator = MetadataValidator(strict=args.strict)
    success, errors, warnings = validator.validate(args.source)

    # Afficher rapport
    validator.print_report()

    # Code retour
    if success:
        print("✅ Validation réussie - Prêt pour l'export\n")
        return 0
    else:
        print("❌ Validation échouée - Corriger les erreurs avant export\n")
        return 1


if __name__ == '__main__':
    exit(main())
