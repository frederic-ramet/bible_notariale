# 🎯 Amélioration #2 : Reranking Cognitif

[← Retour à l'index](./00_INDEX.md)

---

## 📊 Fiche technique

| Attribut | Valeur |
|----------|--------|
| **Priorité** | 🔥 CRITIQUE |
| **Impact** | ⭐⭐⭐⭐⭐ (+50% complétude réponses) |
| **Effort** | 1 jour |
| **Statut** | 📋 À faire |
| **Dépendances** | #1 Routage sémantique (recommandé mais pas obligatoire) |
| **Repo principal** | `application` |

---

## 🔴 Problème identifié

### Symptômes
- **20% des échecs** dus à réponses incomplètes
- Chunks pertinents manqués
- Contexte tronqué ou imprécis

### Exemples d'échecs
```
❌ TEST_USER_001 : "Quelles sont les règles de prévoyance ?"
Réponse actuelle : Info partielle, manque détails sur contributions
Cause : top_k=5 trop faible, chunks importants en position 7-12

❌ TEST_USER_007 : "Comment gérer les congés dans un office ?"
Réponse actuelle : Manque contexte CCN
Cause : Chunk CCN score 6e position, non inclus dans contexte LLM
```

### Cause racine

**Top-k trop faible + Pas de réordonnancement** : La recherche vectorielle ramène 5 chunks, mais :
- Chunks pertinents souvent en position 6-15
- Pas de filtrage par pertinence réelle à la question
- Envoi direct au LLM sans vérification

```python
# Code actuel
results = await self.neo4j.vector_search(question, top_k=5)
# ❌ Envoie directement les 5 premiers au LLM
# Même si certains sont peu pertinents et d'autres pertinents manqués
```

---

## ✅ Solution proposée

### Principe

**Élargir puis filtrer** : Récupérer plus de chunks (20), puis utiliser un LLM pour reranker et sélectionner les 8 meilleurs.

### Architecture

```
┌─────────────┐
│  Question   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ ÉTAPE 1 : Recherche large│
│ top_k = 20 chunks        │  ← 🆕 Augmenté de 5 → 20
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ ÉTAPE 2 : Reranking LLM  │  ← 🆕 NOUVEAU
│ Score 0-10 par chunk     │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ ÉTAPE 3 : Sélection      │  ← 🆕 NOUVEAU
│ Top 8 chunks (score >7)  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ ÉTAPE 4 : Synthèse LLM   │  ← Existant optimisé
│ Génération réponse       │
└──────────────────────────┘
```

---

## 🏗️ Implémentation détaillée

### ÉTAPE 1 : Créer le module de reranking

**Repo** : `application`
**Fichier** : `services/reranker_service.py` (🆕 À créer)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service de reranking des résultats de recherche vectorielle
Utilise un LLM pour scorer la pertinence réelle de chaque chunk
"""

from typing import List, Dict
from openai import AsyncOpenAI
from dataclasses import dataclass


@dataclass
class ScoredChunk:
    """Chunk avec son score de pertinence"""
    text: str
    metadata: Dict
    doc_titre: str
    vector_score: float
    relevance_score: float  # 0-10


RERANKING_PROMPT = """Tu es un expert en analyse de pertinence documentaire pour le notariat français.

Ta tâche : Évaluer la pertinence d'un extrait de document par rapport à une question.

QUESTION :
{question}

EXTRAIT DE DOCUMENT :
Source : {doc_titre}
Contenu : {chunk_text}

INSTRUCTIONS :
1. Analyse si l'extrait contient des informations directement utiles pour répondre à la question
2. Attribue un score de pertinence de 0 à 10 :
   - 10 : Répond directement et complètement à la question
   - 7-9 : Contient des éléments de réponse importants
   - 4-6 : Contexte général utile mais pas central
   - 1-3 : Vaguement lié au sujet
   - 0 : Non pertinent

3. Pénalise si :
   - L'extrait est trop générique
   - L'extrait parle d'un domaine différent
   - L'extrait ne contient que du contexte sans info concrète

RÉPONDS UNIQUEMENT AVEC LE SCORE (un nombre entre 0 et 10).
"""


class RerankerService:
    """
    Service de reranking des résultats de recherche
    """

    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client

    async def score_chunk(
        self,
        question: str,
        chunk_text: str,
        doc_titre: str
    ) -> float:
        """
        Score la pertinence d'un chunk par rapport à la question

        Args:
            question: Question de l'utilisateur
            chunk_text: Texte du chunk
            doc_titre: Titre du document source

        Returns:
            Score de pertinence (0-10)
        """
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",  # Rapide et économique
            messages=[
                {
                    "role": "user",
                    "content": RERANKING_PROMPT.format(
                        question=question,
                        chunk_text=chunk_text[:500],  # Limiter pour coût
                        doc_titre=doc_titre
                    )
                }
            ],
            temperature=0,
            max_tokens=5
        )

        try:
            score = float(response.choices[0].message.content.strip())
            # Borner entre 0 et 10
            return max(0.0, min(10.0, score))
        except (ValueError, AttributeError):
            # Si parsing échoue, score neutre
            return 5.0

    async def rerank(
        self,
        question: str,
        chunks: List[Dict],
        top_k: int = 8,
        min_score: float = 7.0
    ) -> List[ScoredChunk]:
        """
        Rerank les chunks par pertinence réelle

        Args:
            question: Question de l'utilisateur
            chunks: Liste des chunks bruts de la recherche vectorielle
            top_k: Nombre de chunks à retourner
            min_score: Score minimum pour être retenu

        Returns:
            Liste des chunks rerankés et filtrés
        """
        scored_chunks = []

        # Scorer tous les chunks en parallèle (asyncio)
        import asyncio
        tasks = []

        for chunk in chunks:
            task = self.score_chunk(
                question=question,
                chunk_text=chunk.get('text', ''),
                doc_titre=chunk.get('doc_titre', 'Document sans titre')
            )
            tasks.append(task)

        # Attendre tous les scores
        scores = await asyncio.gather(*tasks)

        # Créer les chunks scorés
        for chunk, relevance_score in zip(chunks, scores):
            scored_chunks.append(ScoredChunk(
                text=chunk.get('text', ''),
                metadata=chunk.get('metadata', {}),
                doc_titre=chunk.get('doc_titre', ''),
                vector_score=chunk.get('score', 0.0),
                relevance_score=relevance_score
            ))

        # Filtrer et trier
        filtered = [c for c in scored_chunks if c.relevance_score >= min_score]
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)

        # Retourner top_k
        return filtered[:top_k]


    async def rerank_hybrid(
        self,
        question: str,
        chunks: List[Dict],
        top_k: int = 8
    ) -> List[ScoredChunk]:
        """
        Reranking hybride : combine score vectoriel et score LLM

        Formule : score_final = 0.3 * vector_score + 0.7 * llm_score
        """
        scored_chunks = []
        import asyncio
        tasks = [
            self.score_chunk(
                question,
                chunk.get('text', ''),
                chunk.get('doc_titre', '')
            )
            for chunk in chunks
        ]

        llm_scores = await asyncio.gather(*tasks)

        for chunk, llm_score in zip(chunks, llm_scores):
            vector_score = chunk.get('score', 0.0)

            # Normaliser vector_score (0-1) → (0-10)
            vector_score_normalized = vector_score * 10

            # Score hybride
            final_score = (
                0.3 * vector_score_normalized +
                0.7 * llm_score
            )

            scored_chunks.append(ScoredChunk(
                text=chunk.get('text', ''),
                metadata=chunk.get('metadata', {}),
                doc_titre=chunk.get('doc_titre', ''),
                vector_score=vector_score,
                relevance_score=final_score
            ))

        # Trier par score final
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_chunks[:top_k]
```

---

### ÉTAPE 2 : Modifier le service RAG

**Repo** : `application`
**Fichier** : `services/notaria_rag_service.py` (🔧 À modifier)

```python
from services.reranker_service import RerankerService

class NotariaRAGService:
    def __init__(self, ...):
        # ... existant
        self.reranker = RerankerService(openai_client)


    async def query(self, question: str):
        # ÉTAPE 1 : Classifier (si amélioration #1 activée)
        domain = await self.classifier.classify(question)

        if domain == "HORS_PERIMETRE":
            return self._hors_perimetre_response()

        # ÉTAPE 2 : Recherche LARGE
        raw_chunks = await self.neo4j.vector_search_filtered(
            question=question,
            domain_filter=domain,
            top_k=20  # ← 🆕 Augmenté de 5 → 20
        )

        # ÉTAPE 3 : 🆕 RERANKING
        reranked_chunks = await self.reranker.rerank(
            question=question,
            chunks=raw_chunks,
            top_k=8,          # Sélectionne les 8 meilleurs
            min_score=7.0     # Score minimum 7/10
        )

        # Si pas assez de chunks avec score >7, utiliser top 8 quand même
        if len(reranked_chunks) < 5:
            reranked_chunks = await self.reranker.rerank_hybrid(
                question=question,
                chunks=raw_chunks,
                top_k=8
            )

        # ÉTAPE 4 : Construire le contexte pour le LLM final
        context = self._build_context(reranked_chunks)

        # ÉTAPE 5 : Générer la réponse
        response = await self._generate_answer(question, context)

        return {
            "answer": response,
            "sources": [c.doc_titre for c in reranked_chunks],
            "scores": [c.relevance_score for c in reranked_chunks],
            "domain": domain
        }


    def _build_context(self, scored_chunks: List[ScoredChunk]) -> str:
        """
        Construit le contexte pour le LLM final
        """
        context_parts = []

        for i, chunk in enumerate(scored_chunks, 1):
            context_parts.append(
                f"[Document {i}] {chunk.doc_titre}\n"
                f"Pertinence: {chunk.relevance_score:.1f}/10\n"
                f"{chunk.text}\n"
            )

        return "\n---\n".join(context_parts)
```

---

## 📊 Gains attendus

### Performance

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Chunks analysés** | 5 | 20 → 8 | +60% initiaux, -20% finaux |
| **Complétude réponses** | 50% | 95% | **+90%** |
| **Précision contexte** | 60% | 90% | **+50%** |
| **Taux réussite tests** | 34% | 65% | **+91%** |

### Qualité

- ✅ Chunks pertinents en position 6-15 maintenant capturés
- ✅ Chunks peu pertinents filtrés (score <7)
- ✅ Contexte LLM final optimisé (8 meilleurs au lieu de 5 moyens)

### Coût

```
Avant :
- 1 requête Neo4j (top_k=5)
- 1 appel LLM génération
= ~0.02€ par question

Après :
- 1 requête Neo4j (top_k=20)
- 20 appels LLM reranking (gpt-4o-mini)
- 1 appel LLM génération
= ~0.05€ par question (+150% mais acceptable)
```

**Optimisation coût possible** :
- Reranking par batch (10 chunks par appel)
- Cache des scores pour questions similaires

---

## 🧪 Tests & Validation

### Test unitaire du reranker

```python
# tests/test_reranker.py
import pytest
from services.reranker_service import RerankerService

@pytest.mark.asyncio
async def test_reranker_score_pertinent():
    """Test que le reranker donne un bon score aux chunks pertinents"""
    reranker = RerankerService(openai_client)

    question = "Quel est le salaire minimum d'un clerc ?"
    chunk_pertinent = "Article 15 de la CCN : Le salaire minimum d'un clerc débutant est de..."
    chunk_non_pertinent = "Les congés payés sont de 25 jours par an..."

    score_pertinent = await reranker.score_chunk(question, chunk_pertinent, "CCN")
    score_non_pertinent = await reranker.score_chunk(question, chunk_non_pertinent, "CCN")

    assert score_pertinent >= 8.0, "Chunk pertinent devrait avoir score >=8"
    assert score_non_pertinent <= 5.0, "Chunk non pertinent devrait avoir score <=5"


@pytest.mark.asyncio
async def test_reranker_full_pipeline():
    """Test du pipeline complet de reranking"""
    reranker = RerankerService(openai_client)

    question = "Comment fonctionne la prévoyance ?"
    chunks = [
        {"text": "La prévoyance couvre les risques décès, invalidité...", "doc_titre": "Guide prévoyance", "score": 0.8},
        {"text": "Les congés payés sont calculés...", "doc_titre": "CCN", "score": 0.7},
        {"text": "Le taux de cotisation prévoyance est de 1.5%...", "doc_titre": "Avenant 48", "score": 0.75},
    ]

    reranked = await reranker.rerank(question, chunks, top_k=2, min_score=7.0)

    # Vérifier que seuls les chunks pertinents sont retenus
    assert len(reranked) >= 1
    assert all(c.relevance_score >= 7.0 for c in reranked)
    assert reranked[0].relevance_score >= reranked[-1].relevance_score  # Ordre décroissant
```

### Test d'intégration

```python
# tests/test_rag_with_reranking.py
import pytest

@pytest.mark.asyncio
async def test_rag_with_reranking():
    """Test end-to-end avec reranking"""
    rag = NotariaRAGService()

    # Question complexe nécessitant plusieurs sources
    response = await rag.query(
        "Quelles sont les règles de prévoyance et combien ça coûte ?"
    )

    # Vérifier que la réponse est complète
    assert "prévoyance" in response['answer'].lower()
    assert any(word in response['answer'].lower() for word in ["taux", "cotisation", "coût", "%"])

    # Vérifier que plusieurs sources sont utilisées
    assert len(response['sources']) >= 3

    # Vérifier que les scores sont bons
    assert all(score >= 7.0 for score in response['scores'])
```

---

## 📊 Métriques de monitoring

### À tracker en production

```python
# Logs à ajouter dans notaria_rag_service.py
import logging

logger.info("Reranking stats", extra={
    "question_id": question_id,
    "raw_chunks_count": len(raw_chunks),
    "reranked_chunks_count": len(reranked_chunks),
    "min_score": min([c.relevance_score for c in reranked_chunks]),
    "max_score": max([c.relevance_score for c in reranked_chunks]),
    "avg_score": sum([c.relevance_score for c in reranked_chunks]) / len(reranked_chunks),
    "filtered_out": len(raw_chunks) - len(reranked_chunks)
})
```

### Dashboard recommandé

- Distribution des scores de reranking
- Taux de chunks filtrés (<7/10)
- Corrélation score vectoriel vs score LLM
- Temps de reranking moyen

---

## 🔄 Rollback si échec

### Désactivation rapide

```python
# Configuration
USE_RERANKING = True  # Variable d'environnement

async def query(self, question: str):
    raw_chunks = await self.neo4j.vector_search(..., top_k=20 if USE_RERANKING else 5)

    if USE_RERANKING:
        chunks = await self.reranker.rerank(question, raw_chunks)
    else:
        chunks = raw_chunks[:5]  # Comportement ancien

    # ...
```

### Optimisation progressive

```python
# Mode A/B test
import random

if random.random() < 0.5:
    # 50% avec reranking
    chunks = await self.reranker.rerank(question, raw_chunks)
else:
    # 50% sans reranking
    chunks = raw_chunks[:5]

# Comparer métriques satisfaction
```

---

## 📅 Planning d'implémentation

### Demi-journée 1
- ✅ Créer `reranker_service.py`
- ✅ Tests unitaires reranker
- ✅ Validation prompt de scoring

### Demi-journée 2
- ✅ Modifier `notaria_rag_service.py`
- ✅ Augmenter top_k 5→20
- ✅ Intégrer reranking dans pipeline
- ✅ Tests d'intégration
- ✅ Validation sur dataset 15 questions

---

## ✅ Checklist de déploiement

- [ ] `reranker_service.py` créé et testé
- [ ] Tests unitaires reranker : 100% passent
- [ ] Prompt de scoring validé (précision >85%)
- [ ] Service RAG modifié avec reranking
- [ ] top_k augmenté à 20 dans recherche vectorielle
- [ ] Tests d'intégration : 100% passent
- [ ] Logs et métriques en place
- [ ] Coût par requête mesuré et validé (<0.10€)
- [ ] Variable de rollback `USE_RERANKING` en place
- [ ] Validation manuelle sur 15 questions test
- [ ] Amélioration complétude mesurée (>+40%)

---

## 🎯 Critères de succès

**Déploiement validé si :**
- ✅ Complétude réponses passe de 50% → **>90%**
- ✅ Taux de succès tests passe de 34% → **>60%** (combiné avec #1)
- ✅ Score moyen reranking **>7.5/10**
- ✅ Coût par requête **<0.10€**
- ✅ Latence ajoutée **<2 secondes**

---

[← Retour à l'index](./00_INDEX.md) | [Amélioration suivante : Gestion des limites →](./03_gestion_limites.md)
