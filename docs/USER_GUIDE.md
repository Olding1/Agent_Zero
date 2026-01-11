# Agent Zero v6.0 - 使用指南

## 🚀 快速开始

### 1. 系统要求

- Python 3.11+
- Git
- 网络连接（用于安装依赖和调用 API）

### 2. 安装步骤

```bash
# 1. 克隆项目
cd c:\Users\Administrator\Desktop\game\Agent_Zero

# 2. 安装依赖（可选，如果要开发 Agent Zero 本身）
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.template .env
```

### 3. 配置 API 密钥

编辑 `.env` 文件，填入你的 API 配置：

```env
# Builder API（用于构建 Agent）
BUILDER_PROVIDER=openai
BUILDER_MODEL=gpt-4o
BUILDER_API_KEY=your-api-key-here
BUILDER_BASE_URL=https://api.openai.com/v1

# Runtime API（用于运行 Agent）
RUNTIME_PROVIDER=openai
RUNTIME_MODEL=gpt-3.5-turbo
RUNTIME_API_KEY=your-api-key-here
RUNTIME_BASE_URL=https://api.openai.com/v1
```

**支持的提供商：**
- `openai` - OpenAI API
- `anthropic` - Anthropic Claude
- `ollama` - 本地 Ollama（无需 API Key）

---

## 📖 使用方法

### 方式一：交互式启动（推荐）

```bash
python start.py
```

这将：
1. 检查系统健康状态
2. 验证 API 连接
3. 显示交互式菜单

**菜单选项：**
- 🏗️ 创建新 Agent（即将推出）
- 📦 列出已生成的 Agent
- 🔧 配置 API 设置
- 🧪 运行测试
- 📖 查看文档
- 🚪 退出

### 方式二：生成并运行 Agent

```bash
# 1. 生成测试 Agent
python tests/e2e/test_phase1_hello_world.py

# 2. 运行生成的 Agent
python run_agent.py
```

运行器会：
- 列出所有可用的 Agent
- 自动创建 `.env` 文件（如果不存在）
- 验证虚拟环境
- 启动 Agent

---

## 🎯 使用场景

### 场景 1：创建简单聊天机器人

```python
# 使用 E2E 测试脚本生成
python tests/e2e/test_phase1_hello_world.py
```

生成的 Agent 位于 `agents/hello_world_test/`，包含：
- `agent.py` - 主程序
- `prompts.yaml` - 提示词配置
- `.venv/` - 虚拟环境
- `.env` - 环境配置

### 场景 2：自定义 Agent

1. **定义项目元信息**：
```python
from src.schemas import ProjectMeta, TaskType

project_meta = ProjectMeta(
    agent_name="MyCustomBot",
    description="我的自定义助手",
    has_rag=False,
    task_type=TaskType.CHAT,
    language="zh-CN",
    user_intent_summary="创建一个友好的聊天助手",
)
```

2. **定义图结构**：
```python
from src.schemas import GraphStructure, NodeDef

graph = GraphStructure(
    nodes=[
        NodeDef(id="agent", type="llm"),
    ],
    edges=[],
    entry_point="agent",
)
```

3. **编译生成**：
```python
from src.core.compiler import Compiler
from pathlib import Path

compiler = Compiler(template_dir=Path("src/templates"))
result = compiler.compile(
    project_meta=project_meta,
    graph=graph,
    rag_config=None,
    tools_config=ToolsConfig(enabled_tools=[]),
    output_dir=Path("agents/my_custom_bot"),
)
```

---

## 🔧 配置说明

### Builder API vs Runtime API

| 配置 | 用途 | 推荐模型 |
|------|------|---------|
| **Builder API** | 构建 Agent 时使用，需要强大的推理能力 | GPT-4o, Claude 3.5 Sonnet |
| **Runtime API** | 运行 Agent 时使用，可以使用更经济的模型 | GPT-3.5-turbo, Ollama |

### 使用 Ollama（本地模型）

1. **安装 Ollama**：
```bash
# 访问 https://ollama.ai 下载安装
```

2. **启动 Ollama**：
```bash
ollama serve
```

3. **配置 Runtime API**：
```env
RUNTIME_PROVIDER=ollama
RUNTIME_MODEL=llama2
RUNTIME_BASE_URL=http://localhost:11434
# RUNTIME_API_KEY 不需要
```

---

## 🧪 测试

### 运行所有测试

```bash
# E2E 测试
python tests/e2e/test_phase1_hello_world.py

# 健康检查测试（需要安装依赖）
python tests/integration/test_health_check.py
```

### 验证系统状态

```bash
python start.py
```

系统会自动检查：
- ✅ Builder API 连通性
- ✅ Runtime API 连通性
- ✅ 响应时间
- ✅ 配置完整性

---

## 📁 生成的 Agent 结构

```
agents/my_agent/
├── .venv/              # 虚拟环境
├── .env                # 环境配置
├── agent.py            # 主程序
├── prompts.yaml        # 提示词
├── requirements.txt    # 依赖
├── graph.json          # 图结构
└── state.db            # 状态存储（运行时生成）
```

### 运行生成的 Agent

**方式一：使用运行器**
```bash
python run_agent.py
```

**方式二：直接运行**
```bash
# Windows
agents\my_agent\.venv\Scripts\activate
python agents\my_agent\agent.py

# Linux/Mac
source agents/my_agent/.venv/bin/activate
python agents/my_agent/agent.py
```

---

## ❓ 常见问题

### Q: 健康检查失败怎么办？

**A:** 检查以下几点：
1. API Key 是否正确配置
2. 网络连接是否正常
3. API 服务是否可用
4. Ollama 是否正在运行（如果使用本地模型）

### Q: 依赖安装失败？

**A:** 尝试：
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 生成的 Agent 运行报错？

**A:** 确保：
1. 已配置 `.env` 文件
2. 虚拟环境已创建
3. API Key 有效
4. 网络连接正常

### Q: 如何修改生成的 Agent？

**A:** 可以直接编辑：
- `prompts.yaml` - 修改提示词
- `.env` - 修改 API 配置
- `agent.py` - 修改代码逻辑（高级）

---

## 📚 更多资源

- [项目计划书](file:///c:/Users/Administrator/Desktop/game/Agent_Zero/Agent%20Zero项目计划书.md)
- [详细实施计划](file:///c:/Users/Administrator/Desktop/game/Agent_Zero/Agent_Zero_详细实施计划.md)
- [开发文档](file:///C:/Users/Administrator/.gemini/antigravity/brain/9198a334-3370-4138-be3f-dd3b09e1d28b/walkthrough.md)

---

## 🤝 获取帮助

如有问题，请：
1. 查看文档
2. 运行健康检查：`python start.py`
3. 查看日志输出
4. 提交 Issue

---

**祝使用愉快！🎉**
