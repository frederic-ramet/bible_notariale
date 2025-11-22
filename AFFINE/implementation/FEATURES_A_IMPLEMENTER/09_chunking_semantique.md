# 📄 Amélioration #9 : Chunking Sémantique

[← Retour à l'index](./00_INDEX.md)

---

## 📊 Fiche technique

| Attribut | Valeur |
|----------|--------|
| **Priorité** | 🟡 LONG TERME |
| **Impact** | ⭐⭐⭐ (Qualité des chunks) |
| **Effort** | 1.5 jours |
| **Statut** | 📋 À faire |
| **Dépendances** | Aucune (indépendant) |
| **Repo** | `application` |

---

## 🎯 Problème identifié

### Observations

**Problème** : Le chunking actuel coupe les documents de manière arbitraire (taille fixe)

**Symptômes** :
- Chunks coupés au milieu d'une phrase ou d'un paragraphe
- Perte de contexte sémantique
- Informations fragmentées entre plusieurs chunks

**Impact** :
- ❌ Chunks non cohérents sémantiquement
- ❌ Contexte perdu (chunk ne fait pas sens seul)
- ❌ LLM doit reconstituer le sens depuis plusieurs chunks

**Exemple concret** :

```
Document original :

"Article 45 - Congés payés

Les clercs de notaire bénéficient de 30 jours ouvrables de congés payés par an,
acquis à raison de 2.5 jours par mois de travail effectif.

La période de référence court du 1er juin de l'année N au 31 mai de l'année N+1.

Les congés doivent être pris..."

❌ Chunking par taille fixe (200 caractères) :

Chunk 1 : "Article 45 - Congés payés\n\nLes clercs de notaire bénéficient de 30 jours
ouvrables de congés payés par an, acquis à raison de 2.5 jours par mois de travail effectif.\n\nLa période de ré"

Chunk 2 : "férence court du 1er juin de l'année N au 31 mai de l'année N+1.\n\nLes congés doivent être pris..."

→ Chunk 1 coupé au milieu de "référence"
→ Chunk 2 commence par "férence" (incompréhensible seul)

✅ Chunking sémantique :

Chunk 1 : "Article 45 - Congés payés\n\nLes clercs de notaire bénéficient de 30 jours
ouvrables de congés payés par an, acquis à raison de 2.5 jours par mois de travail effectif."

Chunk 2 : "La période de référence court du 1er juin de l'année N au 31 mai de l'année N+1."

Chunk 3 : "Les congés doivent être pris..."

→ Chaque chunk est sémantiquement cohérent
→ Peut être compris indépendamment
```

---

## 💡 Solution proposée

### Vue d'ensemble

**Chunking sémantique hiérarchique** :

1. **Niveau 1** : Découpage par sections (titres, articles)
2. **Niveau 2** : Découpage par paragraphes
3. **Niveau 3** : Fusion si trop petit, split si trop grand

### Stratégie

```python
# Règles de chunking sémantique

1. Si document a une structure (articles, sections) :
   → Découper par article/section
   → Garder le titre avec le contenu

2. Sinon, découper par paragraphes :
   → Chaque paragraphe = 1 chunk potentiel
   → Fusionner paragraphes courts (< 100 caractères)

3. Respecter taille cible :
   → Minimum : 200 caractères
   → Optimal : 400-600 caractères
   → Maximum : 1000 caractères

4. Préserver contexte :
   → Ajouter overlap de 50 caractères entre chunks
   → Inclure titre de section dans chaque chunk
```

---

## 🔧 Implémentation détaillée

### Nouveau service : `services/semantic_chunker.py`

```python
"""
Chunking sémantique pour documents
"""

import re
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Chunk:
    """Représente un chunk sémantique"""
    text: str
    start_char: int
    end_char: int
    section_title: str = None
    metadata: dict = None


class SemanticChunker:
    """
    Découpe les documents de manière sémantique
    """

    def __init__(
        self,
        min_chunk_size: int = 200,
        optimal_chunk_size: int = 500,
        max_chunk_size: int = 1000,
        overlap: int = 50
    ):
        self.min_chunk_size = min_chunk_size
        self.optimal_chunk_size = optimal_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk_document(self, text: str, doc_metadata: dict = None) -> List[Chunk]:
        """
        Découpe un document en chunks sémantiques

        Args:
            text: Texte du document
            doc_metadata: Métadonnées du document

        Returns:
            Liste de chunks
        """

        # 1. Détecter structure (articles, sections)
        sections = self._detect_sections(text)

        if sections:
            # Document structuré → chunking par sections
            chunks = self._chunk_by_sections(sections)
        else:
            # Document non structuré → chunking par paragraphes
            chunks = self._chunk_by_paragraphs(text)

        # 2. Post-traitement : fusionner/splitter si nécessaire
        chunks = self._optimize_chunk_sizes(chunks)

        # 3. Ajouter overlap entre chunks
        chunks = self._add_overlap(chunks, text)

        # 4. Ajouter métadonnées
        for chunk in chunks:
            chunk.metadata = doc_metadata or {}

        return chunks

    def _detect_sections(self, text: str) -> List[Dict]:
        """
        Détecte les sections structurées (articles, titres)

        Returns:
            Liste de {title, content, start_pos}
        """

        sections = []

        # Pattern 1 : Articles (ex: "Article 45 - Congés payés")
        article_pattern = r'^(Article\s+\d+[A-Z]?\s*-?\s*[^\n]+)\n(.+?)(?=^Article\s+\d+|$)'

        for match in re.finditer(article_pattern, text, re.MULTILINE | re.DOTALL):
            title = match.group(1).strip()
            content = match.group(2).strip()
            start_pos = match.start()

            sections.append({
                'title': title,
                'content': content,
                'start_pos': start_pos
            })

        if sections:
            return sections

        # Pattern 2 : Sections numérotées (ex: "1. Introduction", "2. Conditions")
        section_pattern = r'^(\d+\.\s+[^\n]+)\n(.+?)(?=^\d+\.\s+|$)'

        for match in re.finditer(section_pattern, text, re.MULTILINE | re.DOTALL):
            title = match.group(1).strip()
            content = match.group(2).strip()
            start_pos = match.start()

            sections.append({
                'title': title,
                'content': content,
                'start_pos': start_pos
            })

        if sections:
            return sections

        # Pattern 3 : Titres en majuscules
        heading_pattern = r'^([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ\s]{5,})\n(.+?)(?=^[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜŸÇ\s]{5,}|$)'

        for match in re.finditer(heading_pattern, text, re.MULTILINE | re.DOTALL):
            title = match.group(1).strip()
            content = match.group(2).strip()
            start_pos = match.start()

            sections.append({
                'title': title,
                'content': content,
                'start_pos': start_pos
            })

        return sections

    def _chunk_by_sections(self, sections: List[Dict]) -> List[Chunk]:
        """
        Découpe par sections détectées
        """

        chunks = []

        for section in sections:
            title = section['title']
            content = section['content']
            start_pos = section['start_pos']

            # Si section trop grande, découper par paragraphes
            if len(content) > self.max_chunk_size:
                para_chunks = self._chunk_by_paragraphs(content)

                # Ajouter titre à chaque chunk
                for chunk in para_chunks:
                    chunk.text = f"{title}\n\n{chunk.text}"
                    chunk.section_title = title
                    chunk.start_char += start_pos

                chunks.extend(para_chunks)
            else:
                # Section assez petite, garder entière
                chunk = Chunk(
                    text=f"{title}\n\n{content}",
                    start_char=start_pos,
                    end_char=start_pos + len(title) + len(content) + 2,
                    section_title=title
                )
                chunks.append(chunk)

        return chunks

    def _chunk_by_paragraphs(self, text: str) -> List[Chunk]:
        """
        Découpe par paragraphes
        """

        # Splitter par double saut de ligne
        paragraphs = re.split(r'\n\s*\n', text)

        chunks = []
        current_chunk = ""
        current_start = 0

        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue

            # Si ajout de ce paragraphe dépasse la taille optimale → créer chunk
            if len(current_chunk) + len(para) > self.optimal_chunk_size and current_chunk:
                chunk = Chunk(
                    text=current_chunk.strip(),
                    start_char=current_start,
                    end_char=current_start + len(current_chunk)
                )
                chunks.append(chunk)

                current_chunk = para
                current_start = text.find(para, current_start)
            else:
                # Ajouter paragraphe au chunk courant
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                    current_start = text.find(para)

        # Dernier chunk
        if current_chunk:
            chunk = Chunk(
                text=current_chunk.strip(),
                start_char=current_start,
                end_char=current_start + len(current_chunk)
            )
            chunks.append(chunk)

        return chunks

    def _optimize_chunk_sizes(self, chunks: List[Chunk]) -> List[Chunk]:
        """
        Optimise la taille des chunks :
        - Fusionne chunks trop petits
        - Split chunks trop grands
        """

        optimized = []
        i = 0

        while i < len(chunks):
            chunk = chunks[i]

            # Chunk trop petit → fusionner avec le suivant
            if len(chunk.text) < self.min_chunk_size and i + 1 < len(chunks):
                next_chunk = chunks[i + 1]

                merged = Chunk(
                    text=chunk.text + "\n\n" + next_chunk.text,
                    start_char=chunk.start_char,
                    end_char=next_chunk.end_char,
                    section_title=chunk.section_title
                )

                optimized.append(merged)
                i += 2  # Sauter le chunk suivant (fusionné)

            # Chunk trop grand → splitter
            elif len(chunk.text) > self.max_chunk_size:
                # Split au niveau des phrases
                sentences = re.split(r'(?<=[.!?])\s+', chunk.text)

                sub_chunk = ""
                sub_start = chunk.start_char

                for sentence in sentences:
                    if len(sub_chunk) + len(sentence) > self.optimal_chunk_size and sub_chunk:
                        optimized.append(Chunk(
                            text=sub_chunk.strip(),
                            start_char=sub_start,
                            end_char=sub_start + len(sub_chunk),
                            section_title=chunk.section_title
                        ))

                        sub_chunk = sentence
                        sub_start = sub_start + len(sub_chunk)
                    else:
                        sub_chunk += " " + sentence

                # Dernier sous-chunk
                if sub_chunk:
                    optimized.append(Chunk(
                        text=sub_chunk.strip(),
                        start_char=sub_start,
                        end_char=chunk.end_char,
                        section_title=chunk.section_title
                    ))

                i += 1

            else:
                # Taille OK
                optimized.append(chunk)
                i += 1

        return optimized

    def _add_overlap(self, chunks: List[Chunk], original_text: str) -> List[Chunk]:
        """
        Ajoute un overlap entre chunks pour préserver le contexte
        """

        if self.overlap == 0:
            return chunks

        overlapped = []

        for i, chunk in enumerate(chunks):
            # Ajouter overlap avec chunk précédent
            if i > 0:
                prev_chunk = chunks[i - 1]
                overlap_start = max(0, prev_chunk.end_char - self.overlap)
                overlap_text = original_text[overlap_start:prev_chunk.end_char]

                chunk.text = f"... {overlap_text}\n\n{chunk.text}"

            overlapped.append(chunk)

        return overlapped


# Fonction utilitaire pour ré-indexer avec chunking sémantique
async def reindex_with_semantic_chunking(
    documents: List[Dict],
    chunker: SemanticChunker
):
    """
    Ré-indexe tous les documents avec chunking sémantique
    """

    all_chunks = []

    for doc in documents:
        doc_id = doc['document_id']
        text = doc['text']  # Texte extrait du PDF
        metadata = doc.get('classification', {})

        # Chunking sémantique
        chunks = chunker.chunk_document(text, metadata)

        # Préparer pour Neo4j
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                'doc_id': doc_id,
                'chunk_id': f"{doc_id}_chunk_{i}",
                'text': chunk.text,
                'section_title': chunk.section_title,
                'chunk_index': i,
                'metadata': chunk.metadata
            })

    return all_chunks
```

---

## ✅ Tests et validation

### Tests unitaires

```python
"""
Tests pour chunking sémantique
"""

import pytest
from services.semantic_chunker import SemanticChunker

def test_chunk_by_articles():
    """Test chunking d'un document avec articles"""

    text = """Article 45 - Congés payés

Les clercs de notaire bénéficient de 30 jours ouvrables de congés payés par an.

La période de référence court du 1er juin au 31 mai.

Article 46 - Congés exceptionnels

Des congés exceptionnels sont accordés dans les cas suivants :
- Mariage : 4 jours
- Naissance : 3 jours
"""

    chunker = SemanticChunker(min_chunk_size=50, optimal_chunk_size=200, max_chunk_size=500)
    chunks = chunker.chunk_document(text)

    # Devrait créer 2 chunks (1 par article)
    assert len(chunks) >= 2

    # Chaque chunk doit contenir le titre
    assert "Article 45" in chunks[0].text
    assert "Article 46" in chunks[1].text

    # Pas de coupure au milieu d'un mot
    for chunk in chunks:
        assert not chunk.text.startswith(' ')
        assert not chunk.text.endswith(' ')

def test_chunk_optimization():
    """Test fusion de chunks trop petits"""

    text = """Petit paragraphe 1.

Petit paragraphe 2.

Petit paragraphe 3.
"""

    chunker = SemanticChunker(min_chunk_size=100, optimal_chunk_size=200)
    chunks = chunker.chunk_document(text)

    # Les petits paragraphes doivent être fusionnés
    assert len(chunks) == 1
    assert "Petit paragraphe 1" in chunks[0].text
    assert "Petit paragraphe 2" in chunks[0].text
```

---

## 📈 Impact attendu

### Avant amélioration

- ❌ Chunks coupés arbitrairement
- ❌ Perte de contexte sémantique
- ❌ Chunks incompréhensibles seuls

### Après amélioration

- ✅ Chunks sémantiquement cohérents
- ✅ Contexte préservé (titre + contenu)
- ✅ Meilleure qualité de récupération

---

## 📅 Planning d'implémentation

**Total** : 1.5 jours

### Jour 1 (8h)

- ✅ Créer `semantic_chunker.py`
- ✅ Implémenter détection sections
- ✅ Implémenter chunking par paragraphes
- ✅ Tests unitaires

### Jour 2 (4h)

- ✅ Ré-indexation complète avec nouveau chunking
- ✅ Tests manuels comparatifs
- ✅ Validation qualité chunks

---

[← Retour à l'index](./00_INDEX.md) | [Amélioration suivante : Filtrage temporel →](./10_filtrage_temporel.md)
