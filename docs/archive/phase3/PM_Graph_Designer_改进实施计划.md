# Agent Zero v6.0 - PM & Graph Designer 改进实施计划

> **基于**: PM_Graph_Designer_Improved_Plan.md  
> **创建日期**: 2026-01-14  
> **目标**: 从"线性生成"转向"蓝图仿真"架构

---

## 📋 改进概述

### 核心理念变化

| 维度 | 当前状态 | 改进后 |
|------|----------|--------|
| **设计模式** | 线性生成 (Linear Translator) | 蓝图仿真 (Blueprint Simulation) |
| **PM 角色** | 单次分析 | 双脑模式 (Clarifier + Planner) |
| **Graph Designer** | 简单节点连接 | Pattern + State + Nodes |
| **验证机制** | 运行后发现问题 | 编译前沙盘推演 |
| **错误反馈** | 单一回路 | 双重反馈 (Runtime Error / Logic Error) |

### 新架构流向

```
User Input → PM Clarifier → PM Planner → Graph Designer → Simulator → User Approval → Compiler → Code
```

---

## 🔍 与现有文档的变更对比

### 1. Agent Zero项目计划书.md 需变更内容

#### 1.1 PM 节点定义变更 (第69-88行)

**现有定义**:
```markdown
#### 1. Node: PM (需求分析师)
*   **核心逻辑**: 澄清需求：如果需求模糊，生成反问句
*   **输出**: `project_meta.json`
```

**需新增**:
```markdown
#### 1. Node: PM (需求分析师) - 双脑模式

##### 1.1 PM Clarifier (澄清者)
*   **触发条件**: 信息完整度 < 80%
*   **核心逻辑**: 强制反问，形成双向澄清回路
*   **输出**: 状态字段 `status: "clarifying" | "ready"`

##### 1.2 PM Planner (规划者)
*   **触发条件**: PM Clarifier 验证通过
*   **核心逻辑**: 生成分层任务清单 (Hierarchical Planning)
*   **新增输出**: `execution_plan` 字段
```

#### 1.2 Graph Designer 节点定义变更 (第94-116行)

**现有定义**:
```markdown
#### 2. Node: Graph_Designer (图设计师)
*   **输出**: `graph_structure.json` (nodes, edges, conditional_edges)
```

**需新增**:
```markdown
#### 2. Node: Graph_Designer (图设计师) - 三步设计法

##### 2.1 Pattern Selection (模式选择)
*   **预置模式**: Sequential, Reflection, Supervisor, Plan-and-Execute

##### 2.2 State Schema Definition (状态定义)
*   **新增输出**: `state_schema` 字段 (定义节点间传递的数据结构)

##### 2.3 Nodes & Edges (节点连接)
*   **增强**: `conditional_edges` 支持 `condition_logic` 表达式
```

#### 1.3 新增 Simulator 节点 (在阶段四后新增)

```markdown
### 🟡 阶段三.五：沙盘推演 (Simulation Phase) [新增]

#### 7.5 Node: Simulator (沙盘推演)
*   **角色**: 在编译前进行逻辑验证
*   **输入**: `graph_structure.json` + `user_input`
*   **核心逻辑**:
    *   LLM 扮演 Simulator，按图结构模拟运行
    *   不生成代码，不调用 API
    *   输出推演日志，暴露死循环/逻辑错误
*   **输出**: `simulation_log.txt`
*   **交互**: Blueprint Review UI，用户验收
```

#### 1.4 Judge 节点反馈机制变更 (第229-238行)

**现有定义**:
```markdown
#### 10. Node: Judge (质检员)
*   **输出**: PASS → Git_Commit | FAIL → Compiler
```

**需变更为**:
```markdown
#### 10. Node: Judge (质检员) - 双重反馈
*   **输出**:
    *   PASS → Git_Commit
    *   FAIL (Runtime Error: 语法/依赖) → Compiler
    *   FAIL (Logic Error: 死循环/答案错误) → Graph_Designer
```

---

### 2. Agent_Zero_详细实施计划.md 需变更内容

#### 2.1 Pydantic Schema 变更

##### 新增 `src/schemas/state_schema.py`

