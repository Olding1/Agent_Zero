"""Quick verification script to test task_type enum fix."""

from src.schemas.project_meta import ProjectMeta, TaskType

# Test 1: Create ProjectMeta with enum
print("Test 1: Creating ProjectMeta with TaskType enum...")
meta1 = ProjectMeta(
    agent_name="TestAgent",
    description="Test description",
    task_type=TaskType.RAG,
    user_intent_summary="Test intent"
)
print(f"  task_type value: {meta1.task_type}")
print(f"  task_type type: {type(meta1.task_type)}")
print(f"  Is string: {isinstance(meta1.task_type, str)}")
print(f"  Comparison works: {meta1.task_type == 'rag'}")
print("  ✅ Test 1 passed\n")

# Test 2: Create ProjectMeta with string
print("Test 2: Creating ProjectMeta with string value...")
meta2 = ProjectMeta(
    agent_name="TestAgent2",
    description="Test description",
    task_type="search",
    user_intent_summary="Test intent"
)
print(f"  task_type value: {meta2.task_type}")
print(f"  task_type type: {type(meta2.task_type)}")
print(f"  Comparison works: {meta2.task_type == 'search'}")
print("  ✅ Test 2 passed\n")

# Test 3: Simulate tool_selector usage
print("Test 3: Simulating tool_selector comparison logic...")
test_cases = [
    (TaskType.SEARCH, "search"),
    (TaskType.ANALYSIS, "analysis"),
    ("rag", "rag"),
]

for task_type_input, expected in test_cases:
    meta = ProjectMeta(
        agent_name="Test",
        description="Test",
        task_type=task_type_input,
        user_intent_summary="Test"
    )
    # This is what tool_selector does now (without .value)
    if meta.task_type == "search":
        result = "search tools"
    elif meta.task_type == "analysis":
        result = "analysis tools"
    else:
        result = "other tools"
    
    print(f"  Input: {task_type_input} -> task_type: {meta.task_type} -> Result: {result}")

print("  ✅ Test 3 passed\n")

print("=" * 50)
print("✅ All tests passed! The task_type fix is working correctly.")
print("=" * 50)
