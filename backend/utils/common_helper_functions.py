"""Utility helper functions."""
import json
import hashlib
from typing import Any, Dict, List, Optional
from pathlib import Path
from datetime import datetime


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file.

    Args:
        file_path: Path to file

    Returns:
        Hexadecimal hash string
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_text_hash(text: str) -> str:
    """Calculate SHA256 hash of text.

    Args:
        text: Input text

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(text.encode()).hexdigest()


def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary content
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> None:
    """Save data to JSON file.

    Args:
        file_path: Path to output file
        data: Data to save
        indent: JSON indentation
    """
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO string.

    Args:
        dt: Datetime object, defaults to now

    Returns:
        ISO formatted timestamp
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat() + "Z"


def parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO timestamp string.

    Args:
        timestamp: ISO formatted timestamp

    Returns:
        Datetime object
    """
    if timestamp.endswith("Z"):
        timestamp = timestamp[:-1]
    return datetime.fromisoformat(timestamp)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to append if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary.

    Args:
        d: Input dictionary
        parent_key: Parent key prefix
        sep: Separator

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = ".") -> Dict[str, Any]:
    """Unflatten dictionary.

    Args:
        d: Flattened dictionary
        sep: Separator

    Returns:
        Nested dictionary
    """
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def batch_items(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Batch items into chunks.

    Args:
        items: List of items
        batch_size: Batch size

    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def get_language_from_extension(ext: str) -> str:
    """Get language name from file extension.

    Args:
        ext: File extension (e.g., ".py")

    Returns:
        Language name
    """
    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JSX",
        ".tsx": "TSX",
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
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".xml": "XML",
        ".md": "Markdown",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Bash",
        ".zsh": "Zsh",
        ".ps1": "PowerShell",
    }
    return lang_map.get(ext.lower(), "Unknown")