```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from enum import Enum

class StateFieldType(str, Enum):
    STRING = "str"
    INT = "int"
    BOOL = "bool"
    LIST_MESSAGE = "List[BaseMessage]"
    LIST_STR = "List[str]"
    DICT = "Dict[str, Any]"

class StateField(BaseModel):
    """状态字段定义"""
    name: str = Field(..., description="字段名")
    type: StateFieldType = Field(..., description="字段类型")
    description: Optional[str] = Field(None, description="字段说明")
    default: Optional[Any] = Field(None, description="默认值")

class StateSchema(BaseModel):
    """完整状态定义"""
    fields: List[StateField] = Field(..., description="状态字段列表")
```

##### 新增 `src/schemas/pattern.py`

```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List

class PatternType(str, Enum):
    SEQUENTIAL = "sequential"      # A -> B -> C
    REFLECTION = "reflection"      # Generate <-> Critique
    SUPERVISOR = "supervisor"      # Manager -> [Workers] -> Manager
    PLAN_EXECUTE = "plan_execute"  # Planner -> Executor -> Replanner
    CUSTOM = "custom"

class PatternConfig(BaseModel):
    """设计模式配置"""
    pattern_type: PatternType = Field(..., description="模式类型")
    max_iterations: int = Field(default=3, ge=1, le=10, description="最大循环次数")
    termination_condition: Optional[str] = Field(None, description="终止条件表达式")
```

##### 修改 `src/schemas/graph_structure.py`

```python
# 新增字段
class ConditionalEdgeDef(BaseModel):
    source: str
    condition: str = Field(..., description="条件函数名")
    condition_logic: Optional[str] = Field(None, description="条件逻辑表达式")  # 新增
    branches: Dict[str, str]

class GraphStructure(BaseModel):
    pattern: PatternConfig = Field(..., description="设计模式")          # 新增
    state_schema: StateSchema = Field(..., description="状态定义")       # 新增
    nodes: List[NodeDef]
    edges: List[EdgeDef]
    conditional_edges: List[ConditionalEdgeDef]
    entry_point: str = Field(default="agent")
```

##### 修改 `src/schemas/project_meta.py`

```python
class ExecutionStep(BaseModel):
    """执行计划步骤"""
    step: int = Field(..., description="步骤序号")
    role: str = Field(..., description="角色名称")
    goal: str = Field(..., description="步骤目标")
    expected_output: Optional[str] = Field(None, description="预期输出")

class ProjectMeta(BaseModel):
    # ... 现有字段 ...
    status: Literal["clarifying", "ready"] = Field(default="ready")  # 新增
    execution_plan: Optional[List[ExecutionStep]] = Field(None)       # 新增
    complexity_score: int = Field(default=1, ge=1, le=10)             # 新增
```

#### 2.2 核心模块变更

##### 修改 `src/core/pm.py` - 双脑模式

```python
class PMAnalyzer:
    async def clarify_requirements(
        self, 
        user_query: str,
        chat_history: List[Dict]
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        澄清者角色：检查需求完整度
        
        Returns:
            (is_ready, clarification_questions)
        """
        pass
    
    async def create_execution_plan(
        self,
        project_meta: ProjectMeta
    ) -> List[ExecutionStep]:
        """
        规划者角色：生成分层任务清单
        """
        pass
    
    async def analyze_with_clarification_loop(
        self,
        user_query: str,
        chat_history: List[Dict],
        file_paths: Optional[List[str]] = None
    ) -> ProjectMeta:
        """
        完整的双脑模式分析流程
        """
        pass
```

##### 修改 `src/core/graph_designer.py` - 三步设计法

```python
class GraphDesigner:
    def __init__(self):
        self.pattern_templates = self._load_pattern_templates()
    
    async def select_pattern(
        self,
        project_meta: ProjectMeta
    ) -> PatternConfig:
        """Step 1: 选择设计模式"""
        pass
    
    async def define_state_schema(
        self,
        project_meta: ProjectMeta,
        pattern: PatternConfig
    ) -> StateSchema:
        """Step 2: 定义状态结构"""
        pass
    
    async def design_nodes_and_edges(
        self,
        project_meta: ProjectMeta,
        pattern: PatternConfig,
        state_schema: StateSchema,
        tools_config: Optional[ToolsConfig] = None,
        rag_config: Optional[RAGConfig] = None
    ) -> GraphStructure:
        """Step 3: 设计节点和边"""
        pass
    
    async def design_graph(
        self,
        project_meta: ProjectMeta,
        tools_config: Optional[ToolsConfig] = None,
        rag_config: Optional[RAGConfig] = None
    ) -> GraphStructure:
        """完整的三步设计流程"""
        pattern = await self.select_pattern(project_meta)
        state_schema = await self.define_state_schema(project_meta, pattern)
        graph = await self.design_nodes_and_edges(
            project_meta, pattern, state_schema, tools_config, rag_config
        )
        return graph
```

