# Bible Notariale

**Base documentaire complète pour les professionnels du notariat français**

📚 **242 documents** | 📅 **2019-2025** | 🔄 Mise à jour : 21/11/2025

---

## Présentation

Ce dépôt centralise la documentation professionnelle du notariat français :

- **Circulaires et instructions** du Conseil Supérieur du Notariat (CSN)
- **Convention Collective Nationale** et ses avenants (IDCC 2205)
- **Accords de branche** négociés entre partenaires sociaux
- **Bulletins d'actualité** (Fil-Infos) pour la veille juridique
- **Guides pratiques** et documentation métier
- **Textes réglementaires** (décrets, ordonnances)
- **Assurances** et prévoyance professionnelle
- **Données immobilières** et observatoires

---

## Catégories documentaires

Cliquez sur une catégorie pour accéder à la liste complète des documents :

---

## Vue d'ensemble

### Par type de document

| Catégorie | Nombre | Période |
|-----------|--------|---------|

### Par année

| Année | Documents |
|-------|-----------|
| 2025 | 155 |
| 2024 | 31 |
| 2023 | 23 |
| 2022 | 10 |
| 2021 | 8 |
| 2020 | 7 |
| 2019 | 7 |
| 2018 | 1 |

---

## Système d'indexation et métadonnées

Ce dépôt intègre un système complet de métadonnées structurées pour l'outil de **Knowledge Management (KM)**.

### Architecture des données

```
bible_notariale/
├── README.md                           # Ce fichier
├── docs/categories/                    # Pages par catégorie
│   ├── circulaire_csn.md
│   ├── avenant_ccn.md
│   └── ...
├── _metadata/                          # Métadonnées KM
│   ├── index_complet.json             # Index global
│   ├── documents/*.metadata.json      # Métadonnées par document
│   └── vocabulaire_notarial.json      # Lexique avec synonymes
├── _INSTRUCTIONS/                      # Documentation technique
│   └── PLAN_ACTION_INDEX.md
└── sources_documentaires/              # Documents PDF/DOCX/XLSX
```

### Structure des métadonnées KM

Chaque document possède un fichier `.metadata.json` contenant :

- **Identification** : ID unique, titre, date de publication
- **Classification** : Type de document, domaines juridiques, année de référence
- **Vocabulaire spécifique** : Termes techniques avec synonymes (pour enrichir les embeddings)
- **Questions typiques** : Questions fréquentes pour améliorer le matching RAG
- **Relations** : Liens entre documents (remplace, modifie, référence)
- **Mots-clés** : Thématiques principales pour la recherche

### Vocabulaire notarial enrichi

Le fichier `vocabulaire_notarial.json` contient un lexique de termes professionnels avec leurs synonymes :

- **CCN** = Convention Collective Nationale, IDCC 2205
- **CSN** = Conseil Supérieur du Notariat
- **LCB-FT** = Lutte anti-blanchiment, LAB, compliance
- **SMO** = Société multi-offices, holding notariale
- **OPCO** = Opérateur de compétences, financement formation
- *Et plus encore...*

### Utilisation pour RAG/GraphRAG

1. **Ingestion** : Charger les `*.metadata.json` avec les documents
2. **Enrichissement** : Utiliser les synonymes pour améliorer les embeddings (+30% pertinence)
3. **Matching** : Exploiter les questions typiques pour le matching sémantique
4. **Graph** : Construire les relations entre documents

---

## Navigation

- **Par catégorie** : Utilisez les liens ci-dessus pour accéder aux listes de documents
- **Recherche** : `Ctrl+F` pour rechercher par mot-clé
- **Téléchargement** : Cliquez sur un document puis sur le bouton de téléchargement GitHub
- **Consultation** : Les PDFs sont consultables directement dans GitHub

---

## Maintenance

Pour régénérer l'index après ajout de documents :

```bash
python3 index_bible_notariale.py
```

Ce script :
- Scanne automatiquement `sources_documentaires/`
- Extrait les métadonnées depuis les noms de fichiers
- Classifie les documents par type
- Génère les fichiers JSON pour le KM tool
- Met à jour le README et les pages de catégories

---

*Généré automatiquement le 21/11/2025 à 10:12 par `index_bible_notariale.py`*
