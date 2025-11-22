# 🎯 Amélioration #3 : Gestion des Limites

[← Retour à l'index](./00_INDEX.md)

---

## 📊 Fiche technique

| Attribut | Valeur |
|----------|--------|
| **Priorité** | 🔥 HAUTE |
| **Impact** | ⭐⭐⭐⭐ (Crédibilité professionnelle) |
| **Effort** | 1 jour |
| **Statut** | 📋 À faire |
| **Dépendances** | #1 Routage sémantique (partiel) |
| **Repo principal** | `application` |

---

## 🔴 Problème identifié

### Symptômes
- **Hallucinations juridiques** : Le chatbot invente des réponses pour questions hors périmètre
- **Conseils personnalisés** : Risque juridique (responsabilité professionnelle)
- **Perte de crédibilité** : Réponses sur des sujets non couverts

### Exemples problématiques

```
❌ Question : "Quelle est la météo aujourd'hui à Caen ?"
Réponse actuelle : Tente de répondre avec données aléatoires
Attendu : Refus poli "Cette question ne concerne pas le notariat"

❌ Question : "Puis-je vendre ma maison sans notaire ?"
Réponse actuelle : Répond oui/non de manière générique
Attendu : "Je ne peux pas donner de conseil personnalisé, consultez un notaire"

❌ Question : "Comment cuisiner un bœuf bourguignon ?"
Réponse actuelle : Hallucine une réponse
Attendu : Refus poli
```

### Risques

**Juridiques** :
- Responsabilité professionnelle si conseil erroné
- Confusion entre information générale et conseil personnalisé
- Non-conformité déontologique

**Réputation** :
- Perte de confiance des utilisateurs
- Crédibilité de l'outil compromise

---

## ✅ Solution proposée

### Principe

**Détection stricte d'intention** avant génération de réponse :
1. Classifier l'intention (périmètre notarial, hors périmètre, conseil personnalisé)
2. Gérer chaque cas différemment
3. Ne répondre QUE dans le périmètre strict de l'outil

### Architecture

```
┌─────────────┐
│  Question   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ ÉTAPE 1 : Classification │  ← 🆕 NOUVEAU
│ intention détaillée      │
└──────┬───────────────────┘
       │
       ├─[HORS_PERIMETRE]──────────► Refus poli
       │
       ├─[CONSEIL_PERSONNALISE]────► Redirection vers expert
       │
       ├─[AMBIGUE]─────────────────► Demande clarification
       │
       └─[PERIMETRE_NOTARIAL]──────► Pipeline RAG normal
```

---

## 🏗️ Implémentation détaillée

### ÉTAPE 1 : Classifier les intentions

**Repo** : `application`
**Fichier** : `agents/intent_classifier.py` (🆕 À créer)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Classificateur d'intention pour détecter les limites du périmètre
"""

from typing import Literal
from openai import AsyncOpenAI
from enum import Enum


class IntentType(str, Enum):
    """Types d'intention détectables"""
    PERIMETRE_NOTARIAL = "PERIMETRE_NOTARIAL"         # Dans le scope
    HORS_PERIMETRE = "HORS_PERIMETRE"                 # Hors du scope
    CONSEIL_PERSONNALISE = "CONSEIL_PERSONNALISE"     # Demande de conseil individuel
    AMBIGUE = "AMBIGUE"                               # Pas clair, clarification nécessaire


INTENT_CLASSIFICATION_PROMPT = """Tu es un expert en analyse d'intention pour un chatbot notarial.

PÉRIMÈTRE DU CHATBOT :
- Information générale sur la déontologie notariale (RPN, obligations professionnelles)
- Information générale sur les RH du notariat (CCN, salaires, formation)
- Information générale sur les assurances professionnelles (RCP, cyber-risques)

HORS PÉRIMÈTRE :
- Questions sans rapport avec le notariat
- Actualités générales, météo, sport, cuisine, etc.
- Questions techniques sur d'autres domaines professionnels

CONSEIL PERSONNALISÉ (INTERDIT) :
- Demandes de conseil sur une situation individuelle spécifique
- "Que dois-je faire dans mon cas ?"
- Aide à la décision personnelle
- Interprétation de contrat individuel

AMBIGU :
- Question trop vague pour déterminer l'intention
- Manque de contexte
- Peut être interprétée de plusieurs façons

QUESTION : {question}

INSTRUCTIONS :
Analyse l'intention et réponds avec UNE SEULE des catégories :
- PERIMETRE_NOTARIAL
- HORS_PERIMETRE
- CONSEIL_PERSONNALISE
- AMBIGUE

Réponds UNIQUEMENT avec le nom de la catégorie.
"""


EXAMPLES = """
EXEMPLES :

Q: "Qu'est-ce que le RPN ?"
→ PERIMETRE_NOTARIAL (information générale sur règlement)

Q: "Quel est le salaire minimum d'un clerc ?"
→ PERIMETRE_NOTARIAL (information CCN)

Q: "Puis-je vendre MA maison sans notaire ?"
→ CONSEIL_PERSONNALISE (situation personnelle)

Q: "Mon employeur peut-il me licencier si j'ai un arrêt maladie ?"
→ CONSEIL_PERSONNALISE (conseil juridique individuel)

Q: "Quelle est la météo aujourd'hui ?"
→ HORS_PERIMETRE (rien à voir avec le notariat)

Q: "Comment cuisiner un bœuf bourguignon ?"
→ HORS_PERIMETRE (hors sujet)

Q: "Aide-moi"
→ AMBIGUE (pas de contexte)

Q: "C'est quoi ça ?"
→ AMBIGUE (question trop vague)
"""


class IntentClassifier:
    """
    Classificateur d'intention avec détection des limites
    """

    def __init__(self, openai_client: AsyncOpenAI):
        self.client = openai_client

    async def classify(self, question: str) -> IntentType:
        """
        Classifie l'intention de la question

        Args:
            question: Question de l'utilisateur

        Returns:
            Type d'intention détecté
        """
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": EXAMPLES
                },
                {
                    "role": "user",
                    "content": INTENT_CLASSIFICATION_PROMPT.format(question=question)
                }
            ],
            temperature=0,
            max_tokens=20
        )

        intent_str = response.choices[0].message.content.strip().upper()

        # Validation et mapping
        try:
            return IntentType(intent_str)
        except ValueError:
            # Si non reconnu, classifier comme ambigu
            return IntentType.AMBIGUE


    async def classify_with_explanation(self, question: str) -> dict:
        """
        Classifie avec explication pour debugging

        Returns:
            {
                "intent": IntentType,
                "explanation": str,
                "confidence": float
            }
        """
        prompt = f"""{INTENT_CLASSIFICATION_PROMPT.format(question=question)}

Réponds au format :
INTENTION: [nom de la catégorie]
EXPLICATION: [pourquoi cette classification]
CONFIANCE: [0-10]
"""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        # Parser la réponse
        content = response.choices[0].message.content
        lines = content.split('\n')

        intent = IntentType.AMBIGUE
        explanation = ""
        confidence = 5.0

        for line in lines:
            if line.startswith("INTENTION:"):
                intent_str = line.replace("INTENTION:", "").strip().upper()
                try:
                    intent = IntentType(intent_str)
                except ValueError:
                    pass
            elif line.startswith("EXPLICATION:"):
                explanation = line.replace("EXPLICATION:", "").strip()
            elif line.startswith("CONFIANCE:"):
                try:
                    confidence = float(line.replace("CONFIANCE:", "").strip())
                except ValueError:
                    pass

        return {
            "intent": intent,
            "explanation": explanation,
            "confidence": confidence
        }