##### 新增 `src/core/simulator.py` - 沙盘推演

```python
class Simulator:
    """沙盘推演器 - 在编译前验证图结构逻辑"""
    
    def __init__(self, llm_client: BuilderClient):
        self.llm = llm_client
    
    async def simulate(
        self,
        graph: GraphStructure,
        sample_input: str,
        max_steps: int = 20
    ) -> SimulationResult:
        """
        模拟执行图结构
        
        Args:
            graph: 图结构定义
            sample_input: 示例用户输入
            max_steps: 最大步骤数（防止死循环）
        
        Returns:
            SimulationResult: 包含推演日志和问题检测
        """
        pass
    
    def detect_issues(
        self,
        simulation_log: List[SimulationStep]
    ) -> List[SimulationIssue]:
        """检测推演中的问题（死循环、unreachable节点等）"""
        pass
    
    def generate_mermaid_trace(
        self,
        simulation_log: List[SimulationStep]
    ) -> str:
        """生成推演轨迹的 Mermaid 图"""
        pass
```

##### 修改 `src/core/judge.py` - 双重反馈

```python
class ErrorType(str, Enum):
    RUNTIME = "runtime"   # 语法错误、依赖缺失
    LOGIC = "logic"       # 死循环、答案错误
    TIMEOUT = "timeout"   # 执行超时
    API = "api"           # API 连接问题

class JudgeFeedback(BaseModel):
    status: ExecutionStatus
    error_type: Optional[ErrorType] = None
    feedback: str
    suggested_fix_target: Literal["compiler", "graph_designer", "none"]

class Judge:
    def classify_error(self, stderr: str, test_results: List[TestResult]) -> ErrorType:
        """分类错误类型"""
        pass
    
    def determine_fix_target(self, error_type: ErrorType) -> str:
        """确定修复目标"""
        if error_type == ErrorType.RUNTIME:
            return "compiler"
        elif error_type == ErrorType.LOGIC:
            return "graph_designer"
        else:
            return "none"
```

#### 2.3 模板变更

##### 修改 `src/templates/agent_template.py.j2`

```jinja2
{# 新增: 状态定义渲染 #}
{% if state_schema %}
from typing import TypedDict, List, Optional, Annotated
from langgraph.graph import add_messages

class AgentState(TypedDict):
{% for field in state_schema.fields %}
    {{ field.name }}: {{ field.type }}{% if field.description %}  # {{ field.description }}{% endif %}
{% endfor %}
{% endif %}

{# 新增: 条件逻辑函数渲染 #}
{% for edge in conditional_edges %}
{% if edge.condition_logic %}
def {{ edge.condition }}(state: AgentState) -> str:
    """Auto-generated condition function"""
    {{ edge.condition_logic | indent(4) }}
{% endif %}
{% endfor %}
```

---

## 📅 实施路线图

### Phase 1: Schema 层改造 (Week 1, Day 1-2)

| 任务 | 文件 | 优先级 | 预估时间 |
|------|------|--------|----------|
| 新建 StateSchema 模型 | `src/schemas/state_schema.py` | ⭐⭐⭐ | 2h |
| 新建 PatternConfig 模型 | `src/schemas/pattern.py` | ⭐⭐⭐ | 2h |
| 修改 GraphStructure 模型 | `src/schemas/graph_structure.py` | ⭐⭐⭐ | 2h |
| 修改 ProjectMeta 模型 | `src/schemas/project_meta.py` | ⭐⭐⭐ | 1h |
| 新建 SimulationResult 模型 | `src/schemas/simulation.py` | ⭐⭐ | 1h |
| 编写 Schema 单元测试 | `tests/unit/test_schemas_v2.py` | ⭐⭐ | 2h |

### Phase 2: PM 双脑模式 (Week 1, Day 3-4)

| 任务 | 文件 | 优先级 | 预估时间 |
|------|------|--------|----------|
| 实现 PM Clarifier | `src/core/pm.py` | ⭐⭐⭐ | 3h |
| 实现 PM Planner | `src/core/pm.py` | ⭐⭐⭐ | 3h |
| 设计澄清 Prompt | `src/prompts/pm_clarifier.txt` | ⭐⭐ | 1h |
| 设计规划 Prompt | `src/prompts/pm_planner.txt` | ⭐⭐ | 1h |
| 编写 PM 单元测试 | `tests/unit/test_pm_v2.py` | ⭐⭐ | 2h |

