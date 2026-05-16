"""
NeuralAgent - 提示工程工作台
提示管理、评估、版本控制、A/B测试

安全特性：
- XSS防护：自动清理HTML和脚本注入
- 输入验证：长度限制、格式检查
- 内容安全：模板内容过滤
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from abc import ABC, abstractmethod


class PromptStatus(Enum):
    """提示状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class EvaluationMetric(Enum):
    """评估指标"""
    RELEVANCE = "relevance"
    ACCURACY = "accuracy"
    COHERENCE = "coherence"
    CREATIVITY = "creativity"
    USEFULNESS = "usefulness"


@dataclass
class PromptVariable:
    """提示变量"""
    name: str
    type: str = "string"
    description: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = True
    examples: List[Any] = field(default_factory=list)


@dataclass
class PromptTemplate:
    """提示模板"""
    id: str
    name: str
    description: str
    content: str
    variables: List[PromptVariable] = field(default_factory=list)
    status: PromptStatus = PromptStatus.DRAFT
    version: int = 1
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptEvaluation:
    """提示评估"""
    id: str
    prompt_id: str
    prompt_version: int
    test_case: str
    output: str
    metrics: Dict[EvaluationMetric, float] = field(default_factory=dict)
    overall_score: Optional[float] = None
    evaluated_by: Optional[str] = None
    evaluated_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None


@dataclass
class ABTest:
    """A/B测试"""
    id: str
    name: str
    description: str
    variants: Dict[str, PromptTemplate]
    test_cases: List[str] = field(default_factory=list)
    results: Dict[str, List[PromptEvaluation]] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    winner: Optional[str] = None


class XSSSanitizer:
    """XSS清理器"""
    
    DANGEROUS_PATTERNS = [
        ("<script", "&lt;script"),
        ("</script>", "&lt;/script&gt;"),
        ("javascript:", "javascript&#58;"),
        ("onerror=", "onerror&#61;"),
        ("onload=", "onload&#61;"),
        ("onclick=", "onclick&#61;"),
        ("onmouseover=", "onmouseover&#61;"),
        ("<iframe", "&lt;iframe"),
        ("</iframe>", "&lt;/iframe&gt;"),
        ("<object", "&lt;object"),
        ("<embed", "&lt;embed"),
        ("<svg", "&lt;svg"),
        ("<style", "&lt;style"),
        ("expression(", "expression&#40;"),
        ("data:", "data&#58;"),
    ]
    
    @classmethod
    def sanitize(cls, text: str) -> str:
        """清理XSS风险"""
        if not text:
            return text
        
        sanitized = text
        for pattern, replacement in cls.DANGEROUS_PATTERNS:
            sanitized = sanitized.replace(pattern, replacement)
            sanitized = sanitized.replace(pattern.upper(), replacement)
        
        return sanitized
    
    @classmethod
    def is_safe(cls, text: str) -> bool:
        """检查文本是否安全"""
        if not text:
            return True
        
        dangerous = [
            "<script", "javascript:", "onerror=", "onload=",
            "<iframe", "<object", "<embed", "expression("
        ]
        
        lower = text.lower()
        for pattern in dangerous:
            if pattern in lower:
                return False
        return True


