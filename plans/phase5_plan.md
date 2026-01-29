# Agent Zero 阶段五：产品化详细计划

## 🚨 关键优化要点 (基于专家评审)

### 1. HITL 交互 - Streamlit 并发陷阱

**问题**: Streamlit 每次交互重新运行脚本,`threading.Event` 会导致 UI 卡死

**解决方案**:
- ✅ 状态持久化: 使用 `st.session_state` 存储 Runner 实例
- ✅ 线程分离: Runner 在后台线程运行,UI 轮询状态队列
- ✅ 标志位通信: 按钮只修改 `session_state`,Runner 轮询标志位

### 2. Dify 导出 - 条件逻辑映射

**问题**: Agent Zero 的 Python 条件逻辑无法直接映射为 Dify 简单条件

**解决方案**:
- ✅ 引入 Code Node: 将 `condition_logic` 填入 Dify Python Code Node
- ✅ 双节点组合: Code Node 输出 → If-Else 节点分流
- ✅ 保证逻辑完整性,不强行简化

### 3. 其他优化

- ✅ 流式日志: 添加 Auto-scroll 功能
- ✅ Dify 变量映射: State 字段映射为 Start 节点 Inputs
- ✅ README: 增加 Dify 导入指南章节

---

## 📊 进度总览

### ✅ 已完成阶段

- **阶段一**: 内核 MVP (Week 1-2) - **100% 完成**
- **阶段二**: 数据流与工具 (Week 3-4) - **100% 完成**
- **阶段三**: 蓝图仿真系统 (Week 5-6) - **100% 完成**
  - ✅ Schema 层升级 (PatternConfig, StateSchema, SimulationResult)
  - ✅ PM 双脑模式 (澄清功能)
  - ✅ Graph Designer 三步设计法
  - ✅ Simulator 沙盘推演
  - ✅ Compiler 模板升级 (工具初始化、ToolMessage)
- **阶段四**: 闭环与进化 (Week 7-8) - **95% 完成**
  - ✅ Test Generator (DeepEval 集成)
  - ✅ Runner 本地执行器
  - ✅ Judge 双重反馈 (错误分类)
  - ⏭️ MCP 集成 (标记为 Future Enhancement)
  - ✅ Git 版本管理

---

## 🎯 阶段五：产品化 (Week 9-10)

**目标**: 提升用户体验,完善交互界面,增加导出功能

**当前状态**: 
- CLI 界面已完成 (`start.py`)
- 基础 UI 组件存在 (`src/ui/components`, `src/ui/pages`)
- 需要增强和完善

---

## 📋 详细任务清单

### Task 5.1: UI 升级 🎨

#### 5.1.1 流式日志显示

**目标**: 实时显示 Agent 构建过程,提升用户体验

**文件**: `src/ui/components/log_viewer.py` (新建)

**实现内容**:
```python
import streamlit as st
from typing import Generator
import time

class LogViewer:
    """流式日志查看器"""
    
    def __init__(self):
        self.log_container = None
        self.log_history = []  # 保存日志历史
        
    def create_log_stream(self) -> st.container:
        """创建日志流容器"""
        self.log_container = st.empty()
        return self.log_container
    
    def append_log(self, message: str, level: str = "INFO"):
        """追加日志消息
        
        Args:
            message: 日志内容
            level: 日志级别 (INFO/WARNING/ERROR/SUCCESS)
        """
        emoji_map = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅",
            "DEBUG": "🔍"
        }
        
        emoji = emoji_map.get(level, "📝")
        timestamp = time.strftime("%H:%M:%S")
        
        # 格式化日志
        formatted = f"{emoji} `[{timestamp}]` {message}"
        self.log_history.append(formatted)
        
        # 更新容器 (带 Auto-scroll)
        if self.log_container:
            with self.log_container:
                # 使用 HTML 实现自动滚动
                log_html = "<div style='max-height: 400px; overflow-y: auto;' id='log-container'>"
                log_html += "<br>".join(self.log_history)
                log_html += "</div>"
                log_html += """
                <script>
                    var logContainer = document.getElementById('log-container');
                    if (logContainer) {
                        logContainer.scrollTop = logContainer.scrollHeight;
                    }
                </script>
                """
                st.markdown(log_html, unsafe_allow_html=True)
```

**集成到 AgentFactory**:
```python
# src/core/agent_factory.py 修改
class AgentFactory:
    def __init__(self, ..., log_callback=None):
        self.log_callback = log_callback
        
    def _log(self, message: str, level: str = "INFO"):
        """统一日志接口"""
        print(f"[{level}] {message}")  # CLI 输出
        if self.log_callback:
            self.log_callback(message, level)  # UI 回调
```

