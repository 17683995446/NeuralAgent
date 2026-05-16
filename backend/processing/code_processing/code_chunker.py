
"""基于tree-sitter的智能代码分片器"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """代码块数据类"""
    id: str
    type: str  # function, class, module, method
    name: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    docstring: Optional[str] = None
    signature: Optional[str] = None
    imports: List[str] = None
    dependencies: List[str] = None
    complexity: int = 1
    language: str = "python"
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []
        if self.dependencies is None:
            self.dependencies = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "docstring": self.docstring,
            "signature": self.signature,
            "imports": self.imports,
            "dependencies": self.dependencies,
            "complexity": self.complexity,
            "language": self.language,
            "line_count": self.end_line - self.start_line + 1
        }


class TreeSitterChunker:
    """基于tree-sitter的智能代码分片器"""
    
    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".cpp": "cpp",
        ".c": "c",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
    }
    
    FUNCTION_TYPES = {
        "python": ["function_definition", "class_definition", "async_function_definition"],
        "javascript": ["function_declaration", "function_expression", "arrow_function", "method_definition", "class_declaration"],
        "typescript": ["function_declaration", "function_expression", "arrow_function", "method_definition", "class_declaration", "interface_declaration"],
        "java": ["method_declaration", "constructor_declaration", "class_declaration", "interface_declaration"],
        "go": ["function_declaration", "method_declaration", "type_declaration"],
        "rust": ["function_item", "impl_item", "struct_item", "enum_item"],
    }
    
    def __init__(self, max_chunk_lines: int = 200, overlap_lines: int = 10):
        """初始化分片器
        
        Args:
            max_chunk_lines: 单个块最大行数
            overlap_lines: 块之间的重叠行数
        """
        self.max_chunk_lines = max_chunk_lines
        self.overlap_lines = overlap_lines
        self.parsers: Dict[str, Any] = {}
        self._init_parsers()
    
    def _init_parsers(self):
        """初始化各语言的parser"""
        try:
            import tree_sitter
            from tree_sitter import Language, Parser
            
            # 加载Python parser
            try:
                from tree_sitter_python import language as py_language
                self.parsers["python"] = Parser(Language(py_language()))
                logger.info("Python parser loaded")
            except ImportError:
                logger.warning("tree-sitter-python not available")
            
            # 加载JavaScript parser
            try:
                from tree_sitter_javascript import language as js_language
                self.parsers["javascript"] = Parser(Language(js_language()))
                self.parsers["jsx"] = self.parsers["javascript"]
                logger.info("JavaScript parser loaded")
            except ImportError:
                logger.warning("tree-sitter-javascript not available")
            
            # 加载Java parser
            try:
                from tree_sitter_java import language as java_language
                self.parsers["java"] = Parser(Language(java_language()))
                logger.info("Java parser loaded")
            except ImportError:
                logger.warning("tree-sitter-java not available")
                
        except ImportError:
            logger.error("tree-sitter not available, using fallback chunking")
    
    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """分片单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            代码块列表
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return []
        
        ext = path.suffix.lower()
        language = self.LANGUAGE_EXTENSIONS.get(ext, "text")
        
        if language in self.parsers:
            return self._chunk_with_ast(path, language)
        else:
            return self._chunk_fallback(path)
    
    def chunk_repository(self, repo_path: str, extensions: List[str] = None) -> List[CodeChunk]:
        """分片整个仓库
        
        Args:
            repo_path: 仓库路径
            extensions: 要处理的文件扩展名列表
            
        Returns:
            所有代码块列表
        """
        if extensions is None:
            extensions = list(self.LANGUAGE_EXTENSIONS.keys())
        
        all_chunks = []
        repo = Path(repo_path)
        
        for ext in extensions:
            for file_path in repo.rglob(f"*{ext}"):
                # 跳过测试文件和特殊目录
                if self._should_skip(file_path):
                    continue
                
                chunks = self.chunk_file(str(file_path))
                all_chunks.extend(chunks)
        
        logger.info(f"Repository chunked: {len(all_chunks)} chunks from {repo_path}")
        return all_chunks
    
    def _should_skip(self, file_path: Path) -> bool:
        """判断是否应该跳过文件"""
        skip_patterns = [
            "__pycache__", ".git", "node_modules", ".venv", "venv",
            ".env", ".pytest_cache", ".mypy_cache", "build", "dist",
            ".egg-info", ".tox", "coverage", ".coverage"
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)
    
    def _chunk_with_ast(self, file_path: Path, language: str) -> List[CodeChunk]:
        """使用AST进行智能分片"""
        chunks = []
        
        try:
            with open(file_path, "rb") as f:
                tree = self.parsers[language].parse(f.read())
            
            root_node = tree.root_node
            file_content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = file_content.split("\n")
            
            # 提取导入语句
            imports = self._extract_imports(root_node, language)
            
            # 提取函数和类定义
            function_types = self.FUNCTION_TYPES.get(language, ["function_declaration"])
            definitions = self._extract_definitions(root_node, function_types, language)
            
            for def_node in definitions:
                chunk = self._create_chunk_from_definition(
                    def_node, file_path, lines, language, imports
                )
                if chunk:
                    chunks.append(chunk)
            
            # 如果没有找到定义，使用回退方案
            if not chunks:
                chunks = self._chunk_fallback(file_path)
                
        except Exception as e:
            logger.warning(f"AST chunking failed for {file_path}: {e}")
            chunks = self._chunk_fallback(file_path)
        
        return chunks
    
    def _extract_imports(self, root_node, language: str) -> List[str]:
        """提取导入语句"""
        imports = []
        
        for child in root_node.children:
            if child.type in ["import_statement", "import_from_statement", "import"]:
                try:
                    imports.append(child.text.decode("utf-8"))
                except:
                    pass
        
        return imports
    
    def _extract_definitions(self, root_node, function_types: List[str], language: str) -> List:
        """提取函数和类定义节点"""
        definitions = []
        
        def traverse(node):
            if node.type in function_types:
                definitions.append(node)
            for child in node.children:
                traverse(child)
        
        traverse(root_node)
        return definitions
    
    def _create_chunk_from_definition(
        self,
        node,
        file_path: Path,
        lines: List[str],
        language: str,
        imports: List[str]
    ) -> Optional[CodeChunk]:
        """从定义节点创建代码块"""
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        
        # 超过最大行数的块需要分割
        if end_line - start_line + 1 > self.max_chunk_lines:
            return None
        
        # 提取代码内容（包含前后context）
        context_start = max(0, start_line - 2)
        context_end = min(len(lines), end_line + 2)
        content_lines = lines[context_start:context_end]
        
        # 提取名称
        name = self._extract_name(node, language)
        
        # 提取签名
        signature = self._extract_signature(node, lines, language)
        
        # 提取docstring
        docstring = self._extract_docstring(node, lines, language)
        
        # 计算复杂度
        complexity = self._calculate_complexity(node)
        
        return CodeChunk(
            id=str(uuid.uuid4()),
            type=self._get_definition_type(node.type),
            name=name,
            file_path=str(file_path),
            start_line=start_line + 1,  # 转为1-based
            end_line=end_line + 1,
            content="\n".join(content_lines),
            docstring=docstring,
            signature=signature,
            imports=imports,
            language=language,
            complexity=complexity
        )
    
    def _extract_name(self, node, language: str) -> str:
        """提取定义名称"""
        if language == "python":
            for child in node.children:
                if child.type == "identifier":
                    return child.text.decode("utf-8")
        return f"unnamed_{node.start_point[0]}"
    
    def _extract_signature(self, node, lines: List[str], language: str) -> Optional[str]:
        """提取函数签名"""
        if node.start_point[0] < len(lines):
            line = lines[node.start_point[0]]
            return line.strip()
        return None
    
    def _extract_docstring(self, node, lines: List[str], language: str) -> Optional[str]:
        """提取文档字符串"""
        if node.start_point[0] + 1 < len(lines):
            next_line = lines[node.start_point[0] + 1].strip()
            if next_line.startswith('"""') or next_line.startswith("'''"):
                return next_line.strip('"\'')
        return None
    
    def _get_definition_type(self, node_type: str) -> str:
        """获取定义类型"""
        type_mapping = {
            "function_definition": "function",
            "async_function_definition": "function",
            "function_declaration": "function",
            "function_expression": "function",
            "arrow_function": "function",
            "method_definition": "method",
            "method_declaration": "method",
            "class_definition": "class",
            "class_declaration": "class",
            "interface_declaration": "interface",
            "struct_item": "struct",
            "impl_item": "impl",
        }
        return type_mapping.get(node_type, "unknown")
    
    def _calculate_complexity(self, node) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        for child in node.children:
            if child.type in ["if_statement", "for_statement", "while_statement",
                            "case_statement", "conditional_expression"]:
                complexity += 1
            if child.type == "binary_expression":
                try:
                    text = child.text.decode("utf-8")
                    if text in ["and", "or"]:
                        complexity += 1
                except:
                    pass
        
        return complexity
    
    def _chunk_fallback(self, file_path: Path) -> List[CodeChunk]:
        """回退方案：按行数分块"""
        chunks = []
        
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")
            
            for i in range(0, len(lines), self.max_chunk_lines - self.overlap_lines):
                chunk_lines = lines[i:i + self.max_chunk_lines]
                
                chunks.append(CodeChunk(
                    id=str(uuid.uuid4()),
                    type="module",
                    name=file_path.stem,
                    file_path=str(file_path),
                    start_line=i + 1,
                    end_line=min(i + self.max_chunk_lines, len(lines)),
                    content="\n".join(chunk_lines),
                    language=self.LANGUAGE_EXTENSIONS.get(file_path.suffix.lower(), "text")
                ))
        except Exception as e:
            logger.error(f"Fallback chunking failed for {file_path}: {e}")
        
        return chunks
    
    def get_chunk_statistics(self, chunks: List[CodeChunk]) -> Dict[str, Any]:
        """获取分片统计信息"""
        type_counts = {}
        total_lines = 0
        total_complexity = 0
        
        for chunk in chunks:
            type_counts[chunk.type] = type_counts.get(chunk.type, 0) + 1
            total_lines += chunk.end_line - chunk.start_line + 1
            total_complexity += chunk.complexity
        
        return {
            "total_chunks": len(chunks),
            "type_distribution": type_counts,
            "total_lines": total_lines,
            "average_chunk_size": total_lines / len(chunks) if chunks else 0,
            "total_complexity": total_complexity,
            "average_complexity": total_complexity / len(chunks) if chunks else 0
        }

