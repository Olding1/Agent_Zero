# Agent Zero 项目结构与模块解析

本文档旨在帮助开发人员快速理解 Agent Zero 项目的架构、目录结构以及核心模块的功能，便于在集成测试和问题排查时快速定位。

## 1. 项目概览

**Agent Zero** 是一个本地化、全自动的智能体构建工厂。它通过 **"Graph as Code"** 的理念，将自然语言需求转化为 LangGraph 拓扑结构，并自动完成代码生成、环境隔离（venv/uv）和自我进化验证。

- **核心理念**: 定义逻辑 -> 生成图谱 -> 自动部署。
- **技术栈**: Python 3.11+, LangGraph, LangChain, Pydantic, Jinja2, uv (构建加速)。

## 2. 目录结构树

```text
Agent_Zero/
├── src/                    # [核心源码]
│   ├── core/              # >> 核心引擎 (工厂、编译器、运行时的逻辑中枢)
│   ├── tools/             # >> 工具系统 (注册表、定义、发现引擎)
│   ├── llm/               # >> LLM 适配层 (Builder/Runtime 双轨制)
│   ├── schemas/           # >> 数据模型 (Pydantic 定义，不仅是类型，更是协议)
│   ├── templates/         # >> 代码模板 (Jinja2 生成 agent.py 等)
│   ├── utils/             # >> 通用工具 (Git, Trace可视化, 下载器等)
│   └── cli/               # >> 命令行入口
├── agents/                # [产物目录] 生成的 Agent 存放于此
├── config/                # [系统配置] 全局配置 (default_prompts 等)
├── tests/                 # [测试套件] 单元测试与 E2E 测试
└── docs/                  # [文档资料] 需求文档、架构图、变更日志
```

## 3. 核心模块详解 (src/core)

这是系统的“大脑”，负责调度和执行核心业务逻辑。

| 模块文件 | 角色 | 功能描述 | 关键方法/类 |
| :--- | :--- | :--- | :--- |
| `agent_factory.py` | **指挥官** | 编排 Agent 生成全生命周期：需求分析 -> 资源准备 -> 蓝图设计 -> 仿真验证 -> 代码构建 -> 测试进化。 | `AgentFactory.create_agent()` |
| `compiler.py` | **建筑师** | 将设计好的 Agent 蓝图 (JSON) 转化为可执行代码 (Python) 和配置文件。 | `Compiler.compile()` |
| `env_manager.py` | **基建处** | 管理生成的 Agent 的 Python 环境。支持 venv，v7.3 起集成 `uv` 实现 10 倍速安装。 | `EnvManager.create_venv()`, `install_dependencies()` |
| `pm.py` | **产品经理** | 分析用户输入的自然语言需求，推断项目元数据 (ProjectMeta)，明确意图。v7.4 引入了智能推断。 | `PM.analyze()` |
| `graph_designer.py` | **架构师** | 将需求转化为 LangGraph 图结构 (Nodes/Edges)。v7.6 实现了启发式 Pattern 选择 (Sequential, Loop, etc.)。 | `GraphDesigner.design_graph()` |
| `simulator.py` | **推演沙盘** | 在生成代码前，对设计的 Graph 进行模拟运行，验证逻辑闭环。 | `Simulator.simulate()` |
| `test_generator.py` | **测试工程师** | 根据需求自动生成 DeepEval 测试用例，用于验证生成的 Agent 是否达标。 | `TestGenerator.generate_tests()` |
| `runner.py` | **执行官** | 负责运行生成的 Agent。它在独立的进程/环境中加载生成的代码并执行。 | `Runner.run_agent()` |
| `judge.py` | **裁判员** | 分析测试结果，判定通过与否，并给出修复建议 (Fix Target)。 | `Judge.analyze_result()` |
| `interface_guard.py` | **卫士** (v8.0) | **[新]** 运行时参数防御系统，拦截错误的工具调用并触发 LLM 自修。 | `InterfaceGuard.validate()` |
| `tool_discovery.py` | **探索引擎** (v8.0) | **[新]** 基于向量检索的本地工具发现系统，替代外部 API 搜索。 | `ToolDiscoveryEngine` |

## 4. 工具系统 (src/tools)

| 模块文件 | 功能描述 |
| :--- | :--- |
| `registry.py` | 工具注册中心。定义了 `ToolMetadata` Schema。 |
| `definitions.py` | **硬编码的精选工具列表**。定义了工具的导入路径和参数 Schema。 |
| `index_builder.py` | (v8.0) 用于构建本地工具索引 (`tools_index.json`) 的脚本。 |

## 5. 关键工作流

### 5.1 Agent 生成流程 (Creation Workflow)
入口: `start.py` -> `AgentFactory.create_agent()`

1.  **PM Analysis**: 用户输入 "帮我写个爬虫" -> `PM` 输出结构化需求。
2.  **Resource**: `ToolSelector` 挑选工具, `RAGBuilder` 准备知识库。
3.  **Design**: `GraphDesigner` 生成图结构 -> `Simulator` 模拟运行验证。
4.  **Build**: `Compiler` 将通过模拟的图渲染为 `agent.py` 和 `requirements.txt`。
5.  **Evolve**:
    - `TestGenerator` 生成测试。
    - `EnvManager` 安装环境 (uv)。
    - `Runner` 运行测试。
    - `Judge` 判卷。如果不通过 -> 触发自动修复 (Refinement Loop)。

### 5.2 Agent 运行流程 (Runtime Workflow)
入口: `run_agent.py` (在生成的 Agent 目录中运行)

1.  加载 `.env` 配置。
2.  实例化生成的 Agent 类 (在 `agent.py` 中)。
3.  执行 `agent.invoke(inputs)`。
4.  (v8.0+) 调用工具前经过 `InterfaceGuard` 校验。

## 6. 版本变更重点 (v7.6 -> v8.0)

在排查问题时，请注意以下近期变更：

-   **构建速度**: 如果依赖安装极快，是因为使用了 `uv` (集成在 `EnvManager`)。
-   **工具发现**: v8.0 移除了不稳定的在线搜索，转为 **本地精选库 (LangChain Community)** + **向量检索**。
-   **参数校验**: 新增 `InterfaceGuard`，如果在日志中看到 "Parameter validation failed" 且自动重试，这是预期行为。

---
*该文档用于辅助快速理解项目架构，具体实现细节请查阅源码。*