**工作量**: 2-3 小时

---

#### 5.1.2 动态图谱可视化

**目标**: 可视化 Agent 的 Graph 结构

**文件**: `src/ui/components/graph_visualizer.py` (新建)

**实现方案**: 使用 Streamlit + Mermaid

```python
import streamlit as st
from src.schemas import GraphStructure

class GraphVisualizer:
    """Graph 可视化组件"""
    
    @staticmethod
    def render_mermaid(graph: GraphStructure) -> str:
        """生成 Mermaid 图"""
        lines = ["graph TD"]
        
        # 添加节点
        for node in graph.nodes:
            node_type_emoji = {
                "llm": "🤖",
                "tool": "🔧",
                "rag": "📚",
                "conditional": "🔀"
            }
            emoji = node_type_emoji.get(node.type, "📦")
            lines.append(f'    {node.id}["{emoji} {node.id}"]')
        
        # 添加普通边
        for edge in graph.edges:
            lines.append(f"    {edge.source} --> {edge.target}")
        
        # 添加条件边
        for cond_edge in graph.conditional_edges:
            for key, target in cond_edge.branches.items():
                label = key if key != "end" else "END"
                lines.append(f'    {cond_edge.source} -->|{label}| {target}')
        
        return "\n".join(lines)
    
    @staticmethod
    def display(graph: GraphStructure):
        """显示 Graph"""
        mermaid_code = GraphVisualizer.render_mermaid(graph)
        
        st.subheader("📊 Agent Graph 结构")
        st.code(mermaid_code, language="mermaid")
        
        # 使用 st-mermaid 组件 (需要安装)
        try:
            import streamlit.components.v1 as components
            components.html(f"""
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <div class="mermaid">
                {mermaid_code}
                </div>
                <script>mermaid.initialize({{startOnLoad:true}});</script>
            """, height=600)
        except:
            st.info("安装 streamlit-mermaid 以获得更好的可视化效果")
```

**工作量**: 3-4 小时

---

#### 5.1.3 Token 消耗统计

**目标**: 实时统计 LLM 调用的 Token 消耗

**文件**: `src/llm/builder_client.py` 修改

```python
class BuilderClient:
    def __init__(self, config: BuilderAPIConfig):
        self.config = config
        self.token_stats = {
            "total_calls": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost_usd": 0.0
        }
    
    async def generate(self, messages, **kwargs):
        """生成响应并统计 Token"""
        response = await self.client.chat.completions.create(...)
        
        # 统计 Token
        if hasattr(response, 'usage'):
            self.token_stats["total_calls"] += 1
            self.token_stats["total_input_tokens"] += response.usage.prompt_tokens
            self.token_stats["total_output_tokens"] += response.usage.completion_tokens
            
            # 计算成本 (示例价格)
            cost = self._calculate_cost(
                response.usage.prompt_tokens,
                response.usage.completion_tokens
            )
            self.token_stats["total_cost_usd"] += cost
        
        return response
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        # GPT-4o 价格 (示例)
        input_price_per_1k = 0.005
        output_price_per_1k = 0.015
        
        return (input_tokens / 1000 * input_price_per_1k + 
                output_tokens / 1000 * output_price_per_1k)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.token_stats.copy()
```

**UI 组件**: `src/ui/components/token_stats.py`

```python
import streamlit as st

def display_token_stats(stats: dict):
    """显示 Token 统计"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总调用次数", stats["total_calls"])
    
    with col2:
        st.metric("输入 Tokens", f"{stats['total_input_tokens']:,}")
    
    with col3:
        st.metric("输出 Tokens", f"{stats['total_output_tokens']:,}")
    
    with col4:
        st.metric("预估成本", f"${stats['total_cost_usd']:.4f}")
```

**工作量**: 2-3 小时

---

#### 5.1.4 Blueprint Review UI

**目标**: 在编译前让用户审查 Graph 结构

**文件**: `src/ui/pages/blueprint_review.py` (新建)

