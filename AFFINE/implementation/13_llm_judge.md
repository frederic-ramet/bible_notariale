# ⚖️ Amélioration #13 : LLM-as-a-Judge

[← Retour à l'index](./00_INDEX.md)

---

## 📊 Fiche technique

| Attribut | Valeur |
|----------|--------|
| **Priorité** | 🟢 MOYEN |
| **Impact** | ⭐⭐⭐ (Monitoring qualité) |
| **Effort** | 1 jour |
| **Statut** | 📋 À faire |
| **Dépendances** | Toutes les autres améliorations |
| **Repo** | `application` |

---

## 🎯 Problème identifié

### Observations

**Problème** : Pas de mesure automatique de la qualité des réponses

**Symptômes** :
- Évaluation manuelle coûteuse (Julien teste 15 questions manuellement)
- Pas de monitoring continu de la qualité
- Régressions détectées tardivement
- Impossible de mesurer impact des améliorations à grande échelle

**Impact** :
- ❌ Détection de régressions tardive
- ❌ Pas de métriques automatiques
- ❌ Validation manuelle chronophage
- ❌ Impossible d'A/B tester à grande échelle

**Exemple concret** :

```
Question : "Combien de congés payés ai-je en tant que clerc ?"

Réponse générée : "Selon la CCN Notariat, les clercs bénéficient de 30 jours
ouvrables de congés payés par an, acquis à raison de 2.5 jours par mois."

❌ Sans LLM-as-a-Judge :
- Impossible de savoir si cette réponse est bonne automatiquement
- Besoin d'un humain pour valider

✅ Avec LLM-as-a-Judge :
- LLM évalue automatiquement la réponse selon critères :
  * Exactitude : 9/10 (info correcte)
  * Complétude : 8/10 (manque info sur période de référence)
  * Format : 10/10 (structure claire)
  * Sources : 10/10 (CCN citée)
- Score global : 9.25/10
- Feedback : "Réponse correcte mais pourrait mentionner la période de référence"
```

---

## 💡 Solution proposée

### Vue d'ensemble

**LLM-as-a-Judge : Évaluation automatique des réponses** :

1. **Après chaque réponse** : LLM juge évalue la qualité
2. **Critères multiples** : Exactitude, complétude, format, sources
3. **Score et feedback** : Note 0-10 + explication
4. **Monitoring continu** : Dashboard avec métriques temps réel

### Architecture

```mermaid
graph LR
    A[Question] --> B[RAG génère réponse]
    B --> C[Réponse]
    C --> D[LLM Judge évalue]
    D --> E[Score + Feedback]
    E --> F[Logs monitoring]
    E --> G{Score < 6 ?}
    G -->|Oui| H[Alerte]
    G -->|Non| I[OK]
```

---

## 🔧 Implémentation détaillée

### Nouveau service : `services/llm_judge.py`

```python
"""
LLM-as-a-Judge : Évaluation automatique de la qualité des réponses
"""

from typing import Dict, List
from dataclasses import dataclass
import json


@dataclass
class JudgeScore:
    """Score d'évaluation du juge"""

    # Scores par critère (0-10)
    exactitude: float  # Information factuelle correcte ?
    completude: float  # Répond complètement à la question ?
    format: float  # Format APRES respecté ?
    sources: float  # Sources citées et pertinentes ?

    # Score global
    score_global: float

    # Feedback textuel
    feedback: str

    # Détails
    strengths: List[str]  # Points forts
    weaknesses: List[str]  # Points faibles
    suggestions: List[str]  # Améliorations suggérées


class LLMJudge:
    """
    Évalue la qualité des réponses générées
    """

    def __init__(self, openai_client):
        self.client = openai_client

    async def evaluate(
        self,
        question: str,
        answer: str,
        context_chunks: List[dict]
    ) -> JudgeScore:
        """
        Évalue une réponse

        Args:
            question: Question posée
            answer: Réponse générée
            context_chunks: Chunks utilisés pour générer la réponse

        Returns:
            Score d'évaluation
        """

        # Construire le prompt d'évaluation
        prompt = self._build_judge_prompt(question, answer, context_chunks)

        # Appeler LLM juge
        response = await self.client.chat.completions.create(
            model="gpt-4o",  # Modèle fort pour juger
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Faible température pour cohérence
            max_tokens=500
        )

        # Parser la réponse JSON
        judge_response = response.choices[0].message.content.strip()

        try:
            scores_dict = json.loads(judge_response)
        except json.JSONDecodeError:
            # Fallback si JSON mal formé
            scores_dict = {
                'exactitude': 5.0,
                'completude': 5.0,
                'format': 5.0,
                'sources': 5.0,
                'feedback': 'Erreur parsing réponse juge',
                'strengths': [],
                'weaknesses': ['Erreur évaluation'],
                'suggestions': []
            }

        # Calculer score global
        score_global = (
            scores_dict['exactitude'] * 0.4 +
            scores_dict['completude'] * 0.3 +
            scores_dict['format'] * 0.15 +
            scores_dict['sources'] * 0.15
        )

        return JudgeScore(
            exactitude=scores_dict['exactitude'],
            completude=scores_dict['completude'],
            format=scores_dict['format'],
            sources=scores_dict['sources'],
            score_global=score_global,
            feedback=scores_dict.get('feedback', ''),
            strengths=scores_dict.get('strengths', []),
            weaknesses=scores_dict.get('weaknesses', []),
            suggestions=scores_dict.get('suggestions', [])
        )

    def _build_judge_prompt(
        self,
        question: str,
        answer: str,
        context_chunks: List[dict]
    ) -> str:
        """
        Construit le prompt d'évaluation
        """

        # Formatter les chunks de contexte
        context_summary = "\n".join([
            f"- {chunk.get('doc_titre', 'Document')}: {chunk.get('text', '')[:200]}..."
            for chunk in context_chunks[:3]  # Limiter à 3 chunks
        ])

        prompt = f"""Évalue la qualité de cette réponse selon les critères définis.

**Question posée** :
{question}

**Réponse générée** :
{answer}

**Contexte documentaire utilisé** :
{context_summary}

Évalue la réponse selon 4 critères (note de 0 à 10 pour chaque) :

1. **Exactitude** : Les informations sont-elles factuellement correctes ?
2. **Complétude** : La réponse répond-elle complètement à la question ?
3. **Format** : Le format APRES (Analyse, Principe, Règle, Sources) est-il respecté ?
4. **Sources** : Les sources sont-elles citées, pertinentes et vérifiables ?

Réponds UNIQUEMENT avec un JSON dans ce format :

{{
  "exactitude": <score 0-10>,
  "completude": <score 0-10>,
  "format": <score 0-10>,
  "sources": <score 0-10>,
  "feedback": "Synthèse en 1-2 phrases",
  "strengths": ["point fort 1", "point fort 2"],
  "weaknesses": ["point faible 1"],
  "suggestions": ["suggestion 1"]
}}
"""

        return prompt


# System prompt pour le juge
JUDGE_SYSTEM_PROMPT = """Tu es un expert en évaluation de réponses juridiques et notariales.

Ta mission : Évaluer la qualité des réponses générées par un chatbot notarial.

Critères d'évaluation :

1. **Exactitude** (0-10) :
   - 10 : Information 100% correcte, vérifiable dans le contexte
   - 7-9 : Information correcte avec nuances mineures manquantes
   - 4-6 : Information partiellement correcte
   - 0-3 : Information incorrecte ou hallucination

2. **Complétude** (0-10) :
   - 10 : Répond complètement à tous les aspects de la question
   - 7-9 : Répond aux aspects principaux, manque détails secondaires
   - 4-6 : Répond partiellement
   - 0-3 : Ne répond pas ou réponse hors sujet

3. **Format** (0-10) :
   - 10 : Format APRES parfaitement respecté (Analyse, Principe, Règle, Sources)
   - 7-9 : Format APRES présent avec sections identifiables
   - 4-6 : Format partiel
   - 0-3 : Pas de structure

4. **Sources** (0-10) :
   - 10 : Sources citées, précises (article, numéro), vérifiables dans le contexte
   - 7-9 : Sources citées mais références imprécises
   - 4-6 : Mention de sources sans précision
   - 0-3 : Pas de sources citées

Sois objectif et rigoureux dans ton évaluation.
"""
```

---

### Intégration dans RAG : `services/notaria_rag_service.py`

```python
"""
Intégration LLM Judge dans le RAG
"""

from services.llm_judge import LLMJudge

class NotariaRAGService:

    def __init__(self):
        # ... autres initialisations
        self.judge = LLMJudge(self.openai_client)

    async def generate_answer(
        self,
        question: str,
        chunks: List[dict],
        intent: str,
        evaluate: bool = True  # Flag pour activer/désactiver évaluation
    ) -> dict:
        """
        Génère une réponse avec évaluation qualité
        """

        # 1. Générer réponse (code existant)
        answer = await self._generate_answer_internal(question, chunks, intent)

        response = {
            "answer": answer,
            "cited_sources": [],  # ...
            "chunks_used": len(chunks)
        }

        # 2. Évaluer la réponse si demandé
        if evaluate:
            judge_score = await self.judge.evaluate(question, answer, chunks)

            response['quality_score'] = {
                'exactitude': judge_score.exactitude,
                'completude': judge_score.completude,
                'format': judge_score.format,
                'sources': judge_score.sources,
                'score_global': judge_score.score_global,
                'feedback': judge_score.feedback
            }

            # Logger le score
            await self._log_quality_score(question, answer, judge_score)

            # Alerte si score faible
            if judge_score.score_global < 6.0:
                await self._alert_low_quality(question, answer, judge_score)

        return response

    async def _log_quality_score(
        self,
        question: str,
        answer: str,
        judge_score: JudgeScore
    ):
        """
        Log le score de qualité dans la base
        """

        await db.insert('quality_scores', {
            'timestamp': datetime.now(),
            'question': question,
            'answer': answer[:500],  # Tronquer si long
            'exactitude': judge_score.exactitude,
            'completude': judge_score.completude,
            'format': judge_score.format,
            'sources': judge_score.sources,
            'score_global': judge_score.score_global,
            'feedback': judge_score.feedback
        })

    async def _alert_low_quality(
        self,
        question: str,
        answer: str,
        judge_score: JudgeScore
    ):
        """
        Alerte si réponse de faible qualité
        """

        logger.warning(f"""
⚠️  RÉPONSE DE FAIBLE QUALITÉ DÉTECTÉE
Score global : {judge_score.score_global}/10

Question : {question}
Feedback : {judge_score.feedback}

Points faibles :
{chr(10).join(f'- {w}' for w in judge_score.weaknesses)}

Suggestions :
{chr(10).join(f'- {s}' for s in judge_score.suggestions)}
        """)

        # Optionnel : envoyer notification Slack/email
```

---

## 📊 Dashboard de monitoring

### Script : `scripts/generate_quality_dashboard.py`

```python
"""
Génère un dashboard de qualité depuis les logs
"""

import asyncio
from datetime import datetime, timedelta


async def generate_quality_report(days: int = 7):
    """
    Génère un rapport de qualité sur les N derniers jours
    """

    # Récupérer scores depuis la base
    scores = await db.query("""
        SELECT *
        FROM quality_scores
        WHERE timestamp >= NOW() - INTERVAL '{days} days'
        ORDER BY timestamp DESC
    """.format(days=days))

    # Statistiques globales
    total = len(scores)
    avg_exactitude = sum(s['exactitude'] for s in scores) / total
    avg_completude = sum(s['completude'] for s in scores) / total
    avg_format = sum(s['format'] for s in scores) / total
    avg_sources = sum(s['sources'] for s in scores) / total
    avg_global = sum(s['score_global'] for s in scores) / total

    # Répartition par tranche de score
    distribution = {
        'Excellent (>8)': sum(1 for s in scores if s['score_global'] > 8),
        'Bon (6-8)': sum(1 for s in scores if 6 <= s['score_global'] <= 8),
        'Faible (<6)': sum(1 for s in scores if s['score_global'] < 6)
    }

    # Top 5 pires réponses
    worst_responses = sorted(scores, key=lambda s: s['score_global'])[:5]

    # Générer rapport markdown
    report = f"""# 📊 Rapport Qualité - {days} derniers jours

**Période** : {datetime.now() - timedelta(days=days)} → {datetime.now()}
**Total réponses évaluées** : {total}

---

## 🎯 Scores moyens

| Critère | Score moyen |
|---------|-------------|
| **Exactitude** | {avg_exactitude:.2f}/10 |
| **Complétude** | {avg_completude:.2f}/10 |
| **Format** | {avg_format:.2f}/10 |
| **Sources** | {avg_sources:.2f}/10 |
| **Score global** | {avg_global:.2f}/10 |

---

## 📈 Répartition

| Tranche | Nombre | Pourcentage |
|---------|--------|-------------|
| Excellent (>8) | {distribution['Excellent (>8)']} | {distribution['Excellent (>8)']/total*100:.1f}% |
| Bon (6-8) | {distribution['Bon (6-8)']} | {distribution['Bon (6-8)']/total*100:.1f}% |
| Faible (<6) | {distribution['Faible (<6)']} | {distribution['Faible (<6)']/total*100:.1f}% |

---

## ⚠️  Top 5 pires réponses

"""

    for i, resp in enumerate(worst_responses, 1):
        report += f"""
### {i}. Score : {resp['score_global']:.2f}/10

**Question** : {resp['question']}
**Feedback** : {resp['feedback']}
**Timestamp** : {resp['timestamp']}

---
"""

    # Sauvegarder rapport
    with open(f'quality_report_{datetime.now().strftime("%Y%m%d")}.md', 'w') as f:
        f.write(report)

    print(f"✅ Rapport généré : quality_report_{datetime.now().strftime('%Y%m%d')}.md")


if __name__ == '__main__':
    asyncio.run(generate_quality_report(days=7))
```

---

## ✅ Tests et validation

### Tests unitaires

```python
"""
Tests pour LLM Judge
"""

import pytest
from services.llm_judge import LLMJudge

@pytest.mark.asyncio
async def test_evaluate_good_answer(openai_client):
    """Test évaluation d'une bonne réponse"""

    judge = LLMJudge(openai_client)

    question = "Combien de congés payés ai-je ?"

    answer = """**Analyse** : La question porte sur le nombre de jours de congés payés.

**Principe** : Selon la CCN Notariat, les clercs bénéficient de congés payés annuels.

**Règle** :
- 30 jours ouvrables de congés payés par an
- Acquis à raison de 2.5 jours par mois de travail effectif

**Sources** :
- CCN Notariat - Article 45 (Congés payés)
"""

    chunks = [
        {'doc_titre': 'CCN Article 45', 'text': 'Les clercs bénéficient de 30 jours...'}
    ]

    score = await judge.evaluate(question, answer, chunks)

    # Vérifier scores élevés
    assert score.exactitude >= 7.0
    assert score.completude >= 7.0
    assert score.format >= 8.0  # Format APRES respecté
    assert score.sources >= 8.0  # Sources citées
    assert score.score_global >= 7.0

@pytest.mark.asyncio
async def test_evaluate_bad_answer(openai_client):
    """Test évaluation d'une mauvaise réponse"""

    judge = LLMJudge(openai_client)

    question = "Combien de congés payés ai-je ?"

    answer = "Je ne sais pas exactement, mais il y a des congés dans le notariat."

    chunks = [
        {'doc_titre': 'CCN Article 45', 'text': 'Les clercs bénéficient de 30 jours...'}
    ]

    score = await judge.evaluate(question, answer, chunks)

    # Vérifier scores faibles
    assert score.exactitude < 6.0  # Info imprécise
    assert score.completude < 5.0  # Ne répond pas vraiment
    assert score.format < 3.0  # Pas de format APRES
    assert score.sources < 3.0  # Pas de sources
    assert score.score_global < 5.0
```

---

## 📈 Impact attendu

### Avant amélioration

- ❌ Pas d'évaluation automatique
- ❌ Tests manuels chronophages
- ❌ Régressions détectées tardivement

### Après amélioration

- ✅ Évaluation automatique 24/7
- ✅ Dashboard de qualité en temps réel
- ✅ Alertes sur réponses faibles
- ✅ Monitoring continu

---

## 📅 Planning d'implémentation

**Total** : 1 jour

### Matin (4h)

- ✅ Créer `llm_judge.py`
- ✅ Implémenter evaluate()
- ✅ Tests unitaires

### Après-midi (4h)

- ✅ Intégrer dans notaria_rag_service.py
- ✅ Créer table quality_scores
- ✅ Script generate_quality_dashboard.py
- ✅ Déploiement

---

## 🎯 Critères de succès

### Critères obligatoires

1. ✅ **Évaluation automatique** : 100% des réponses évaluées
2. ✅ **Corrélation humaine** : Score juge corrélé >80% avec évaluation humaine
3. ✅ **Dashboard fonctionnel** : Rapport généré quotidiennement

---

[← Retour à l'index](./00_INDEX.md)
