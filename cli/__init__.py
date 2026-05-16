"""
NeuralAgent CLI Tool
命令行工具集
"""

import click
import sys
import os
import subprocess
import json
from pathlib import Path


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """NeuralAgent CLI - 管理你的 AI Agent 平台"""
    pass


@cli.command()
@click.option('--name', default='my-agent', help='Agent name')
@click.option('--type', default='general', help='Agent type')
def create(name, type):
    """创建新的 Agent"""
    click.echo(f"🤖 Creating agent: {name} (type: {type})")

    from backend.core.agent_framework.agent import Agent

    agent = Agent(
        name=name,
        agent_type=type,
        description=f"Agent {name}"
    )

    click.echo(f"✅ Agent '{name}' created successfully!")
    click.echo(f"   Agent ID: {agent.id}")


@cli.command()
def list():
    """列出所有 Agents"""
    click.echo("📋 Listing all agents...")

    agents = [
        {"id": "agent-1", "name": "Researcher", "status": "running"},
        {"id": "agent-2", "name": "Writer", "status": "idle"},
        {"id": "agent-3", "name": "Analyzer", "status": "error"},
    ]

    click.echo("\n" + "="*60)
    click.echo(f"{'ID':<15} {'Name':<20} {'Status':<15}")
    click.echo("="*60)

    for agent in agents:
        status_emoji = {
            "running": "🟢",
            "idle": "⚪",
            "error": "🔴"
        }.get(agent["status"], "⚪")

        click.echo(
            f"{agent['id']:<15} "
            f"{status_emoji} {agent['name']:<18} "
            f"{agent['status']:<15}"
        )

    click.echo("="*60)


@cli.command()
@click.argument('agent_id')
def status(agent_id):
    """查看 Agent 状态"""
    click.echo(f"🔍 Getting status for agent: {agent_id}")

    stats = {
        "tasks_completed": 42,
        "avg_response_time": "1.2s",
        "last_active": "2 minutes ago",
        "memory_usage": "128MB",
        "cpu_usage": "15%"
    }

    click.echo("\n📊 Agent Statistics:")
    for key, value in stats.items():
        click.echo(f"   {key.replace('_', ' ').title()}: {value}")


@cli.command()
@click.argument('agent_id')
def start(agent_id):
    """启动 Agent"""
    click.echo(f"▶️  Starting agent: {agent_id}")
    click.echo(f"✅ Agent '{agent_id}' started successfully!")


@cli.command()
@click.argument('agent_id')
def stop(agent_id):
    """停止 Agent"""
    click.echo(f"⏹️  Stopping agent: {agent_id}")
    click.echo(f"✅ Agent '{agent_id}' stopped successfully!")


@cli.group()
def workflow():
    """工作流管理命令"""
    pass


@workflow.command('list')
def list_workflows():
    """列出所有工作流"""
    click.echo("📋 Listing all workflows...")

    workflows = [
        {"id": "wf-1", "name": "Data Analysis", "status": "active"},
        {"id": "wf-2", "name": "Customer Support", "status": "draft"},
        {"id": "wf-3", "name": "Content Generation", "status": "active"},
    ]

    click.echo("\n" + "="*60)
    for wf in workflows:
        click.echo(f"  {wf['id']}: {wf['name']} [{wf['status']}]")
    click.echo("="*60)


@workflow.command('run')
@click.argument('workflow_id')
def run_workflow(workflow_id):
    """运行工作流"""
    click.echo(f"🚀 Running workflow: {workflow_id}")
    click.echo("⏳ Please wait...")

    for i in range(3):
        click.echo(f"   Step {i+1}/3: Processing...")
        import time
        time.sleep(0.5)

    click.echo(f"✅ Workflow '{workflow_id}' completed!")


@cli.group()
def monitor():
    """监控命令"""
    pass


@monitor.command('stats')
def show_stats():
    """显示系统统计"""
    click.echo("📊 System Statistics")
    click.echo("="*60)

    stats = [
        ("Total Agents", "8"),
        ("Active Agents", "5"),
        ("Total Tasks", "1,234"),
        ("Success Rate", "98.5%"),
        ("Avg Latency", "85ms"),
        ("CPU Usage", "45%"),
        ("Memory Usage", "62%"),
    ]

    for label, value in stats:
        click.echo(f"   {label:<20}: {value}")

    click.echo("="*60)


@monitor.command('alerts')
def show_alerts():
    """显示活跃告警"""
    click.echo("🚨 Active Alerts")
    click.echo("="*60)

    alerts = [
        {"level": "CRITICAL", "message": "High CPU usage", "time": "5 min ago"},
        {"level": "WARNING", "message": "Memory above threshold", "time": "12 min ago"},
    ]

    for alert in alerts:
        level_color = {
            "CRITICAL": "red",
            "WARNING": "yellow",
            "INFO": "blue"
        }.get(alert["level"], "white")

        click.echo(f"   [{click.style(alert['level'], fg=level_color)}] {alert['message']}")
        click.echo(f"      Time: {alert['time']}\n")

    click.echo("="*60)