```

---

### ÉTAPE 2 : Créer les réponses par défaut

**Repo** : `application`
**Fichier** : `prompts/boundary_responses.py` (🆕 À créer)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Réponses standardisées pour les cas hors périmètre
"""

HORS_PERIMETRE_RESPONSE = """Je suis désolé, mais cette question ne concerne pas le domaine notarial que je couvre.

Mon périmètre d'expertise se limite à :
- La déontologie notariale (RPN, obligations professionnelles)
- Les ressources humaines du notariat (CCN, formation, salaires)
- Les assurances professionnelles notariales (RCP, cyber-risques)

Pour des questions générales ou d'autres domaines, je vous invite à consulter des ressources appropriées.
"""


CONSEIL_PERSONNALISE_RESPONSE = """Je ne peux pas vous fournir de conseil personnalisé sur votre situation spécifique.

**Pourquoi ?**
- Risque de responsabilité professionnelle
- Chaque situation requiert une analyse individuelle complète
- Un conseil inadapté pourrait avoir des conséquences juridiques

**Ce que je peux faire :**
- Vous donner des informations générales sur les règles applicables
- Vous orienter vers les textes de référence (RPN, CCN, etc.)

**Ce que vous devez faire :**
- Consulter votre Chambre des Notaires départementale
- Contacter le CRIDON pour une consultation juridique
- Échanger avec un confrère expert du sujet

📞 **Contacts utiles :**
- CRIDON : consultation juridique spécialisée
- Chambre des Notaires : conseil et accompagnement
- CSN : questions déontologiques
"""


AMBIGUE_RESPONSE = """Je n'ai pas bien compris votre question.

Pourriez-vous la reformuler de manière plus précise ?

**Par exemple :**
- Au lieu de : "Aidez-moi"
  → Précisez : "Quelles sont les règles de la CCN sur les congés payés ?"

- Au lieu de : "C'est quoi ça ?"
  → Précisez : "Qu'est-ce que le RPN ?"

Je suis là pour vous aider sur les thématiques :
- Déontologie notariale
- RH et convention collective
- Assurances professionnelles
"""


REFORMULATION_SUGGESTIONS = {
    "vague": [
        "Pourriez-vous préciser votre question ?",
        "De quel aspect du notariat souhaitez-vous parler ?",
        "Voulez-vous parler de déontologie, RH ou assurances ?"
    ],
    "trop_generale": [
        "Votre question est très large. Pourriez-vous la préciser ?",
        "Sur quel point spécifique souhaitez-vous des informations ?",
        "Pouvez-vous restreindre le périmètre de votre question ?"
    ]
}
```

