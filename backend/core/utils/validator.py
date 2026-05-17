"""
NeuralAgent 输入验证和边界条件处理
增强输入验证，防止异常数据
"""

from typing import Any, Optional, List
from dataclasses import dataclass


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    message: str
    code: str


class InputValidator:
    """输入验证器"""

    MAX_KEY_LENGTH = 1024
    MAX_VALUE_LENGTH = 1024 * 1024 * 10  # 10MB
    MAX_USERNAME_LENGTH = 256
    MAX_EMAIL_LENGTH = 320

    @classmethod
    def validate_cache_key(cls, key: str) -> tuple[bool, Optional[ValidationError]]:
        """验证缓存键"""
        if not key:
            return False, ValidationError(
                field="key",
                message="Cache key cannot be empty",
                code="EMPTY_KEY"
            )
        
        if not key.strip():
            return False, ValidationError(
                field="key",
                message="Cache key cannot be whitespace only",
                code="WHITESPACE_KEY"
            )

        if len(key) > cls.MAX_KEY_LENGTH:
            return False, ValidationError(
                field="key",
                message=f"Cache key too long (max {cls.MAX_KEY_LENGTH} chars)",
                code="KEY_TOO_LONG"
            )

        if "\x00" in key:
            return False, ValidationError(
                field="key",
                message="Cache key contains null bytes",
                code="INVALID_KEY"
            )

        return True, None

    @classmethod
    def validate_cache_value(cls, value: Any) -> tuple[bool, Optional[ValidationError]]:
        """验证缓存值"""
        if value is None:
            return False, ValidationError(
                field="value",
                message="Cache value cannot be None",
                code="NULL_VALUE"
            )

        if isinstance(value, str) and len(value) > cls.MAX_VALUE_LENGTH:
            return False, ValidationError(
                field="value",
                message=f"Cache value too large (max {cls.MAX_VALUE_LENGTH} bytes)",
                code="VALUE_TOO_LARGE"
            )

        return True, None

    @classmethod
    def validate_username(cls, username: str) -> tuple[bool, Optional[ValidationError]]:
        """验证用户名"""
        if not username:
            return False, ValidationError(
                field="username",
                message="Username cannot be empty",
                code="EMPTY_USERNAME"
            )

        if len(username) > cls.MAX_USERNAME_LENGTH:
            return False, ValidationError(
                field="username",
                message=f"Username too long (max {cls.MAX_USERNAME_LENGTH} chars)",
                code="USERNAME_TOO_LONG"
            )

        if not username.replace("_", "").replace("-", "").isalnum():
            return False, ValidationError(
                field="username",
                message="Username can only contain letters, numbers, hyphens and underscores",
                code="INVALID_USERNAME"
            )

        return True, None

    @classmethod
    def validate_email(cls, email: str) -> tuple[bool, Optional[ValidationError]]:
        """验证邮箱"""
        if not email:
            return False, ValidationError(
                field="email",
                message="Email cannot be empty",
                code="EMPTY_EMAIL"
            )

        if len(email) > cls.MAX_EMAIL_LENGTH:
            return False, ValidationError(
                field="email",
                message=f"Email too long (max {cls.MAX_EMAIL_LENGTH} chars)",
                code="EMAIL_TOO_LONG"
            )

        if "@" not in email or email.count("@") != 1:
            return False, ValidationError(
                field="email",
                message="Invalid email format",
                code="INVALID_EMAIL"
            )

        return True, None

    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """清理 HTML 和 XSS 风险"""
        if not text:
            return text

        dangerous_patterns = [
            ("<script", "&lt;script"),
            ("javascript:", "javascript&#58;"),
            ("onerror=", "onerror&#61;"),
            ("onload=", "onload&#61;"),
            ("onclick=", "onclick&#61;"),
            ("<iframe", "&lt;iframe"),
            ("<object", "&lt;object"),
            ("<embed", "&lt;embed"),
        ]

        sanitized = text
        for pattern, replacement in dangerous_patterns:
            sanitized = sanitized.replace(pattern, replacement)
            sanitized = sanitized.replace(pattern.upper(), replacement)

        return sanitized

    @classmethod
    def validate_prompt_template(cls, name: str, content: str) -> tuple[bool, List[ValidationError]]:
        """验证提示模板"""
        errors = []

        if not name or not name.strip():
            errors.append(ValidationError(
                field="name",
                message="Template name cannot be empty",
                code="EMPTY_NAME"
            ))

        if name and len(name) > 256:
            errors.append(ValidationError(
                field="name",
                message="Template name too long (max 256 chars)",
                code="NAME_TOO_LONG"
            ))

        sanitized_name = cls.sanitize_html(name)
        if sanitized_name != name:
            errors.append(ValidationError(
                field="name",
                message="Template name contains potentially dangerous HTML",
                code="XSS_RISK"
            ))

        if content and len(content) > 100000:
            errors.append(ValidationError(
                field="content",
                message="Template content too long (max 100000 chars)",
                code="CONTENT_TOO_LONG"
            ))

        return len(errors) == 0, errors
