"""Input Layer - FastAPI + Pydantic + GitPython integration."""
import os
import shutil
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import uuid

import git
from git import Repo, GitCommandError

from backend.config import settings
from backend.api.schemas import TaskInput, TaskContext
from backend.models.persistent_data_models import TaskModel

logger = logging.getLogger(__name__)


class InputLayer:
    """Input layer for task initialization.

    Responsibilities:
    - Receive and validate user input
    - Clone/read code repository
    - Initialize task context
    - Trigger forward propagation
    """

    def __init__(self, db_session: Any):
        """Initialize input layer.

        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.output_dir = Path(settings.task_output_dir)
        self.repos_dir = Path(settings.code_repos_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    async def process_task_input(
        self,
        task_input: TaskInput
    ) -> TaskContext:
        """Process task input and initialize task.

        Args:
            task_input: Validated task input

        Returns:
            TaskContext with initialized task information

        Raises:
            ValueError: If input validation fails
            GitCommandError: If Git operations fail
        """
        logger.info(f"Processing task input: {task_input.task_id}")

        if not task_input.code_repo_url and not task_input.local_code_path:
            raise ValueError("Either code_repo_url or local_code_path must be provided")

        code_repo_path = await self._prepare_code_repository(task_input)

        task_output_dir = self.output_dir / task_input.task_id
        task_output_dir.mkdir(parents=True, exist_ok=True)

        (task_output_dir / "convolution").mkdir(exist_ok=True)
        (task_output_dir / "pooling").mkdir(exist_ok=True)
        (task_output_dir / "fc1").mkdir(exist_ok=True)
        (task_output_dir / "fc2").mkdir(exist_ok=True)
        (task_output_dir / "fc3").mkdir(exist_ok=True)
        (task_output_dir / "output").mkdir(exist_ok=True)

        task_model = TaskModel(
            task_id=task_input.task_id,
            user_requirement=task_input.user_requirement,
            code_repo_url=task_input.code_repo_url,
            local_code_path=code_repo_path,
            target_branch=task_input.target_branch,
            status="initialized",
            max_iteration=task_input.max_iteration,
            learning_rate=task_input.learning_rate,
            current_iteration=0,
            output_path=str(task_output_dir),
        )

        self.db_session.add(task_model)
        self.db_session.commit()

        logger.info(f"Task {task_input.task_id} initialized successfully")

        return TaskContext(
            task_id=task_input.task_id,
            status="initialized",
            user_requirement=task_input.user_requirement,
            code_repo_path=code_repo_path,
            max_iteration=task_input.max_iteration,
            learning_rate=task_input.learning_rate,
            created_at=datetime.utcnow().isoformat(),
            message="Task initialized successfully, forward propagation ready to start"
        )

    async def _prepare_code_repository(
        self,
        task_input: TaskInput
    ) -> str:
        """Prepare code repository for processing.

        Args:
            task_input: Task input with repository information

        Returns:
            Path to prepared code repository

        Raises:
            GitCommandError: If Git operations fail
        """
        if task_input.local_code_path:
            local_path = Path(task_input.local_code_path)
            if not local_path.exists():
                raise ValueError(f"Local code path does not exist: {task_input.local_code_path}")
            return str(local_path.resolve())

        if task_input.code_repo_url:
            return await self._clone_repository(task_input)

        raise ValueError("No code repository information provided")

    async def _clone_repository(
        self,
        task_input: TaskInput
    ) -> str:
        """Clone Git repository.

        Args:
            task_input: Task input with repository URL

        Returns:
            Path to cloned repository

        Raises:
            GitCommandError: If clone fails
        """
        repo_name = self._extract_repo_name(task_input.code_repo_url)
        target_dir = self.repos_dir / task_input.task_id

        if target_dir.exists():
            shutil.rmtree(target_dir)

        try:
            logger.info(f"Cloning repository: {task_input.code_repo_url}")
            repo = Repo.clone_from(
                task_input.code_repo_url,
                target_dir,
                branch=task_input.target_branch,
                depth=100
            )

            if task_input.target_branch != repo.active_branch.name:
                repo.git.checkout(task_input.target_branch)

            logger.info(f"Repository cloned to: {target_dir}")
            return str(target_dir)

        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL.

        Args:
            repo_url: Git repository URL

        Returns:
            Repository name
        """
        from pathlib import Path
        url_path = Path(repo_url.rstrip("/"))
        return url_path.stem or f"repo_{uuid.uuid4().hex[:8]}"

    async def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task context by task ID.

        Args:
            task_id: Task identifier

        Returns:
            Task context dictionary or None
        """
        task = self.db_session.query(TaskModel).filter_by(task_id=task_id).first()

        if not task:
            return None

        return {
            "task_id": task.task_id,
            "user_requirement": task.user_requirement,
            "code_repo_path": task.local_code_path,
            "target_branch": task.target_branch,
            "status": task.status,
            "max_iteration": task.max_iteration,
            "learning_rate": task.learning_rate,
            "current_iteration": task.current_iteration,
            "output_path": task.output_path,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        current_layer: Optional[str] = None
    ) -> bool:
        """Update task status.

        Args:
            task_id: Task identifier
            status: New status
            current_layer: Current executing layer

        Returns:
            True if updated successfully
        """
        task = self.db_session.query(TaskModel).filter_by(task_id=task_id).first()

        if not task:
            return False

        task.status = status
        if current_layer:
            task.updated_at = datetime.utcnow()

        self.db_session.commit()
        return True

    async def increment_iteration(self, task_id: str) -> int:
        """Increment task iteration counter.

        Args:
            task_id: Task identifier

        Returns:
            New iteration count
        """
        task = self.db_session.query(TaskModel).filter_by(task_id=task_id).first()

        if not task:
            return 0

        task.current_iteration += 1
        task.updated_at = datetime.utcnow()
        self.db_session.commit()

        return task.current_iteration

    async def validate_repository(self, repo_path: str) -> Dict[str, Any]:
        """Validate repository structure and contents.

        Args:
            repo_path: Path to repository

        Returns:
            Validation result dictionary
        """
        repo = Repo(repo_path)
        valid_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
            ".rs", ".cpp", ".c", ".h", ".hpp", ".cs", ".rb",
            ".php", ".swift", ".kt", ".scala", ".vue", ".svelte"
        }

        file_count = 0
        total_lines = 0
        languages = set()

        for root, dirs, files in os.walk(repo_path):
            if ".git" in root or "node_modules" in root or "__pycache__" in root:
                continue

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in valid_extensions:
                    file_count += 1
                    try:
                        file_path = Path(root) / file
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            total_lines += len(f.readlines())
                        languages.add(self._get_language_from_ext(ext))
                    except Exception:
                        pass

        return {
            "valid": file_count > 0,
            "file_count": file_count,
            "total_lines": total_lines,
            "languages": list(languages),
            "repo_branch": repo.active_branch.name,
            "last_commit": repo.head.commit.hexsha[:8],
        }

    def _get_language_from_ext(self, ext: str) -> str:
        """Get programming language from file extension.

        Args:
            ext: File extension

        Returns:
            Language name
        """
        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React",
            ".tsx": "React TS",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++ Header",
            ".hpp": "C++ Header",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".vue": "Vue",
            ".svelte": "Svelte",
        }
        return lang_map.get(ext, "Unknown")