```python
import streamlit as st
from src.schemas import GraphStructure, SimulationResult

def show_blueprint_review(
    graph: GraphStructure,
    simulation: SimulationResult
):
    """Blueprint 审查页面"""
    
    st.title("📐 Blueprint 审查")
    
    # Tab 1: Graph 结构
    tab1, tab2, tab3 = st.tabs(["📊 Graph 结构", "🎬 仿真结果", "⚙️ 配置"])
    
    with tab1:
        from src.ui.components.graph_visualizer import GraphVisualizer
        GraphVisualizer.display(graph)
        
        # 节点详情
        st.subheader("节点详情")
        for node in graph.nodes:
            with st.expander(f"{node.id} ({node.type})"):
                st.json({
                    "id": node.id,
                    "type": node.type,
                    "role_description": node.role_description,
                    "config": node.config
                })
    
    with tab2:
        st.subheader("仿真执行轨迹")
        st.text(simulation.execution_trace)
        
        if simulation.issues:
            st.warning(f"发现 {len(simulation.issues)} 个问题")
            for issue in simulation.issues:
                st.error(f"[{issue.severity}] {issue.description}")
    
    with tab3:
        st.subheader("模式配置")
        st.json({
            "pattern_type": graph.pattern.pattern_type,
            "max_iterations": graph.pattern.max_iterations,
            "description": graph.pattern.description
        })
        
        st.subheader("状态字段")
        for field in graph.state_schema.fields:
            st.text(f"- {field.name}: {field.type}")
    
    # 审批按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 批准并构建", type="primary"):
            return "approve"
    with col2:
        if st.button("❌ 拒绝", type="secondary"):
            return "reject"
    
    return None
```

**工作量**: 3-4 小时

---

### Task 5.2: HITL 人工干预 🤚

**目标**: 允许用户在 Agent 运行时暂停、检查、修改状态

#### 5.2.1 暂停/继续执行 (⚠️ 关键优化)

**文件**: `src/core/runner.py` 修改

**⚠️ 重要**: Streamlit 的并发陷阱 - 必须使用线程分离 + 状态轮询

```python
import threading
from enum import Enum
from queue import Queue

class ExecutionControl(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"

class Runner:
    def __init__(self):
        self.control = ExecutionControl.RUNNING
        self.status_queue = Queue()  # 状态队列,供 UI 轮询
        self.log_queue = Queue()     # 日志队列
    
    def pause(self):
        """暂停执行"""
        self.control = ExecutionControl.PAUSED
        self.status_queue.put({"status": "paused"})
    
    def resume(self):
        """继续执行"""
        self.control = ExecutionControl.RUNNING
        self.status_queue.put({"status": "running"})
    
    def stop(self):
        """停止执行"""
        self.control = ExecutionControl.STOPPED
        self.status_queue.put({"status": "stopped"})
    
    def run_agent_async(self, agent_path: str, query: str):
        """在后台线程运行 Agent"""
        def _run():
            # 在关键点检查控制状态
            while self.control == ExecutionControl.PAUSED:
                time.sleep(0.1)  # 轮询等待
            
            if self.control == ExecutionControl.STOPPED:
                self.log_queue.put({"level": "WARNING", "message": "执行已停止"})
                return
            
            # 继续执行 Agent
            # ... 原有逻辑 ...
            self.log_queue.put({"level": "INFO", "message": "Agent 执行中..."})
        
        # 启动后台线程
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread
```

**UI 控制**: `src/ui/components/execution_control.py`

```python
import streamlit as st
import time

def show_execution_controls():
    """显示执行控制按钮 (线程安全版本)"""
    
    # 初始化 session_state
    if 'runner' not in st.session_state:
        st.session_state.runner = None
    if 'runner_thread' not in st.session_state:
        st.session_state.runner_thread = None
    
    # 控制按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏸️ 暂停"):
            if st.session_state.runner:
                st.session_state.runner.pause()
                st.success("已暂停")
    
    with col2:
        if st.button("▶️ 继续"):
            if st.session_state.runner:
                st.session_state.runner.resume()
                st.success("已继续")
    
    with col3:
        if st.button("⏹️ 停止"):
            if st.session_state.runner:
                st.session_state.runner.stop()
                st.error("已停止")
    
    # 状态轮询 (每 0.5 秒刷新)
    if st.session_state.runner:
        status_placeholder = st.empty()
        log_placeholder = st.empty()
        
        # 显示状态
        try:
            status = st.session_state.runner.status_queue.get_nowait()
            status_placeholder.info(f"状态: {status['status']}")
        except:
            pass
        
        # 显示日志
        try:
            log = st.session_state.runner.log_queue.get_nowait()
            log_placeholder.write(f"{log['level']}: {log['message']}")
        except:
            pass
        
        # 自动刷新
        time.sleep(0.5)
        st.rerun()
```

**工作量**: 5 小时 (增加缓冲)

---

#### 5.2.2 查看/修改中间状态

**文件**: `src/ui/components/state_inspector.py` (新建)

```python
import streamlit as st
import json

def show_state_inspector(current_state: dict):
    """状态检查器"""
    st.subheader("🔍 当前状态")
    
    # 显示状态
    state_json = json.dumps(current_state, indent=2, ensure_ascii=False)
    edited_state = st.text_area(
        "编辑状态 (JSON 格式)",
        value=state_json,
        height=400
    )
    
    if st.button("💾 应用修改"):
        try:
            new_state = json.loads(edited_state)
            st.success("状态已更新")
            return new_state
        except json.JSONDecodeError as e:
            st.error(f"JSON 格式错误: {e}")
            return None
    
    return None
```

