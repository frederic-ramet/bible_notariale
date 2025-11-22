# 🎯 Amélioration #1 : Routage Sémantique

[← Retour à l'index](./00_INDEX.md)

---

## 📊 Fiche technique

| Attribut | Valeur |
|----------|--------|
| **Priorité** | 🔥 CRITIQUE |
| **Impact** | ⭐⭐⭐⭐⭐ (-70% erreurs de sources) |
| **Effort** | 2 jours |
| **Statut** | ✅ Métadonnées prêtes / 📋 Application à modifier |
| **Dépendances** | #5 Enrichissement métadonnées (✅ FAIT) |
| **Repo principal** | `application` |

---

## 🔴 Problème identifié

### Symptômes
- **70% des échecs** dus à mauvaise sélection de sources
- Questions déontologie → cherche dans guides immobiliers
- Questions RH → ramène des documents assurances

### Exemple d'échec
```
❌ TEST_DEON_001 : "Qu'est-ce que le RPN ?"
Réponse actuelle : Cite le guide de négociation immobilière
Attendu : Citer le Règlement Professionnel du Notariat
```

### Cause racine
**Architecture "Flat Retrieval"** : Les 234 documents sont interrogés uniformément sans discrimination contextuelle.

```python
# Code actuel dans application/services/notaria_rag_service.py
async def query(self, question: str):
    # ❌ Recherche sur TOUS les documents
    results = await self.neo4j.vector_search(
        question=question,
        top_k=5  # Parmi 234 docs × ~500 chunks = 117000 chunks
    )
```

**Résultat** : Dilution de la pertinence, bruit vectoriel, contamination de contextes.

---

## ✅ Solution proposée

### Principe
**Classifier AVANT de chercher** : Identifier le domaine métier de la question, puis restreindre la recherche aux documents pertinents.

### Architecture

```
┌─────────────┐
│  Question   │
│  utilisateur│
└──────┬──────┘
       │
       ▼
┌──────────────────────┐
│ ÉTAPE 1 : Classifier │  ← 🆕 NOUVEAU
│ (LLM léger)          │
│ → Domaine métier     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ ÉTAPE 2 : Filtrage   │  ← 🆕 NOUVEAU
│ Neo4j par domaine    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ ÉTAPE 3 : Recherche  │  ← Existant optimisé
│ vectorielle ciblée   │
└──────────────────────┘
```

---

## 🏗️ Implémentation détaillée

### ÉTAPE 1 : Enrichir Neo4j avec catégories métier

**Repo** : `application`
**Fichier** : `scripts/enrich_neo4j_categories.py` (🆕 À créer)

#### Code complet

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'enrichissement Neo4j avec les catégories métier
Injecte les métadonnées depuis bible_notariale dans Neo4j
"""

import json
import asyncio
from pathlib import Path
from neo4j import AsyncGraphDatabase

# Configuration
BIBLE_NOTARIALE_PATH = Path("../bible_notariale")  # Chemin relatif vers l'autre repo
METADATA_DIR = BIBLE_NOTARIALE_PATH / "_metadata"
INDEX_FILE = METADATA_DIR / "index_complet.json"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_password"


async def enrich_neo4j():
    """
    Enrichit tous les documents Neo4j avec les métadonnées
    """
    # 1. Charger l'index complet
    print("📂 Chargement de l'index complet...")
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        index_data = json.load(f)

    documents = index_data.get('documents', [])
    print(f"✅ {len(documents)} documents trouvés\n")

    # 2. Connexion Neo4j
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    async with driver.session() as session:
        enriched_count = 0
        missing_count = 0

        for doc in documents:
            doc_id = doc.get('document_id', '')
            classification = doc.get('classification', {})

            # Extraire les métadonnées
            domaines_metier = classification.get('domaines_metier', [])
            domaine_principal = classification.get('domaine_metier_principal', '')
            type_document = classification.get('type_document', '')
            sources_document = classification.get('sources_document', '')
            thematiques = classification.get('thematiques', [])

            # Requête Cypher d'enrichissement
            query = """
            MATCH (doc:Document {documentId: $doc_id})
            SET doc.domaines_metier = $domaines,
                doc.domaine_principal = $domaine_principal,
                doc.type_document = $type_document,
                doc.sources_document = $sources_document,
                doc.thematiques = $thematiques,
                doc.enriched = true,
                doc.enriched_at = datetime()
            RETURN doc.documentId as id
            """

            result = await session.run(query, {
                'doc_id': doc_id,
                'domaines': domaines_metier,
                'domaine_principal': domaine_principal,
                'type_document': type_document,
                'sources_document': sources_document,
                'thematiques': thematiques
            })

            record = await result.single()
            if record:
                enriched_count += 1
                if enriched_count % 50 == 0:
                    print(f"  Enrichis : {enriched_count}/{len(documents)}...")
            else:
                missing_count += 1
                print(f"  ⚠️  Document non trouvé dans Neo4j : {doc_id}")

        # 3. Créer les index pour performance
        print("\n📊 Création des index Neo4j...")

        indexes = [
            "CREATE INDEX document_domaine_principal IF NOT EXISTS FOR (d:Document) ON (d.domaine_principal)",
            "CREATE INDEX document_type IF NOT EXISTS FOR (d:Document) ON (d.type_document)",
            "CREATE INDEX document_sources IF NOT EXISTS FOR (d:Document) ON (d.sources_document)"
        ]

        for idx_query in indexes:
            await session.run(idx_query)

        print("✅ Index créés\n")

    await driver.close()

    print("="*80)
    print(f"✅ Enrichissement terminé !")
    print(f"   Documents enrichis : {enriched_count}")
    print(f"   Documents manquants : {missing_count}")
    print("="*80)


if __name__ == '__main__':
    asyncio.run(enrich_neo4j())
```

#### Exécution

```bash
cd application/scripts
python3 enrich_neo4j_categories.py
```

**Résultat attendu** : 242 documents Neo4j enrichis avec domaines métier.

---

### ÉTAPE 2 : Créer le classificateur

**Repo** : `application`
**Fichier** : `agents/domain_classifier.py` (🆕 À créer)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classificateur de domaine métier pour routage pré-recherche
"""

from typing import Literal
from openai import AsyncOpenAI

DomainType = Literal["RH", "DEONTOLOGIE", "ASSURANCES", "HORS_PERIMETRE"]

CLASSIFICATION_PROMPT = """Tu es un expert du notariat français. Ta tâche est de classifier la question de l'utilisateur dans UN SEUL domaine métier.

DOMAINES DISPONIBLES :
- RH : Ressources humaines, convention collective, salaires, formation, contrats de travail, congés, prévoyance
- DEONTOLOGIE : Déontologie notariale, RPN, obligations professionnelles, discipline, inspections, conformité LCB-FT
- ASSURANCES : Assurances professionnelles, RCP, cyber-risques, garanties
- HORS_PERIMETRE : Questions sans rapport avec le notariat ou trop générales

EXEMPLES :
- "Quel est le salaire minimum d'un clerc ?" → RH
- "Qu'est-ce que le RPN ?" → DEONTOLOGIE
- "Comment fonctionne l'assurance cyber ?" → ASSURANCES
- "Quelle est la météo aujourd'hui ?" → HORS_PERIMETRE

QUESTION : {question}

Réponds UNIQUEMENT avec le nom du domaine (RH, DEONTOLOGIE, ASSURANCES, ou HORS_PERIMETRE).
"""


class DomainClassifier:
    """
    Classificateur de domaine métier
    """

    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client

    async def classify(self, question: str) -> DomainType:
        """
        Classifie la question dans un domaine métier

        Args:
            question: Question de l'utilisateur

        Returns:
            Domaine métier (RH, DEONTOLOGIE, ASSURANCES, HORS_PERIMETRE)
        """
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",  # Modèle léger et rapide
            messages=[
                {
                    "role": "user",
                    "content": CLASSIFICATION_PROMPT.format(question=question)
                }
            ],
            temperature=0,  # Déterministe
            max_tokens=10
        )

        domain = response.choices[0].message.content.strip().upper()

        # Validation
        valid_domains = ["RH", "DEONTOLOGIE", "ASSURANCES", "HORS_PERIMETRE"]
        if domain not in valid_domains:
            # Fallback : essayer de détecter
            if "RH" in domain:
                return "RH"
            elif "DEONTO" in domain:
                return "DEONTOLOGIE"
            elif "ASSUR" in domain:
                return "ASSURANCES"
            else:
                return "HORS_PERIMETRE"

        return domain