---

### ÉTAPE 3 : Intégrer dans le service RAG

**Repo** : `application`
**Fichier** : `services/notaria_rag_service.py` (🔧 À modifier)

```python
from agents.intent_classifier import IntentClassifier, IntentType
from prompts.boundary_responses import (
    HORS_PERIMETRE_RESPONSE,
    CONSEIL_PERSONNALISE_RESPONSE,
    AMBIGUE_RESPONSE
)


class NotariaRAGService:
    def __init__(self, ...):
        # ... existant
        self.intent_classifier = IntentClassifier(openai_client)


    async def query(self, question: str) -> dict:
        # 🆕 ÉTAPE 0 : Classification d'intention (AVANT tout le reste)
        intent = await self.intent_classifier.classify(question)

        # 🆕 Gestion des cas limites
        if intent == IntentType.HORS_PERIMETRE:
            return {
                "answer": HORS_PERIMETRE_RESPONSE,
                "sources": [],
                "intent": intent.value,
                "handled_by": "boundary_detection"
            }

        if intent == IntentType.CONSEIL_PERSONNALISE:
            return {
                "answer": CONSEIL_PERSONNALISE_RESPONSE,
                "sources": [],
                "intent": intent.value,
                "handled_by": "boundary_detection"
            }

        if intent == IntentType.AMBIGUE:
            return {
                "answer": AMBIGUE_RESPONSE,
                "sources": [],
                "intent": intent.value,
                "handled_by": "boundary_detection"
            }

        # ✅ Si PERIMETRE_NOTARIAL : continuer le pipeline normal
        # ÉTAPE 1 : Classifier le domaine
        domain = await self.domain_classifier.classify(question)

        # ÉTAPE 2 : Recherche vectorielle
        # ...

        # ÉTAPE 3 : Reranking
        # ...

        # ÉTAPE 4 : Génération réponse
        # ...
```

---

## 📊 Gains attendus

### Sécurité juridique

| Risque | Avant | Après |
|--------|-------|-------|
| **Hallucinations** | Fréquent | Éliminé |
| **Conseil personnalisé** | Non détecté | Bloqué + redirection |
| **Hors périmètre** | Répond quand même | Refus poli |

### Crédibilité

- ✅ Reconnaissance claire des limites
- ✅ Redirection vers ressources appropriées
- ✅ Pas de fausse promesse
- ✅ Image professionnelle renforcée

---

## 🧪 Tests & Validation

### Tests unitaires