**工作量**: 2 小时

---

### Task 5.3: 导出功能 📦

#### 5.3.1 ZIP 打包

**文件**: `src/utils/export_utils.py` (新建)

```python
import zipfile
from pathlib import Path
import shutil

def export_agent_to_zip(agent_path: Path, output_path: Path):
    """将 Agent 打包为 ZIP
    
    Args:
        agent_path: Agent 目录路径
        output_path: 输出 ZIP 文件路径
    """
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in agent_path.rglob('*'):
            if file_path.is_file():
                # 排除不必要的文件
                if any(exclude in str(file_path) for exclude in [
                    '__pycache__', '.pyc', 'venv', '.git', '.trace'
                ]):
                    continue
                
                arcname = file_path.relative_to(agent_path.parent)
                zipf.write(file_path, arcname)
    
    return output_path
```

**UI 集成**:
```python
# 在 Agent 列表页面添加导出按钮
if st.button("📦 导出为 ZIP"):
    zip_path = export_agent_to_zip(agent_path, output_dir / f"{agent_name}.zip")
    
    with open(zip_path, "rb") as f:
        st.download_button(
            label="⬇️ 下载 ZIP",
            data=f,
            file_name=f"{agent_name}.zip",
            mime="application/zip"
        )
```

**工作量**: 1-2 小时

---

#### 5.3.2 Dify YAML 格式导出 (重点功能)

**目标**: 将 Agent 导出为 Dify Chatflow DSL,支持在 Dify 平台导入和运行

**背景**: Dify 使用基于 YAML 的 DSL 定义工作流,对应 Agent Zero 的是 **"advanced-chat" (Chatflow)** 模式

---

##### Step 1: 定义 Dify Schema

**文件**: `src/exporters/dify/schema.py` (新建)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DifyNodeData(BaseModel):
    """Dify 节点数据"""
    title: str
    type: str  # start, llm, tool, knowledge-retrieval, if-else, answer
    desc: str = ""
    selected: bool = False
    
    # LLM 节点特有字段
    model: Optional[Dict[str, str]] = None  # {"provider": "openai", "name": "gpt-4o"}
    prompt_template: Optional[List[Dict[str, str]]] = None  # [{"role": "system", "text": "..."}]
    
    # Tool 节点特有字段
    provider_id: Optional[str] = None  # "tavily"
    tool_name: Optional[str] = None  # "tavily_search"
    tool_parameters: Optional[Dict[str, Any]] = None
    
    # Knowledge Retrieval 特有字段
    dataset_ids: Optional[List[str]] = None  # 知识库 ID (导出时留空)
    retrieval_mode: Optional[str] = "single"
    
    # Start 节点特有字段
    variables: Optional[List[Dict[str, Any]]] = None
    
    # Answer 节点特有字段
    answer: Optional[str] = None  # 输出变量引用

class DifyNode(BaseModel):
    """Dify 节点"""
    id: str
    data: DifyNodeData
    position: Dict[str, int]  # {"x": 0, "y": 0}
    sourcePosition: str = "right"
    targetPosition: str = "left"
    width: int = 240
    height: int = 90

class DifyEdge(BaseModel):
    """Dify 连线"""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None  # 条件边需要
    targetHandle: Optional[str] = None
    type: str = "default"

class DifyGraph(BaseModel):
    """Dify Graph"""
    nodes: List[DifyNode]
    edges: List[DifyEdge]

class DifyWorkflow(BaseModel):
    """Dify Workflow"""
    graph: DifyGraph
    version: str = "0.1.0"

class DifyApp(BaseModel):
    """Dify App (顶层结构)"""
    app: Dict[str, Any]  # name, mode, icon, description
    kind: str = "app"
    version: str = "0.1.0"
    workflow: DifyWorkflow
```

**工作量**: 1-2 小时

---

##### Step 2: 实现节点映射器

**文件**: `src/exporters/dify/mapper.py` (新建)

```python
from src.schemas import GraphStructure, NodeDef
from .schema import DifyNode, DifyNodeData