### Phase 3: Graph Designer 三步法 (Week 1, Day 5 - Week 2, Day 2)

| 任务 | 文件 | 优先级 | 预估时间 |
|------|------|--------|----------|
| 创建模式模板库 | `config/patterns/` | ⭐⭐⭐ | 3h |
| 实现 Pattern Selector | `src/core/graph_designer.py` | ⭐⭐⭐ | 3h |
| 实现 State Schema Generator | `src/core/graph_designer.py` | ⭐⭐⭐ | 4h |
| 实现增强的 Node/Edge 设计 | `src/core/graph_designer.py` | ⭐⭐⭐ | 4h |
| 编写 Graph Designer 测试 | `tests/unit/test_graph_designer_v2.py` | ⭐⭐ | 3h |

### Phase 4: Simulator 沙盘推演 (Week 2, Day 3-4)

| 任务 | 文件 | 优先级 | 预估时间 |
|------|------|--------|----------|
| 实现 Simulator 核心逻辑 | `src/core/simulator.py` | ⭐⭐⭐ | 5h |
| 实现问题检测算法 | `src/core/simulator.py` | ⭐⭐⭐ | 3h |
| 实现 Mermaid 轨迹生成 | `src/core/simulator.py` | ⭐⭐ | 2h |
| 设计 Simulator Prompt | `src/prompts/simulator.txt` | ⭐⭐ | 1h |
| 编写 Simulator 测试 | `tests/unit/test_simulator.py` | ⭐⭐ | 2h |

### Phase 5: Compiler 模板升级 (Week 2, Day 5 - Week 3, Day 1)

| 任务 | 文件 | 优先级 | 预估时间 |
|------|------|--------|----------|
| 添加 TypedDict 渲染 | `src/templates/agent_template.py.j2` | ⭐⭐⭐ | 3h |
| 添加条件函数渲染 | `src/templates/agent_template.py.j2` | ⭐⭐⭐ | 3h |
| 添加模式特定代码块 | `src/templates/patterns/*.j2` | ⭐⭐ | 4h |
| 修改 Compiler 逻辑 | `src/core/compiler.py` | ⭐⭐⭐ | 3h |
| 编写渲染测试 | `tests/unit/test_compiler_v2.py` | ⭐⭐ | 2h |

### Phase 6: Judge 双重反馈 (Week 3, Day 2-3)

| 任务 | 文件 | 优先级 | 预估时间 |
|------|------|--------|----------|
| 实现错误分类器 | `src/core/judge.py` | ⭐⭐⭐ | 3h |
| 实现反馈路由 | `src/core/judge.py` | ⭐⭐⭐ | 2h |
| 修改反馈回路逻辑 | `src/core/orchestrator.py` | ⭐⭐ | 3h |
| 编写 Judge 测试 | `tests/unit/test_judge_v2.py` | ⭐⭐ | 2h |

### Phase 7: E2E 测试与集成 (Week 3, Day 4-5)

| 任务 | 文件 | 优先级 | 预估时间 |
|------|------|--------|----------|
| E2E: 简单顺序模式测试 | `tests/e2e/test_sequential_pattern.py` | ⭐⭐⭐ | 3h |
| E2E: 反思模式测试 | `tests/e2e/test_reflection_pattern.py` | ⭐⭐⭐ | 3h |
| E2E: 完整仿真流程测试 | `tests/e2e/test_simulation_flow.py` | ⭐⭐⭐ | 4h |
| 更新项目文档 | `docs/`, `README.md` | ⭐⭐ | 2h |

---

## 📁 新增/修改文件清单

### 新增文件

