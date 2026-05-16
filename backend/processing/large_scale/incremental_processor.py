
"""增量处理引擎 - 支持Git变更检测和缓存机制
"""
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import logging
import time

logger = logging.getLogger(__name__)

# Git集成（可选）
try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    logger.warning("Git not available, using file hash based change detection")


@dataclass
class FileChange:
    """文件变更"""
    path: str
    change_type: str  # added, modified, deleted, renamed
    old_path: Optional[str] = None


@dataclass
class IncrementalStats:
    """增量处理统计"""
    total_files: int
    changed_files: int
    new_files: int
    modified_files: int
    deleted_files: int
    execution_time: float


class GitChangeDetector:
    """Git变更检测器"""
    
    def __init__(self, repo_path: str):
        """初始化Git变更检测器
        
        Args:
            repo_path: Git仓库路径
        """
        self.repo_path = Path(repo_path)
        
        if GIT_AVAILABLE and self.repo_path.joinpath(".git").exists():
            try:
                self.repo = git.Repo(str(self.repo_path))
                self.use_git = True
            except Exception as e:
                logger.warning(f"Git repo init failed: {e}, using file hash mode")
                self.repo = None
                self.use_git = False
        else:
            self.repo = None
            self.use_git = False
    
    def detect_changes(self, since_commit: Optional[str] = None) -> List[FileChange]:
        """检测变更
        
        Args:
            since_commit: 比较的提交（可选）
            
        Returns:
            文件变更列表
        """
        if self.use_git and self.repo:
            return self._detect_changes_git(since_commit)
        else:
            return self._detect_changes_hash()
    
    def _detect_changes_git(self, since_commit: Optional[str]) -> List[FileChange]:
        """使用Git检测变更"""
        changes = []
        
        try:
            if since_commit:
                # 与指定提交比较
                diff = self.repo.git.diff(since_commit, name_status=True)
            else:
                # 与工作区比较
                diff = self.repo.git.diff(name_status=True)
                # 同时检查未跟踪文件
                untracked = self.repo.untracked_files
                for f in untracked:
                    changes.append(FileChange(path=f, change_type="added"))
            
            for line in diff.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t", 1)
                if len(parts) < 2:
                    continue
                status, path = parts[0], parts[1]
                
                if status.startswith("A"):
                    changes.append(FileChange(path=path, change_type="added"))
                elif status.startswith("M"):
                    changes.append(FileChange(path=path, change_type="modified"))
                elif status.startswith("D"):
                    changes.append(FileChange(path=path, change_type="deleted"))
                elif status.startswith("R"):
                    # 重命名：old_path -> new_path
                    old_new = path.split("\t")
                    if len(old_new) >= 2:
                        changes.append(FileChange(
                            path=old_new[1],
                            change_type="renamed",
                            old_path=old_new[0]
                        ))
            
            return changes
            
        except Exception as e:
            logger.warning(f"Git diff failed: {e}, falling back to hash mode")
            return self._detect_changes_hash()
    
    def _detect_changes_hash(self) -> List[FileChange]:
        """使用文件哈希检测变更"""
        # 默认返回空（需要用户自己处理）
        logger.info("Using hash-based change detection (not yet implemented)")
        return []


class IncrementalProcessor:
    """增量处理引擎"""
    
    def __init__(self, cache_path: str = "./.neural_agent_cache"):
        """初始化增量处理器
        
        Args:
            cache_path: 缓存路径
        """
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.hash_cache_file = self.cache_path / "file_hashes.json"
        self.hash_cache = self._load_hash_cache()
    
    def _load_hash_cache(self):
        """加载哈希缓存"""
        if self.hash_cache_file.exists():
            try:
                with open(self.hash_cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_hash_cache(self):
        """保存哈希缓存"""
        try:
            with open(self.hash_cache_file, "w") as f:
                json.dump(self.hash_cache, f)
        except Exception as e:
            logger.warning(f"Failed to save hash cache: {e}")
    
    def compute_file_hash(self, file_path: str) -> str:
        """计算文件哈希
        
        Args:
            file_path: 文件路径
            
        Returns:
            哈希值
        """
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""
    
    def detect_changes(self, repo_path: str) -> List[FileChange]:
        """检测代码变更（集成Git和文件哈希）
        
        Args:
            repo_path: 代码仓库路径
            
        Returns:
            文件变更列表
        """
        start_time = time.time()
        
        # 先尝试Git
        git_detector = GitChangeDetector(repo_path)
        git_changes = git_detector.detect_changes()
        
        if git_changes:
            return git_changes
        
        # Git没有检测到变更，使用文件哈希
        repo_path_obj = Path(repo_path)
        changes = []
        
        # 遍历Python文件
        for py_file in repo_path_obj.rglob("*.py"):
            try:
                rel_path = str(py_file.relative_to(repo_path_obj))
                current_hash = self.compute_file_hash(str(py_file))
                old_hash = self.hash_cache.get(rel_path, "")
                
                if rel_path not in self.hash_cache:
                    # 新文件
                    changes.append(FileChange(path=rel_path, change_type="added"))
                elif current_hash != old_hash:
                    # 修改的文件
                    changes.append(FileChange(path=rel_path, change_type="modified"))
                
                # 更新缓存
                self.hash_cache[rel_path] = current_hash
                
            except Exception as e:
                logger.debug(f"Failed to check {py_file}: {e}")
        
        # 保存缓存
        self._save_hash_cache()
        
        elapsed = time.time() - start_time
        logger.info(f"Detected {len(changes)} changes in {elapsed:.2f}s")
        
        return changes
    
    def filter_relevant_changes(
        self,
        changes: List[FileChange],
        requirement: str = "",
        include_extensions: Optional[List[str]] = None
    ) -> List[FileChange]:
        """过滤相关变更
        
        Args:
            changes: 变更列表
            requirement: 用户需求（用于相关性过滤）
            include_extensions: 包含的文件扩展名
            
        Returns:
            过滤后的变更列表
        """
        if include_extensions is None:
            include_extensions = [".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".h", ".rs"]
        
        filtered = []
        for change in changes:
            path = Path(change.path)
            
            # 只处理特定扩展名
            if path.suffix not in include_extensions:
                continue
            
            # 忽略隐藏文件和目录
            if any(part.startswith(".") for part in path.parts):
                continue
            
            # 忽略测试文件夹
            if "test" in path.parts or "tests" in path.parts:
                continue
            
            filtered.append(change)
        
        return filtered
    
    def get_incremental_stats(self, changes: List[FileChange]) -> IncrementalStats:
        """获取增量处理统计
        
        Args:
            changes: 变更列表
            
        Returns:
            统计信息
        """
        new = 0
        modified = 0
        deleted = 0
        
        for change in changes:
            if change.change_type == "added":
                new += 1
            elif change.change_type == "modified":
                modified += 1
            elif change.change_type == "deleted":
                deleted += 1
        
        return IncrementalStats(
            total_files=len(self.hash_cache),
            changed_files=len(changes),
            new_files=new,
            modified_files=modified,
            deleted_files=deleted,
            execution_time=0.0
        )