class NodeMapper:
    """Agent Zero -> Dify 节点映射器"""
    
    # 工具名称映射表
    TOOL_MAPPING = {
        "tavily_search": {
            "provider_id": "tavily",
            "tool_name": "tavily_search",
            "supported": True
        },
        "wikipedia": {
            "provider_id": "wikipedia",
            "tool_name": "wikipedia_search",
            "supported": True
        },
        # 其他工具标记为不支持
    }
    
    @staticmethod
    def map_llm_node(node: NodeDef, node_id: str, position: Dict[str, int]) -> DifyNode:
        """映射 LLM 节点"""
        return DifyNode(
            id=node_id,
            data=DifyNodeData(
                title=node.id,
                type="llm",
                desc=node.role_description or "",
                model={
                    "provider": "openai",
                    "name": "gpt-4o"  # 默认模型
                },
                prompt_template=[
                    {
                        "role": "system",
                        "text": node.role_description or "You are a helpful assistant."
                    }
                ]
            ),
            position=position
        )
    
    @staticmethod
    def map_rag_node(node: NodeDef, node_id: str, position: Dict[str, int]) -> DifyNode:
        """映射 RAG 节点"""
        return DifyNode(
            id=node_id,
            data=DifyNodeData(
                title="Knowledge Retrieval",
                type="knowledge-retrieval",
                desc="⚠️ 需要在 Dify 中手动绑定知识库",
                dataset_ids=[],  # 留空,用户导入后手动配置
                retrieval_mode="single"
            ),
            position=position
        )
    
    @staticmethod
    def map_tool_node(node: NodeDef, node_id: str, position: Dict[str, int]) -> DifyNode:
        """映射工具节点"""
        tool_name = node.config.get("tool_name") if node.config else node.id
        
        # 查找映射
        mapping = NodeMapper.TOOL_MAPPING.get(tool_name)
        
        if mapping and mapping["supported"]:
            # 支持的工具
            return DifyNode(
                id=node_id,
                data=DifyNodeData(
                    title=tool_name,
                    type="tool",
                    provider_id=mapping["provider_id"],
                    tool_name=mapping["tool_name"],
                    tool_parameters={}
                ),
                position=position
            )
        else:
            # 不支持的工具 - 转为 Note 提示
            return DifyNode(
                id=node_id,
                data=DifyNodeData(
                    title=f"⚠️ Unsupported Tool: {tool_name}",
                    type="note",
                    desc=f"Agent Zero 使用了 {tool_name},但 Dify 不支持。请手动替换为等效工具。"
                ),
                position=position
            )
```

**工作量**: 2-3 小时

---

##### Step 3: 实现转换器核心

**文件**: `src/exporters/dify/converter.py` (新建)

```python
from src.schemas import GraphStructure
from .schema import DifyApp, DifyWorkflow, DifyGraph, DifyNode, DifyEdge, DifyNodeData
from .mapper import NodeMapper
from typing import List, Tuple

