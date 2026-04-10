# RAG Service - Retrieval Augmented Generation cho Log Analysis
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from app.core.config import settings


@dataclass
class RetrievedContext:
    """Context được retrieve từ KB"""
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class RAGResult:
    """Kết quả RAG retrieval"""
    contexts: List[RetrievedContext]
    query: str
    total_found: int


class RAGService:
    """
    RAG Service - Retrieval Augmented Generation
    - Sử dụng Ollama để tạo embeddings (local, miễn phí)
    - ChromaDB làm vector store
    - Hỗ trợ Apache error knowledge base
    """

    def __init__(self):
        self.embedding_model = settings.rag.embedding_model
        self.embedding_dim = settings.rag.embedding_dim
        self.collection_name = "apache_errors"
        self.top_k = settings.rag.top_k
        self.min_score = settings.rag.min_score

        self._vector_store = None
        self._embeddings = None
        self._initialized = False

    def _get_vector_store_path(self) -> Path:
        """Lấy đường dẫn vector store"""
        base_path = Path(settings.rag.vector_db_path)
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path / "chroma_db"

    def initialize(self):
        """
        Khởi tạo RAG service
        - Load embeddings model
        - Load hoặc tạo ChromaDB collection
        """
        if self._initialized:
            return

        try:
            # Import các thư viện cần thiết
            from chromadb import PersistentClient
            from langchain_ollama import OllamaEmbeddings

            # Khởi tạo Ollama embeddings
            logger.info(f"Khởi tạo Ollama embeddings: {self.embedding_model}")
            self._embeddings = OllamaEmbeddings(
                model=self.embedding_model,
                base_url=settings.ollama.base_url,
            )

            # Kiểm tra Ollama có chạy không
            test_emb = self._embeddings.embed_query("test")
            logger.info(f"Embedding dimension: {len(test_emb)}")

            # Khởi tạo ChromaDB persistent client
            db_path = self._get_vector_store_path()
            logger.info(f"Khởi tạo ChromaDB tại: {db_path}")

            self._client = PersistentClient(path=str(db_path))

            # Thử load collection, nếu không có thì tạo mới
            try:
                self._collection = self._client.get_collection(
                    name=self.collection_name,
                    embedding_function=None  # Chúng ta dùng LangChain embeddings
                )
                count = self._collection.count()
                logger.info(f"Loaded collection '{self.collection_name}' với {count} documents")
            except Exception:
                logger.info(f"Tạo collection mới: {self.collection_name}")
                self._collection = self._client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Apache Error Knowledge Base"}
                )

            self._initialized = True
            logger.info("✅ RAG Service đã khởi tạo thành công")

        except Exception as e:
            logger.error(f"Lỗi khởi tạo RAG: {e}")
            raise

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ):
        """
        Thêm documents vào vector store

        Args:
            documents: List of dict với keys: content, source, metadata
            ids: Optional list of IDs, tự động tạo nếu không có
        """
        if not self._initialized:
            self.initialize()

        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        # Embed documents
        contents = [doc["content"] for doc in documents]
        embeddings = self._embeddings.embed_documents(contents)

        # Prepare metadata
        metadatas = []
        for doc in documents:
            meta = {
                "source": doc.get("source", "unknown"),
                **doc.get("metadata", {})
            }
            metadatas.append(meta)

        # Add to collection
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )

        logger.info(f"Added {len(documents)} documents to collection")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> RAGResult:
        """
        Retrieve relevant documents từ vector store

        Args:
            query: Query string để tìm kiếm
            top_k: Số lượng results (override default)
            filter_metadata: Filter theo metadata

        Returns:
            RAGResult với list các RetrievedContext
        """
        if not self._initialized:
            self.initialize()

        k = top_k or self.top_k

        # Embed query
        query_embedding = self._embeddings.embed_query(query)

        # Search
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=filter_metadata,
            include=["documents", "metadatas", "distances"]
        )

        # Parse results
        contexts = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results["distances"] else 1.0
                # Convert distance to similarity score (0-1, higher is better)
                score = max(0, 1 - distance)

                if score >= self.min_score:
                    contexts.append(RetrievedContext(
                        content=doc,
                        source=results["metadatas"][0][i].get("source", "unknown"),
                        score=score,
                        metadata=results["metadatas"][0][i]
                    ))

        return RAGResult(
            contexts=contexts,
            query=query,
            total_found=len(contexts)
        )

    def retrieve_for_log_analysis(
        self,
        access_logs: List[str],
        error_logs: List[str],
        top_k: int = 5
    ) -> Tuple[List[RetrievedContext], str]:
        """
        Retrieve context cho việc phân tích log

        Args:
            access_logs: Danh sách access logs
            error_logs: Danh sách error logs
            top_k: Số lượng context

        Returns:
            Tuple[List[RetrievedContext], str] - contexts và query đã dùng
        """
        # Tạo query từ error logs
        if error_logs:
            # Lấy một vài error log để làm query
            sample_errors = error_logs[:3]
            query = " | ".join(sample_errors)
        elif access_logs:
            # Lấy các request lỗi
            query = " | ".join(access_logs[:3])
        else:
            return [], ""

        result = self.retrieve(query=query, top_k=top_k)
        return result.contexts, query

    def build_rag_context(
        self,
        contexts: List[RetrievedContext],
        max_context_length: int = 2000
    ) -> str:
        """
        Build context string từ retrieved documents

        Args:
            contexts: List RetrievedContext
            max_context_length: Độ dài tối đa (chars)

        Returns:
            String context để đưa vào prompt
        """
        if not contexts:
            return ""

        context_parts = [
            "## 📚 Knowledge Base Context (Apache Error Reference)",
            ""
        ]

        total_length = 0
        for i, ctx in enumerate(contexts, 1):
            # Kiểm tra độ dài
            part_length = len(ctx.content) + len(ctx.source) + 50
            if total_length + part_length > max_context_length:
                break

            context_parts.extend([
                f"### [{i}] {ctx.source}",
                f"**Relevance:** {ctx.score:.2%}",
                "",
                ctx.content,
                ""
            ])
            total_length += part_length

        return "\n".join(context_parts)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Lấy thống kê collection"""
        if not self._initialized:
            self.initialize()

        return {
            "collection_name": self.collection_name,
            "total_documents": self._collection.count(),
            "embedding_model": self.embedding_model,
            "embedding_dim": self.embedding_dim,
        }

    def clear_collection(self):
        """Xóa tất cả documents trong collection"""
        if not self._initialized:
            self.initialize()

        self._client.delete_collection(name=self.collection_name)
        self._collection = self._client.create_collection(
            name=self.collection_name,
            metadata={"description": "Apache Error Knowledge Base"}
        )
        logger.info(f"Cleared collection '{self.collection_name}'")


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Lấy RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