```

---

### ÉTAPE 3 : Modifier le service RAG

**Repo** : `application`
**Fichier** : `services/notaria_rag_service.py` (🔧 À modifier)

```python
# AVANT
async def query(self, question: str):
    # ❌ Recherche sur tous les documents
    results = await self.neo4j.vector_search(
        question=question,
        top_k=5
    )
    # ...


# APRÈS
async def query(self, question: str):
    # 🆕 ÉTAPE 1 : Classifier la question
    domain = await self.classifier.classify(question)

    # 🆕 ÉTAPE 2 : Gérer hors périmètre
    if domain == "HORS_PERIMETRE":
        return {
            "answer": "Je suis désolé, mais cette question ne concerne pas le domaine notarial que je peux couvrir. Je peux vous aider sur les sujets de déontologie, RH ou assurances du notariat.",
            "sources": [],
            "domain": domain
        }

    # 🆕 ÉTAPE 3 : Recherche filtrée par domaine
    results = await self.neo4j.vector_search_filtered(
        question=question,
        domain_filter=domain,  # ← Nouveau paramètre
        top_k=5
    )
    # ...
```

---

### ÉTAPE 4 : Modifier la requête Neo4j

**Repo** : `application`
**Fichier** : `services/neo4j_service.py` (🔧 À modifier)

```python
async def vector_search_filtered(
    self,
    question: str,
    domain_filter: str,
    top_k: int = 5
):
    """
    Recherche vectorielle filtrée par domaine métier
    """
    # Générer l'embedding de la question
    question_embedding = await self.get_embedding(question)

    # 🆕 Requête Cypher avec filtrage
    query = """
    // PHASE 1 : Filtrage symbolique (pré-filtre)
    MATCH (doc:Document)-[:CONTAINS]->(chunk:Chunk)
    WHERE doc.domaine_principal = $domain
       OR $domain IN doc.domaines_metier

    // PHASE 2 : Recherche vectorielle (sur sous-ensemble filtré)
    WITH chunk
    CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $embedding)
    YIELD node AS c, score
    WHERE c = chunk

    // PHASE 3 : Récupération contexte
    MATCH (c)<-[:CONTAINS]-(d:Document)
    RETURN c.text as text,
           c.metadata as metadata,
           d.titre as doc_titre,
           d.type_document as type_document,
           d.domaine_principal as domaine,
           score
    ORDER BY score DESC
    LIMIT $top_k
    """

    results = await self.session.run(query, {
        'domain': domain_filter,
        'embedding': question_embedding,
        'top_k': top_k
    })

    return [record async for record in results]