class AgentZeroToDifyConverter:
    """Agent Zero -> Dify DSL 转换器"""
    
    def __init__(self, graph: GraphStructure, agent_name: str):
        self.graph = graph
        self.agent_name = agent_name
        self.node_id_counter = 1
        self.node_id_map = {}  # Agent Zero node.id -> Dify node id
    
    def convert(self) -> DifyApp:
        """执行转换"""
        # 1. 创建节点
        nodes = self._create_nodes()
        
        # 2. 创建连线
        edges = self._create_edges()
        
        # 3. 构建 Workflow
        workflow = DifyWorkflow(
            graph=DifyGraph(nodes=nodes, edges=edges)
        )
        
        # 4. 构建 App
        app = DifyApp(
            app={
                "name": self.agent_name,
                "mode": "advanced-chat",  # Chatflow 模式
                "icon": "🤖",
                "description": self.graph.pattern.description,
                "use_icon_as_answer_icon": False
            },
            workflow=workflow
        )
        
        return app
    
    def _create_nodes(self) -> List[DifyNode]:
        """创建所有节点"""
        nodes = []
        
        # 1. Start 节点 (必须)
        start_node = self._create_start_node()
        nodes.append(start_node)
        
        # 2. 转换 Agent Zero 节点
        for i, node in enumerate(self.graph.nodes):
            dify_node_id = str(self.node_id_counter)
            self.node_id_counter += 1
            self.node_id_map[node.id] = dify_node_id
            
            # 计算位置 (简单横向布局)
            position = {"x": (i + 1) * 300, "y": 0}
            
            # 根据类型映射
            if node.type == "llm":
                dify_node = NodeMapper.map_llm_node(node, dify_node_id, position)
            elif node.type == "rag":
                dify_node = NodeMapper.map_rag_node(node, dify_node_id, position)
            elif node.type == "tool":
                dify_node = NodeMapper.map_tool_node(node, dify_node_id, position)
            else:
                # 其他类型转为 Note
                dify_node = DifyNode(
                    id=dify_node_id,
                    data=DifyNodeData(
                        title=f"Unknown: {node.id}",
                        type="note",
                        desc=f"Type: {node.type}"
                    ),
                    position=position
                )
            
            nodes.append(dify_node)
        
        # 3. Answer 节点 (必须)
        answer_node = self._create_answer_node(len(nodes))
        nodes.append(answer_node)
        
        return nodes
    
    def _create_start_node(self) -> DifyNode:
        """创建 Start 节点"""
        start_id = str(self.node_id_counter)
        self.node_id_counter += 1
        self.node_id_map["START"] = start_id
        
        # ⚠️ 优化: 映射 State 字段为 Start 节点 Variables
        variables = [
            {
                "variable": "query",
                "type": "text-input",
                "label": "用户输入",
                "required": True
            }
        ]
        
        # 添加 State 字段作为可选输入
        for field in self.graph.state_schema.fields:
            if field.name not in ["messages", "trace_file"]:  # 排除内部字段
                variables.append({
                    "variable": field.name,
                    "type": self._map_field_type(field.type),
                    "label": field.description or field.name,
                    "required": False
                })
        
        return DifyNode(
            id=start_id,
            data=DifyNodeData(
                title="开始",
                type="start",
                variables=variables
            ),
            position={"x": 0, "y": 0}
        )
    
    def _map_field_type(self, field_type: str) -> str:
        """映射 State 字段类型到 Dify 输入类型"""
        mapping = {
            "str": "text-input",
            "int": "number-input",
            "bool": "select",
            "List[str]": "text-input"  # 简化处理
        }
        return mapping.get(field_type, "text-input")
    
    def _create_answer_node(self, index: int) -> DifyNode:
        """创建 Answer 节点"""
        answer_id = str(self.node_id_counter)
        self.node_id_counter += 1
        self.node_id_map["END"] = answer_id
        
        return DifyNode(
            id=answer_id,
            data=DifyNodeData(
                title="回答",
                type="answer",
                answer="{{#llm.text#}}"  # 引用最后一个 LLM 节点的输出
            ),
            position={"x": index * 300, "y": 0}
        )
    
    def _create_edges(self) -> List[DifyEdge]:
        """创建连线"""
        edges = []
        edge_counter = 1
        
        # 1. Start -> Entry Point
        entry_point_id = self.node_id_map.get(self.graph.entry_point)
        if entry_point_id:
            edges.append(DifyEdge(
                id=f"edge_{edge_counter}",
                source=self.node_id_map["START"],
                target=entry_point_id
            ))
            edge_counter += 1
        
        # 2. 转换普通边
        for edge in self.graph.edges:
            source_id = self.node_id_map.get(edge.source)
            target_id = self.node_id_map.get(edge.target)
            
            if source_id and target_id:
                edges.append(DifyEdge(
                    id=f"edge_{edge_counter}",
                    source=source_id,
                    target=target_id
                ))
                edge_counter += 1
        
        # 3. 转换条件边 (⚠️ 优化: 使用 Code Node + If-Else 组合)
        for cond_edge in self.graph.conditional_edges:
            source_id = self.node_id_map.get(cond_edge.source)
            
            if not source_id:
                continue
            
            # 创建 Code Node 执行条件逻辑
            code_node_id = str(self.node_id_counter)
            self.node_id_counter += 1
            
            code_node = DifyNode(
                id=code_node_id,
                data=DifyNodeData(
                    title=f"Condition: {cond_edge.condition}",
                    type="code",
                    desc="执行条件判断逻辑",
                    code=cond_edge.condition_logic or "# 条件逻辑\nresult = 'end'",
                    code_language="python3",
                    outputs={
                        "result": {
                            "type": "string",
                            "children": None
                        }
                    }
                ),
                position={"x": (len(nodes) + edge_counter) * 300, "y": 100}
            )
            nodes.append(code_node)
            
            # Source -> Code Node
            edges.append(DifyEdge(
                id=f"edge_{edge_counter}",
                source=source_id,
                target=code_node_id
            ))
            edge_counter += 1
            
            # 创建 If-Else 节点
            ifelse_node_id = str(self.node_id_counter)
            self.node_id_counter += 1
            
            ifelse_node = DifyNode(
                id=ifelse_node_id,
                data=DifyNodeData(
                    title="Route Decision",
                    type="if-else",
                    desc="根据条件结果路由",
                    conditions=[
                        {
                            "variable_selector": ["code", "result"],
                            "comparison_operator": "is",
                            "value": key
                        }
                        for key in cond_edge.branches.keys() if key != "end"
                    ]
                ),
                position={"x": (len(nodes) + edge_counter) * 300, "y": 100}
            )
            nodes.append(ifelse_node)
            
            # Code Node -> If-Else
            edges.append(DifyEdge(
                id=f"edge_{edge_counter}",
                source=code_node_id,
                target=ifelse_node_id
            ))
            edge_counter += 1
            
            # If-Else -> Targets
            for key, target in cond_edge.branches.items():
                if target == "END":
                    target_id = self.node_id_map.get("END")
                else:
                    target_id = self.node_id_map.get(target)
                
                if target_id:
                    edges.append(DifyEdge(
                        id=f"edge_{edge_counter}",
                        source=ifelse_node_id,
                        target=target_id,
                        sourceHandle=key
                    ))
                    edge_counter += 1
        
        return edges
