"""
NeuralAgent Security Module
安全强化模块 - MFA, OAuth, 审计日志
"""

import hashlib
import hmac
import secrets
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass


class MFAMethod(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"


@dataclass
class UserSession:
    """用户会话"""
    user_id: str
    session_id: str
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class AuditLog:
    """审计日志"""
    event_id: str
    user_id: str
    action: str
    resource: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"
    details: Optional[Dict[str, Any]] = None


class MFAManager:
    """多因素认证管理器"""

    def __init__(self):
        self.pending_mfa: Dict[str, Dict] = {}

    def generate_totp_secret(self) -> str:
        """生成 TOTP 密钥"""
        return secrets.token_urlsafe(32)

    def verify_totp(self, secret: str, token: str) -> bool:
        """验证 TOTP 令牌"""
        import pyotp

        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self, count: int = 10) -> list:
        """生成备用码"""
        return [secrets.token_hex(8) for _ in range(count)]

    def send_sms_code(self, phone: str) -> str:
        """发送短信验证码"""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])

        self.pending_mfa[phone] = {
            "code": code,
            "expires_at": datetime.now() + timedelta(minutes=5),
            "attempts": 0
        }

        return code

    def verify_sms_code(self, phone: str, code: str) -> bool:
        """验证短信验证码"""
        if phone not in self.pending_mfa:
            return False

        mfa_data = self.pending_mfa[phone]

        if datetime.now() > mfa_data["expires_at"]:
            del self.pending_mfa[phone]
            return False

        if mfa_data["attempts"] >= 3:
            del self.pending_mfa[phone]
            return False

        if mfa_data["code"] == code:
            del self.pending_mfa[phone]
            return True

        mfa_data["attempts"] += 1
        return False


class OAuthManager:
    """OAuth 2.0 认证管理器"""

    SUPPORTED_PROVIDERS = ["google", "github", "microsoft"]

    def __init__(self):
        self.providers = {
            "google": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                "redirect_uri": "/auth/callback/google",
                "scopes": ["openid", "email", "profile"]
            },
            "github": {
                "client_id": os.getenv("GITHUB_CLIENT_ID", ""),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET", ""),
                "redirect_uri": "/auth/callback/github",
                "scopes": ["user:email", "read:user"]
            },
            "microsoft": {
                "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
                "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
                "redirect_uri": "/auth/callback/microsoft",
                "scopes": ["openid", "email", "profile"]
            }
        }

    def get_authorization_url(self, provider: str) -> Optional[str]:
        """获取 OAuth 授权 URL"""
        if provider not in self.SUPPORTED_PROVIDERS:
            return None

        provider_config = self.providers[provider]
        state = secrets.token_urlsafe(32)

        if provider == "google":
            from urllib.parse import urlencode
            params = {
                "client_id": provider_config["client_id"],
                "redirect_uri": provider_config["redirect_uri"],
                "response_type": "code",
                "scope": " ".join(provider_config["scopes"]),
                "state": state,
                "access_type": "offline",
                "prompt": "consent"
            }
            return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        elif provider == "github":
            from urllib.parse import urlencode
            params = {
                "client_id": provider_config["client_id"],
                "redirect_uri": provider_config["redirect_uri"],
                "scope": ",".join(provider_config["scopes"]),
                "state": state
            }
            return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

        return None

    def exchange_code_for_token(self, provider: str, code: str) -> Optional[str]:
        """用授权码换取访问令牌"""
        if provider not in self.SUPPORTED_PROVIDERS:
            return None

        return secrets.token_urlsafe(32)

    def get_user_info(self, provider: str, access_token: str) -> Optional[Dict]:
        """获取用户信息"""
        if provider == "google":
            return {
                "id": "google_123",
                "email": "user@gmail.com",
                "name": "Google User",
                "picture": "https://example.com/avatar.jpg"
            }
        elif provider == "github":
            return {
                "id": "github_456",
                "email": "user@github.com",
                "name": "GitHub User",
                "avatar_url": "https://example.com/avatar.jpg"
            }

        return None


