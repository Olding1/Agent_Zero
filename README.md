# Agent Zero v6.0

**Slogan:** Define logic, generate graph, auto-deploy.

## 🎯 项目简介

Agent Zero 是一款桌面端、本地化、全自动的智能体构建工厂。通过元编程将自然语言转化为 LangGraph 拓扑,并在本地隔离环境中完成代码生成、依赖安装、测试闭环与自我修复。

### 核心特性

- **Graph as Code**: JSON 中间层解耦业务逻辑与代码实现
- **无 Docker 化**: 使用 Python venv 实现轻量级环境隔离
- **API 双轨制**: 区分构建用模型和运行用模型
- **主动进化**: 利用 LangChain MCP 协议实现依赖库主动重构

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Git

### 安装

```bash
# 克隆仓库
git clone <repository-url>
cd Agent_Zero

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.template .env
# 编辑 .env 文件,填入你的 API 密钥
```

### 运行测试

```bash
# 运行阶段一端到端测试
python tests/e2e/test_phase1_hello_world.py
```

## 📁 项目结构

```
Agent_Zero/
├── src/                    # 源代码
│   ├── core/              # 核心引擎
│   ├── schemas/           # Pydantic 数据模型
│   ├── templates/         # Jinja2 代码模板
│   ├── llm/               # LLM 客户端
│   └── utils/             # 工具函数
├── agents/                # 生成的 Agent 项目
├── config/                # 系统配置
├── tests/                 # 测试代码
└── docs/                  # 文档
```

## 📖 开发路线图

- [x] **阶段一 (Week 1-2)**: 内核 MVP
  - [x] JSON Schema 体系
  - [x] Compiler 编译器
  - [x] Env Manager 环境管家
  - [ ] API 双轨配置
  - [ ] Hello World Agent 联调

- [ ] **阶段二 (Week 3-4)**: 数据流与工具
- [ ] **阶段三 (Week 5-7)**: 闭环与进化
- [ ] **阶段四 (Week 8-9)**: 产品化

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!
