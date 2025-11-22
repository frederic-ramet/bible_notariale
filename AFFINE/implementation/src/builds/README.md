# 📦 Builds - Métadonnées enrichies (Prêt à l'emploi)

Ce dossier contient les **fichiers JSON prêts à l'emploi** pour le chatbot notarial.

---

## 📄 Fichiers disponibles

### `index_complet.json` (787 KB)

**Quoi** : Index complet des 242 documents avec métadonnées enrichies

**Structure** :
```json
{
  "documents": [
    {
      "document_id": "ccn_avenant_2024",
      "fichier": "CCN/avenant_2024.pdf",
      "classification": {
        "type_document": "Convention collectives Notariat",
        "sources_document": "avenant_ccn",
        "domaines_metier": ["RH"],
        "domaine_metier_principal": "RH",
        "thematiques": ["Rémunération", "Temps de travail"]
      },
      "vocabulaire_specifique": [
        {
          "terme": "Convention Collective Nationale",
          "synonymes": ["CCN", "convention collective"],
          "definition": "Accord négocié entre partenaires sociaux..."
        }
      ]
    }
  ]
}
```

**Utilisation** :
- Export vers Neo4j (voir `../scripts/metadata_export/`)
- Alimentation vector database
- Routage sémantique (domaines_metier)
- Expansion requête (vocabulaire_specifique)

---

### `domaines_metier_report.json` (59 KB)

**Quoi** : Rapport de distribution des documents par domaine métier

**Structure** :
```json
{
  "summary": {
    "total_documents": 242,
    "RH": 156,
    "DEONTOLOGIE": 48,
    "ASSURANCES": 38
  },
  "documents_by_domain": {
    "RH": ["ccn_avenant_2024", ...],
    "DEONTOLOGIE": ["guide_deonto_2023", ...],
    "ASSURANCES": ["assurance_rc_2024", ...]
  }
}
```

**Utilisation** :
- Statistiques de couverture
- Validation de l'équilibre documentaire
- Monitoring distribution par domaine

---

### `vocabulaire_notarial.json` (3.9 KB)

**Quoi** : Vocabulaire notarial unique extrait de tous les documents

**Structure** :
```json
{
  "vocabulaire": [
    {
      "terme": "Acte authentique",
      "synonymes": ["acte notarié"],
      "definition": "Document rédigé par un notaire...",
      "documents": ["guide_actes_2023", "procedure_authentification"]
    }
  ]
}
```

**Utilisation** :
- Expansion de requêtes par synonymes
- Glossaire métier
- Détection entités nommées

---

## 🔄 Mise à jour des builds

Les builds sont régénérés après chaque enrichissement métadonnées :

```bash
# 1. Enrichir les métadonnées (bible_notariale/scripts)
cd ../../../scripts
python3 enrich_categories_metier.py

# 2. Régénérer l'index
python3 index_bible_notariale.py

# 3. Copier les nouveaux builds
cd ../AFFINE/implementation
cp ../../../_metadata/index_complet.json src/builds/
cp ../../../_metadata/domaines_metier_report.json src/builds/
cp ../../../_metadata/vocabulaire_notarial.json src/builds/
```

---

## ✅ Validation avant utilisation

**TOUJOURS valider** avant d'utiliser les builds :

```bash
cd ../scripts/validation
python3 validate_metadata.py --source ../../builds/index_complet.json
```

**Code retour** :
- `0` : Builds valides, prêt à l'emploi
- `1` : Erreurs détectées, corriger avant utilisation

---

## 📊 Export vers Neo4j

Une fois validé, exporter vers Neo4j :

```bash
cd ../scripts/metadata_export
python3 export_to_neo4j.py \
  --source ../../builds/index_complet.json \
  --neo4j-password your_password
```

---

## 📞 Support

Questions sur les builds :
1. Vérifier la structure attendue dans `../../FEATURES_A_IMPLEMENTER/05_enrichissement_metadata.md`
2. Consulter les scripts de validation/export dans `../scripts/`
3. Contacter l'équipe dev

---

**Dernière mise à jour** : 2025-11-22
**Version** : 1.0 (242 documents, 3 domaines métier)