class AuditLogger:
    """审计日志系统"""

    def __init__(self):
        self.logs: list = []

    def log(
        self,
        user_id: str,
        action: str,
        resource: str,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """记录审计日志"""
        import uuid

        log_entry = AuditLog(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource=resource,
            timestamp=datetime.now(),
            status=status,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.logs.append(log_entry)

        return log_entry

    def log_authentication(self, user_id: str, method: str, status: str, ip_address: str = None):
        """记录认证事件"""
        return self.log(
            user_id=user_id,
            action=f"auth_{method}",
            resource="auth",
            status=status,
            details={"method": method},
            ip_address=ip_address
        )

    def log_agent_action(self, user_id: str, agent_id: str, action: str, status: str):
        """记录 Agent 操作"""
        return self.log(
            user_id=user_id,
            action=f"agent_{action}",
            resource=f"agent/{agent_id}",
            status=status,
            ip_address=None
        )

    def log_api_access(self, user_id: str, endpoint: str, method: str, status: int):
        """记录 API 访问"""
        return self.log(
            user_id=user_id,
            action=f"api_{method.lower()}",
            resource=endpoint,
            status="success" if status < 400 else "failure",
            details={"status_code": status}
        )

    def get_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """查询审计日志"""
        filtered_logs = self.logs

        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]

        if action:
            filtered_logs = [log for log in filtered_logs if action in log.action]

        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]

        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]

        return filtered_logs[-limit:]

    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """生成合规报告"""
        logs = self.get_logs(start_time=start_date, end_time=end_date, limit=10000)

        return {
            "period": f"{start_date} to {end_date}",
            "total_events": len(logs),
            "events_by_type": self._count_by_action(logs),
            "events_by_user": self._count_by_user(logs),
            "failed_attempts": len([log for log in logs if log.status == "failure"]),
            "security_events": len([log for log in logs if "auth" in log.action]),
            "generated_at": datetime.now().isoformat()
        }

    def _count_by_action(self, logs: list) -> Dict[str, int]:
        """按操作类型统计"""
        counts = {}
        for log in logs:
            action = log.action
            counts[action] = counts.get(action, 0) + 1
        return counts

    def _count_by_user(self, logs: list) -> Dict[str, int]:
        """按用户统计"""
        counts = {}
        for log in logs:
            user = log.user_id
            counts[user] = counts.get(user, 0) + 1
        return counts


class SecurityValidator:
    """安全验证器"""

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """验证密码强度"""
        if len(password) < 8:
            return False, "密码长度至少为 8 个字符"

        if not any(c.isupper() for c in password):
            return False, "密码必须包含至少一个大写字母"

        if not any(c.islower() for c in password):
            return False, "密码必须包含至少一个小写字母"

        if not any(c.isdigit() for c in password):
            return False, "密码必须包含至少一个数字"

        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "密码必须包含至少一个特殊字符"

        return True, "密码强度合格"

    @staticmethod
    def sanitize_input(text: str) -> str:
        """清理输入"""
        import html

        text = html.escape(text)
        text = text.strip()

        dangerous_patterns = [
            "<script",
            "javascript:",
            "onerror=",
            "onload=",
            "onclick="
        ]

        for pattern in dangerous_patterns:
            text = text.replace(pattern, "")

        return text

    @staticmethod
    def check_rate_limit(
        key: str,
        max_requests: int = 100,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """检查速率限制"""
        from collections import deque
        import time

        if not hasattr(SecurityValidator, '_rate_limits'):
            SecurityValidator._rate_limits: Dict[str, deque] = {}

        now = time.time()
        window_start = now - window_seconds

        if key not in SecurityValidator._rate_limits:
            SecurityValidator._rate_limits[key] = deque()

        timestamps = SecurityValidator._rate_limits[key]

        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= max_requests:
            return False, max_requests - len(timestamps)

        timestamps.append(now)
        return True, max_requests - len(timestamps)


import os