```

**工作量**: 3-4 小时

---

##### Step 4: 导出接口

**文件**: `src/exporters/dify/exporter.py` (新建)

```python
import yaml
from pathlib import Path
from src.schemas import GraphStructure
from .converter import AgentZeroToDifyConverter

class DifyExporter:
    """Dify 导出器"""
    
    @staticmethod
    def export_to_yaml(
        graph: GraphStructure,
        agent_name: str,
        output_path: Path
    ) -> Path:
        """导出为 Dify YAML
        
        Args:
            graph: Graph 结构
            agent_name: Agent 名称
            output_path: 输出文件路径
        
        Returns:
            输出文件路径
        """
        # 转换
        converter = AgentZeroToDifyConverter(graph, agent_name)
        dify_app = converter.convert()
        
        # 序列化为 YAML
        yaml_content = yaml.dump(
            dify_app.model_dump(exclude_none=True),
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False
        )
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        return output_path
    
    @staticmethod
    def export_to_string(graph: GraphStructure, agent_name: str) -> str:
        """导出为 YAML 字符串"""
        converter = AgentZeroToDifyConverter(graph, agent_name)
        dify_app = converter.convert()
        
        return yaml.dump(
            dify_app.model_dump(exclude_none=True),
            allow_unicode=True,
            sort_keys=False
        )
```

**工作量**: 1 小时

---

##### Step 5: UI 集成

**修改文件**: `src/cli/factory_cli.py` 或 Agent 列表页面

```python
# 在 Agent 构建完成后添加导出选项
if st.button("📤 导出为 Dify YAML"):
    from src.exporters.dify import DifyExporter
    
    output_path = agent_dir / f"{agent_name}_dify.yml"
    DifyExporter.export_to_yaml(graph, agent_name, output_path)
    
    with open(output_path, 'r', encoding='utf-8') as f:
        yaml_content = f.read()
    
    st.download_button(
        label="⬇️ 下载 Dify YAML",
        data=yaml_content,
        file_name=f"{agent_name}_dify.yml",
        mime="text/yaml"
    )
    
    st.success("✅ Dify YAML 已生成!")
    st.info("📝 导入 Dify 后需要手动配置:\n1. 知识库绑定 (如有 RAG)\n2. API Keys\n3. 不支持的工具替换")
```

**工作量**: 1 小时

---

##### 总工作量: 8-11 小时

##### 关键难点与解决方案

| 难点 | 解决方案 |
|------|---------|
| RAG 知识库 ID | 导出时留空,提示用户手动绑定 |
| 不支持的工具 | 转为 Note 节点,提示用户替换 |
| 条件边复杂逻辑 | 简化为单分支,或转为 if-else 节点 |
| 节点布局 | 简单横向布局,用户可在 Dify 中调整 |

---

#### 5.3.3 README 生成

**文件**: `src/templates/readme_template.md.j2` (新建)

```markdown
# {{ agent_name }}

> 由 Agent Zero v8.0 自动生成

## 📝 描述

{{ description }}

## 🏗️ 架构

**设计模式**: {{ pattern.pattern_type }}

**Graph 结构**:

```mermaid
{{ mermaid_graph }}
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.template` 为 `.env` 并填写 API Keys:

```bash
cp .env.template .env
```

### 3. 运行 Agent

```bash
python agent.py
```

## 🧪 运行测试

```bash
pytest tests/test_deepeval.py -v
```

## 📊 性能指标

- **测试通过率**: {{ pass_rate }}%
- **平均响应时间**: {{ avg_response_time }}ms

## 🔧 配置

### RAG 配置

{% if has_rag %}
- Chunk Size: {{ rag_config.chunk_size }}
- K Retrieval: {{ rag_config.k_retrieval }}
- Splitter: {{ rag_config.splitter }}
{% else %}
未启用 RAG
{% endif %}

### 工具配置

{% if tools %}
启用的工具:
{% for tool in tools %}
- {{ tool }}
{% endfor %}
{% else %}
未启用工具
{% endif %}

## 📤 导出到 Dify