```python
# tests/test_intent_classifier.py
import pytest
from agents.intent_classifier import IntentClassifier, IntentType

@pytest.mark.asyncio
async def test_hors_perimetre():
    classifier = IntentClassifier(openai_client)

    questions = [
        "Quelle est la météo ?",
        "Comment cuisiner un bœuf bourguignon ?",
        "Qui a gagné le match hier ?",
        "Convertis 100€ en dollars"
    ]

    for q in questions:
        intent = await classifier.classify(q)
        assert intent == IntentType.HORS_PERIMETRE, f"Échec pour : {q}"


@pytest.mark.asyncio
async def test_conseil_personnalise():
    classifier = IntentClassifier(openai_client)

    questions = [
        "Puis-je vendre ma maison sans notaire ?",
        "Mon patron peut-il me licencier ?",
        "Que dois-je faire dans mon cas ?",
        "Aidez-moi à décider si je dois signer ce contrat"
    ]

    for q in questions:
        intent = await classifier.classify(q)
        assert intent == IntentType.CONSEIL_PERSONNALISE, f"Échec pour : {q}"


@pytest.mark.asyncio
async def test_perimetre_notarial():
    classifier = IntentClassifier(openai_client)

    questions = [
        "Qu'est-ce que le RPN ?",
        "Quel est le salaire minimum d'un clerc ?",
        "Comment fonctionne l'assurance RCP ?",
        "Quelles sont les obligations LCB-FT ?"
    ]

    for q in questions:
        intent = await classifier.classify(q)
        assert intent == IntentType.PERIMETRE_NOTARIAL, f"Échec pour : {q}"
```

### Tests d'intégration

```python
# tests/test_boundary_handling.py
import pytest

@pytest.mark.asyncio
async def test_hors_perimetre_response():
    """Vérifie que les questions hors périmètre sont bien gérées"""
    rag = NotariaRAGService()

    response = await rag.query("Quelle est la météo ?")

    assert response['intent'] == "HORS_PERIMETRE"
    assert "ne concerne pas le domaine notarial" in response['answer']
    assert len(response['sources']) == 0


@pytest.mark.asyncio
async def test_conseil_personnalise_response():
    """Vérifie que les demandes de conseil sont bien bloquées"""
    rag = NotariaRAGService()

    response = await rag.query("Puis-je vendre ma maison sans notaire ?")

    assert response['intent'] == "CONSEIL_PERSONNALISE"
    assert "conseil personnalisé" in response['answer'].lower()
    assert "CRIDON" in response['answer']  # Redirection
```

---

## 📊 Métriques de monitoring

### Dashboard recommandé

```python
# Logs à ajouter
logger.info("Intent classification", extra={
    "question_id": question_id,
    "intent": intent.value,
    "question_length": len(question),
    "handled_by": "boundary_detection" if intent != IntentType.PERIMETRE_NOTARIAL else "rag_pipeline"
})
```

**Métriques à tracker** :
- % questions hors périmètre
- % demandes conseil personnalisé
- % questions ambigües
- Taux de reformulation (questions ambigües suivies d'une 2e question)

---

## 🔄 Rollback si échec

```python
# Variable de configuration
USE_INTENT_FILTER = True

async def query(self, question: str):
    if USE_INTENT_FILTER:
        intent = await self.intent_classifier.classify(question)
        if intent != IntentType.PERIMETRE_NOTARIAL:
            return self._handle_boundary(intent)

    # Pipeline normal
    # ...
```

---

## 📅 Planning d'implémentation

### Demi-journée 1
- ✅ Créer `intent_classifier.py`
- ✅ Créer `boundary_responses.py`
- ✅ Tests unitaires classificateur (80% précision min)

### Demi-journée 2
- ✅ Intégrer dans `notaria_rag_service.py`
- ✅ Tests d'intégration
- ✅ Validation manuelle sur cas limites
- ✅ Ajustement prompts si nécessaire

---

## ✅ Checklist de déploiement

- [ ] `intent_classifier.py` créé et testé
- [ ] `boundary_responses.py` créé avec réponses validées par métier
- [ ] Tests unitaires : précision >85%
- [ ] Réponses hors périmètre validées juridiquement
- [ ] Redirection vers CRIDON/Chambre validée
- [ ] Intégration dans pipeline RAG
- [ ] Tests d'intégration : 100% passent
- [ ] Logs et métriques en place
- [ ] Variable de rollback activée
- [ ] Validation manuelle sur 20 cas limites

---

## 🎯 Critères de succès

**Déploiement validé si :**
- ✅ **0 hallucination** sur questions hors périmètre
- ✅ **0 conseil personnalisé** donné
- ✅ Précision classification **>85%**
- ✅ Satisfaction utilisateurs sur refus polis **>70%**
- ✅ Taux de reformulation après ambigü **>50%**

---

[← Retour à l'index](./00_INDEX.md) | [Amélioration suivante : Expertise notariale →](./04_expertise_notariale.md)
