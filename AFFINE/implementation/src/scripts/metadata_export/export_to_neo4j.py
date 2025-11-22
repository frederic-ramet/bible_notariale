#!/usr/bin/env python3
"""
Export des métadonnées enrichies vers Neo4j

Ce script exporte TOUTES les métadonnées enrichies (classification 5 niveaux,
ontologie, vocabulaire) vers Neo4j pour être utilisées par le chatbot.

Usage:
    python3 export_to_neo4j.py --source ../../../../_metadata/index_complet.json --neo4j-uri bolt://localhost:7687

Arguments:
    --source : Chemin vers index_complet.json (bible_notariale)
    --neo4j-uri : URI Neo4j
    --neo4j-user : User Neo4j (défaut: neo4j)
    --neo4j-password : Password Neo4j
    --dry-run : Mode dry-run (affiche sans modifier)
"""

import json
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from neo4j import AsyncGraphDatabase


class MetadataExporter:
    """
    Exporte les métadonnées vers Neo4j
    """

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str, dry_run: bool = False):
        self.dry_run = dry_run

        if not dry_run:
            self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        else:
            print("🔍 MODE DRY-RUN : Aucune modification ne sera effectuée")
            self.driver = None

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def export_metadata(self, index_path: str):
        """
        Exporte toutes les métadonnées

        1. Classification (type_document, sources_document, domaines_metier, thématiques)
        2. Vocabulaire spécifique (termes + synonymes)
        3. Relations ontologiques
        """

        # Charger index
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)

        documents = index.get('documents', [])

        print(f"\n📊 Export de {len(documents)} documents vers Neo4j")
        print(f"Timestamp : {datetime.now()}\n")

        # Statistiques
        stats = {
            'documents_updated': 0,
            'classifications_updated': 0,
            'vocabulaire_injected': 0,
            'errors': 0
        }

        async with self.driver.session() as session:

            for doc in documents:
                try:
                    doc_id = doc['document_id']

                    # 1. Mettre à jour classification
                    await self._update_classification(session, doc_id, doc.get('classification', {}))
                    stats['classifications_updated'] += 1

                    # 2. Injecter vocabulaire
                    vocab_count = await self._inject_vocabulary(session, doc_id, doc.get('vocabulaire_specifique', []))
                    stats['vocabulaire_injected'] += vocab_count

                    stats['documents_updated'] += 1

                    if stats['documents_updated'] % 50 == 0:
                        print(f"  ✓ {stats['documents_updated']}/{len(documents)} documents traités")

                except Exception as e:
                    print(f"  ❌ Erreur pour {doc.get('document_id')}: {e}")
                    stats['errors'] += 1

        print(f"\n✅ Export terminé")
        print(f"   - Documents mis à jour : {stats['documents_updated']}")
        print(f"   - Classifications : {stats['classifications_updated']}")
        print(f"   - Termes vocabulaire : {stats['vocabulaire_injected']}")
        print(f"   - Erreurs : {stats['errors']}")

        return stats

    async def _update_classification(self, session, doc_id: str, classification: dict):
        """
        Met à jour la classification d'un document dans Neo4j
        """

        if self.dry_run:
            print(f"[DRY-RUN] Mise à jour classification pour {doc_id}")
            return

        await session.run("""
            MATCH (d:Document {documentId: $doc_id})
            SET d.type_document = $type_doc,
                d.sources_document = $sources_doc,
                d.domaines_metier = $domaines,
                d.domaine_metier_principal = $domaine_principal,
                d.thematiques = $thematiques,
                d.metadata_updated_at = datetime()
        """,
            doc_id=doc_id,
            type_doc=classification.get('type_document'),
            sources_doc=classification.get('sources_document'),
            domaines=classification.get('domaines_metier', []),
            domaine_principal=classification.get('domaine_metier_principal'),
            thematiques=classification.get('thematiques', [])
        )

    async def _inject_vocabulary(self, session, doc_id: str, vocabulaire: list) -> int:
        """
        Injecte le vocabulaire spécifique dans Neo4j
        Crée des relations Document --[MENTIONNE]--> Terme
        """

        if self.dry_run:
            print(f"[DRY-RUN] Injection vocabulaire pour {doc_id} : {len(vocabulaire)} termes")
            return len(vocabulaire)

        count = 0

        for vocab_item in vocabulaire:
            if not isinstance(vocab_item, dict):
                continue

            terme = vocab_item.get('terme', '').strip()
            synonymes = vocab_item.get('synonymes', [])
            definition = vocab_item.get('definition', '')

            if not terme:
                continue

            # Créer le nœud Terme et la relation
            await session.run("""
                MATCH (d:Document {documentId: $doc_id})
                MERGE (t:Terme {name: $terme})
                SET t.definition = $definition,
                    t.synonymes = $synonymes
                MERGE (d)-[:MENTIONNE]->(t)
            """,
                doc_id=doc_id,
                terme=terme,
                definition=definition,
                synonymes=synonymes
            )

            count += 1

        return count


async def main():
    """
    Point d'entrée principal
    """

    parser = argparse.ArgumentParser(description='Export métadonnées vers Neo4j')
    parser.add_argument('--source', required=True, help='Chemin vers index_complet.json')
    parser.add_argument('--neo4j-uri', default='bolt://localhost:7687', help='URI Neo4j')
    parser.add_argument('--neo4j-user', default='neo4j', help='User Neo4j')
    parser.add_argument('--neo4j-password', required=True, help='Password Neo4j')
    parser.add_argument('--dry-run', action='store_true', help='Mode dry-run (pas de modification)')

    args = parser.parse_args()

    # Vérifier que le fichier source existe
    if not Path(args.source).exists():
        print(f"❌ Erreur : Fichier source introuvable : {args.source}")
        return 1

    # Créer exporter
    exporter = MetadataExporter(
        neo4j_uri=args.neo4j_uri,
        neo4j_user=args.neo4j_user,
        neo4j_password=args.neo4j_password,
        dry_run=args.dry_run
    )

    try:
        # Exporter
        await exporter.export_metadata(args.source)

    finally:
        await exporter.close()

    return 0


if __name__ == '__main__':
    exit(asyncio.run(main()))
