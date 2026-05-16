"""
NeuralAgent 示例工作流
提供可直接使用的工作流模板
"""

from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    id: str
    name: str
    description: str
    workflow: Dict[str, Any]


class CodeAnalysisWorkflow:
    """代码分析工作流"""
    
    ID = "code_analysis"
    NAME = "代码分析工作流"
    DESCRIPTION = "分析代码库，生成代码质量报告"
    
    @staticmethod
    def create() -> Dict[str, Any]:
        """创建工作流"""
        return {
            "id": "code_analysis",
            "name": "代码分析工作流",
            "description": "分析代码库，识别问题和优化建议",
            "nodes": [
                {
                    "id": "input",
                    "type": "task",
                    "name": "输入处理",
                    "config": {
                        "handler": "input_handler"
                    }
                },
                {
                    "id": "analysis",
                    "type": "task",
                    "name": "代码分析",
                    "config": {
                        "handler": "code_analyzer"
                    }
                },
                {
                    "id": "report",
                    "type": "task",
                    "name": "报告生成",
                    "config": {
                        "handler": "report_generator"
                    }
                },
                {
                    "id": "output",
                    "type": "end",
                    "name": "完成"
                }
            ],
            "edges": [
                {"source": "input", "target": "analysis"},
                {"source": "analysis", "target": "report"},
                {"source": "report", "target": "output"}
            ]
        }


class SmartAssistantWorkflow:
    """智能助手工作流"""
    
    ID = "smart_assistant"
    NAME = "智能助手工作流"
    DESCRIPTION = "多功能智能助手，回答问题，提供建议"
    
    @staticmethod
    def create() -> Dict[str, Any]:
        """创建工作流"""
        return {
            "id": "smart_assistant",
            "name": "智能助手工作流",
            "description": "智能助手，提供问题解答和建议",
            "nodes": [
                {
                    "id": "understand",
                    "type": "task",
                    "name": "意图理解",
                    "config": {
                        "handler": "intent_understanding"
                    }
                },
                {
                    "id": "retrieve",
                    "type": "task",
                    "name": "信息检索",
                    "config": {
                        "handler": "info_retrieval"
                    }
                },
                {
                    "id": "generate",
                    "type": "task",
                    "name": "答案生成",
                    "config": {
                        "handler": "answer_generation"
                    }
                },
                {
                    "id": "respond",
                    "type": "end",
                    "name": "响应"
                }
            ],
            "edges": [
                {"source": "understand", "target": "retrieve"},
                {"source": "retrieve", "target": "generate"},
                {"source": "generate", "target": "respond"}
            ]
        }


class QAWorkflow:
    """知识库问答工作流"""
    
    ID = "knowledge_qa"
    NAME = "知识库问答工作流"
    DESCRIPTION = "基于知识库的智能问答系统"
    
    @staticmethod
    def create() -> Dict[str, Any]:
        """创建工作流"""
        return {
            "id": "knowledge_qa",
            "name": "知识库问答工作流",
            "description": "基于知识库的智能问答",
            "nodes": [
                {
                    "id": "query_parse",
                    "type": "task",
                    "name": "查询解析",
                    "config": {
                        "handler": "query_parser"
                    }
                },
                {
                    "id": "vector_search",
                    "type": "task",
                    "name": "向量检索",
                    "config": {
                        "handler": "vector_search"
                    }
                },
                {
                    "id": "context_combine",
                    "type": "task",
                    "name": "上下文整合",
                    "config": {
                        "handler": "context_combiner"
                    }
                },
                {
                    "id": "answer",
                    "type": "task",
                    "name": "答案生成",
                    "config": {
                        "handler": "answer_generator"
                    }
                },
                {
                    "id": "finish",
                    "type": "end",
                    "name": "完成"
                }
            ],
            "edges": [
                {"source": "query_parse", "target": "vector_search"},
                {"source": "vector_search", "target": "context_combine"},
                {"source": "context_combine", "target": "answer"},
                {"source": "answer", "target": "finish"}
            ]
        }


# 工作流模板库
WORKFLOW_TEMPLATES = {
    CodeAnalysisWorkflow.ID: CodeAnalysisWorkflow,
    SmartAssistantWorkflow.ID: SmartAssistantWorkflow,
    QAWorkflow.ID: QAWorkflow,
}


def get_workflow_template(template_id: str) -> WorkflowTemplate:
    """获取工作流模板"""
    if template_id not in WORKFLOW_TEMPLATES:
        raise ValueError(f"工作流模板不存在: {template_id}")
    return WORKFLOW_TEMPLATES[template_id]


def list_workflow_templates() -> list[WorkflowTemplate]:
    """列出所有工作流模板"""
    templates = []
    for template_id, template_cls in WORKFLOW_TEMPLATES.items():
        templates.append(
            WorkflowTemplate(
                id=template_id,
                name=template_cls.NAME,
                description=template_cls.DESCRIPTION,
                workflow=template_cls.create()
            )
        )
    return templates


def register_workflow_templates():
    """注册工作流模板到引擎"""
    try:
        from backend.core.workflow_engine import get_workflow_engine
        
        engine = get_workflow_engine()
        
        for template in list_workflow_templates():
            engine.add_workflow_from_dict(template.workflow)
            logger.info(f"已注册工作流: {template.name}")
        
        logger.info(f"成功注册 {len(WORKFLOW_TEMPLATES)} 个工作流模板")
    except Exception as e:
        logger.error(f"注册工作流模板失败: {e}")
