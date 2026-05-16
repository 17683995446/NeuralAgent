"""Database models for NeuralAgent System."""
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

try:
    from sqlalchemy import (
        Column, String, Integer, Float, DateTime, Text,
        Boolean, JSON, ForeignKey, Index
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
    SQLALCHEMY_AVAILABLE = True
    Base = declarative_base()
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = None
    String = None
    Integer = None
    Float = None
    DateTime = None
    Text = None
    Boolean = None
    JSON = None
    ForeignKey = None
    Index = None
    declarative_base = None
    relationship = None

    class Base:
        pass



if SQLALCHEMY_AVAILABLE:
    class TaskModel(Base):
        """Task metadata model."""

        __tablename__ = "tasks"

        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        task_id = Column(String(36), unique=True, nullable=False, index=True)
        user_requirement = Column(Text, nullable=False)
        code_repo_url = Column(String(500), nullable=True)
        local_code_path = Column(String(500), nullable=True)
        target_branch = Column(String(100), default="main")
        status = Column(String(50), default="pending")
        max_iteration = Column(Integer, default=5)
        learning_rate = Column(Float, default=0.1)
        current_iteration = Column(Integer, default=0)
        output_path = Column(String(500), nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        trust_matrices = relationship("TrustModel", back_populates="task", cascade="all, delete-orphan")
        agent_outputs = relationship("AgentOutputModel", back_populates="task", cascade="all, delete-orphan")

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "task_id": self.task_id,
                "user_requirement": self.user_requirement,
                "code_repo_url": self.code_repo_url,
                "local_code_path": self.local_code_path,
                "target_branch": self.target_branch,
                "status": self.status,
                "max_iteration": self.max_iteration,
                "learning_rate": self.learning_rate,
                "current_iteration": self.current_iteration,
                "output_path": self.output_path,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            }
else:
    class TaskModel:
        """Task metadata model (in-memory version without SQLAlchemy."""
        def __init__(self, **kwargs):
            self.id = kwargs.get('id', str(uuid.uuid4()))
            self.task_id = kwargs.get('task_id', '')
            self.user_requirement = kwargs.get('user_requirement', '')
            self.code_repo_url = kwargs.get('code_repo_url')
            self.local_code_path = kwargs.get('local_code_path')
            self.target_branch = kwargs.get('target_branch', 'main')
            self.status = kwargs.get('status', 'pending')
            self.max_iteration = kwargs.get('max_iteration', 5)
            self.learning_rate = kwargs.get('learning_rate', 0.1)
            self.current_iteration = kwargs.get('current_iteration', 0)
            self.output_path = kwargs.get('output_path')
            self.created_at = kwargs.get('created_at', datetime.utcnow())
            self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        
        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "task_id": self.task_id,
                "user_requirement": self.user_requirement,
                "code_repo_url": self.code_repo_url,
                "local_code_path": self.local_code_path,
                "target_branch": self.target_branch,
                "status": self.status,
                "max_iteration": self.max_iteration,
                "learning_rate": self.learning_rate,
                "current_iteration": self.current_iteration,
                "output_path": self.output_path,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            }



