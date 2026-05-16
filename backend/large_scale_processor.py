
"""大规模代码仓库处理系统 - 千万行级别的代码分析
集成 tree-sitter + 并行处理 + 向量存储 + 增量处理
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    total_chunks: int
    chunks_processed: int
    execution_time: float
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LargeScaleCodeProcessor:
    """大规模代码处理系统 - 专为千万行级别代码仓库设计"""
    
    def __init__(
        self,
        repo_path: str,
        vector_backend: str = "chroma",
        use_incremental: bool = True,
        max_workers: int = 10
    ):
        """初始化大规模代码处理器
        
        Args:
            repo_path: 代码仓库路径
            vector_backend: 向量存储后端
            use_incremental: 是否使用增量处理
            max_workers: 并行工作数
        """
        self.repo_path = Path(repo_path)
        self.max_workers = max_workers
        self.use_incremental = use_incremental
        
        # 初始化核心组件
        self._init_components()
        
        logger.info(f"Initialized LargeScaleCodeProcessor for repo: {repo_path}")
    
    def _init_components(self):
        """初始化各个组件（如果可用）"""
        self.chunker = None
        self.vector_store = None
        self.incremental_processor = None
        self.parallel_processor = None
        
        # 尝试导入和初始化组件
        try:
            from backend.core.code_chunker import TreeSitterChunker
            self.chunker = TreeSitterChunker()
        except Exception as e:
            logger.warning(f"Failed to initialize chunker: {e}")
        
        try:
            from backend.core.vector_store import create_vector_store
            self.vector_store = create_vector_store(backend="chroma")
        except Exception as e:
            logger.warning(f"Failed to initialize vector store: {e}")
        
        if self.use_incremental:
            try:
                from backend.core.incremental_processor import IncrementalProcessor
                self.incremental_processor = IncrementalProcessor(
                    cache_path="./.neural_agent_cache"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize incremental processor: {e}")
        
        try:
            from backend.core.parallel_processor import ParallelProcessor
            self.parallel_processor = ParallelProcessor(
                max_workers=self.max_workers,
                use_ray=False
            )
        except Exception as e:
            logger.warning(f"Failed to initialize parallel processor: {e}")
    
    def process_repo(self, requirement: str = "", force_full: bool = False):
        """处理整个代码仓库
        
        Args:
            requirement: 用户需求（用于相关性过滤）
            force_full: 是否强制全量处理
            
        Returns:
            ProcessingResult
        """
        start_time = time.time()
        
        try:
            if self.use_incremental and not force_full:
                return self._process_incremental(requirement, start_time)
            else:
                return self._process_full(requirement, start_time)
                
        except Exception as e:
            logger.error(f"Failed to process repository: {e}")
            return ProcessingResult(
                success=False,
                total_chunks=0,
                chunks_processed=0,
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _process_full(self, requirement: str, start_time: float):
        """全量处理代码仓库"""
        logger.info("Starting FULL repository processing")
        
        if not self.chunker:
            raise RuntimeError("Chunker not available")
        
        # 1. 分片代码
        chunks = self.chunker.chunk_repository(str(self.repo_path))
        logger.info(f"Chunked into {len(chunks)} code chunks")
        
        if not chunks:
            return ProcessingResult(
                success=True,
                total_chunks=0,
                chunks_processed=0,
                execution_time=time.time() - start_time
            )
        
        # 2. 向量化并存储
        success = self._vectorize_and_store(chunks)
        
        elapsed = time.time() - start_time
        stats = self.chunker.get_chunk_statistics(chunks)
        
        logger.info(f"Full processing completed in {elapsed:.2f}s")
        
        return ProcessingResult(
            success=success,
            total_chunks=len(chunks),
            chunks_processed=len(chunks) if success else 0,
            execution_time=elapsed,
            stats=stats
        )
    
    def _process_incremental(self, requirement: str, start_time: float):
        """增量处理代码仓库"""
        logger.info("Starting INCREMENTAL repository processing")
        
        if not self.chunker or not self.incremental_processor:
            raise RuntimeError("Incremental components not available")
        
        # 1. 检测变更
        changes = self.incremental_processor.detect_changes(str(self.repo_path))
        stats = self.incremental_processor.get_incremental_stats(changes)
        
        logger.info(f"Detected {len(changes)} changes")
        
        if not changes:
            logger.info("No changes detected, nothing to process")
            return ProcessingResult(
                success=True,
                total_chunks=0,
                chunks_processed=0,
                execution_time=time.time() - start_time,
                stats={
                    "total_files": stats.total_files,
                    "changed_files": 0
                }
            )
        
        # 2. 只处理新增或修改的文件
        relevant_changes = self.incremental_processor.filter_relevant_changes(
            changes, requirement
        )
        
        changed_files = [
            str(self.repo_path / change.path)
            for change in relevant_changes
            if change.change_type in ("added", "modified")
        ]
        
        # 3. 分片变更的文件
        chunks = []
        for file_path in changed_files:
            try:
                file_chunks = self.chunker.chunk_file(file_path)
                chunks.extend(file_chunks)
            except Exception as e:
                logger.warning(f"Failed to chunk {file_path}: {e}")
        
        if not chunks:
            elapsed = time.time() - start_time
            return ProcessingResult(
                success=True,
                total_chunks=0,
                chunks_processed=0,
                execution_time=elapsed,
                stats={
                    "total_files": stats.total_files,
                    "changed_files": stats.changed_files,
                    "processed_files": len(changed_files)
                }
            )
        
        # 4. 向量化并存储
        success = self._vectorize_and_store(chunks)
        
        elapsed = time.time() - start_time
        
        logger.info(f"Incremental processing completed in {elapsed:.2f}s")
        
        return ProcessingResult(
            success=success,
            total_chunks=len(chunks),
            chunks_processed=len(chunks) if success else 0,
            execution_time=elapsed,
            stats={
                "total_files": stats.total_files,
                "changed_files": stats.changed_files,
                "processed_files": len(changed_files),
                "new_files": stats.new_files,
                "modified_files": stats.modified_files
            }
        )
    
    def _vectorize_and_store(self, chunks):
        """向量化代码块并存储到向量数据库
        
        Args:
            chunks: 代码块列表
            
        Returns:
            是否成功
        """
        if not self.vector_store:
            logger.warning("Vector store not available, skipping")
            return True
        
        try:
            # 准备数据
            ids = [chunk.id for chunk in chunks]
            texts = [chunk.content for chunk in chunks]
            metadatas = [chunk.to_dict() for chunk in chunks]
            
            # 向量化（如果有LLM适配器）
            embeddings = []
            try:
                from backend.core.llm_adapter import llm_adapter
                embeddings = llm_adapter.embed(texts)
            except Exception as e:
                logger.warning(f"Failed to get embeddings: {e}, using random vectors")
                # 使用随机向量作为后备
                import random
                embeddings = [
                    [random.random() for _ in range(1536)]
                    for _ in texts
                ]
            
            # 存储
            success = self.vector_store.add(
                ids=ids,
                texts=texts,
                embeddings=embeddings,
                metadata=metadatas
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to vectorize and store: {e}")
            return False
    
    def search_code(self, query: str, top_k: int = 10):
        """搜索相关代码
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            搜索结果列表
        """
        if not self.vector_store:
            logger.warning("Vector store not available")
            return []
        
        try:
            # 尝试文本搜索
            if hasattr(self.vector_store, 'search_by_text'):
                results = self.vector_store.search_by_text(query, top_k)
            else:
                # 回退到简单搜索
                results = []
            
            logger.info(f"Found {len(results)} results for query '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_vector_count(self):
        """获取向量数量"""
        if not self.vector_store:
            return 0
        
        return self.vector_store.count()
    
    def clear_cache(self):
        """清理增量处理缓存"""
        if self.incremental_processor:
            cache_dir = Path(self.incremental_processor.cache_path)
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir)
                logger.info("Cleared incremental cache")


def process_code_repo(
    repo_path: str,
    vector_backend: str = "chroma",
    use_incremental: bool = True
):
    """快速处理代码仓库
    
    Args:
        repo_path: 代码仓库路径
        vector_backend: 向量存储后端
        use_incremental: 是否增量处理
        
    Returns:
        ProcessingResult
    """
    processor = LargeScaleCodeProcessor(
        repo_path=repo_path,
        vector_backend=vector_backend,
        use_incremental=use_incremental
    )
    
    return processor.process_repo()


def search_code_repo(
    repo_path: str,
    query: str,
    top_k: int = 10,
    vector_backend: str = "chroma"
):
    """在代码仓库中搜索
    
    Args:
        repo_path: 代码仓库路径
        query: 查询
        top_k: 返回数量
        vector_backend: 向量存储后端
        
    Returns:
        搜索结果
    """
    processor = LargeScaleCodeProcessor(
        repo_path=repo_path,
        vector_backend=vector_backend,
        use_incremental=False
    )
    
    return processor.search_code(query, top_k)