```
src/
├── schemas/
│   ├── state_schema.py        # [NEW] 状态定义模型
│   ├── pattern.py             # [NEW] 设计模式模型
│   └── simulation.py          # [NEW] 仿真结果模型
├── core/
│   ├── simulator.py           # [NEW] 沙盘推演器
│   └── orchestrator.py        # [NEW] 流程编排器
├── prompts/
│   ├── pm_clarifier.txt       # [NEW] 澄清 Prompt
│   ├── pm_planner.txt         # [NEW] 规划 Prompt
│   └── simulator.txt          # [NEW] 仿真 Prompt
└── templates/
    └── patterns/              # [NEW] 模式模板库
        ├── sequential.j2
        ├── reflection.j2
        ├── supervisor.j2
        └── plan_execute.j2

config/
└── patterns/                  # [NEW] 模式配置
    ├── sequential.yaml
    ├── reflection.yaml
    ├── supervisor.yaml
    └── plan_execute.yaml

tests/
├── unit/
│   ├── test_schemas_v2.py     # [NEW]
│   ├── test_pm_v2.py          # [NEW]
│   ├── test_graph_designer_v2.py  # [NEW]
│   ├── test_simulator.py      # [NEW]
│   ├── test_compiler_v2.py    # [NEW]
│   └── test_judge_v2.py       # [NEW]
└── e2e/
    ├── test_sequential_pattern.py  # [NEW]
    ├── test_reflection_pattern.py  # [NEW]
    └── test_simulation_flow.py     # [NEW]
```

### 修改文件

```
src/
├── schemas/
│   ├── graph_structure.py     # [MODIFY] 添加 pattern, state_schema
│   └── project_meta.py        # [MODIFY] 添加 status, execution_plan
├── core/
│   ├── pm.py                  # [MODIFY] 双脑模式
│   ├── graph_designer.py      # [MODIFY] 三步设计法
│   ├── compiler.py            # [MODIFY] 支持新模板
│   └── judge.py               # [MODIFY] 双重反馈
└── templates/
    └── agent_template.py.j2   # [MODIFY] TypedDict + 条件函数

Agent Zero项目计划书.md        # [MODIFY] 更新架构说明
Agent_Zero_详细实施计划.md     # [MODIFY] 更新实施任务
```

---

## ✅ 验证计划

### 1. 单元测试

```bash
# 运行所有新增的单元测试
pytest tests/unit/test_schemas_v2.py -v
pytest tests/unit/test_pm_v2.py -v
pytest tests/unit/test_graph_designer_v2.py -v
pytest tests/unit/test_simulator.py -v
pytest tests/unit/test_compiler_v2.py -v
pytest tests/unit/test_judge_v2.py -v
```

### 2. 集成测试

```bash
# 测试完整改进流程
pytest tests/e2e/test_sequential_pattern.py -v
pytest tests/e2e/test_reflection_pattern.py -v
pytest tests/e2e/test_simulation_flow.py -v
```

### 3. 手动验证场景

| 场景 | 输入 | 预期行为 |
|------|------|----------|
| 需求澄清 | "帮我写个爬虫" | PM 返回 status="clarifying" + 2-3个反问 |
| 复杂任务规划 | "写一个贪吃蛇游戏" | PM 生成 4+ 步骤的 execution_plan |
| 模式选择 | 包含"审核"关键词的需求 | Graph Designer 选择 Reflection 模式 |
| 状态定义 | 任何循环任务 | 生成包含 retry_count 的 state_schema |
| 沙盘推演 | 包含条件分支的图 | Simulator 输出完整推演日志 |
| 错误分类 | ImportError | Judge 返回 "compiler" 作为修复目标 |
| 逻辑错误 | 死循环检测 | Judge 返回 "graph_designer" 作为修复目标 |

---

## 🎯 预期收益

1. **减少调试成本**: 沙盘推演在编码前发现 80%+ 的架构问题
2. **支持复杂任务**: 通过 Pattern + State 支持循环、反思、多角色协作
3. **提升用户体验**: 双向澄清回路避免"瞎猜需求"
4. **精准错误修复**: 双重反馈机制将错误路由到正确的修复模块

---

## ⚠️ 风险与应对

| 风险 | 严重级 | 应对策略 |
|------|--------|----------|
| Simulator 推演不准确 | 🔥🔥 | 使用强模型 (GPT-4) + 详细 Prompt |
| 模式模板过于僵化 | 🔥 | 支持 CUSTOM 模式，允许完全自定义 |
| 状态定义过于复杂 | 🔥 | 提供"快速模式"，自动生成基础状态 |
| 向后兼容问题 | 🔥🔥 | Schema 使用 Optional 字段，保持旧格式可用 |

---

## 📝 下一步行动

1. **立即**: 确认此实施计划
2. **Week 1**: 完成 Schema 层改造 + PM 双脑模式
3. **Week 2**: 完成 Graph Designer + Simulator
4. **Week 3**: 完成 Compiler + Judge + E2E 测试
