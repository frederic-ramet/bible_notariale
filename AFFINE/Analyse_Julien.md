# 📄 RAPPORT D'AUDIT ET FEUILLE DE ROUTE DE REMÉDIATION TECHNIQUE

## 1. SYNTHÈSE

L'audit de l'architecture actuelle révèle que la couche ontologique n'est pas exploitée dans la version actuelle. Il s'agit, à l'heure actuelle, d'une recherche vectorielle naïve qui expose le système à des hallucinations juridiques (mélange de contextes, anachronismes réglementaires...).

Pour garantir la fiabilité requise par la profession notariale, il est impératif de restaurer l'architecture "Double Helix" (Vecteur + Graphe Ontologique) initialement conçue. Ce plan d'action en 5 étapes vise à réintroduire la structuration sémantique et le contrôle temporel.

---

## 2. PLAN D'IMPLÉMENTATION DÉTAILLÉ DES QWICK-WINS

### ÉTAPE 1 : Restauration et extension de la dorsale ontologique
**Objectif :** Transformer l'ontologie passive (`.owl`) en filtre actif de recherche.

**Action :**
1.  **Réintégration :** Le fichier `notaria_ontology.owl` ne doit plus être un simple dictionnaire de synonymes. Il doit définir la taxonomie stricte des documents.
2.  **Extension des domaines :** Ajouter une classe racine `DomaineMetier` dans l'ontologie pour segmenter le corpus.
    *   *Classes :* `DroitImmobilier`, `DroitDeLaFamille`, `DroitDesSocietes`, `Fiscalite`, `Deontologie`.
    *   *Propriétés :* `est_regi_par`, `appartient_au_domaine`.

**Implémentation Technique (Neo4j / OntologyService) :**
```cypher
// Injection de la taxonomie dans le Graph
MERGE (d:Domaine {nom: "DroitImmobilier"})
MERGE (c:Concept {nom: "Vente en l'état futur d'achèvement"})
MERGE (c)-[:APPARTIENT_A]->(d)
// Les documents ingérés devront être liés à ces nœuds Domaines
```

---

### ÉTAPE 2 : Chunking Sémantique (Context-Aware)
**Objectif :** Arrêter le découpage arbitraire (512 tokens) qui brise l'unité légale des articles.

**Action :** Utiliser la structure détectée par `Docling` pour un découpage intelligent.
1.  **Unité Atomique :** 1 Article de loi = 1 Chunk. 1 Clause de contrat = 1 Chunk.
2.  **Enrichissement du Chunk :** Chaque chunk doit porter en métadonnées son chemin hiérarchique (ex: "Titre I > Chapitre 2 > Section 4 > Article 12").

**Implémentation (Python) :**
```python
# Au lieu de split par tokens, on split par structure logique
def semantic_chunking(document_structure):
    chunks = []
    for section in document_structure.sections:
        # Le contexte parent est injecté dans le texte du chunk pour l'embedding
        context_header = f"{document.title} > {section.path}"
        chunk_content = f"{context_header}\n{section.text}"
        chunks.append(Chunk(content=chunk_content, meta={"type": "Article"}))
    return chunks
```

---

### ÉTAPE 3 : Filtrage temporel strict (Time-Travel Logic)
**Objectif :** Empêcher le RAG de citer des textes abrogés ou futurs.

**Action :**
1.  **Métadonnées Temporelles :** Chaque nœud `Document` et `Chunk` dans Neo4j reçoit les attributs : `validity_start`, `validity_end`, `status` (VIGUEUR/ABROGE).
2.  **Injection au Query Time :** Le moteur de recherche doit accepter un paramètre `reference_date`.

_à voir pour les documents sans date !_
**Implémentation (Cypher) :**
```cypher
// Filtre dur avant la recherche vectorielle
MATCH (d:Document)-[:CONTAINS]->(c:Chunk)
WHERE d.validity_start <= $query_date 
  AND (d.validity_end IS NULL OR d.validity_end >= $query_date)
// Seulement ensuite, on calcule la similarité vectorielle sur ces chunks
CALL db.index.vector.queryNodes('chunk_embeddings', 10, $embedding) 
YIELD node AS c, score
```

---

