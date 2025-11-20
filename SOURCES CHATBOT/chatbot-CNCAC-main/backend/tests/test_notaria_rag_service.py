import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.notaria_rag_service import RAGService, RAGStrategy
import json

@pytest.mark.unit
class TestNotariaRAGService:

    @pytest.fixture
    def mock_neo4j(self):
        mock = Mock()
        # Mock des méthodes async avec AsyncMock
        mock.search_chunks_by_vector = AsyncMock(return_value=[])
        mock.search_chunks_by_fulltext = AsyncMock(return_value=[])
        mock.find_paths_between_entities = AsyncMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_minio(self):
        return Mock()

    @pytest.fixture
    def mock_openai(self):
        mock = Mock()
        mock.chat = Mock()
        mock.chat.completions = Mock()
        mock.chat.completions.create = AsyncMock()
        return mock

    @pytest.fixture
    def rag_service(self, mock_neo4j, mock_minio, mock_openai):
        with patch('openai.AsyncOpenAI', return_value=mock_openai):
            service = RAGService(neo4j_service=mock_neo4j, minio_service=mock_minio)
            yield service

    @pytest.mark.asyncio
    async def test_select_query_strategy_vector(self, rag_service):
        rag_service.openai_client.chat.completions.create = AsyncMock(
            return_value=Mock(choices=[Mock(message=Mock(content='{"strategy": "VECTOR_ONLY"}'))])
        )

        strategy = await rag_service._select_rag_strategy("What is the definition of X?")
        assert strategy == RAGStrategy.VECTOR_ONLY

    @pytest.mark.asyncio
    async def test_select_query_strategy_graph(self, rag_service):
        rag_service.openai_client.chat.completions.create = AsyncMock(
            return_value=Mock(choices=[Mock(message=Mock(content='{"strategy": "GRAPH_FIRST"}'))])
        )

        strategy = await rag_service._select_rag_strategy("Who is John Doe?")
        assert strategy == RAGStrategy.GRAPH_FIRST

    @pytest.mark.asyncio
    async def test_select_query_strategy_hybrid(self, rag_service):
        rag_service.openai_client.chat.completions.create = AsyncMock(
            return_value=Mock(choices=[Mock(message=Mock(content='{"strategy": "HYBRID"}'))])
        )

        strategy = await rag_service._select_rag_strategy("Complex legal question")
        assert strategy == RAGStrategy.HYBRID

    @pytest.mark.asyncio
    async def test_extract_entities(self, rag_service):
        rag_service.openai_client.chat.completions.create = AsyncMock(
            return_value=Mock(choices=[Mock(message=Mock(content=json.dumps({
                "entities": ["John Doe", "Company ABC"]
            })))])
        )

        entities = await rag_service._extract_entities_from_query("John Doe works at Company ABC")
        assert len(entities) == 2
        assert "John Doe" in entities

    @pytest.mark.asyncio
    async def test_query_with_results(self, rag_service):
        """Test de query() avec le PROTOCOLE DAN v5"""
        # Mock _reasoning_step
        rag_service._reasoning_step = AsyncMock(return_value={
            "thought": "Test thought",
            "search_query": "optimized query"
        })

        # Mock _get_embeddings pour _hybrid_search_step
        rag_service._get_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        # Mock search_chunks_by_vector et search_chunks_by_fulltext
        rag_service.neo4j.search_chunks_by_vector = AsyncMock(return_value=[
            {
                "text": "Vector result 1",
                "documentPath": "doc1.pdf",
                "documentId": "doc1",
                "chunkId": "chunk1",
                "score": 0.9
            }
        ])
        rag_service.neo4j.search_chunks_by_fulltext = AsyncMock(return_value=[
            {
                "text": "Fulltext result 1",
                "documentPath": "doc2.pdf",
                "documentId": "doc2",
                "chunkId": "chunk2",
                "score": 0.8
            }
        ])

        # Mock _rerank_chunks (retourne les chunks tels quels)
        rag_service._rerank_chunks = AsyncMock(side_effect=lambda q, chunks: chunks[:5])

        # Mock _synthesize_answer_with_citations
        rag_service._synthesize_answer_with_citations = AsyncMock(return_value={
            "answer": "Test response basé sur Source 1 - Document: doc1.pdf",
            "citations": ["doc1.pdf"]
        })

        response = await rag_service.query("Test question")

        assert "Test response" in response["answer"]
        assert "citations" in response
        assert response["citations"] == ["doc1.pdf"]
        rag_service.neo4j.search_chunks_by_vector.assert_called_once()
        rag_service.neo4j.search_chunks_by_fulltext.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_empty_results(self, rag_service):
        """Test quand aucun résultat n'est trouvé (DAN v5)"""
        # Mock _reasoning_step
        rag_service._reasoning_step = AsyncMock(return_value={
            "thought": "No results expected",
            "search_query": "query with no results"
        })

        # Mock _get_embeddings
        rag_service._get_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        # Aucun résultat de recherche
        rag_service.neo4j.search_chunks_by_vector = AsyncMock(return_value=[])
        rag_service.neo4j.search_chunks_by_fulltext = AsyncMock(return_value=[])

        response = await rag_service.query("Question sans résultat")

        assert response["answer"] == "L'information n'est pas disponible dans les documents fournis."
        assert response["citations"] == []

    @pytest.mark.asyncio
    async def test_query_embedding_failure(self, rag_service):
        """Test quand l'embedding échoue (DAN v5)"""
        # Mock _reasoning_step
        rag_service._reasoning_step = AsyncMock(return_value={
            "thought": "Embedding will fail",
            "search_query": "test query"
        })

        # L'embedding échoue
        rag_service._get_embeddings = AsyncMock(return_value=None)

        response = await rag_service.query("Test question")

        assert response["answer"] == "L'information n'est pas disponible dans les documents fournis."
        assert response["citations"] == []

    @pytest.mark.asyncio
    async def test_query_with_multiple_sources(self, rag_service):
        """Test avec plusieurs sources (DAN v5)"""
        # Mock _reasoning_step
        rag_service._reasoning_step = AsyncMock(return_value={
            "thought": "Multiple sources",
            "search_query": "complex query"
        })

        # Mock _get_embeddings
        rag_service._get_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        # Mock search avec plusieurs sources
        rag_service.neo4j.search_chunks_by_vector = AsyncMock(return_value=[
            {
                "text": "First result",
                "documentPath": "doc1.pdf",
                "documentId": "doc1",
                "chunkId": "chunk1",
                "score": 0.9
            },
            {
                "text": "Second result",
                "documentPath": "doc2.pdf",
                "documentId": "doc2",
                "chunkId": "chunk2",
                "score": 0.8
            }
        ])
        rag_service.neo4j.search_chunks_by_fulltext = AsyncMock(return_value=[
            {
                "text": "Third result",
                "documentPath": "doc3.pdf",
                "documentId": "doc3",
                "chunkId": "chunk3",
                "score": 0.7
            }
        ])

        # Mock _rerank_chunks
        rag_service._rerank_chunks = AsyncMock(side_effect=lambda q, chunks: chunks[:5])

        # Mock _synthesize_answer_with_citations avec citations multiples
        rag_service._synthesize_answer_with_citations = AsyncMock(return_value={
            "answer": "Response citing Source 1 - Document: doc1.pdf and Source 2 - Document: doc2.pdf",
            "citations": ["doc1.pdf", "doc2.pdf"]
        })

        response = await rag_service.query("Complex question")

        assert "Response citing" in response["answer"]
        assert "citations" in response
        assert len(response["citations"]) == 2
        assert "doc1.pdf" in response["citations"]
        assert "doc2.pdf" in response["citations"]

    @pytest.mark.asyncio
    async def test_error_handling(self, rag_service):
        """Test de gestion d'erreur lors de la recherche (DAN v5)"""
        # Mock _reasoning_step
        rag_service._reasoning_step = AsyncMock(return_value={
            "thought": "Will fail",
            "search_query": "failing query"
        })

        # Mock _get_embeddings
        rag_service._get_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        # La recherche vectorielle échoue
        rag_service.neo4j.search_chunks_by_vector = AsyncMock(
            side_effect=Exception("Database error")
        )

        # Avec DAN v5, les exceptions sont propagées
        with pytest.raises(Exception) as exc_info:
            await rag_service.query("Test question")

        assert "Database error" in str(exc_info.value)
