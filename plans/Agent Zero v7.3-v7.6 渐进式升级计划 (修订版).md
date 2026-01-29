# Agent Zero v7.3-v7.6 渐进式升级计划 (修订版)

**基于**: v7.2 LLM 语义路由成功  
**目标**: 分阶段实施 v8.0 核心功能  
**原则**: 小步快跑,充分验证,稳定优先

> **📝 修订说明 (2026-01-22)**:  
> 根据工程审查结果,本计划已调整以下内容:
> 1. ✅ **保持同步实现** - 移除 async/await,使用同步方法
> 2. ✅ **扩展现有 Schema** - v7.4 扩展 ProjectMeta 而非新建 AgentSpec
> 3. ✅ **优化现有模块** - v7.5 扩展 ToolMetadata 而非新建 ToolDef
> 4. ✅ **基于已有实现** - 大部分基础设施已实现,只需优化

---

## 📋 总体规划

| 版本 | 核心功能 | 时间 | 优先级 | 风险 |
|------|----------|------|--------|------|
| **v7.3** | uv 集成 + 结构化 Trace | Week 1-2 | 高 | 中 |
| **v7.4** | PM 推断式重构 | Week 2-3 | 高 | 中 |
| **v7.5** | 工具系统增强 | Week 3-4 | 高 | 中 |
| **v7.6** | 架构自动映射 | Week 4-5 | 中 | 低 |

---

## 🚀 v7.3: 基础设施升级 (Week 1-2)

### 目标
1. ✅ 集成 uv,实现 10 倍构建加速
2. ✅ 实现结构化 Trace,支持可视化调试

### 模块 1: uv 集成

#### 技术方案

**Step 1: uv 二进制自动下载**
```python
# src/core/env_manager.py

class UVDownloader:
    """自动下载 uv 二进制到项目目录"""
    
    UV_VERSION = "0.1.0"  # 或最新稳定版
    UV_URLS = {
        "win32": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-pc-windows-msvc.exe",
        "linux": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-unknown-linux-gnu",
        "darwin": f"https://github.com/astral-sh/uv/releases/download/{UV_VERSION}/uv-x86_64-apple-darwin"
    }
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.bin_dir = project_root / "bin"
        self.uv_path = self.bin_dir / ("uv.exe" if sys.platform == "win32" else "uv")
    
    def ensure_uv(self) -> Path:
        """确保 uv 可用,如果不存在则下载"""
        if self.uv_path.exists():
            return self.uv_path
        
        # 创建 bin 目录
        self.bin_dir.mkdir(exist_ok=True)
        
        # 下载 uv
        url = self.UV_URLS[sys.platform]
        print(f"⬇️  下载 uv ({sys.platform})...")
        
        import urllib.request
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                content = response.read()
                self.uv_path.write_bytes(content)
        except Exception as e:
            raise RuntimeError(f"Failed to download uv: {e}")
        
        # 设置可执行权限 (Unix)
        if sys.platform != "win32":
            os.chmod(self.uv_path, 0o755)
        
        print(f"✅ uv 已就绪: {self.uv_path}")
        return self.uv_path
```

**Step 2: EnvManager 集成**
```python
# src/core/env_manager.py

class EnvManager:
    def __init__(self, agent_dir: Path):
        self.agent_dir = agent_dir
        self.venv_path = agent_dir / ".venv"
        self.uv_downloader = UVDownloader(agent_dir.parent.parent)  # 项目根目录
        self._uv_path: Optional[Path] = None
    
    def setup_environment(self) -> EnvSetupResult:
        """使用 uv 创建环境并安装依赖"""
        try:
            # 确保 uv 可用
            self._uv_path = self.uv_downloader.ensure_uv()
            
            # 创建 venv (使用 uv)
            if not self.venv_path.exists():
                print(f"⚡ 使用 uv 创建虚拟环境...")
                self._create_venv_with_uv()
            
            # 安装依赖 (使用 uv)
            requirements_file = self.agent_dir / "requirements.txt"
            if requirements_file.exists():
                print("⚡ 使用 uv 安装依赖...")
                self._install_with_uv(requirements_file)
            
            return EnvSetupResult(success=True, venv_path=self.venv_path, python_executable=self.get_python_executable())
        except Exception as e:
            # 回退到 venv (容错)
            print(f"⚠️  uv 失败,回退到 venv: {e}")
            return self._fallback_to_venv()
    
    def _create_venv_with_uv(self):
        """使用 uv 创建 venv"""
        cmd = [str(self._uv_path), "venv", str(self.venv_path)]
        process = self._run_command(cmd, timeout=10)
        if process.returncode != 0:
            raise RuntimeError(f"uv venv failed: {process.stderr}")
    
    def _install_with_uv(self, requirements_file: Path):
        """使用 uv 安装依赖"""
        python_exe = self.get_python_executable()
        cmd = [
            str(self._uv_path),
            "pip",
            "install",
            "-r",
            str(requirements_file),
            "--python",
            str(python_exe)
        ]
        process = self._run_command(cmd, timeout=300)
        if process.returncode != 0:
            raise RuntimeError(f"uv pip install failed: {process.stderr}")
```

