"""
NeuralAgent - RAG（检索增强生成）系统
完整的RAG流水线：加载 -> 分块 -> 嵌入 -> 检索 -> 生成
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re


class DocumentType(Enum):
    """文档类型"""
    TEXT = "text"
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


class ChunkingStrategy(Enum):
    """分块策略"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"
    PARAGRAPH = "paragraph"


@dataclass
class ChunkConfig:
    """分块配置"""
    strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", ". ", " "])


@dataclass
class RAGResult:
    """RAG结果"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentLoader(ABC):
    """文档加载器抽象基类"""
    
    @abstractmethod
    def load(self, path: str) -> List[Dict[str, Any]]:
        """加载文档"""
        pass
    
    @abstractmethod
    def supports(self, document_type: DocumentType) -> bool:
        """检查是否支持该文档类型"""
        pass


class SimpleTextLoader(DocumentLoader):
    """简单文本加载器"""
    
    def load(self, path: str) -> List[Dict[str, Any]]:
        file_path = Path(path)
        if not file_path.exists():
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return [{
            "content": content,
            "metadata": {
                "source": path,
                "type": DocumentType.TEXT.value,
                "size": len(content)
            }
        }]
    
    def supports(self, document_type: DocumentType) -> bool:
        return document_type in [DocumentType.TEXT, DocumentType.MARKDOWN]


class TextChunker:
    """文本分块器"""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """将文本分块"""
        if self.config.strategy == ChunkingStrategy.FIXED_SIZE:
            return self._fixed_size_chunk(text, metadata)
        elif self.config.strategy == ChunkingStrategy.PARAGRAPH:
            return self._paragraph_chunk(text, metadata)
        else:
            return self._fixed_size_chunk(text, metadata)
    
    def _fixed_size_chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.config.chunk_size
            
            if end < len(text):
                for sep in self.config.separators:
                    pos = text.rfind(sep, start, end)
                    if pos != -1:
                        end = pos + len(sep)
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "metadata": {
                        **(metadata or {}),
                        "chunk_id": chunk_id,
                        "start_index": start,
                        "end_index": end
                    }
                })
            
            start = end - self.config.chunk_overlap
            chunk_id += 1
        
        return chunks
    
    def _paragraph_chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        paragraphs = re.split(r'\n\s*\n', text)
        chunks = []
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if para:
                chunks.append({
                    "content": para,
                    "metadata": {
                        **(metadata or {}),
                        "chunk_id": i,
                        "type": "paragraph"
                    }
                })
        
        return chunks


class Retriever:
    """检索器"""
    
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    async def retrieve(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_expr: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """检索相关文档"""
        docs = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_expr=filter_expr
        )
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.content,
                "score": doc.score,
                "metadata": doc.metadata,
                "id": doc.id
            })
        
        return results


class RAGSystem:
    """完整的RAG系统"""
    
    def __init__(
        self,
        vector_store,
        chunker: Optional[TextChunker] = None,
        loaders: Optional[List[DocumentLoader]] = None
    ):
        self.vector_store = vector_store
        self.chunker = chunker or TextChunker()
        self.loaders = loaders or [SimpleTextLoader()]
        self.retriever = Retriever(vector_store)
    
    async def add_documents(
        self,
        paths: List[str],
        embedding_fn: Optional[Callable[[str], List[float]]] = None
    ) -> List[str]:
        """添加文档到RAG系统"""
        all_docs = []
        
        for path in paths:
            for loader in self.loaders:
                # 简单的类型检测
                doc_type = DocumentType.TEXT
                if path.endswith('.md'):
                    doc_type = DocumentType.MARKDOWN
                elif path.endswith('.pdf'):
                    doc_type = DocumentType.PDF
                
                if loader.supports(doc_type):
                    loaded_docs = loader.load(path)
                    all_docs.extend(loaded_docs)
                    break
        
        all_chunks = []
        for doc in all_docs:
            chunks = self.chunker.chunk(doc["content"], doc["metadata"])
            all_chunks.extend(chunks)
        
        if embedding_fn:
            from backend.core.vector_store.base import VectorDocument
            vector_docs = []
            embeddings = []
            
            for chunk in all_chunks:
                chunk_id = f"chunk_{hash(chunk['content'])}"
                embedding = embedding_fn(chunk["content"])
                
                vector_docs.append(VectorDocument(
                    id=chunk_id,
                    content=chunk["content"],
                    metadata=chunk["metadata"]
                ))
                embeddings.append(embedding)
            
            return await self.vector_store.add_documents(vector_docs, embeddings)
        
        return []
    
    async def query(
        self,
        query_text: str,
        query_embedding: List[float],
        top_k: int = 5,
        llm_fn: Optional[Callable[[str, List[str]], str]] = None
    ) -> RAGResult:
        """执行RAG查询"""
        sources = await self.retriever.retrieve(query_embedding, top_k)
        
        context = "\n\n".join([s["content"] for s in sources])
        
        if llm_fn:
            prompt = self._build_prompt(query_text, context)
            answer = llm_fn(query_text, [s["content"] for s in sources])
        else:
            answer = f"Based on {len(sources)} sources, here's relevant information:\n{context}"
        
        avg_score = sum(s.get("score", 0) for s in sources) / len(sources) if sources else 0
        
        return RAGResult(
            answer=answer,
            sources=sources,
            confidence=avg_score,
            metadata={
                "num_sources": len(sources),
                "query": query_text
            }
        )
    
    def _build_prompt(self, query: str, context: str) -> str:
        """构建提示词"""
        return f"""Context information:
{context}

Query: {query}

Please answer the query based on the context provided. If the answer is not in the context, say you don't know."""


def create_rag_system(vector_store) -> RAGSystem:
    """创建RAG系统"""
    return RAGSystem(vector_store)