class PromptStore(ABC):
    """提示存储抽象基类"""
    
    @abstractmethod
    def save(self, template: PromptTemplate) -> bool:
        """保存提示模板"""
        pass
    
    @abstractmethod
    def get(self, template_id: str) -> Optional[PromptTemplate]:
        """获取提示模板"""
        pass
    
    @abstractmethod
    def list(
        self,
        status: Optional[PromptStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[PromptTemplate]:
        """列出提示模板"""
        pass
    
    @abstractmethod
    def delete(self, template_id: str) -> bool:
        """删除提示模板"""
        pass


class InMemoryPromptStore(PromptStore):
    """内存提示存储"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.history: Dict[str, List[PromptTemplate]] = {}
    
    def save(self, template: PromptTemplate) -> bool:
        # 如果已存在，保存历史版本
        if template.id in self.templates:
            old = self.templates[template.id]
            if template.id not in self.history:
                self.history[template.id] = []
            self.history[template.id].append(old)
            template.version = old.version + 1
        
        template.updated_at = datetime.now()
        self.templates[template.id] = template
        return True
    
    def get(self, template_id: str) -> Optional[PromptTemplate]:
        return self.templates.get(template_id)
    
    def list(
        self,
        status: Optional[PromptStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[PromptTemplate]:
        templates = list(self.templates.values())
        
        if status:
            templates = [t for t in templates if t.status == status]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        templates.sort(key=lambda t: t.updated_at, reverse=True)
        return templates[:limit]
    
    def delete(self, template_id: str) -> bool:
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False


class PromptWorkbench:
    """提示工程工作台"""
    
    MAX_NAME_LENGTH = 256
    MAX_CONTENT_LENGTH = 100000
    MAX_DESCRIPTION_LENGTH = 2000
    
    def __init__(self, store: Optional[PromptStore] = None):
        self.store = store or InMemoryPromptStore()
        self.evaluations: Dict[str, PromptEvaluation] = {}
        self.ab_tests: Dict[str, ABTest] = {}
    
    def create_prompt(
        self,
        name: str,
        description: str,
        content: str,
        variables: Optional[List[PromptVariable]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None
    ) -> PromptTemplate:
        """创建提示模板 - 带XSS防护"""
        import uuid
        
        sanitized_name = XSSSanitizer.sanitize(name) if name else name
        sanitized_description = XSSSanitizer.sanitize(description) if description else description
        sanitized_content = XSSSanitizer.sanitize(content) if content else content
        
        if len(sanitized_name) > self.MAX_NAME_LENGTH:
            sanitized_name = sanitized_name[:self.MAX_NAME_LENGTH]
        if len(sanitized_description) > self.MAX_DESCRIPTION_LENGTH:
            sanitized_description = sanitized_description[:self.MAX_DESCRIPTION_LENGTH]
        if len(sanitized_content) > self.MAX_CONTENT_LENGTH:
            sanitized_content = sanitized_content[:self.MAX_CONTENT_LENGTH]
        
        template = PromptTemplate(
            id=str(uuid.uuid4()),
            name=sanitized_name,
            description=sanitized_description,
            content=sanitized_content,
            variables=variables or [],
            tags=tags or [],
            created_by=created_by
        )
        self.store.save(template)
        return template
    
    def update_prompt(
        self,
        template_id: str,
        content: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[PromptStatus] = None
    ) -> Optional[PromptTemplate]:
        """更新提示模板 - 带XSS防护"""
        template = self.store.get(template_id)
        if not template:
            return None
        
        if content is not None:
            template.content = XSSSanitizer.sanitize(content)
            if len(template.content) > self.MAX_CONTENT_LENGTH:
                template.content = template.content[:self.MAX_CONTENT_LENGTH]
        if description is not None:
            template.description = XSSSanitizer.sanitize(description)
            if len(template.description) > self.MAX_DESCRIPTION_LENGTH:
                template.description = template.description[:self.MAX_DESCRIPTION_LENGTH]
        if status is not None:
            template.status = status
        
        self.store.save(template)
        return template
    
    def render_prompt(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """渲染提示"""
        template = self.store.get(template_id)
        if not template:
            return None
        
        rendered = template.content
        
        for var in template.variables:
            placeholder = f"{{{var.name}}}"
            value = variables.get(var.name, var.default_value)
            if value is not None:
                rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    def evaluate_prompt(
        self,
        template_id: str,
        test_case: str,
        output: str,
        metrics: Dict[EvaluationMetric, float],
        evaluated_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> PromptEvaluation:
        """评估提示"""
        import uuid
        
        template = self.store.get(template_id)
        overall_score = sum(metrics.values()) / len(metrics) if metrics else None
        
        evaluation = PromptEvaluation(
            id=str(uuid.uuid4()),
            prompt_id=template_id,
            prompt_version=template.version if template else 1,
            test_case=test_case,
            output=output,
            metrics=metrics,
            overall_score=overall_score,
            evaluated_by=evaluated_by,
            notes=notes
        )
        
        self.evaluations[evaluation.id] = evaluation
        return evaluation
    
    def get_prompt_evaluations(
        self,
        template_id: str,
        limit: int = 100
    ) -> List[PromptEvaluation]:
        """获取提示评估记录"""
        evals = [
            e for e in self.evaluations.values()
            if e.prompt_id == template_id
        ]
        evals.sort(key=lambda e: e.evaluated_at, reverse=True)
        return evals[:limit]
    
    def create_ab_test(
        self,
        name: str,
        description: str,
        variants: Dict[str, PromptTemplate],
        test_cases: Optional[List[str]] = None
    ) -> ABTest:
        """创建A/B测试"""
        import uuid
        
        ab_test = ABTest(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            variants=variants,
            test_cases=test_cases or [],
            results={var_id: [] for var_id in variants.keys()}
        )
        
        self.ab_tests[ab_test.id] = ab_test
        return ab_test
    
    def run_ab_test_evaluation(
        self,
        test_id: str,
        variant_id: str,
        test_case: str,
        output: str,
        metrics: Dict[EvaluationMetric, float],
        evaluated_by: Optional[str] = None
    ) -> Optional[PromptEvaluation]:
        """运行A/B测试评估"""
        ab_test = self.ab_tests.get(test_id)
        if not ab_test or variant_id not in ab_test.variants:
            return None
        
        template = ab_test.variants[variant_id]
        evaluation = self.evaluate_prompt(
            template_id=template.id,
            test_case=test_case,
            output=output,
            metrics=metrics,
            evaluated_by=evaluated_by
        )
        
        if ab_test.id not in ab_test.results:
            ab_test.results[ab_test.id] = []
        ab_test.results[variant_id].append(evaluation)
        
        return evaluation
    
    def complete_ab_test(self, test_id: str) -> Optional[ABTest]:
        """完成A/B测试并确定胜者"""
        ab_test = self.ab_tests.get(test_id)
        if not ab_test:
            return None
        
        # 计算每个变体的平均得分
        variant_scores: Dict[str, float] = {}
        for var_id, evals in ab_test.results.items():
            scores = [e.overall_score for e in evals if e.overall_score is not None]
            if scores:
                variant_scores[var_id] = sum(scores) / len(scores)
        
        # 确定胜者
        if variant_scores:
            ab_test.winner = max(variant_scores.keys(), key=lambda k: variant_scores[k])
        
        ab_test.completed_at = datetime.now()
        return ab_test
    
    def list_prompts(
        self,
        status: Optional[PromptStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[PromptTemplate]:
        """列出提示模板"""
        return self.store.list(status, tags, limit)


def create_prompt_workbench() -> PromptWorkbench:
    """创建提示工程工作台"""
    return PromptWorkbench()
