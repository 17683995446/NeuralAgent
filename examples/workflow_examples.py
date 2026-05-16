"""
NeuralAgent - Workflow Examples
工作流引擎使用示例
"""

def example_basic_workflow():
    """示例1：基本工作流"""
    from backend.core.workflow.enhanced_workflow import (
        EnhancedWorkflowEngine,
        RetryPolicy,
        RetryStrategy
    )
    
    print("=" * 60)
    print("示例1：基本工作流")
    print("=" * 60)
    
    engine = EnhancedWorkflowEngine()
    
    async def fetch_data(results, context):
        print("  → 步骤1：获取数据")
        return {"data": [1, 2, 3]}
    
    async def process_data(results, context):
        print("  → 步骤2：处理数据")
        data = results["fetch"]["data"]
        return {"processed": [x * 2 for x in data]}
    
    async def save_results(results, context):
        print("  → 步骤3：保存结果")
        print(f"  → 结果：{results['process']['processed']}")
        return {"saved": True}
    
    engine.add_step("fetch", fetch_data)
    engine.add_step("process", process_data, depends_on=["fetch"])
    engine.add_step("save", save_results, depends_on=["process"])
    
    print("\n✓ 工作流定义完成")
    print("\n提示：运行 execute() 来执行工作流")
    print("=" * 60)
    
    return engine


def example_retry_policy():
    """示例2：重试策略"""
    from backend.core.workflow.enhanced_workflow import (
        EnhancedWorkflowEngine,
        RetryPolicy,
        RetryStrategy
    )
    
    print("\n" + "=" * 60)
    print("示例2：重试策略")
    print("=" * 60)
    
    engine = EnhancedWorkflowEngine()
    
    # 固定延迟重试
    fixed_retry = RetryPolicy(
        max_attempts=3,
        strategy=RetryStrategy.FIXED_DELAY,
        initial_delay=1.0,
        jitter=False
    )
    
    # 指数退避重试
    exp_retry = RetryPolicy(
        max_attempts=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        initial_delay=0.5,
        max_delay=10.0,
        backoff_factor=2.0,
        jitter=True
    )
    
    async def unstable_api(results, context):
        print("  → 调用不稳定的API...")
        return {"success": True}
    
    engine.add_step("unstable", unstable_api, retry_policy=exp_retry)
    
    print("\n✓ 重试策略配置完成")
    print(f"  - 最大尝试次数：{exp_retry.max_attempts}")
    print(f"  - 策略：{exp_retry.strategy}")
    print(f"  - 初始延迟：{exp_retry.initial_delay}s")
    print("=" * 60)
    
    return engine


def example_workflow_events():
    """示例3：工作流事件监听"""
    from backend.core.workflow.enhanced_workflow import (
        EnhancedWorkflowEngine,
        WorkflowEventListener,
        WorkflowEvent
    )
    
    print("\n" + "=" * 60)
    print("示例3：工作流事件")
    print("=" * 60)
    
    class SimpleListener(WorkflowEventListener):
        async def on_event(self, event: WorkflowEvent):
            print(f"  📢 事件：{event.event_type}")
    
    engine = EnhancedWorkflowEngine()
    engine.add_listener(SimpleListener())
    
    print("\n✓ 事件监听器已添加")
    print("  - 支持的事件类型：")
    print("    * WorkflowStartedEvent")
    print("    * WorkflowCompletedEvent")
    print("    * WorkflowFailedEvent")
    print("    * StepStartedEvent")
    print("    * StepCompletedEvent")
    print("    * StepFailedEvent")
    print("    * StepRetryingEvent")
    print("=" * 60)
    
    return engine


def example_plugin_system():
    """示例4：插件系统"""
    from backend.core.plugins import (
        PluginManager,
        SimpleLoggingPlugin,
        HookType
    )
    
    print("\n" + "=" * 60)
    print("示例4：插件系统")
    print("=" * 60)
    
    manager = PluginManager()
    
    plugin = SimpleLoggingPlugin()
    
    print(f"\n✓ 插件信息：")
    print(f"  - 名称：{plugin.info.name}")
    print(f"  - 版本：{plugin.info.version}")
    print(f"  - 描述：{plugin.info.description}")
    print(f"  - 作者：{plugin.info.author}")
    
    print("\n✓ 支持的钩子类型：")
    for hook in HookType:
        print(f"  - {hook.value}")
    
    print("=" * 60)
    
    return manager


def example_http_client():
    """示例5：HTTP客户端"""
    from backend.core.http_client import (
        HTTPClientConfig,
        HTTPMethod
    )
    
    print("\n" + "=" * 60)
    print("示例5：HTTP客户端")
    print("=" * 60)
    
    config = HTTPClientConfig(
        timeout=30.0,
        max_connections=100,
        retries=3,
        retry_delay=1.0,
        follow_redirects=True
    )
    
    print(f"\n✓ HTTP客户端配置：")
    print(f"  - 超时：{config.timeout}s")
    print(f"  - 最大连接：{config.max_connections}")
    print(f"  - 重试次数：{config.retries}")
    print(f"  - 重试状态码：{config.retry_status_codes}")
    
    print(f"\n✓ HTTP方法：")
    for method in HTTPMethod:
        print(f"  - {method.name}")
    
    print("\n提示：使用 HTTPClient 进行请求")
    print("=" * 60)
    
    return config


def example_data_validation():
    """示例6：数据验证"""
    from backend.core.models import (
        validate_email,
        validate_length,
        validate_range,
        validate_required
    )
    
    print("\n" + "=" * 60)
    print("示例6：数据验证")
    print("=" * 60)
    
    test_cases = [
        ("test@example.com", True),
        ("invalid-email", False),
        ("hello", True),
        ("", False),
    ]
    
    print("\n✓ 邮箱验证：")
    for email, expected in test_cases[:2]:
        result = validate_email(email)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {email}")
    
    print("\n✓ 长度验证：")
    try:
        validate_length("hello", 1, 10)
        print("  ✓ 'hello' (1-10 chars)")
    except:
        pass
    
    print("\n✓ 范围验证：")
    try:
        validate_range(5, 1, 10)
        print("  ✓ 5 范围 (1-10)")
    except:
        pass
    
    print("=" * 60)


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "NeuralAgent 工作流示例" + " " * 24 + "║")
    print("╚" + "=" * 58 + "╝")
    
    example_basic_workflow()
    example_retry_policy()
    example_workflow_events()
    example_plugin_system()
    example_http_client()
    example_data_validation()
    
    print("\n" + "=" * 60)
    print("✓ 所有示例演示完成！")
    print("=" * 60)
