# ✅ Scripts de validation métadonnées

Ce dossier contient les scripts pour **valider la qualité** des métadonnées avant export vers Neo4j.

---

## 🎯 Objectif

**Garantir zéro erreur** lors de l'export vers Neo4j en validant :
1. Structure JSON conforme
2. Tous les champs requis présents
3. Valeurs cohérentes (domaines valides, types de documents corrects)
4. Vocabulaire bien formé

---

## 📋 Scripts disponibles

### `validate_metadata.py` (Principal)

**Quoi** : Valide l'index_complet.json complet

**Utilisation** :
```bash
python3 validate_metadata.py --source ../../builds/index_complet.json
```

**Options** :
- `--source` : Chemin vers index_complet.json (REQUIS)
- `--strict` : Mode strict (warnings = erreurs)

**Validations effectuées** :

1. ✅ **Structure JSON** : Format JSON valide
2. ✅ **Champs requis** : `document_id`, `fichier`, `classification` présents
3. ✅ **Classification 5 niveaux** :
   - `type_document` dans liste autorisée
   - `sources_document` cohérente
   - `domaines_metier` = RH, DEONTOLOGIE, ou ASSURANCES
   - `domaine_metier_principal` dans `domaines_metier`
   - `thematiques` non vide
4. ✅ **Vocabulaire spécifique** :
   - Structure `{terme, synonymes, definition}` valide
   - Pas de termes vides

**Output** :

```
🔍 Validation de 242 documents...

============================================================
📋 RAPPORT DE VALIDATION
============================================================

✅ AUCUNE ERREUR - Métadonnées valides !

============================================================

✅ Validation réussie - Prêt pour l'export
```

**Code retour** :
- `0` : Succès, prêt pour export
- `1` : Échec, corriger les erreurs

---

## 🔄 Workflow recommandé

### Avant chaque export vers Neo4j

```bash
# 1. TOUJOURS valider avant export
cd AFFINE/implementation/src/scripts/validation
python3 validate_metadata.py --source ../../builds/index_complet.json

# 2. Si validation OK (code retour 0), procéder à l'export
if [ $? -eq 0 ]; then
  cd ../metadata_export
  python3 export_to_neo4j.py \
    --source ../../builds/index_complet.json \
    --neo4j-password your_password
fi
```

---

### Après enrichissement métadonnées

```bash
# 1. Enrichir les métadonnées
cd bible_notariale/scripts
python3 enrich_categories_metier.py

# 2. Régénérer l'index
python3 index_bible_notariale.py

# 3. Copier le nouveau build
cp ../_metadata/index_complet.json ../AFFINE/implementation/src/builds/

# 4. VALIDER IMMÉDIATEMENT
cd ../AFFINE/implementation/src/scripts/validation
python3 validate_metadata.py --source ../../builds/index_complet.json

# 5. Corriger les erreurs si nécessaire
# (Relire le rapport, modifier les métadonnées, régénérer l'index, revalider)

# 6. Export seulement si validation OK
```

---

## ❌ Exemples d'erreurs détectées

### Erreur 1 : Domaine métier invalide

```
❌ fil_infos_fil_info_265 : domaine invalide : FISCAL_SUCCESSION
```

**Cause** : Le domaine FISCAL_SUCCESSION n'existe plus (seulement RH, DEONTOLOGIE, ASSURANCES)

**Solution** : Corriger l'enrichissement dans `enrich_categories_metier.py`

---

### Erreur 2 : domaine_metier_principal pas dans domaines_metier

```
❌ ccn_avenant_2024 : domaine_metier_principal (PROCEDURE) pas dans domaines_metier
```

**Cause** : Incohérence entre domaine principal et liste des domaines

**Solution** : Vérifier la logique de sélection du domaine principal

---

### Erreur 3 : Vocabulaire mal formé

```
❌ fil_infos_fil_info_128 : vocabulaire[2] : terme vide
```

**Cause** : Un élément du vocabulaire a un terme vide

**Solution** : Nettoyer le vocabulaire, supprimer les entrées vides

---

## ⚠️  Mode strict

En mode strict, les **warnings deviennent des erreurs**.

**Utilisation** :
```bash
python3 validate_metadata.py --source path/to/index.json --strict
```

**Quand l'utiliser** :
- Avant un export en production
- Pour garantir une qualité maximale
- Quand on veut forcer la complétude (pas de champs vides)

**Exemple** :
```
⚠️  fil_infos_fil_info_100 : thematiques vide
```

En mode normal : Warning (validation passe)
En mode strict : Erreur (validation échoue)

---

## 🐛 Dépannage

### Erreur : "JSON invalide"

**Cause** : Le fichier index_complet.json est malformé

**Solution** :
1. Ouvrir le fichier dans un éditeur
2. Vérifier la syntaxe JSON (virgules, accolades, guillemets)
3. Utiliser un validateur JSON en ligne si nécessaire

---

### Erreur : "Fichier introuvable"

**Cause** : Le chemin vers index_complet.json est incorrect

**Solution** : Vérifier le chemin relatif
```bash
ls ../../builds/index_complet.json
```

---

### Nombreuses erreurs "domaine invalide"

**Cause** : Les anciens domaines (IMMOBILIER, PROCEDURE, FISCAL_SUCCESSION) sont encore présents

**Solution** : Réexécuter la migration
```bash
cd bible_notariale/scripts
python3 migrate_metadata_structure.py
python3 index_bible_notariale.py
```

---

## 📞 Support

Pour toute question sur la validation :
1. Consulter le rapport d'erreurs généré
2. Vérifier la structure attendue dans `../../FEATURES_A_IMPLEMENTER/05_enrichissement_metadata.md`
3. Contacter l'équipe dev