```

---

## 📊 Gains attendus

### Performance
| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Documents scannés** | 234 (100%) | ~60 (25%) | **-75%** |
| **Chunks scannés** | 117 000 | ~30 000 | **-75%** |
| **Temps de recherche** | 800ms | 200ms | **-75%** |
| **Précision sources** | 30% | 90% | **+200%** |

### Qualité
- ✅ Questions déontologie → **UNIQUEMENT** documents RPN, circulaires CSN
- ✅ Questions RH → **UNIQUEMENT** CCN, avenants, accords
- ✅ Questions assurances → **UNIQUEMENT** contrats RCP, cyber
- ✅ Hors périmètre → **Refus poli** au lieu d'hallucination

---

## 🧪 Tests & Validation

### Test unitaire du classificateur

```python
# tests/test_domain_classifier.py
import pytest
from agents.domain_classifier import DomainClassifier

@pytest.mark.asyncio
async def test_classification_rh():
    classifier = DomainClassifier(openai_client)

    questions = [
        "Quel est le salaire minimum d'un clerc ?",
        "Combien de jours de congés payés ?",
        "Comment fonctionne la formation OPCO ?"
    ]

    for q in questions:
        domain = await classifier.classify(q)
        assert domain == "RH", f"Échec pour : {q}"


@pytest.mark.asyncio
async def test_classification_deontologie():
    classifier = DomainClassifier(openai_client)

    questions = [
        "Qu'est-ce que le RPN ?",
        "Quelles sont les obligations LCB-FT ?",
        "Comment fonctionne l'inspection des offices ?"
    ]

    for q in questions:
        domain = await classifier.classify(q)
        assert domain == "DEONTOLOGIE", f"Échec pour : {q}"