### ÉTAPE 4 : Connexion Neuro-Symbolique (ReAct + Ontologie)
**Objectif :** Le cerveau (Agent ReAct) doit consulter la carte (Ontologie) avant de marcher.

**Action :** Modifier le `notaria_rag_service.py`.
1.  **Reasoning (Étape 1) :** L'agent analyse la question pour extraire les concepts clés.
2.  **Ontology Lookup (Étape 2) :** L'agent interroge l'`OntologyService` pour savoir à quel `Domaine` appartiennent ces concepts.
3.  **Targeted Retrieval (Étape 3) :** La recherche vectorielle est confinée au sous-graphe du domaine identifié.

**Workflow de l'Agent :**
> *Utilisateur :* "Quel délai pour la SRU ?"
> *Agent (Reason) :* "SRU" -> Concept identifié.
> *Ontologie :* "SRU" appartient au domaine "DroitImmobilier".
> *Agent (Act) :* Exécute la recherche vectorielle UNIQUEMENT sur les nœuds étiquetés `DroitImmobilier`.

---

### ÉTAPE 5 : Automatisation du "Tribunal" (LLM-as-a-Judge)
**Objectif :** Remplacer la validation humaine fastidieuse par une évaluation massive et continue.

**Action :** Déployer un pipeline d'évaluation automatisé utilisant un modèle à large fenêtre contextuelle et hautes capacités de raisonnement (ex : Gemini 1.5 Pro ou GPT-4o) pour agir comme "Juge Suprême".

**Critères d'évaluation du Juge (Prompt Système) :**
1.  **Exactitude Juridique :** La réponse contredit-elle les textes fournis ?
2.  **Respect Temporel :** Les textes cités étaient-ils en vigueur à la date de référence ?
3.  **Complétude :** Manque-t-il une clause d'exclusion mentionnée dans le contrat source ?

**Output Automatisé :**
Génération d'un rapport de conformité (Score /100) à chaque modification du code ou de la base documentaire, bloquant le déploiement en cas de régression du score de fiabilité.

---

## 3. PLAN D'IMPLÉMENTATION DÉTAILLÉ DU "DENSIFYER"

Actuellement, le pipeline d'ingestion Notaria extrait des entités brutes.
    Exemple : Il trouve "Bail précaire", "Convention d'occupation", "Bail dérogatoire".
    Problème : Pour le système, ce sont trois objets différents. Il n'y a pas de lien logique.
    Conséquence : Si on cherche "Bail commercial", on rate ces documents.

**La proposition DENSIFYER :** C'est un agent autonome qui tourne en tâche de fond. Il prend les entités orphelines, demande à un LLM de les classer dans l'ontologie, et crée les relations hiérarchiques.

**Résultat après densification :** Bail précaire --[EST_UN_TYPE_DE]--> Bail commercial --[APPARTIENT_A]--> Droit Immobilier.

Objectif cible : 
    - Réduction de la dette sémantique : Plus besoin de maintenir l'ontologie à la main. Le système apprend des documents qu'il ingère.
    - Performance de recherche : Grâce aux alias générés par le Densifyer, si un utilisateur tape "compromis", le système trouve les documents parlant de "promesse synallagmatique de vente".
    - Scalabilité : On peut ingérer 10 000 documents ; le Densifyer nettoiera le bazar sémantique automatiquement la nuit.