本 Agent 支持导出为 Dify YAML 格式,可在 Dify 平台导入和运行。

### 导入步骤

1. **下载 YAML 文件**: `{{ agent_name }}_dify.yml`

2. **登录 Dify**: 访问 [Dify Cloud](https://cloud.dify.ai) 或本地部署的 Dify

3. **导入工作流**:
   - 进入"工作室" → "创建应用" → "Chatflow"
   - 点击"导入 DSL" → 上传 YAML 文件

4. **配置必需项** (⚠️ 重要):
   {% if has_rag %}
   - **知识库绑定**: 在 `Knowledge Retrieval` 节点中,点击"选择知识库",创建或选择知识库
   - **上传文档**: 将原始文档上传到 Dify 知识库
   {% endif %}
   - **API Keys**: 在 LLM 节点中配置 OpenAI/DeepSeek API Key
   {% if tools %}
   - **工具配置**: 检查工具节点,配置所需的 API Keys (如 Tavily)
   {% endif %}

5. **测试运行**: 点击"调试"按钮,输入测试问题验证功能

### 注意事项

- **条件逻辑**: 复杂的 Python 条件已转换为 Code Node,请检查逻辑是否正确
- **不支持的工具**: 标记为 Note 的节点需要手动替换为 Dify 支持的等效工具
- **变量映射**: State 字段已映射为 Start 节点的输入变量

---

## 📄 License

MIT

---

Generated by [Agent Zero](https://github.com/your-repo/agent-zero) v8.0
```

**生成器**: `src/utils/readme_generator.py`

```python
from jinja2 import Template
from pathlib import Path

def generate_readme(
    agent_name: str,
    graph: GraphStructure,
    test_results: dict,
    output_path: Path
):
    """生成 README.md"""
    template_path = Path(__file__).parent.parent / "templates" / "readme_template.md.j2"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    # 生成 Mermaid 图
    from src.ui.components.graph_visualizer import GraphVisualizer
    mermaid_graph = GraphVisualizer.render_mermaid(graph)
    
    # 渲染模板
    readme_content = template.render(
        agent_name=agent_name,
        description=graph.pattern.description,
        pattern=graph.pattern,
        mermaid_graph=mermaid_graph,
        pass_rate=test_results.get("pass_rate", 0),
        avg_response_time=test_results.get("avg_response_time", 0),
        has_rag=any(n.type == "rag" for n in graph.nodes),
        tools=[n.id for n in graph.nodes if n.type == "tool"]
    )
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
```

**工作量**: 2 小时

---

## 📅 实施时间表 (已调整)

| 任务 | 原估算 | 调整后 | 优先级 | 备注 |
|------|--------|--------|--------|------|
| 5.1.1 流式日志显示 | 2-3h | 3h | 高 | 增加 Auto-scroll |
| 5.1.2 动态图谱可视化 | 3-4h | 4h | 高 | - |
| 5.1.3 Token 消耗统计 | 2-3h | 3h | 中 | - |
| 5.1.4 Blueprint Review UI | 3-4h | 4h | 高 | - |
| 5.2.1 暂停/继续执行 | 2-3h | **5h** | 中 | ⚠️ Streamlit 线程安全 |
| 5.2.2 查看/修改状态 | 2h | 2h | 低 | - |
| 5.3.1 ZIP 打包 | 1-2h | 2h | 高 | - |
| 5.3.2 Dify YAML 导出 | 8-11h | **12h** | 高 | ⚠️ Code Node 映射 |
| 5.3.3 README 生成 | 2h | 2h | 高 | 增加 Dify 指南 |

**原总工时**: 25-34 小时  
**调整后总工时**: **37 小时** (约 5 个工作日)

**调整说明**:
- HITL 增加 2h (Streamlit 调试复杂度)
- Dify 导出增加 1h (Code Node 逻辑)
- 总体增加 20% 缓冲时间

---

## 🎯 验收标准

### UI 升级
- [ ] 日志实时显示,无延迟
- [ ] Graph 可视化清晰,支持交互
- [ ] Token 统计准确,成本计算正确
- [ ] Blueprint Review 界面完整,支持审批

### HITL 干预
- [ ] 暂停/继续功能正常
- [ ] 状态查看和编辑功能正常
- [ ] 不影响 Agent 执行逻辑

### 导出功能
- [ ] ZIP 打包完整,可解压运行
- [ ] Dify YAML 格式正确,可导入
- [ ] README 内容完整,格式规范

---

## 🚀 下一步

完成阶段五后:
1. 进行完整的 E2E 测试
2. 编写用户文档
3. 准备 v8.0 发布
4. 收集用户反馈
5. 规划 v8.1 增强功能 (包括 MCP 集成)
