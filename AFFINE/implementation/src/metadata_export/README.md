# 📤 Scripts d'export métadonnées

Ce dossier contient les scripts pour **exporter les métadonnées enrichies** depuis le repo `bible_notariale` vers le repo `application` (Neo4j).

---

## 🎯 Objectif

Permettre aux **experts métier** de :
1. Enrichir les métadonnées dans `bible_notariale`
2. Exporter facilement vers Neo4j (chatbot)
3. Maintenir à jour sans risque de casse

---

## 📋 Scripts disponibles

### 1. `export_to_neo4j.py` (Principal)

**Quoi** : Exporte TOUTES les métadonnées enrichies vers Neo4j

**Utilisation** :
```bash
python3 export_to_neo4j.py \
  --source ../../../../_metadata/index_complet.json \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-password your_password
```

**Options** :
- `--source` : Chemin vers `index_complet.json` (bible_notariale)
- `--neo4j-uri` : URI Neo4j (défaut: bolt://localhost:7687)
- `--neo4j-user` : User Neo4j (défaut: neo4j)
- `--neo4j-password` : Password Neo4j (REQUIS)
- `--dry-run` : Mode dry-run (affiche sans modifier)

**Ce qui est exporté** :
- ✅ Classification 5 niveaux (type_document, sources_document, domaines_metier, thématiques, vocabulaire)
- ✅ Vocabulaire spécifique (termes + synonymes + définitions)
- ✅ Relations Document →[MENTIONNE]→ Terme

**Durée** : ~2-3 minutes pour 242 documents

---

### 2. `export_ontology.py`

**Quoi** : Exporte l'ontologie complète (domaines, thématiques, termes, relations)

**Utilisation** :
```bash
python3 export_ontology.py \
  --source ../../../../_metadata/ontology.json \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-password your_password
```

**Ce qui est exporté** :
- ✅ Nœuds Domaine (RH, DEONTOLOGIE, ASSURANCES)
- ✅ Nœuds Thématique
- ✅ Nœuds Terme
- ✅ Relations Domaine →[CONTIENT]→ Thématique
- ✅ Relations Thématique →[INCLUT]→ Terme
- ✅ Relations Terme →[SYNONYME_DE]→ Terme

---

### 3. `export_vocabulary.py`

**Quoi** : Exporte UNIQUEMENT le vocabulaire spécifique

**Utilisation** :
```bash
python3 export_vocabulary.py \
  --source ../../../../_metadata/index_complet.json \
  --neo4j-uri bolt://localhost:7687 \
  --neo4j-password your_password
```

**Cas d'usage** : Mise à jour rapide du vocabulaire sans re-exporter tout

---

### 4. `update_from_experts.py`

**Quoi** : Permet aux experts de mettre à jour le vocabulaire depuis un fichier CSV

**Workflow** :
1. Expert reçoit `vocabulaire_export.csv`
2. Expert enrichit le vocabulaire (ajoute termes, synonymes, définitions)
3. Expert renvoie le CSV
4. Dev exécute `update_from_experts.py` pour injecter les changements

**Utilisation** :
```bash
python3 update_from_experts.py \
  --csv vocabulaire_experts.csv \
  --index ../../../../_metadata/index_complet.json
```

**Effet** : Met à jour `index_complet.json` avec les enrichissements experts

---

## 🔄 Workflow typique

### Scénario 1 : Premier export (initial)

```bash
# 1. Valider les métadonnées (voir ../validation/)
cd ../validation
python3 validate_metadata.py --source ../../../../_metadata/index_complet.json

# 2. Si validation OK, exporter vers Neo4j
cd ../metadata_export
python3 export_to_neo4j.py \
  --source ../../../../_metadata/index_complet.json \
  --neo4j-password your_password
```

---

### Scénario 2 : Mise à jour vocabulaire (experts)

```bash
# 1. Exporter vocabulaire actuel en CSV
python3 export_vocabulary.py \
  --source ../../../../_metadata/index_complet.json \
  --output vocabulaire_export.csv

# 2. Envoyer vocabulaire_export.csv aux experts métier
# (Ils enrichissent le vocabulaire)

# 3. Réceptionner vocabulaire_experts.csv enrichi

# 4. Mettre à jour index_complet.json
python3 update_from_experts.py \
  --csv vocabulaire_experts.csv \
  --index ../../../../_metadata/index_complet.json

# 5. Valider
cd ../validation
python3 validate_metadata.py --source ../../../../_metadata/index_complet.json

# 6. Exporter vers Neo4j
cd ../metadata_export
python3 export_to_neo4j.py \
  --source ../../../../_metadata/index_complet.json \
  --neo4j-password your_password
```

---

### Scénario 3 : Ajout de nouveaux documents

```bash
# 1. Enrichir les nouveaux documents dans bible_notariale
cd bible_notariale/scripts
python3 enrich_categories_metier.py

# 2. Régénérer l'index
python3 index_bible_notariale.py

# 3. Valider
cd AFFINE/implementation/src/validation
python3 validate_metadata.py --source ../../../../_metadata/index_complet.json

# 4. Exporter vers Neo4j
cd ../metadata_export
python3 export_to_neo4j.py \
  --source ../../../../_metadata/index_complet.json \
  --neo4j-password your_password
```

---

## ⚠️ Précautions

### Avant chaque export

1. ✅ **TOUJOURS valider** avant d'exporter :
   ```bash
   cd ../validation
   python3 validate_metadata.py --source path/to/index_complet.json
   ```

2. ✅ **Tester en dry-run** d'abord :
   ```bash
   python3 export_to_neo4j.py --source ... --dry-run
   ```

3. ✅ **Backup Neo4j** avant export massif

---

## 🐛 Dépannage

### Erreur : "Fichier source introuvable"

**Cause** : Le chemin vers `index_complet.json` est incorrect

**Solution** : Vérifier le chemin relatif depuis le dossier courant
```bash
ls ../../../../_metadata/index_complet.json
```

---

### Erreur : "Connection refused to Neo4j"

**Cause** : Neo4j n'est pas démarré ou URI incorrecte

**Solution** :
1. Vérifier que Neo4j tourne : `sudo systemctl status neo4j`
2. Vérifier l'URI : `bolt://localhost:7687` par défaut
3. Vérifier le password Neo4j

---

### Erreur : "Authentication failed"

**Cause** : Password Neo4j incorrect

**Solution** : Vérifier le mot de passe Neo4j
```bash
# Réinitialiser si nécessaire
neo4j-admin set-initial-password new_password
```

---

## 📞 Support

Pour toute question :
1. Consulter la documentation des améliorations : `../FEATURES_A_IMPLEMENTER/`
2. Vérifier les logs d'export
3. Contacter l'équipe dev
