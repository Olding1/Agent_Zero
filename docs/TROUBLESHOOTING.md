# Agent Zero v6.0 - 快速修复指南

## 问题：ModuleNotFoundError: No module named 'langchain_anthropic'

### 原因
系统缺少某些 LangChain 提供商的依赖包。

### 解决方案

#### 方式一：安装所有依赖（推荐）

```bash
pip install langchain-openai langchain-anthropic -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 方式二：只安装需要的提供商

**如果只使用 OpenAI：**
```bash
pip install langchain-openai -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**如果只使用 Anthropic：**
```bash
pip install langchain-anthropic -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**如果使用本地 Ollama：**
不需要额外安装，系统已支持。

### 已修复的问题

1. ✅ 将提供商导入改为可选导入
2. ✅ 添加了友好的错误提示
3. ✅ 系统现在可以在缺少某些提供商库的情况下启动

### 验证修复

运行以下命令验证系统正常：

```bash
python start.py
```

应该看到：
```
======================================================================
🚀 Agent Zero v6.0 - Intelligent Agent Construction Factory
======================================================================

⚠️  No .env file found!

Please create a .env file from the template:
   cp .env.template .env
```

这表示系统已正常启动！

### 下一步

1. 创建 `.env` 文件：
   ```bash
   cp .env.template .env
   ```

2. 编辑 `.env` 文件，添加你的 API 密钥

3. 再次运行：
   ```bash
   python start.py
   ```

## 其他常见问题

### Q: 如何使用本地 Ollama？

A: 在 `.env` 中配置：
```env
RUNTIME_PROVIDER=ollama
RUNTIME_MODEL=llama2
RUNTIME_BASE_URL=http://localhost:11434
# RUNTIME_API_KEY 不需要
```

### Q: 如何切换不同的 LLM 提供商？

A: 编辑 `.env` 文件中的 `BUILDER_PROVIDER` 和 `RUNTIME_PROVIDER`：
- `openai` - OpenAI API
- `anthropic` - Anthropic Claude
- `ollama` - 本地 Ollama

### Q: 依赖安装失败？

A: 尝试使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
