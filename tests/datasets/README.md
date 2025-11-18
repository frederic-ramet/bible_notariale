# Dataset de Test pour le Chatbot Bible Notariale

## 📋 Vue d'ensemble

Ce répertoire contient le dataset de test pour valider les performances du futur chatbot RAG (Retrieval-Augmented Generation) de la Bible Notariale. L'objectif est de s'assurer que le chatbot cite les bonnes sources documentaires et fournit des réponses pertinentes aux questions des notaires.

## 🎯 Objectifs du dataset

### Validation multi-niveaux
1. **Précision de récupération** : Le chatbot identifie-t-il les bons documents sources ?
2. **Précision de citation** : Le chatbot cite-t-il correctement les références (circulaires, avenants, articles) ?
3. **Pertinence de la réponse** : Les éléments clés attendus sont-ils présents dans la réponse ?
4. **Gestion des cas limites** : Comment le chatbot se comporte-t-il face à des questions hors périmètre ou très larges ?

### Couverture thématique
- **70% déontologie** (35 questions) : cœur de métier des questions à la Chambre des Notaires
- **20% juridique spécifique** (10 questions) : CCN, avenants, statut, organisation professionnelle
- **10% edge cases** (5 questions) : questions larges, hors périmètre, comportement du chatbot

## 📊 Structure du dataset

Le fichier `chatbot_test_dataset.json` contient un tableau de questions structurées comme suit :

```json
{
  "id": "Q001",
  "categorie": "deontologie|juridique|edge_case",
  "difficulte": "facile|moyen|pointu",
  "question": "La question posée par le notaire",
  "documents_sources_attendus": [
    "document_id_1",
    "document_id_2"
  ],
  "elements_cles_reponse": [
    "Point clé 1 qui devrait apparaître dans la réponse",
    "Point clé 2 qui devrait apparaître dans la réponse"
  ],
  "reponse_attendue_resumee": "Résumé en 2-3 phrases de ce que devrait répondre le chatbot",
  "articles_references": [
    "Article X du Code de déontologie",
    "Article Y du RPN"
  ],
  "necessite_multi_documents": false,
  "notes_validation": "Notes de l'expert métier après validation"
}
```

## 🏗️ Méthodologie de création

### 1. Sources d'inspiration
Les questions ont été créées en analysant :
- Les 245 documents indexés dans `_metadata/index_complet.json`
- Les ~1000 questions typiques déjà présentes dans les métadonnées individuelles
- Focus particulier sur :
  - Circulaires CSN (20 documents)
  - Guides pratiques (28 documents)
  - Fil-Info (153 documents)
  - Documents spécifiques à la déontologie et au RPN

### 2. Répartition par difficulté

#### Questions faciles (35%)
- Définitions de base
- Règles déontologiques simples
- Questions à réponse directe dans un seul document
- Ex: "Qu'est-ce que la LCB-FT ?"

#### Questions moyennes (40%)
- Situations pratiques courantes
- Interprétation de règles
- Nécessitent de croiser quelques informations
- Ex: "Quelles sont les obligations du notaire en matière de médiation de la consommation ?"

#### Questions pointues (25%)
- Cas complexes ou rares
- Interprétation fine de textes
- Croisement de plusieurs documents
- Références juridiques précises
- Ex: "Dans quel cas un notaire peut-il déroger au secret professionnel selon l'article X du code de déontologie ?"

### 3. Variété des types de questions

- **Questions factuelles** : recherche d'information précise
- **Questions procédurales** : "Comment faire X ?"
- **Questions d'interprétation** : "Dans quel cas puis-je..."
- **Questions de références** : "Quel article traite de..."
- **Questions temporelles** : "Qu'est-ce qui a changé en 2024 ?"
- **Questions multi-documents** : nécessitent de croiser plusieurs sources
- **Questions hors périmètre** : pour tester les limites du chatbot

## 🔄 Workflow d'utilisation

### Phase 1 : Création initiale ✅
1. Analyse des documents de la Bible Notariale
2. Génération de 50 questions avec métadonnées complètes
3. Export JSON structuré

### Phase 2 : Validation métier 📋
1. Transmission du dataset à un expert métier (notaire senior, déontologue)
2. Validation de :
   - Pertinence des questions
   - Exactitude des documents sources attendus
   - Complétude des éléments clés de réponse
   - Pertinence des réponses attendues
3. Ajout de notes dans le champ `notes_validation`
4. Correction/enrichissement si nécessaire

### Phase 3 : Test avec le chatbot 🤖
1. Implémentation du chatbot RAG
2. Pour chaque question du dataset :
   - Soumission au chatbot
   - Collecte de la réponse et des sources citées
   - Comparaison avec les valeurs attendues
3. Calcul des métriques de performance

## 📈 Métriques d'évaluation

### Métriques de récupération
- **Recall@K** : % de documents pertinents retrouvés dans les K premiers résultats
- **Precision@K** : % de documents retrouvés qui sont pertinents
- **MRR (Mean Reciprocal Rank)** : position moyenne du premier document pertinent

### Métriques de réponse
- **Présence des éléments clés** : % d'éléments clés mentionnés dans la réponse
- **Exactitude des citations** : % de citations correctement attribuées
- **Complétude** : la réponse couvre-t-elle tous les aspects attendus ?

### Métriques de comportement
- **Taux de refus approprié** : % de questions hors périmètre correctement identifiées
- **Confiance calibrée** : le chatbot exprime-t-il une confiance proportionnelle à la qualité de sa réponse ?

## 🛠️ Utilisation du dataset

### Format de test automatisé (exemple Python)
```python
import json

# Charger le dataset
with open('chatbot_test_dataset.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# Tester chaque question
results = []
for qa in dataset['qa_pairs']:
    # Soumettre au chatbot
    response = chatbot.query(qa['question'])

    # Comparer avec les attentes
    score = evaluate_response(
        response=response,
        expected_docs=qa['documents_sources_attendus'],
        expected_keys=qa['elements_cles_reponse']
    )

    results.append({
        'question_id': qa['id'],
        'score': score,
        'sources_found': response.sources,
        'missing_keys': identify_missing_keys(response, qa)
    })

# Générer rapport
generate_evaluation_report(results)
```

## 📝 Notes importantes

### Évolution du dataset
Ce dataset est **vivant** et doit être enrichi au fil du temps :
- Ajout de nouvelles questions basées sur les cas réels
- Ajustement des réponses attendues selon les retours métier
- Mise à jour lors de l'ajout de nouveaux documents à la Bible Notariale
- Versionnage du dataset pour tracer les évolutions

### Limitations connues
- Les questions sont en français uniquement
- Focus sur la déontologie et le droit notarial français
- Certaines questions peuvent avoir plusieurs réponses valides
- La validation métier est essentielle avant utilisation

### Maintenance
- **Propriétaire** : Équipe produit Bible Notariale
- **Fréquence de mise à jour** : Trimestrielle ou lors d'ajouts documentaires majeurs
- **Validation** : Par expert métier à chaque mise à jour

## 📚 Références

- Index complet des documents : `/_metadata/index_complet.json`
- Vocabulaire notarial : `/_metadata/vocabulaire_notarial.json`
- Documentation technique : `/_INSTRUCTIONS/PLAN_ACTION_INDEX.md`

---

**Dernière mise à jour** : 2025-11-18
**Version du dataset** : 1.0
**Nombre de questions** : 50
