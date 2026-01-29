# 无限循环问题修复方案

## 问题诊断

### 根本原因
Sequential Pattern 在使用工具时会陷入无限循环:
```
Agent → Tool → Agent → Tool → Agent → ...
```

原因:
1. LLM 在模拟时总是生成 `tool_calls`
2. 没有机制让 Agent 停止调用工具并返回最终答案

### 当前优化器的问题
`GraphDesigner.fix_logic()` 生成的 condition_logic 缺少 `return` 语句:
```python
# ❌ 错误: 只是表达式,没有返回值
state['iteration_count'] < state['max_iterations']

# ✅ 正确: 需要返回分支 key
return 'true' if state['iteration_count'] < state['max_iterations'] else 'false'
```

---

## 修复方案

### 方案 A: 修复 `fix_logic` Prompt (推荐)

**文件**: `src/core/graph_designer.py:838-876`

**修改**: 在 prompt 中添加明确的 `condition_logic` 规范

```python
prompt = f\"\"\"# Graph Repair Task

## Current Graph
Pattern: {current_graph.pattern.pattern_type}
Nodes: {', '.join(n.id for n in current_graph.nodes)}

## Issues Detected
{issues_desc}

## Requirement
Please fix the graph structure based on the issues above.
Focus on:
1. Breaking infinite loops (e.g., adding iteration limits)
2. Connecting unreachable nodes
3. Fixing logic errors in conditional edges

## CRITICAL CONSTRAINTS

### 1. Node Targets - Use 'END' for termination
All edge targets MUST be either:
- Actual node IDs from the nodes list above
- The special node \"END\" (all caps) to terminate the workflow

### 2. Condition Logic - MUST return a value
**CRITICAL**: condition_logic MUST contain a return statement!

Examples:
✅ CORRECT:
```python
return 'true' if state['count'] < 5 else 'false'
```

✅ CORRECT:
```python
if state['messages'][-1].tool_calls:
    return state['messages'][-1].tool_calls[0]['name']
return 'end'
```

❌ WRONG (no return):
```python
state['count'] < 5  # This is just an expression!
```

### 3. Prevent Infinite Loops
For tool-calling patterns, ensure the agent can STOP calling tools:
- Add iteration counters with max limits
- OR check if tool results are sufficient
- OR add explicit "done" conditions

Example for Sequential + Tools:
```python
# Add state fields
{
  "name": "tool_call_count",
  "type": "int",
  "default": 0
}

# Condition logic
if state['tool_call_count'] >= 2:  # Max 2 tool calls
    return 'end'
if state['messages'][-1].tool_calls:
    return state['messages'][-1].tool_calls[0]['name']
return 'end'
```

Return the full updated GraphStructure JSON.
\"\"\"
```

### 方案 B: 修改 Sequential Pattern 默认逻辑

**文件**: `src/core/graph_designer.py:384-401`

**当前问题**: 默认逻辑允许无限调用工具

**修改**: 添加工具调用计数限制

```python
# 🔗 Fallback for Sequential Pattern
if not default_cond_edges and pattern.pattern_type == PatternType.SEQUENTIAL:
    print("🔧 [GraphDesigner] Using hardcoded fallback for Sequential Conditional Edges")
    
    # 🆕 添加 tool_call_count 状态字段
    # (需要在 _get_pattern_state_fields 中添加)
    
    default_cond_edges = [{
        "source": "agent",
        "condition": "should_continue",
        "condition_logic": \"\"\"
# 🆕 防止无限循环: 最多调用工具 2 次
tool_call_count = state.get('tool_call_count', 0)
if tool_call_count >= 2:
    return 'end'

# 检查是否需要调用工具
last_msg = state.get("messages", [])[-1] if state.get("messages") else None
if last_msg and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
    # 增加计数
    state['tool_call_count'] = tool_call_count + 1
    return last_msg.tool_calls[0]["name"]
return "end"
\"\"\",
        "branches": {
            "continue": "tools",  # Placeholder
            "end": "END"
        }
    }]
```

**同时在 `_get_pattern_state_fields` 中添加**:

```python
def _get_pattern_state_fields(self, pattern: PatternConfig) -> List[StateField]:
    \"\"\"Get pattern-specific state fields.\"\"\"
    fields = []
    
    if pattern.pattern_type == PatternType.SEQUENTIAL:
        # 🆕 添加工具调用计数
        fields.append(
            StateField(
                name="tool_call_count",
                type=StateFieldType.INT,
                default=0,
                description="工具调用次数计数器"
            )
        )
    
    # ... 其他 pattern 的字段
```

### 方案 C: 改进 LLM Prompt (治标)

**文件**: `src/core/simulator.py:215-270`

**修改**: 让 LLM 知道何时停止调用工具

```python
prompt = f\"\"\"You are simulating an LLM node in a LangGraph agent.

Node: {node_def.id}
Role: {role_desc}
Current State: {self._format_state_for_llm(state)}

User Input: {sample_input}
{tools_context}

**Task**: Generate the LLM's output (NOT routing decision).

**IMPORTANT**: You should NOT call tools repeatedly!
- If you have already called a tool and received results, generate a FINAL ANSWER
- Only call tools if you truly need NEW information
- Check state['messages'] to see if tools were already called

Output JSON:
{{
    "content": "your response message",
    "tool_calls": [  // ONLY if you NEED to call a tool
        {{"name": "exact_tool_name", "args": {{}}}}
    ]
}}

**Critical Rules**:
1. If you see tool results in previous messages, DO NOT call tools again - generate final answer
2. If user asks to search/find/query AND no tool was called yet, include tool_calls
3. Use EXACT tool name from available tools: {available_tools}
4. If no tool needed OR tool already called, omit tool_calls or set to []
\"\"\"
```

---

## 推荐实施顺序

1. **立即**: 实施方案 B (修改 Sequential Pattern 默认逻辑)
   - 添加 `tool_call_count` 状态字段
   - 更新 condition_logic 检查计数

2. **短期**: 实施方案 A (修复 `fix_logic` Prompt)
   - 确保优化器生成的 condition_logic 有 return 语句
   - 添加防无限循环的指导

3. **可选**: 实施方案 C (改进 LLM Prompt)
   - 让 LLM 更智能地决定何时停止

---

## 验证方法

修复后,运行相同的测试:
```bash
python start.py
# 选择 1, 输入相同的 Agent 描述
```

**预期结果**:
```
✅ 仿真通过
问题数: 0
```

**执行流程**:
```
Agent (生成 tool_calls) 
  → Tool (执行搜索)
  → Agent (tool_call_count=1, 生成 tool_calls)
  → Tool (执行搜索)
  → Agent (tool_call_count=2, 达到上限)
  → END
```
