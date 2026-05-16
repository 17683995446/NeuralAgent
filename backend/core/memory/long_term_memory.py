"""Long-term memory implementation using Milvus/Chroma vector store."""
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

from backend.config import settings


@dataclass
class MemoryEntry:
    """Memory entry data class."""
    id: str
    agent_id: str
    task_type: str
    content: str
    metadata: Dict[str, Any]
    trust_trend: Optional[Dict[str, float]] = None
    task_result: Optional[str] = None
    create_time: datetime = None
    embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "task_type": self.task_type,
            "content": self.content,
            "metadata": self.metadata,
            "trust_trend": self.trust_trend,
            "task_result": self.task_result,
            "create_time": self.create_time.isoformat() if self.create_time else None,
        }


class LongTermMemory:
    """Long-term memory using Milvus/Chroma vector store.

    Stores historical task experiences, trust trends, and successful patterns.
    Supports similarity search for experience retrieval.
    """

    def __init__(
        self,
        vector_store: Any,
        embedding_model: Optional[Any] = None,
        use_milvus: bool = True
    ):
        """Initialize long-term memory.

        Args:
            vector_store: Vector store instance (Milvus or Chroma)
            embedding_model: Optional embedding model for custom embeddings
            use_milvus: Whether using Milvus (True) or Chroma (False)
        """
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.use_milvus = use_milvus

    def save_memory(
        self,
        agent_id: str,
        content: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Save memory to vector store.

        Args:
            agent_id: Agent identifier
            content: Memory content dictionary
            metadata: Memory metadata

        Returns:
            Memory entry ID
        """
        memory_id = str(uuid.uuid4())
        content_text = json.dumps(content, ensure_ascii=False)

        extra_metadata = {
            "agent_id": agent_id,
            "memory_id": memory_id,
            "create_time": datetime.utcnow().isoformat(),
        }
        full_metadata = {**metadata, **extra_metadata}

        if self.use_milvus:
            from pymilvus import Collection, FieldSchema, CollectionSchema, DataType, utility

            collection_name = "long_term_memory"
            if not utility.has_collection(collection_name):
                fields = [
                    FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36),
                    FieldSchema(name="agent_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="task_type", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.vector_dimension),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535),
                ]
                schema = CollectionSchema(fields=fields, description="Long-term memory storage")
                collection = Collection(name=collection_name, schema=schema)

                index_params = {
                    "metric_type": "COSINE",
                    "index_type": "HNSW",
                    "params": {"ef": 64, "M": 16}
                }
                collection.create_index(field_name="embedding", index_params=index_params)
            else:
                collection = Collection(name=collection_name)

            if self.embedding_model:
                embedding = self.embedding_model.embed_query(content_text)
            else:
                from backend.core.llm_adapter import llm_adapter
                embedding = llm_adapter.embed_single(content_text)

            entities = [[memory_id], [agent_id], [metadata.get("task_type", "general")],
                        [content_text], [embedding], [json.dumps(full_metadata)]]
            collection.insert(entities)
            collection.flush()

        else:
            from langchain_community.vectorstores import Chroma
            from langchain_core.documents import Document

            doc = Document(
                page_content=content_text,
                metadata=full_metadata
            )

            if isinstance(self.vector_store, Chroma):
                self.vector_store.add_documents([doc], ids=[memory_id])

        return memory_id

    def retrieve_similar(
        self,
        query: str,
        agent_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.8
    ) -> List[MemoryEntry]:
        """Retrieve similar memories based on query.

        Args:
            query: Query text
            agent_id: Optional agent ID filter
            top_k: Number of results to return
            threshold: Similarity threshold

        Returns:
            List of matching MemoryEntry objects
        """
        results = []

        if self.use_milvus:
            from pymilvus import Collection

            collection = Collection("long_term_memory")
            collection.load()

            if self.embedding_model:
                query_embedding = self.embedding_model.embed_query(query)
            else:
                from backend.core.llm_adapter import llm_adapter
                query_embedding = llm_adapter.embed_single(query)

            search_params = {"metric_type": "COSINE", "params": {"ef": 64}}

            expr = ""
            if agent_id:
                expr = f"agent_id == '{agent_id}'"

            search_results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["id", "agent_id", "task_type", "content", "metadata"]
            )

            for hits in search_results:
                for hit in hits:
                    if hit.score >= threshold:
                        metadata = json.loads(hit.entity.get("metadata", "{}"))
                        results.append(MemoryEntry(
                            id=hit.entity.get("id"),
                            agent_id=hit.entity.get("agent_id"),
                            task_type=hit.entity.get("task_type", "general"),
                            content=hit.entity.get("content", ""),
                            metadata=metadata,
                            create_time=datetime.fromisoformat(
                                metadata.get("create_time", datetime.utcnow().isoformat())
                            )
                        ))

        else:
            docs = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k,
                filter={"agent_id": agent_id} if agent_id else None
            )

            for doc, score in docs:
                if score >= threshold:
                    metadata = doc.metadata
                    results.append(MemoryEntry(
                        id=metadata.get("memory_id", str(uuid.uuid4())),
                        agent_id=metadata.get("agent_id", ""),
                        task_type=metadata.get("task_type", "general"),
                        content=doc.page_content,
                        metadata=metadata,
                        create_time=datetime.fromisoformat(
                            metadata.get("create_time", datetime.utcnow().isoformat())
                        )
                    ))

        return results

    def update_trust_trend(
        self,
        agent_id: str,
        trust_matrix: Dict[str, float],
        task_result: str = "success"
    ) -> str:
        """Update trust trend for agent.

        Args:
            agent_id: Agent identifier
            trust_matrix: Current trust matrix
            task_result: Task execution result

        Returns:
            Memory entry ID
        """
        return self.save_memory(
            agent_id=agent_id,
            content={"type": "trust_trend", "trust_matrix": trust_matrix},
            metadata={"type": "trust_trend", "task_result": task_result}
        )

    def get_trust_trend(self, agent_id: str) -> List[Dict[str, Any]]:
        """Retrieve trust trend history for agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of trust trend records
        """
        memories = self.retrieve_similar(
            query="trust trend history",
            agent_id=agent_id,
            top_k=10,
            threshold=0.5
        )

        trends = []
        for memory in memories:
            if memory.metadata.get("type") == "trust_trend":
                try:
                    content = json.loads(memory.content)
                    trends.append({
                        "create_time": memory.create_time,
                        "trust_matrix": content.get("trust_matrix", {}),
                        "task_result": memory.metadata.get("task_result"),
                    })
                except json.JSONDecodeError:
                    continue

        return trends

    def save_successful_pattern(
        self,
        agent_id: str,
        pattern: Dict[str, Any],
        pattern_type: str = "code_generation"
    ) -> str:
        """Save successful code pattern for future reference.

        Args:
            agent_id: Agent identifier
            pattern: Pattern content
            pattern_type: Type of pattern

        Returns:
            Memory entry ID
        """
        return self.save_memory(
            agent_id=agent_id,
            content={
                "type": "successful_pattern",
                "pattern": pattern,
                "pattern_type": pattern_type
            },
            metadata={"type": "successful_pattern", "pattern_type": pattern_type}
        )

    def retrieve_successful_patterns(
        self,
        query: str,
        agent_id: Optional[str] = None,
        pattern_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve successful patterns matching query.

        Args:
            query: Query text
            agent_id: Optional agent ID filter
            pattern_type: Optional pattern type filter
            top_k: Number of results

        Returns:
            List of matching patterns
        """
        memories = self.retrieve_similar(
            query=query,
            agent_id=agent_id,
            top_k=top_k,
            threshold=0.6
        )

        patterns = []
        for memory in memories:
            if memory.metadata.get("type") == "successful_pattern":
                if pattern_type and memory.metadata.get("pattern_type") != pattern_type:
                    continue
                try:
                    content = json.loads(memory.content)
                    patterns.append({
                        "pattern": content.get("pattern", {}),
                        "pattern_type": content.get("pattern_type"),
                        "agent_id": memory.agent_id,
                        "create_time": memory.create_time,
                    })
                except json.JSONDecodeError:
                    continue

        return patterns

    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory entry by ID.

        Args:
            memory_id: Memory entry ID

        Returns:
            True if deleted, False otherwise
        """
        if self.use_milvus:
            from pymilvus import Collection

            collection = Collection("long_term_memory")
            expr = f"id == '{memory_id}'"
            collection.delete(expr)
            collection.flush()
            return True
        else:
            self.vector_store.delete(ids=[memory_id])
            return True


def create_vector_store(
    use_milvus: bool = True,
    persist_directory: Optional[str] = None
) -> Any:
    """Create vector store instance.

    Args:
        use_milvus: Whether to use Milvus (True) or Chroma (False)
        persist_directory: Directory for Chroma persistence

    Returns:
        Vector store instance
    """
    if use_milvus:
        from pymilvus import connections, Collection

        connections.connect(
            alias="default",
            host=settings.milvus_url.replace("http://", "").split(":")[0],
            port=settings.milvus_url.split(":")[-1]
        )
        return Collection("long_term_memory")
    else:
        from langchain_community.vectorstores import Chroma
        from langchain_openai import OpenAIEmbeddings

        embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key
        )

        return Chroma(
            client=None,
            embedding_function=embeddings,
            persist_directory=persist_directory or "./chroma_db"
        )