**Step 3: 性能监控**
```python
# 添加性能指标收集
import time

class PerformanceMetrics:
    def __init__(self):
        self.venv_create_time = 0
        self.install_time = 0
    
    def record_venv_create(self, duration: float):
        self.venv_create_time = duration
    
    def record_install(self, duration: float):
        self.install_time = duration
    
    def report(self):
        total = self.venv_create_time + self.install_time
        print(f"⚡ 性能报告:")
        print(f"   - 创建环境: {self.venv_create_time:.2f}s")
        print(f"   - 安装依赖: {self.install_time:.2f}s")
        print(f"   - 总计: {total:.2f}s")
```

#### 验收标准
- ✅ uv 自动下载成功率 > 95%
- ✅ 环境创建时间 < 5s
- ✅ 依赖安装时间 < 15s (LangChain + DeepEval)
- ✅ 回退机制正常工作
- ✅ 所有现有测试通过

---

### 模块 2: 结构化 Trace

#### 技术方案

**Step 1: Trace Schema 定义**
```python
# src/schemas/trace.py

class TraceEntry(BaseModel):
    """单个 Trace 条目"""
    step: int
    node_id: str
    node_type: str  # llm, rag, tool, etc.
    timestamp: str
    action: str  # intent_routing, rag_retrieval, llm_call, etc.
    status: Literal["success", "failed", "skipped"]
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None

class StructuredTrace(BaseModel):
    """完整的 Trace 记录"""
    trace_id: str
    agent_name: str
    query: str
    start_time: str
    end_time: Optional[str] = None
    total_duration_ms: Optional[int] = None
    entries: List[TraceEntry] = []
    final_status: Literal["success", "failed", "timeout"] = "success"
```

**Step 2: Simulator 输出格式升级**
```python
# src/core/simulator.py

class Simulator:
    async def simulate(self, graph: GraphStructure, sample_input: str) -> StructuredTrace:
        """沙盘推演,返回结构化 Trace"""
        trace = StructuredTrace(
            trace_id=f"sim_{uuid.uuid4().hex[:8]}",
            agent_name=graph.pattern.pattern_type,
            query=sample_input,
            start_time=datetime.now().isoformat()
        )
        
        current_node = graph.entry_point
        step = 1
        
        while current_node != "END":
            start_time = time.time()
            
            # 模拟节点执行
            result = await self._simulate_node(current_node, graph)
            
            # 记录 Trace
            trace.entries.append(TraceEntry(
                step=step,
                node_id=current_node,
                node_type=result.node_type,
                timestamp=datetime.now().isoformat(),
                action=result.action,
                status=result.status,
                duration_ms=int((time.time() - start_time) * 1000),
                metadata=result.metadata
            ))
            
            current_node = result.next_node
            step += 1
        
        trace.end_time = datetime.now().isoformat()
        trace.total_duration_ms = sum(e.duration_ms for e in trace.entries)
        
        return trace
```

**Step 3: UI 可视化支持**
```python
# 生成 Trace 可视化 HTML
def generate_trace_html(trace: StructuredTrace) -> str:
    """生成 Trace 可视化 HTML"""
    html = f"""
    <div class="trace-timeline">
        <h3>🕹️ 执行轨迹: {trace.agent_name}</h3>
        <div class="timeline">
    """
    
    for entry in trace.entries:
        status_icon = "✅" if entry.status == "success" else "❌"
        html += f"""
        <div class="trace-entry {entry.status}">
            <span class="step">Step {entry.step}</span>
            <span class="node">{entry.node_id}</span>
            <span class="action">{entry.action}</span>
            <span class="duration">{entry.duration_ms}ms</span>
            <span class="status">{status_icon}</span>
        </div>
        """
    
    html += """
        </div>
    </div>
    """
    return html
```

#### 验收标准
- ✅ Simulator 输出 JSON 格式 Trace
- ✅ Trace 包含所有节点执行信息
- ✅ 生成 HTML 可视化报告
- ✅ 错误节点高亮显示
- ✅ 性能指标准确记录

---

## 🧠 v7.4: PM 推断式重构 (Week 2-3)

### 目标
实现 "推断与确认" 模式,减少用户交互,提升体验

### 技术方案