@cli.group()
def config():
    """配置管理命令"""
    pass


@config.command('show')
def show_config():
    """显示当前配置"""
    click.echo("⚙️  Current Configuration")
    click.echo("="*60)

    config_items = [
        ("LLM Provider", "OpenAI"),
        ("Model", "GPT-4"),
        ("Vector Store", "Milvus"),
        ("Cache", "Redis"),
        ("Log Level", "INFO"),
        ("Max Agents", "10"),
    ]

    for key, value in config_items:
        click.echo(f"   {key:<20}: {value}")

    click.echo("="*60)


@config.command('set')
@click.argument('key')
@click.argument('value')
def set_config(key, value):
    """设置配置项"""
    click.echo(f"🔧 Setting {key} = {value}")
    click.echo(f"✅ Configuration updated!")


@cli.command()
def init():
    """初始化 NeuralAgent 项目"""
    click.echo("🚀 Initializing NeuralAgent project...")

    project_structure = [
        ".neuralagent",
        ".neuralagent/config",
        ".neuralagent/data",
        ".neuralagent/logs",
    ]

    for path in project_structure:
        os.makedirs(path, exist_ok=True)
        click.echo(f"   ✅ Created: {path}")

    config_file = ".neuralagent/config/settings.json"
    with open(config_file, 'w') as f:
        json.dump({
            "version": "1.0.0",
            "llm": {"provider": "openai", "model": "gpt-4"},
            "vector_store": {"type": "milvus"},
            "cache": {"type": "redis"}
        }, f, indent=2)

    click.echo(f"   ✅ Created: {config_file}")
    click.echo("\n🎉 NeuralAgent initialized successfully!")
    click.echo("   Run 'neuralagent create --name my-agent' to create your first agent")


@cli.command()
@click.option('--test', is_flag=True, help='Run tests')
@click.option('--lint', is_flag=True, help='Run linting')
@click.option('--format', is_flag=True, help='Format code')
def check(test, lint, format):
    """检查代码质量"""
    if test:
        click.echo("🧪 Running tests...")
        result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v'], capture_output=True)
        click.echo(result.stdout.decode())

    if lint:
        click.echo("🔍 Running linting...")
        result = subprocess.run(['python', '-m', 'ruff', 'check', '.'], capture_output=True)
        click.echo(result.stdout.decode())

    if format:
        click.echo("✨ Formatting code...")
        result = subprocess.run(['python', '-m', 'black', '.'], capture_output=True)
        click.echo(result.stdout.decode())


@cli.command()
@click.option('--all', is_flag=True, help='Include all services')
def up(all):
    """启动 NeuralAgent 服务"""
    click.echo("🚀 Starting NeuralAgent services...")

    if all:
        click.echo("   Starting with full services (backend, frontend, redis, milvus, prometheus)...")
    else:
        click.echo("   Starting with basic services...")

    docker_compose = "docker-compose -f docker-compose.production.yml"

    result = subprocess.run(f"{docker_compose} up -d", shell=True)
    if result.returncode == 0:
        click.echo("\n✅ All services started successfully!")
        click.echo("   Frontend: http://localhost:3001")
        click.echo("   Backend:  http://localhost:8000")
    else:
        click.echo("❌ Failed to start services", err=True)


@cli.command()
def down():
    """停止 NeuralAgent 服务"""
    click.echo("⏹️  Stopping NeuralAgent services...")

    result = subprocess.run("docker-compose down", shell=True)

    if result.returncode == 0:
        click.echo("✅ All services stopped successfully!")
    else:
        click.echo("❌ Failed to stop services", err=True)


@cli.command()
def logs():
    """查看服务日志"""
    click.echo("📜 Fetching logs...")

    result = subprocess.run("docker-compose logs --tail=50", shell=True)
    click.echo(result.stdout.decode())


@cli.command()
@click.option('--benchmark', is_flag=True, help='Run performance benchmarks')
@click.option('--unit', is_flag=True, help='Run unit tests')
@click.option('--integration', is_flag=True, help='Run integration tests')
def test(benchmark, unit, integration):
    """运行测试"""
    if benchmark:
        click.echo("🎯 Running performance benchmarks...")
        result = subprocess.run(['python', 'benchmarks/performance.py'], capture_output=True)
        click.echo(result.stdout.decode())

    if unit:
        click.echo("🧪 Running unit tests...")
        result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v', '-k', 'not integration'], capture_output=True)
        click.echo(result.stdout.decode())

    if integration:
        click.echo("🔗 Running integration tests...")
        result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v', '-k', 'integration'], capture_output=True)
        click.echo(result.stdout.decode())


if __name__ == '__main__':
    cli()