@pytest.mark.asyncio
async def test_classification_hors_perimetre():
    classifier = DomainClassifier(openai_client)

    questions = [
        "Quelle est la météo aujourd'hui ?",
        "Comment cuisiner un bœuf bourguignon ?",
        "Qui a gagné la coupe du monde 2018 ?"
    ]

    for q in questions:
        domain = await classifier.classify(q)
        assert domain == "HORS_PERIMETRE", f"Échec pour : {q}"
```

### Test d'intégration

```python
# tests/test_routing_integration.py
import pytest

@pytest.mark.asyncio
async def test_routing_end_to_end():
    """
    Test complet : Question → Classification → Filtrage → Résultats
    """
    rag = NotariaRAGService()

    # Test 1 : Question RH
    response = await rag.query("Quel est le salaire minimum ?")
    assert response['domain'] == "RH"
    assert all('ccn' in src.lower() or 'avenant' in src.lower()
               for src in response['sources'])

    # Test 2 : Question déontologie
    response = await rag.query("Qu'est-ce que le RPN ?")
    assert response['domain'] == "DEONTOLOGIE"
    assert any('rpn' in src.lower() for src in response['sources'])

    # Test 3 : Hors périmètre
    response = await rag.query("Quelle est la météo ?")
    assert response['domain'] == "HORS_PERIMETRE"
    assert len(response['sources']) == 0
```

---

## 🔄 Rollback si échec

Si le routage dégrade les performances :

### 1. Désactiver temporairement

```python
# Dans notaria_rag_service.py
USE_ROUTING = False  # ← Variable de configuration

async def query(self, question: str):
    if USE_ROUTING:
        domain = await self.classifier.classify(question)
        results = await self.neo4j.vector_search_filtered(question, domain)
    else:
        # Retour à l'ancien comportement
        results = await self.neo4j.vector_search(question)
```

### 2. Logs détaillés

```python
import logging

logger.info(f"Question: {question}")
logger.info(f"Domaine classifié: {domain}")
logger.info(f"Documents filtrés: {filtered_count}")
logger.info(f"Résultats trouvés: {len(results)}")
```

### 3. Métriques A/B

Comparer pendant 1 semaine :
- 50% traffic avec routing
- 50% traffic sans routing
- Analyser taux de satisfaction

---

## 📅 Planning d'implémentation

### Jour 1
- ✅ Matin : Script `enrich_neo4j_categories.py`
- ✅ Matin : Exécution sur Neo4j (30 min)
- ✅ Après-midi : Classificateur `domain_classifier.py`
- ✅ Après-midi : Tests unitaires classificateur

### Jour 2
- ✅ Matin : Modification `notaria_rag_service.py`
- ✅ Matin : Modification `neo4j_service.py`
- ✅ Après-midi : Tests d'intégration
- ✅ Après-midi : Validation sur dataset 15 questions

---

## ✅ Checklist de déploiement

- [ ] Script `enrich_neo4j_categories.py` créé et testé
- [ ] 242 documents Neo4j enrichis (vérifier avec requête Cypher)
- [ ] Index Neo4j créés (`domaine_principal`, `type_document`)
- [ ] Classificateur `domain_classifier.py` créé
- [ ] Tests unitaires classificateur : 100% passent
- [ ] Service RAG modifié avec routage
- [ ] Service Neo4j modifié avec filtrage
- [ ] Tests d'intégration : 100% passent
- [ ] Validation manuelle sur 15 questions de test
- [ ] Métriques avant/après documentées
- [ ] Variable de rollback `USE_ROUTING` en place
- [ ] Logs détaillés activés
- [ ] Documentation mise à jour

---

## 🎯 Critères de succès

**Déploiement validé si :**
- ✅ Taux de succès passe de 34% → **>70%** sur dataset test
- ✅ Temps de recherche réduit de **>50%**
- ✅ Questions hors périmètre détectées à **>90%**
- ✅ Aucune régression sur questions fonctionnelles avant migration

---

[← Retour à l'index](./00_INDEX.md) | [Amélioration suivante : Reranking cognitif →](./02_reranking_cognitif.md)
