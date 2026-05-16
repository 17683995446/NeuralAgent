"""
数据库服务层 - 提供代码处理相关的数据库操作
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.models.persistent_data_models import (
    CodeProcessingJobModel,
    CodeChunkModel,
    VectorStoreIndexModel
)

logger = logging.getLogger(__name__)


class CodeProcessingDatabaseService:
    """代码处理数据库服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self,
        job_id: str,
        repo_url: Optional[str] = None,
        local_path: Optional[str] = None,
        branch: str = "main",
        languages: Optional[List[str]] = None,
        enable_parallel: bool = True,
        max_workers: int = 4,
        chunk_size: int = 2000,
        enable_incremental: bool = False
    ) -> CodeProcessingJobModel:
        """创建代码处理作业"""
        try:
            job = CodeProcessingJobModel(
                job_id=job_id,
                repo_url=repo_url,
                local_path=local_path,
                branch=branch,
                languages=languages or [],
                enable_parallel=enable_parallel,
                max_workers=max_workers,
                chunk_size=chunk_size,
                enable_incremental=enable_incremental,
                status="pending"
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Created code processing job: {job_id}")
            return job
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to create job: {e}")
            raise

    def get_job(self, job_id: str) -> Optional[CodeProcessingJobModel]:
        """获取作业信息"""
        return self.db.query(CodeProcessingJobModel).filter(
            CodeProcessingJobModel.job_id == job_id
        ).first()

    def update_job_status(
        self,
        job_id: str,
        status: str,
        total_files: Optional[int] = None,
        processed_files: Optional[int] = None,
        failed_files: Optional[int] = None,
        total_chunks: Optional[int] = None,
        processed_chunks: Optional[int] = None,
        progress_percentage: Optional[float] = None,
        error_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Optional[CodeProcessingJobModel]:
        """更新作业状态"""
        try:
            job = self.get_job(job_id)
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return None

            update_data = {"status": status}
            
            if total_files is not None:
                update_data["total_files"] = total_files
            if processed_files is not None:
                update_data["processed_files"] = processed_files
            if failed_files is not None:
                update_data["failed_files"] = failed_files
            if total_chunks is not None:
                update_data["total_chunks"] = total_chunks
            if processed_chunks is not None:
                update_data["processed_chunks"] = processed_chunks
            if progress_percentage is not None:
                update_data["progress_percentage"] = progress_percentage
            if error_message is not None:
                update_data["error_message"] = error_message
            if result is not None:
                update_data["result"] = result
            if start_time is not None:
                update_data["start_time"] = start_time
            if end_time is not None:
                update_data["end_time"] = end_time

            for key, value in update_data.items():
                setattr(job, key, value)

            self.db.commit()
            self.db.refresh(job)
            logger.debug(f"Updated job {job_id} status: {status}")
            return job
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update job: {e}")
            raise

    def list_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[CodeProcessingJobModel]:
        """列出作业"""
        query = self.db.query(CodeProcessingJobModel)
        if status:
            query = query.filter(CodeProcessingJobModel.status == status)
        return query.order_by(
            CodeProcessingJobModel.created_at.desc()
        ).offset(offset).limit(limit).all()

    def add_chunk(
        self,
        chunk_id: str,
        job_id: str,
        file_path: str,
        language: str,
        start_line: int,
        end_line: int,
        size_bytes: int,
        content_hash: str,
        content_preview: Optional[str] = None
    ) -> CodeChunkModel:
        """添加代码分片"""
        try:
            chunk = CodeChunkModel(
                chunk_id=chunk_id,
                job_id=job_id,
                file_path=file_path,
                language=language,
                start_line=start_line,
                end_line=end_line,
                size_bytes=size_bytes,
                content_hash=content_hash,
                content_preview=content_preview
            )
            self.db.add(chunk)
            self.db.commit()
            self.db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to add chunk: {e}")
            raise

    def get_chunk(self, chunk_id: str) -> Optional[CodeChunkModel]:
        """获取代码分片"""
        return self.db.query(CodeChunkModel).filter(
            CodeChunkModel.chunk_id == chunk_id
        ).first()

    def update_chunk_embedding(
        self,
        chunk_id: str,
        embedding: List[float],
        status: str = "embedded"
    ) -> Optional[CodeChunkModel]:
        """更新代码分片的嵌入向量"""
        try:
            chunk = self.get_chunk(chunk_id)
            if not chunk:
                return None

            chunk.embedding = embedding
            chunk.embedding_status = status
            self.db.commit()
            self.db.refresh(chunk)
            return chunk
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update chunk embedding: {e}")
            raise

    def get_chunks_by_job(
        self,
        job_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[CodeChunkModel]:
        """获取作业的所有代码分片"""
        return self.db.query(CodeChunkModel).filter(
            CodeChunkModel.job_id == job_id
        ).offset(offset).limit(limit).all()

    def get_or_create_vector_index(
        self,
        index_name: str,
        vector_store_type: str = "milvus",
        dimension: int = 1536
    ) -> VectorStoreIndexModel:
        """获取或创建向量存储索引"""
        try:
            index = self.db.query(VectorStoreIndexModel).filter(
                VectorStoreIndexModel.index_name == index_name
            ).first()

            if not index:
                index = VectorStoreIndexModel(
                    index_name=index_name,
                    vector_store_type=vector_store_type,
                    dimension=dimension
                )
                self.db.add(index)
                self.db.commit()
                self.db.refresh(index)
                logger.info(f"Created vector index: {index_name}")

            return index
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to get/create vector index: {e}")
            raise

    def update_vector_index_stats(
        self,
        index_name: str,
        total_vectors: Optional[int] = None,
        storage_size_bytes: Optional[int] = None,
        language_distribution: Optional[Dict[str, int]] = None
    ) -> Optional[VectorStoreIndexModel]:
        """更新向量存储索引统计"""
        try:
            index = self.db.query(VectorStoreIndexModel).filter(
                VectorStoreIndexModel.index_name == index_name
            ).first()

            if not index:
                return None

            if total_vectors is not None:
                index.total_vectors = total_vectors
            if storage_size_bytes is not None:
                index.storage_size_bytes = storage_size_bytes
            if language_distribution is not None:
                index.language_distribution = language_distribution
            index.last_indexed_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(index)
            return index
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update vector index stats: {e}")
            raise

    def delete_job(self, job_id: str) -> bool:
        """删除作业"""
        try:
            job = self.get_job(job_id)
            if not job:
                return False

            self.db.delete(job)
            self.db.commit()
            logger.info(f"Deleted job: {job_id}")
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to delete job: {e}")
            raise