**Step 1: 扩展 ProjectMeta Schema**
```python
# src/schemas/project_meta.py

# 在现有 ProjectMeta 类中添加新字段:
class ProjectMeta(BaseModel):
    # ... 现有字段 ...
    
    # 🆕 v7.4: 推断式重构新增字段
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="推断置信度")
    missing_info: List[str] = Field(default_factory=list, description="缺失的关键信息")
```

**Step 2: PM 推断 Prompt (优化现有方法)**
```python
# src/core/pm.py

# 优化现有的 analyze_with_clarification_loop 方法
class PM:
    async def analyze_with_inference(self, user_input: str, file_paths: Optional[List[Path]] = None) -> ProjectMeta:
        """推断式分析 (基于现有 ProjectMeta)"""
        
        # 1. 先进行基础分析
        project_meta = await self.analyze_requirements(user_input, file_paths)
        
        # 2. 评估置信度
        confidence = self._calculate_confidence(project_meta, user_input)
        project_meta.confidence = confidence
        
        # 3. 识别缺失信息
        missing_info = self._identify_missing_info(project_meta)
        project_meta.missing_info = missing_info
        
        # 4. 如果置信度低或有缺失信息,进入追问环节
        if confidence < 0.7 or missing_info:
            project_meta.status = "clarifying"
            # 生成澄清问题
            questions = await self.ask_clarification(project_meta)
            project_meta.clarification_questions = questions
        else:
            project_meta.status = "ready"
        
        return project_meta
    
    def _calculate_confidence(self, project_meta: ProjectMeta, user_input: str) -> float:
        """计算推断置信度"""
        confidence = 1.0
        
        # 如果描述过于简短,降低置信度
        if len(user_input) < 20:
            confidence -= 0.3
        
        # 如果任务类型不明确,降低置信度
        if project_meta.task_type == TaskType.CUSTOM:
            confidence -= 0.2
        
        # 如果复杂度高但没有执行计划,降低置信度
        if project_meta.complexity_score > 5 and not project_meta.execution_plan:
            confidence -= 0.2
        
        return max(0.0, confidence)
    
    def _identify_missing_info(self, project_meta: ProjectMeta) -> List[str]:
        """识别缺失的关键信息"""
        missing = []
        
        # 检查是否缺少工具信息
        if project_meta.complexity_score > 5 and not project_meta.execution_plan:
            missing.append("具体的实现步骤")
        
        # 检查 RAG 相关信息
        if project_meta.has_rag and not project_meta.file_paths:
            missing.append("知识库文件路径")
        
        return missing
```

**Step 3: 确认卡片生成**
```python
# src/cli/factory_cli.py

def generate_confirmation_card(project_meta: ProjectMeta) -> str:
    """生成确认卡片"""
    tools_str = "待选择" if not hasattr(project_meta, 'tools') else "已配置"
    rag_str = "✅ 已启用" if project_meta.has_rag else "❌ 未启用"
    
    card = f"""
╔══════════════════════════════════════════════════════════╗
║  🤖 准备构建: {project_meta.agent_name}
╠══════════════════════════════════════════════════════════╣
║  📝 角色设定: {project_meta.description[:40]}...
║  🛠️  工具: {tools_str}
║  📚 知识库: {rag_str}
║  ⚙️  复杂度: {project_meta.complexity_score}/10
║  🎯 置信度: {project_meta.confidence:.0%}
╚══════════════════════════════════════════════════════════╝

[ ✅ 立即构建 ]  [ ✏️ 修改设定 ]  [ ❌ 取消 ]
"""
    return card
```

#### 验收标准
- ✅ 简单需求 (如 "贪吃蛇游戏") 零追问
- ✅ 模糊需求最多追问 1-2 个关键问题
- ✅ 推断准确率 > 85%
- ✅ 确认卡片清晰易懂
- ✅ 用户可以修改推断结果

---

## 🔧 v7.5: 工具系统增强 (Week 3-4)

### 目标
1. 扩展工具注册,支持 Schema 存储
2. 实现基础工具搜索
3. 为 Interface Guard 做准备

### 技术方案

**Step 1: 扩展 ToolMetadata**
```python
# src/tools/registry.py

class ToolMetadata(BaseModel):
    """工具元数据 (扩展版)"""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    category: str = Field(default="general", description="Tool category")
    tags: List[str] = Field(default_factory=list, description="Tool tags for search")
    requires_api_key: bool = Field(default=False, description="Whether tool requires API key")
    
    # 🆕 v7.5: Schema 支持
    openapi_schema: Optional[Dict[str, Any]] = Field(default=None, description="OpenAPI 3.0 Schema")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="使用示例")
```