class TrustModel(Base):
    """Trust matrix model for Agent trust management."""

    __tablename__ = "trust_matrices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.task_id"), nullable=False)
    agent_id = Column(String(100), nullable=False)
    layer_name = Column(String(50), nullable=False)
    trust_matrix = Column(JSON, nullable=False, default=dict)
    update_count = Column(Integer, default=0)
    last_reward = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("TaskModel", back_populates="trust_matrices")

    __table_args__ = (
        Index("idx_agent_layer", "agent_id", "layer_name"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "layer_name": self.layer_name,
            "trust_matrix": self.trust_matrix,
            "update_count": self.update_count,
            "last_reward": self.last_reward,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AgentOutputModel(Base):
    """Agent output storage model."""

    __tablename__ = "agent_outputs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.task_id"), nullable=False)
    agent_id = Column(String(100), nullable=False)
    layer_name = Column(String(50), nullable=False)
    output_type = Column(String(50), nullable=False)
    output_content = Column(JSON, nullable=False)
    confidence = Column(Float, default=1.0)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("TaskModel", back_populates="agent_outputs")

    __table_args__ = (
        Index("idx_task_agent", "task_id", "agent_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "layer_name": self.layer_name,
            "output_type": self.output_type,
            "output_content": self.output_content,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserFeedbackModel(Base):
    """User feedback model for backpropagation."""

    __tablename__ = "user_feedbacks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.task_id"), nullable=False)
    iteration = Column(Integer, nullable=False)
    satisfaction_score = Column(Integer, nullable=False)
    feedback_items = Column(JSON, nullable=False, default=list)
    reward = Column(Float, nullable=False)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_task_iteration", "task_id", "iteration"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "iteration": self.iteration,
            "satisfaction_score": self.satisfaction_score,
            "feedback_items": self.feedback_items,
            "reward": self.reward,
            "is_processed": self.is_processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CodeProcessingJobModel(Base):
    """大规模代码处理作业模型."""

    __tablename__ = "code_processing_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), unique=True, nullable=False, index=True)
    repo_url = Column(String(500), nullable=True)
    local_path = Column(String(500), nullable=True)
    branch = Column(String(100), default="main")
    languages = Column(JSON, nullable=True)
    enable_parallel = Column(Boolean, default=True)
    max_workers = Column(Integer, default=4)
    chunk_size = Column(Integer, default=2000)
    enable_incremental = Column(Boolean, default=False)
    status = Column(String(50), default="pending")
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    processed_chunks = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    code_chunks = relationship("CodeChunkModel", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "repo_url": self.repo_url,
            "local_path": self.local_path,
            "branch": self.branch,
            "languages": self.languages,
            "enable_parallel": self.enable_parallel,
            "max_workers": self.max_workers,
            "chunk_size": self.chunk_size,
            "enable_incremental": self.enable_incremental,
            "status": self.status,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files,
            "total_chunks": self.total_chunks,
            "processed_chunks": self.processed_chunks,
            "progress_percentage": self.progress_percentage,
            "error_message": self.error_message,
            "result": self.result,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CodeChunkModel(Base):
    """代码分片存储模型."""

    __tablename__ = "code_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chunk_id = Column(String(100), unique=True, nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("code_processing_jobs.job_id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    language = Column(String(50), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    content_preview = Column(Text, nullable=True)
    embedding = Column(JSON, nullable=True)
    embedding_status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("CodeProcessingJobModel", back_populates="code_chunks")

    __table_args__ = (
        Index("idx_file_path", "file_path"),
        Index("idx_language", "language"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chunk_id": self.chunk_id,
            "job_id": self.job_id,
            "file_path": self.file_path,
            "language": self.language,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "size_bytes": self.size_bytes,
            "content_hash": self.content_hash,
            "content_preview": self.content_preview,
            "embedding_status": self.embedding_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VectorStoreIndexModel(Base):
    """向量存储索引模型."""

    __tablename__ = "vector_store_indices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    index_name = Column(String(100), unique=True, nullable=False)
    vector_store_type = Column(String(50), default="milvus")  # milvus, chroma
    total_vectors = Column(Integer, default=0)
    storage_size_bytes = Column(Integer, default=0)
    dimension = Column(Integer, default=1536)
    language_distribution = Column(JSON, nullable=True)
    last_indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "index_name": self.index_name,
            "vector_store_type": self.vector_store_type,
            "total_vectors": self.total_vectors,
            "storage_size_bytes": self.storage_size_bytes,
            "dimension": self.dimension,
            "language_distribution": self.language_distribution,
            "last_indexed_at": self.last_indexed_at.isoformat() if self.last_indexed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
