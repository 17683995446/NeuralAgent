"""
NeuralAgent - 多语言支持（i18n）系统
国际化、本地化、多语言翻译
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class Language(Enum):
    """支持的语言"""
    ENGLISH = "en"
    CHINESE_SIMPLIFIED = "zh-CN"
    CHINESE_TRADITIONAL = "zh-TW"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    JAPANESE = "ja"
    KOREAN = "ko"


@dataclass
class I18nConfig:
    """i18n配置"""
    default_language: Language = Language.ENGLISH
    fallback_language: Language = Language.ENGLISH
    translations_dir: str = "translations"
    auto_detect: bool = True
    rtl_languages: List[Language] = field(default_factory=list)


class TranslationStore:
    """翻译存储"""
    
    def __init__(self, config: I18nConfig):
        self.config = config
        self.translations: Dict[Language, Dict[str, str]] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """加载翻译文件"""
        translations_dir = Path(self.config.translations_dir)
        if not translations_dir.exists():
            translations_dir.mkdir(parents=True, exist_ok=True)
        
        for lang in Language:
            file_path = translations_dir / f"{lang.value}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
            else:
                self.translations[lang] = {}
    
    def get_translation(
        self,
        key: str,
        language: Language,
        fallback: Optional[str] = None
    ) -> str:
        """获取翻译"""
        lang_translations = self.translations.get(language, {})
        if key in lang_translations:
            return lang_translations[key]
        
        if self.config.fallback_language != language:
            fallback_translations = self.translations.get(self.config.fallback_language, {})
            if key in fallback_translations:
                return fallback_translations[key]
        
        return fallback or key
    
    def set_translation(
        self,
        key: str,
        value: str,
        language: Language
    ) -> None:
        """设置翻译"""
        if language not in self.translations:
            self.translations[language] = {}
        self.translations[language][key] = value
    
    def save_translations(self, language: Optional[Language] = None) -> None:
        """保存翻译到文件"""
        translations_dir = Path(self.config.translations_dir)
        languages = [language] if language else list(self.translations.keys())
        
        for lang in languages:
            file_path = translations_dir / f"{lang.value}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.translations[lang], f, ensure_ascii=False, indent=2)


class I18nManager:
    """i18n管理器"""
    
    def __init__(self, config: Optional[I18nConfig] = None):
        self.config = config or I18nConfig()
        self.store = TranslationStore(self.config)
        self._user_languages: Dict[str, Language] = {}
    
    def t(
        self,
        key: str,
        language: Optional[Language] = None,
        **kwargs
    ) -> str:
        """翻译快捷方法"""
        lang = language or self.config.default_language
        translation = self.store.get_translation(key, lang)
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return translation
    
    def translate(
        self,
        key: str,
        language: Optional[Language] = None,
        **kwargs
    ) -> str:
        """翻译方法"""
        return self.t(key, language, **kwargs)
    
    def set_user_language(self, user_id: str, language: Language) -> None:
        """设置用户语言偏好"""
        self._user_languages[user_id] = language
    
    def get_user_language(self, user_id: str) -> Language:
        """获取用户语言偏好"""
        return self._user_languages.get(user_id, self.config.default_language)
    
    def detect_language(self, text: str) -> Optional[Language]:
        """简单的语言检测（简化版）"""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        if chinese_chars > len(text) * 0.3:
            return Language.CHINESE_SIMPLIFIED
        
        # 其他语言检测可以在这里添加
        return None
    
    def is_rtl(self, language: Language) -> bool:
        """检查是否是RTL语言"""
        return language in self.config.rtl_languages
    
    def get_available_languages(self) -> List[Language]:
        """获取可用语言列表"""
        return [lang for lang in Language if self.translations.get(lang)]


# 默认翻译（英文）
DEFAULT_TRANSLATIONS = {
    "welcome": "Welcome to NeuralAgent!",
    "error": "An error occurred",
    "success": "Operation successful",
    "loading": "Loading...",
    "submit": "Submit",
    "cancel": "Cancel",
    "save": "Save",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "settings": "Settings",
    "help": "Help",
    "about": "About",
    "chat.input_placeholder": "Type your message here...",
    "chat.send": "Send",
    "memory.added": "Memory added successfully",
    "memory.not_found": "Memory not found",
    "workflow.started": "Workflow started",
    "workflow.completed": "Workflow completed",
    "workflow.failed": "Workflow failed"
}


def create_i18n_manager(
    default_language: Language = Language.ENGLISH,
    **kwargs
) -> I18nManager:
    """创建i18n管理器"""
    config = I18nConfig(default_language=default_language, **kwargs)
    manager = I18nManager(config)
    
    # 初始化默认翻译
    for key, value in DEFAULT_TRANSLATIONS.items():
        manager.store.set_translation(key, value, default_language)
    
    return manager