**Step 2: 工具搜索**
```python
# src/tools/registry.py

class ToolRegistry:
    def search(self, query: str, top_k: int = 5) -> List[ToolDef]:
        """基于关键词搜索工具"""
        results = []
        
        for tool in self._tools.values():
            score = self._calculate_relevance(query, tool)
            if score > 0:
                results.append((score, tool))
        
        results.sort(reverse=True, key=lambda x: x[0])
        return [tool for _, tool in results[:top_k]]
    
    def _calculate_relevance(self, query: str, tool: ToolDef) -> float:
        """计算相关性分数"""
        score = 0.0
        query_lower = query.lower()
        
        # 名称匹配
        if query_lower in tool.name.lower():
            score += 1.0
        
        # 描述匹配
        if query_lower in tool.description.lower():
            score += 0.5
        
        # 标签匹配
        for tag in tool.tags:
            if query_lower in tag.lower():
                score += 0.3
        
        return score
```

**Step 3: 添加示例工具 Schema**
```python
# src/tools/preset_tools.py

# 为现有工具添加 OpenAPI Schema
TAVILY_SEARCH_SCHEMA = {
    "openapi": "3.0.0",
    "info": {"title": "Tavily Search", "version": "1.0.0"},
    "paths": {
        "/search": {
            "post": {
                "parameters": {
                    "query": {"type": "string", "required": True},
                    "max_results": {"type": "integer", "default": 5}
                }
            }
        }
    }
}

tavily_search_tool = ToolDef(
    name="tavily_search",
    description="Search the web using Tavily API",
    category="search",
    openapi_schema=TAVILY_SEARCH_SCHEMA,
    tags=["search", "web", "realtime"],
    examples=[
        {"query": "latest AI news", "max_results": 3}
    ]
)
```

#### 验收标准
- ✅ 所有预置工具都有 Schema
- ✅ 工具搜索准确率 > 80%
- ✅ 支持 3-5 个示例工具
- ✅ Schema 验证正常工作

---

## 🗺️ v7.6: 架构自动映射 (Week 4-5)

### 目标
根据 AgentSpec 自动选择最佳 Pattern

### 技术方案

**映射规则表**
```python
# src/core/archetype_mapper.py

class ArchetypeMapper:
    """架构原型映射器"""
    
    MAPPING_RULES = [
        {
            "condition": lambda spec: spec.complexity == "simple" and not spec.use_rag,
            "pattern": "sequential",
            "reason": "简单任务,顺序执行即可"
        },
        {
            "condition": lambda spec: spec.use_rag,
            "pattern": "rag_with_router",
            "reason": "需要知识库,使用 RAG + 语义路由"
        },
        {
            "condition": lambda spec: spec.complexity == "complex" and "python" in spec.tools,
            "pattern": "reflection",
            "reason": "复杂任务需要代码,使用反思模式"
        },
        {
            "condition": lambda spec: len(spec.tools) > 2,
            "pattern": "plan_execute",
            "reason": "多工具协作,使用规划-执行模式"
        }
    ]
    
    def select_pattern(self, spec: AgentSpec) -> str:
        """选择最佳 Pattern"""
        for rule in self.MAPPING_RULES:
            if rule["condition"](spec):
                print(f"📐 选择模式: {rule['pattern']}")
                print(f"   原因: {rule['reason']}")
                return rule["pattern"]
        
        # 默认
        return "sequential"
```

#### 验收标准
- ✅ 映射规则覆盖 90% 场景
- ✅ 用户可以覆盖自动选择
- ✅ 选择理由清晰可见

---

## 📊 总体验收标准

### v7.3
- ✅ uv 集成成功率 > 95%
- ✅ 构建速度提升 > 5 倍
- ✅ Trace 可视化正常工作

### v7.4
- ✅ PM 推断准确率 > 85%
- ✅ 用户交互次数减少 > 50%
- ✅ 确认卡片满意度 > 90%

### v7.5
- ✅ 工具搜索准确率 > 80%
- ✅ 所有工具有 Schema

### v7.6
- ✅ Pattern 选择准确率 > 90%
- ✅ 用户可覆盖选择

### 整体
- ✅ 所有现有测试通过
- ✅ 新增测试覆盖率 > 80%
- ✅ 无性能回退
- ✅ 用户体验提升明显

---

## 🎯 成功指标

**速度**:
- 环境创建: 60s → 5s
- 依赖安装: 100s → 10s
- 总构建时间: 160s → 15s ⚡

**体验**:
- PM 交互轮次: 3-5 轮 → 0-1 轮
- 用户满意度: +30%

**质量**:
- 测试通过率: 保持 100%
- Bug 数量: 0 新增

---

## 📝 风险缓解

1. **uv 下载失败**: 自动回退到 venv
2. **PM 推断错误**: 用户可修改
3. **工具搜索不准**: 保留手动选择
4. **Pattern 选择错误**: 用户可覆盖

**核心原则**: 所有自动化都有手动兜底! 🛡️
