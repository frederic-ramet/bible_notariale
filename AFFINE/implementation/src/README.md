# 🔧 Source - Builds et Scripts

Ce dossier contient les **builds prêts à l'emploi** et les **scripts de gestion** des métadonnées enrichies.

---

## 📁 Structure

```
src/
├── builds/              # 📦 Fichiers JSON prêts à l'emploi
│   ├── index_complet.json (787 KB)
│   ├── domaines_metier_report.json (59 KB)
│   └── vocabulaire_notarial.json (3.9 KB)
│
└── scripts/             # 🔧 Scripts Python de gestion
    ├── metadata_export/
    │   ├── export_to_neo4j.py
    │   ├── export_ontology.py
    │   └── README.md
    └── validation/
        ├── validate_metadata.py
        └── README.md
```

---

## 📦 builds/ - Fichiers à exploiter

**Quoi** : Métadonnées enrichies au format JSON, **prêtes à l'emploi**

**Contenu** :
- ✅ Classification 5 niveaux (242 documents)
- ✅ Vocabulaire spécifique notarial
- ✅ Distribution par domaines métier (RH, DEONTOLOGIE, ASSURANCES)

**Pour qui** : Développeur chatbot (consommation directe)

📖 [Documentation complète builds/](builds/README.md)

---

## 🔧 scripts/ - Scripts de gestion

**Quoi** : Scripts Python pour valider, exporter, maintenir les métadonnées

**Contenu** :
- ✅ Validation avant export (garantie zéro erreur)
- ✅ Export vers Neo4j (ontologie + documents)
- ✅ Mise à jour depuis CSV experts

**Pour qui** : Équipe dev/experts métier (maintenance)

📖 Documentation complète :
- [scripts/validation/README.md](scripts/validation/README.md)
- [scripts/metadata_export/README.md](scripts/metadata_export/README.md)

---

## 🚀 Quick Start (Développeur chatbot)

### 1. Utiliser les builds directement

```python
import json

# Charger l'index complet
with open('src/builds/index_complet.json', 'r') as f:
    index = json.load(f)

documents = index['documents']

# Exemple : Routage sémantique par domaine
for doc in documents:
    domaine = doc['classification']['domaine_metier_principal']
    if domaine == 'RH':
        # Recherche confinée au domaine RH
        print(doc['document_id'])
```

### 2. Export vers Neo4j

```bash
cd scripts/metadata_export
python3 export_to_neo4j.py \
  --source ../../builds/index_complet.json \
  --neo4j-password your_password
```

### 3. Validation (avant mise en production)

```bash
cd scripts/validation
python3 validate_metadata.py --source ../../builds/index_complet.json
```

---

## 🔄 Workflow (Experts métier → Dev)

### Mise à jour métadonnées

```
1. Expert enrichit métadonnées (bible_notariale/scripts)
   ↓
2. Régénération builds (index_complet.json)
   ↓
3. Copie vers src/builds/
   ↓
4. VALIDATION (scripts/validation)
   ↓
5. Export Neo4j (scripts/metadata_export)
   ↓
6. Chatbot consomme les nouvelles métadonnées
```

---

## ⚠️ Bonnes pratiques

1. **TOUJOURS valider** avant d'utiliser un build :
   ```bash
   cd scripts/validation
   python3 validate_metadata.py --source ../../builds/index_complet.json
   ```

2. **TOUJOURS tester en dry-run** avant export :
   ```bash
   cd scripts/metadata_export
   python3 export_to_neo4j.py --source ... --dry-run
   ```

3. **Backup Neo4j** avant export massif

---

## 📊 Statistiques actuelles

- **Documents** : 242
- **Domaines métier** : 3 (RH, DEONTOLOGIE, ASSURANCES)
- **Vocabulaire** : ~300 termes notariaux
- **Taux de complétude** : 100% (tous les documents enrichis)

---

## 📞 Support

Questions :
1. Builds : voir [builds/README.md](builds/README.md)
2. Scripts : voir [scripts/validation/README.md](scripts/validation/README.md) et [scripts/metadata_export/README.md](scripts/metadata_export/README.md)
3. Implémentation : voir [../FEATURES_A_IMPLEMENTER/](../FEATURES_A_IMPLEMENTER/)

---

**Dernière mise à jour** : 2025-11-22
**Version** : 1.0