#### Architecture

    1. Harvesting : Identification des nœuds "orphelins" dans Neo4j (entités extraites mais non reliées à l'ontologie).
    2. Reasoning (densification) : Envoi au LLM (GPT-0SS-20B ou modèle mini) avec un set de prompts adapté au type d'extraction choisi : droit notarial, recherche de dates, recherche de personnes... Le but est d'extraire les documents et les informations sous différents angles/perspectives.
    3. Graph injection : Écriture des relations canoniques et des alias dans Neo4j.
    4. Validation : Génération du fichier CSV pour validation humaine ou via le Tribunal.


---

## 4. OPTIMISATION VECTOR SEARCH PAR MÉTADONNÉES 

Les métadonnées offrent un gain réel de pertinence si elles sont utilisées pour structurer l'espace vectoriel et le contexte. Le post-filtering s'est montré décevant dans la majorité des projets RAG, toute la subtilité est dans la structure de l'information et le ciblage de l'information.

#### Problème :
Si tu embeddes le texte brut : "Article 12 : Le mandataire répond de celui qu'il s'est substitué."
Le vecteur est générique. Il y a des "Article 12" dans le Code Civil, le Code de Commerce, le RPN... Le RAG va se perdre.

La Solution (Metadata Injection) :
On injecte la hiérarchie (métadonnée structurelle) directement dans le texte qui est vectorisé.

#### Implémentation :
Au lieu d'embedder chunk.text, tu embeddes :

```python
# Format: [Métadonnée 1] [Métadonnée 2] > Contenu
vector_input = f"Contexte: {doc.titre} > {chapitre.titre} > Article {article.num} | Contenu: {chunk.text}"
```

    Résultat : Le vecteur "sait" mathématiquement qu'il appartient au Code Civil.
    Performance : La séparation sémantique dans l'espace vectoriel est drastiquement améliorée.

---

## 5. PRÉ-FILTRAGE HYBRIDE (HARD FILTERING) POUR LE GRAPH

Au lieu d'utiliser les métadonnées (Date, Catégorie, Juridiction) après la recherche pour trier les résultats (post-processing), nous les utilisons avant pour restreindre l'espace de recherche vectoriel.

#### Implémentation technique (Neo4j)

Nous basculons d'une recherche purement vectorielle à une exécution en deux temps au sein de la même requête Cypher :

    - Phase 1 (Symbolique) : Identification du sous-graphe pertinent via l'agent "REASON".
    Exemple : Si la question concerne "La fiscalité en 2024", le moteur isole instantanément les nœuds Document tagués FISCALITÉ et dont la date_validité couvre 2024.

    - Phase 2 (Vectorielle) : L'algorithme KNN (K-Nearest Neighbors) n'est exécuté que sur les chunks liés à ce sous-graphe réduit.

#### Gains Attendus

- Performance : Vitesse de recherche multipliée par 10 sur les gros volumes (on ne scanne pas l'inutile).
- Fiabilité : Élimination mathématique des hallucinations liées à des documents hors périmètre (ex : confondre une règle RH et une règle immobilière).

---

## 6. PARENT DOCUMENT RETRIEVER

Il existe une contradiction fondamentale dans le RAG :
- Pour chercher, il faut des fragments courts et précis (Micro-Chunks).
- Pour répondre, le LLM a besoin de paragraphes entiers et structurés (Macro-Chunks).

Le "Parent Retriever" découple ces deux besoins. Nous allons restructurer le stockage dans Neo4j :

    Nœud Parent (Macro-Chunk) : Stocke une section complète (ex : un article de loi entier, une clause contractuelle complète). Il n'est pas vectorisé pour la recherche.

    Nœuds Enfants (Micro-Chunks) : Le Parent est découpé en 3 ou 4 phrases clés. Ce sont elles qui sont vectorisées.

    Relation : (Child)-[:PART_OF]->(Parent).

#### Workflow au Runtime

    Le système cherche les vecteurs les plus proches parmi les Enfants (très haute précision).

    Au lieu de renvoyer l'enfant, le système remonte la relation [:PART_OF] pour récupérer le Parent.

    Le LLM reçoit le Parent complet.

#### Gains Attendus

- Cohérence Juridique : Le LLM ne travaille plus sur des phrases tronquées mais sur des unités légales complètes.
- Précision : On détecte des nuances fines (grâce aux petits chunks) sans perdre la vue d'ensemble.

---

## Perspectives

Une fois ces fondations posées, nous ouvrirons la voie à une étape clé : le Graph Clustering (détection de communautés). Passer du stockage de l'information à la découverte de connaissances.

En utilisant les algorithmes de Graph Data Science (GDS) de Neo4j (comme l'algorithme de Louvain), nous pourrons laisser le système découvrir lui-même des liens thématiques non explicites.

    Exemple : Le système détectera que les documents parlant de "Panneaux photovoltaïques" (Immobilier) sont souvent liés sémantiquement aux "Baux emphytéotiques" (Droit rural), créant des méta-catégories dynamiques pour suggérer des connexions invisibles aux notaires juniors.

Je bosse dessus, c'est encore early de mon côté !