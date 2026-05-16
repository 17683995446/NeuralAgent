"""
NeuralAgent 主应用入口
支持多种启动模式
"""

import asyncio
import logging
import sys
import argparse
from typing import Optional
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入配置
from app_config import get_config, NeuralAgentConfig


class NeuralAgentApplication:
    """NeuralAgent 主应用"""
    
    def __init__(self, config: Optional[NeuralAgentConfig] = None):
        self.config = config or get_config()
        self._running = False
        
        # 初始化子系统
        self._init_subsystems()
    
    def _init_subsystems(self):
        """初始化所有子系统"""
        logger.info("正在初始化 NeuralAgent 系统...")
        
        # 1. 配置验证
        self.config.validate()
        
        # 2. 日志配置
        self._setup_logging()
        
        # 3. 初始化模块（按需）
        self._init_memory()
        self._init_cache()
        self._init_llm()
        self._init_monitoring()
        self._init_workflows()
        
        logger.info("NeuralAgent 系统初始化完成")
    
    def _setup_logging(self):
        """配置日志"""
        log_level = getattr(logging, self.config.log_level)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger.info(f"日志级别设置为: {self.config.log_level}")
    
    def _init_memory(self):
        """初始化记忆系统"""
        logger.info("初始化记忆系统...")
        
        try:
            from backend.core.memory.enhanced_memory_v2 import get_enhanced_memory_system
            self.enhanced_memory = get_enhanced_memory_system()
        except Exception as e:
            logger.warning(f"增强记忆系统初始化失败: {e}")
            try:
                from backend.core.memory.unified_memory import get_memory_system
                self.memory = get_memory_system()
            except Exception as e2:
                logger.error(f"统一记忆系统初始化失败: {e2}")
                self.memory = None
        
        logger.info("记忆系统初始化完成")
    
    def _init_cache(self):
        """初始化缓存系统"""
        if not self.config.cache.enabled:
            logger.info("缓存系统已禁用")
            self.cache = None
            return
        
        logger.info("初始化缓存系统...")
        
        try:
            from backend.core.cache.multi_level_cache import get_cache
            self.cache = get_cache()
        except Exception as e:
            logger.error(f"缓存系统初始化失败: {e}")
            self.cache = None
        
        logger.info("缓存系统初始化完成")
    
    def _init_llm(self):
        """初始化 LLM 适配器"""
        logger.info(f"初始化 LLM 适配器 (Provider: {self.config.llm.provider})...")
        
        try:
            from backend.core.llm_adapter import create_llm_adapter, LLMProvider
            self.llm_adapter = create_llm_adapter(
                provider=LLMProvider(self.config.llm.provider),
                model=self.config.llm.model,
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url,
            )
        except Exception as e:
            logger.error(f"LLM 适配器初始化失败: {e}")
            self.llm_adapter = None
        
        logger.info("LLM 适配器初始化完成")
    
    def _init_monitoring(self):
        """初始化监控系统"""
        if not self.config.monitoring.enabled:
            logger.info("监控系统已禁用")
            self.monitoring = None
            return
        
        logger.info("初始化监控系统...")
        
        try:
            from backend.core.monitoring.prometheus_metrics import get_monitoring_server
            self.monitoring = get_monitoring_server(port=self.config.monitoring.prometheus_port)
        except Exception as e:
            logger.error(f"监控系统初始化失败: {e}")
            self.monitoring = None
        
        logger.info("监控系统初始化完成")
    
    def _init_workflows(self):
        """初始化工作流引擎"""
        if not self.config.workflow.enabled:
            logger.info("工作流系统已禁用")
            self.workflow_engine = None
            return
        
        logger.info("初始化工作流引擎...")
        
        try:
            from backend.core.workflow_engine import get_workflow_engine
            self.workflow_engine = get_workflow_engine()
        except Exception as e:
            logger.error(f"工作流引擎初始化失败: {e}")
            self.workflow_engine = None
        
        logger.info("工作流引擎初始化完成")
    
    async def start(self):
        """启动应用"""
        self._running = True
        logger.info("正在启动 NeuralAgent...")
        
        # 启动监控服务器
        if self.monitoring:
            await self.monitoring.start()
            logger.info(f"Prometheus 监控已启动: http://localhost:{self.config.monitoring.prometheus_port}")
        
        logger.info("NeuralAgent 已启动")
    
    async def stop(self):
        """停止应用"""
        if not self._running:
            return
        
        logger.info("正在停止 NeuralAgent...")
        
        if self.monitoring:
            self.monitoring.stop()
        
        self._running = False
        logger.info("NeuralAgent 已停止")
    
    async def run_api_server(self):
        """运行 API 服务器"""
        if not self._running:
            await self.start()
        
        logger.info("正在启动 API 服务器...")
        
        try:
            from backend.api.api_module import NeuralAgentAPI
            api = NeuralAgentAPI()
            api.setup_websocket()
            await api.run_async(self.config.api.host, self.config.api.port)
        except Exception as e:
            logger.error(f"API 服务器启动失败: {e}")
            raise
    
    async def run_demo(self):
        """运行演示模式"""
        if not self._running:
            await self.start()
        
        logger.info("正在运行演示...")
        
        # 简单的演示流程
        print("\n" + "="*60)
        print("🚀 NeuralAgent 演示")
        print("="*60)
        
        if self.llm_adapter:
            print("\n📊 LLM 测试:")
            response = await self.llm_adapter.generate("Hello, NeuralAgent!")
            print(f"响应: {response}")
        
        if self.cache:
            print("\n🔧 缓存测试:")
            await self.cache.set("demo:key", "Hello, Cache!")
            value = await self.cache.get("demo:key")
            print(f"缓存值: {value}")
        
        print("\n" + "="*60)
        print("✅ 演示完成")
        print("="*60)
    
    async def run_interactive(self):
        """运行交互式模式"""
        if not self._running:
            await self.start()
        
        print("\n" + "="*60)
        print("🤖 NeuralAgent 交互式终端")
        print("="*60)
        print("输入 'quit' 或 'exit' 退出\n")
        
        while True:
            try:
                user_input = input(">>> ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    print("👋 再见!")
                    break
                
                if not user_input:
                    continue
                
                # 简单的响应逻辑
                response = self._handle_input(user_input)
                print(f"🤖: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
    
    def _handle_input(self, user_input: str) -> str:
        """处理用户输入（简单实现）"""
        if self.llm_adapter:
            try:
                return asyncio.create_task(self.llm_adapter.generate(user_input)).result(timeout=5)
            except Exception:
                pass
        
        # 简单的回退逻辑
        user_input_lower = user_input.lower()
        
        if "hello" in user_input_lower or "你好" in user_input_lower:
            return "你好！我是 NeuralAgent，很高兴为你服务！"
        elif "help" in user_input_lower or "帮助" in user_input_lower:
            return "我可以帮助你处理各种任务！试试问我任何问题。"
        elif "bye" in user_input_lower or "再见" in user_input_lower:
            return "再见！期待再次为你服务。"
        
        return f"我收到了你的问题: '{user_input}'。让我想想如何回答..."


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="NeuralAgent - 智能代理系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                     # 启动完整应用（API + 监控）
  python main.py --mode api         # 仅启动 API 服务器
  python main.py --mode demo        # 运行演示
  python main.py --mode interactive # 交互式模式
  python main.py --config custom.yaml # 使用自定义配置
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default='api',
        choices=['full', 'api', 'demo', 'interactive'],
        help='运行模式: full（完整）, api（仅API）, demo（演示）, interactive（交互式）'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default=None,
        help='API 服务器监听地址'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='API 服务器监听端口'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    return parser.parse_args()


def load_config(args):
    """加载配置"""
    if args.config:
        config_file = Path(args.config)
        if not config_file.exists():
            print(f"❌ 配置文件不存在: {args.config}")
            sys.exit(1)
        
        if config_file.suffix in ['.yaml', '.yml']:
            from config import NeuralAgentConfig
            config = NeuralAgentConfig.from_yaml(config_file)
        elif config_file.suffix == '.json':
            from config import NeuralAgentConfig
            config = NeuralAgentConfig.from_json(config_file)
        else:
            print(f"❌ 不支持的配置文件格式: {config_file.suffix}")
            sys.exit(1)
    else:
        from config import get_config
        config = get_config()
    
    # 命令行参数覆盖
    if args.host:
        config.api.host = args.host
    if args.port:
        config.api.port = args.port
    if args.debug:
        config.debug = True
        config.log_level = "DEBUG"
    
    return config


async def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    NEURALAGENT                               ║
║                    智能代理系统                               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    args = parse_args()
    config = load_config(args)
    
    # 创建应用
    app = NeuralAgentApplication(config)
    
    try:
        if args.mode == 'full':
            print(f"🚀 启动完整模式: API + 监控")
            await app.run_api_server()
        elif args.mode == 'api':
            print(f"🚀 启动 API 服务器")
            await app.run_api_server()
        elif args.mode == 'demo':
            print(f"🎯 运行演示模式")
            await app.run_demo()
        elif args.mode == 'interactive':
            print(f"💬 启动交互式模式")
            await app.run_interactive()
    except KeyboardInterrupt:
        print("\n\n👋 正在停止...")
        await app.stop()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        await app.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
