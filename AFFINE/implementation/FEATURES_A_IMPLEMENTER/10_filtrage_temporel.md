# ⏰ Amélioration #10 : Filtrage Temporel

[← Retour à l'index](./00_INDEX.md)

---

## 📊 Fiche technique

| Attribut | Valeur |
|----------|--------|
| **Priorité** | 🟢 MOYEN |
| **Impact** | ⭐⭐⭐⭐ (Précision réglementaire) |
| **Effort** | 1.5 jours |
| **Statut** | 📋 À faire |
| **Dépendances** | #5 - Enrichissement métadonnées |
| **Repo** | `bible_notariale` + `application` |

---

## 🎯 Problème identifié

### Observations

**Problème** : Certains documents sont obsolètes ou remplacés par des versions plus récentes

**Symptômes** :
- Directives CSN mises à jour mais anciennes versions encore dans la base
- Conventions collectives amendées mais anciens avenants non marqués comme obsolètes
- Risque de donner une information périmée

**Impact** :
- ❌ Réponses basées sur réglementation obsolète
- ❌ Confusion entre version actuelle et ancienne
- ❌ Risque juridique (conseil basé sur texte périmé)

**Exemple concret** :

```
Question : "Quelle est la grille salariale CCN ?"

❌ Sans filtrage temporel :
- Retourne : Grille CCN 2022 (obsolète) + Grille CCN 2024 (actuelle)
- Utilisateur ne sait pas laquelle est valide
- Risque de se baser sur l'ancienne

✅ Avec filtrage temporel :
- Filtre automatiquement documents valides au 22/11/2025
- Retourne uniquement : Grille CCN 2024 (version actuelle)
- Mentionne : "Remplace la grille du 01/01/2022"
```

---

## 💡 Solution proposée

### Vue d'ensemble

**Enrichir les métadonnées avec informations temporelles** :

1. **date_publication** : Date de publication du document
2. **date_effet** : Date d'entrée en vigueur
3. **date_fin_validite** : Date de fin de validité (optionnel)
4. **statut** : ACTUEL, OBSOLETE, ABROGE
5. **remplace** : ID du document remplacé (si applicable)
6. **remplace_par** : ID du document remplaçant (si obsolète)

### Architecture

```mermaid
graph LR
    A[Question utilisateur] --> B[Détection intention temporelle]
    B -->|Pas de mention temporelle| C[Filtre : documents actuels uniquement]
    B -->|Mention "avant 2023"| D[Filtre : valides avant 2023]
    C --> E[Recherche vectorielle]
    D --> E
    E --> F[Résultats]
    F --> G[Annotation statut temporel]
```

---

## 🔧 Implémentation détaillée

### Phase 1 : Enrichissement métadonnées (repo `bible_notariale`)

#### Script : `scripts/enrich_temporal_metadata.py`

```python
"""
Enrichit les métadonnées avec informations temporelles
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

def extract_date_from_filename(filename: str) -> Optional[str]:
    """
    Extrait la date depuis le nom de fichier

    Examples:
        "fil-info-265.pdf" → Chercher dans le contenu
        "avenant-ccn-2024-01.pdf" → "2024-01-01"
        "CID14_2025M1.pdf" → "2025-01-01"
    """

    # Pattern : YYYY-MM ou YYYY
    match = re.search(r'(\d{4})-(\d{2})', filename)
    if match:
        year, month = match.groups()
        return f"{year}-{month}-01"

    match = re.search(r'(\d{4})M(\d{1,2})', filename)
    if match:
        year, month = match.groups()
        return f"{year}-{month.zfill(2)}-01"

    match = re.search(r'(\d{4})', filename)
    if match:
        year = match.group(1)
        return f"{year}-01-01"

    return None


def determine_status(
    date_publication: Optional[str],
    date_fin_validite: Optional[str],
    today: str = None
) -> str:
    """
    Détermine le statut du document

    Returns:
        "ACTUEL", "OBSOLETE", ou "FUTUR"
    """

    if not today:
        today = datetime.now().strftime('%Y-%m-%d')

    # Si date de fin de validité passée → OBSOLETE
    if date_fin_validite and date_fin_validite < today:
        return "OBSOLETE"

    # Si date de publication future → FUTUR
    if date_publication and date_publication > today:
        return "FUTUR"

    return "ACTUEL"


def enrich_temporal_metadata(index_path: str, output_path: str):
    """
    Enrichit tous les documents avec métadonnées temporelles
    """

    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    # Relations de remplacement connues (à compléter manuellement)
    REPLACEMENTS = {
        # Exemple : fil-info-100 remplacé par fil-info-150
        'fil_infos_fil_info_100': {
            'remplace_par': 'fil_infos_fil_info_150',
            'date_fin_validite': '2024-06-01'
        },

        # CCN : avenants successifs
        'ccn_avenant_2022': {
            'remplace_par': 'ccn_avenant_2024',
            'date_fin_validite': '2024-01-01'
        },
    }

    enriched_count = 0

    for doc in index['documents']:
        doc_id = doc['document_id']
        fichier = doc.get('fichier', '')

        # 1. Extraire date de publication
        date_pub = extract_date_from_filename(fichier)

        # 2. Chercher informations de remplacement
        replacement_info = REPLACEMENTS.get(doc_id, {})
        date_fin = replacement_info.get('date_fin_validite')
        remplace_par = replacement_info.get('remplace_par')
        remplace = replacement_info.get('remplace')

        # 3. Déterminer statut
        statut = determine_status(date_pub, date_fin)

        # 4. Ajouter métadonnées temporelles
        doc['temporal'] = {
            'date_publication': date_pub,
            'date_effet': date_pub,  # Par défaut = date de publication
            'date_fin_validite': date_fin,
            'statut': statut,
            'remplace': remplace,
            'remplace_par': remplace_par
        }

        enriched_count += 1

    # Sauvegarder
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"✅ {enriched_count} documents enrichis avec métadonnées temporelles")

    # Statistiques
    statuts = {}
    for doc in index['documents']:
        statut = doc.get('temporal', {}).get('statut', 'INCONNU')
        statuts[statut] = statuts.get(statut, 0) + 1

    print("\n📊 Répartition par statut :")
    for statut, count in statuts.items():
        print(f"   - {statut}: {count}")


if __name__ == '__main__':
    enrich_temporal_metadata(
        index_path='_metadata/index_complet.json',
        output_path='_metadata/index_complet_temporal.json'
    )
```

**Exécution** :
```bash
cd bible_notariale
python3 scripts/enrich_temporal_metadata.py
```

---

### Phase 2 : Intégration Neo4j (repo `application`)

#### Script : `scripts/inject_temporal_neo4j.py`

```python
"""
Injecte les métadonnées temporelles dans Neo4j
"""

import json
import asyncio
from neo4j import AsyncGraphDatabase


async def inject_temporal_metadata(
    neo4j_uri: str,
    neo4j_user: str,
    neo4j_password: str,
    index_path: str
):
    """
    Enrichit les nœuds Document avec métadonnées temporelles
    """

    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    async with driver.session() as session:
        for doc in index['documents']:
            doc_id = doc['document_id']
            temporal = doc.get('temporal', {})

            await session.run("""
                MATCH (d:Document {documentId: $doc_id})
                SET d.date_publication = $date_pub,
                    d.date_effet = $date_effet,
                    d.date_fin_validite = $date_fin,
                    d.statut = $statut,
                    d.remplace = $remplace,
                    d.remplace_par = $remplace_par
            """,
                doc_id=doc_id,
                date_pub=temporal.get('date_publication'),
                date_effet=temporal.get('date_effet'),
                date_fin=temporal.get('date_fin_validite'),
                statut=temporal.get('statut'),
                remplace=temporal.get('remplace'),
                remplace_par=temporal.get('remplace_par')
            )

        # Créer relations de remplacement
        print("🔗 Création des relations de remplacement...")
        for doc in index['documents']:
            doc_id = doc['document_id']
            temporal = doc.get('temporal', {})

            if temporal.get('remplace'):
                await session.run("""
                    MATCH (d1:Document {documentId: $doc_id})
                    MATCH (d2:Document {documentId: $remplace})
                    MERGE (d1)-[:REMPLACE]->(d2)
                """, doc_id=doc_id, remplace=temporal['remplace'])

    await driver.close()
    print("✅ Métadonnées temporelles injectées")


if __name__ == '__main__':
    asyncio.run(inject_temporal_metadata(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="your_password",
        index_path="data/index_complet_temporal.json"
    ))
```

---

### Phase 3 : Filtrage temporel dans RAG

#### Nouveau service : `services/temporal_filter.py`

```python
"""
Service de filtrage temporel
"""

from datetime import datetime
from typing import List, Dict, Optional


class TemporalFilter:
    """
    Filtre les documents selon critères temporels
    """

    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')

    def detect_temporal_intent(self, question: str) -> Optional[str]:
        """
        Détecte si la question a une intention temporelle

        Returns:
            None : Pas d'intention temporelle (utiliser documents actuels)
            "YYYY-MM-DD" : Date spécifique mentionnée
            "avant YYYY" : Documents valides avant cette date
            "après YYYY" : Documents valides après cette date
        """

        import re

        question_lower = question.lower()

        # Détection "actuellement", "aujourd'hui", "en vigueur"
        if any(word in question_lower for word in ['actuellement', "aujourd'hui", 'en vigueur', 'actuel']):
            return None  # Filtre sur ACTUEL

        # Détection date spécifique
        match = re.search(r'\b(\d{4})\b', question_lower)
        if match:
            year = match.group(1)

            if 'avant' in question_lower or 'jusqu' in question_lower:
                return f"avant {year}"
            elif 'après' in question_lower or 'depuis' in question_lower:
                return f"après {year}"
            else:
                # Mention d'année sans indication → filtre sur cette année
                return f"{year}-01-01"

        return None  # Par défaut : documents actuels

    def build_temporal_filter(self, temporal_intent: Optional[str]) -> str:
        """
        Construit le filtre Cypher pour Neo4j

        Returns:
            Fragment Cypher à ajouter à la requête
        """

        if temporal_intent is None:
            # Filtre : documents actuels uniquement
            return """
            AND (d.statut = 'ACTUEL' OR d.statut IS NULL)
            """

        if temporal_intent.startswith('avant'):
            year = temporal_intent.split()[1]
            return f"""
            AND (d.date_effet < '{year}-12-31' OR d.date_effet IS NULL)
            AND (d.date_fin_validite IS NULL OR d.date_fin_validite >= '{year}-01-01')
            """

        if temporal_intent.startswith('après'):
            year = temporal_intent.split()[1]
            return f"""
            AND (d.date_effet >= '{year}-01-01' OR d.date_effet IS NULL)
            """

        # Date spécifique
        return f"""
        AND (d.date_effet <= '{temporal_intent}' OR d.date_effet IS NULL)
        AND (d.date_fin_validite IS NULL OR d.date_fin_validite >= '{temporal_intent}')
        """

    def annotate_results(self, chunks: List[Dict]) -> List[Dict]:
        """
        Annote les résultats avec informations temporelles
        """

        for chunk in chunks:
            statut = chunk.get('statut', 'ACTUEL')
            date_pub = chunk.get('date_publication')
            date_fin = chunk.get('date_fin_validite')

            # Ajouter annotation
            annotation = ""

            if statut == 'OBSOLETE':
                remplace_par = chunk.get('remplace_par')
                if remplace_par:
                    annotation = f"⚠️  Document obsolète (remplacé par {remplace_par})"
                else:
                    annotation = f"⚠️  Document obsolète depuis {date_fin}"

            elif statut == 'FUTUR':
                annotation = f"🔮 Document futur (applicable à partir de {date_pub})"

            elif date_pub:
                annotation = f"📅 Publié le {date_pub}"

            chunk['temporal_annotation'] = annotation

        return chunks
```

---

#### Intégration dans RAG : `services/notaria_rag_service.py`

```python
"""
Intégration du filtrage temporel
"""

from services.temporal_filter import TemporalFilter

class NotariaRAGService:

    def __init__(self):
        # ... autres initialisations
        self.temporal_filter = TemporalFilter()

    async def search(self, question: str, domain: str = None) -> List[dict]:
        """
        Recherche avec filtrage temporel
        """

        # 1. Détecter intention temporelle
        temporal_intent = self.temporal_filter.detect_temporal_intent(question)

        print(f"⏰ Intention temporelle : {temporal_intent or 'ACTUEL'}")

        # 2. Construire filtre temporel
        temporal_filter_cypher = self.temporal_filter.build_temporal_filter(temporal_intent)

        # 3. Recherche vectorielle avec filtre temporel
        query = """
        CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $embedding)
        YIELD node, score

        MATCH (node)-[:PART_OF]->(d:Document)
        WHERE 1=1
        """ + temporal_filter_cypher

        if domain:
            query += """
            AND $domain IN d.domaines_metier
            """

        query += """
        RETURN node.text as text,
               node.doc_titre as doc_titre,
               node.doc_id as doc_id,
               d.statut as statut,
               d.date_publication as date_publication,
               d.date_fin_validite as date_fin_validite,
               d.remplace_par as remplace_par,
               score
        ORDER BY score DESC
        LIMIT $top_k
        """

        results = await self.neo4j.run(query, {
            'embedding': embedding,
            'top_k': 20,
            'domain': domain
        })

        # 4. Annoter résultats avec infos temporelles
        annotated_results = self.temporal_filter.annotate_results(results)

        return annotated_results
```

---

## ✅ Tests et validation

### Tests d'enrichissement

```bash
# 1. Enrichir métadonnées
cd bible_notariale
python3 scripts/enrich_temporal_metadata.py

# Vérifier
cat _metadata/index_complet_temporal.json | jq '.documents[0].temporal'

# Devrait afficher :
# {
#   "date_publication": "2024-01-15",
#   "date_effet": "2024-01-15",
#   "date_fin_validite": null,
#   "statut": "ACTUEL",
#   "remplace": null,
#   "remplace_par": null
# }
```

### Tests de filtrage

```bash
# 1. Question avec intention temporelle
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelle était la grille salariale CCN avant 2023 ?",
    "session_id": "test_temporal"
  }'

# Vérifier dans les logs :
# ⏰ Intention temporelle : avant 2023
# Documents retournés : seulement ceux valides avant 2023

# 2. Question sans intention temporelle
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quelle est la grille salariale CCN actuelle ?",
    "session_id": "test_temporal"
  }'

# Vérifier :
# ⏰ Intention temporelle : ACTUEL
# Documents retournés : seulement ceux avec statut = ACTUEL
```

---

## 📈 Impact attendu

### Avant amélioration

- ❌ Mélange documents actuels et obsolètes
- ❌ Risque d'information périmée
- ❌ Pas de traçabilité temporelle

### Après amélioration

- ✅ Filtrage automatique sur documents actuels
- ✅ Support questions historiques ("avant 2023")
- ✅ Annotations temporelles claires
- ✅ Traçabilité des remplacements

---

## 📅 Planning d'implémentation

**Total** : 1.5 jours

### Jour 1 (matin - 4h)

- ✅ Créer `enrich_temporal_metadata.py`
- ✅ Identifier relations de remplacement manuellement
- ✅ Exécuter enrichissement
- ✅ Valider métadonnées générées

### Jour 1 (après-midi - 4h)

- ✅ Créer `inject_temporal_neo4j.py`
- ✅ Injecter dans Neo4j
- ✅ Vérifier propriétés temporelles

### Jour 2 (matin - 4h)

- ✅ Créer `temporal_filter.py`
- ✅ Intégrer dans notaria_rag_service.py
- ✅ Tests manuels

---

[← Retour à l'index](./00_INDEX.md) | [Amélioration suivante : Parent Retriever →](./11_parent_retriever.md)
