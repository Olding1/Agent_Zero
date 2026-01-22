"""
Unit tests for new Phase 3 schemas.

Tests PatternConfig, StateSchema, and SimulationResult models.
"""

import pytest
from datetime import datetime
from src.schemas import (
    PatternConfig,
    PatternType,
    StateSchema,
    StateField,
    StateFieldType,
    SimulationResult,
    SimulationStep,
    SimulationIssue,
    SimulationStepType,
    ProjectMeta,
    ExecutionStep,
    GraphStructure,
    NodeDef,
    EdgeDef,
    ConditionalEdgeDef,
)


class TestPatternConfig:
    """Test PatternConfig model."""

    def test_pattern_config_creation(self):
        """Test creating a PatternConfig."""
        pattern = PatternConfig(
            pattern_type=PatternType.REFLECTION,
            max_iterations=3,
            termination_condition="is_finished == True",
            description="Reflection pattern for iterative improvement",
        )

        assert pattern.pattern_type == PatternType.REFLECTION
        assert pattern.max_iterations == 3
        assert pattern.termination_condition == "is_finished == True"

    def test_pattern_config_defaults(self):
        """Test PatternConfig default values."""
        pattern = PatternConfig(pattern_type=PatternType.SEQUENTIAL)

        assert pattern.max_iterations == 3
        assert pattern.termination_condition is None
        assert pattern.description == ""

    def test_pattern_config_validation(self):
        """Test PatternConfig validation."""
        # max_iterations must be between 1 and 10
        with pytest.raises(ValueError):
            PatternConfig(pattern_type=PatternType.SEQUENTIAL, max_iterations=0)

        with pytest.raises(ValueError):
            PatternConfig(pattern_type=PatternType.SEQUENTIAL, max_iterations=11)


class TestStateSchema:
    """Test StateSchema model."""

    def test_state_schema_creation(self):
        """Test creating a StateSchema."""
        schema = StateSchema(
            fields=[
                StateField(
                    name="messages",
                    type=StateFieldType.LIST_MESSAGE,
                    description="Chat history",
                    reducer="add_messages",
                ),
                StateField(
                    name="iteration_count", type=StateFieldType.INT, default=0
                ),
                StateField(
                    name="is_finished", type=StateFieldType.BOOL, default=False
                ),
            ]
        )

        assert len(schema.fields) == 3
        assert schema.has_field("messages")
        assert schema.has_field("iteration_count")
        assert schema.has_field("is_finished")

    def test_state_schema_get_field(self):
        """Test getting a field from StateSchema."""
        schema = StateSchema(
            fields=[
                StateField(name="draft", type=StateFieldType.STRING, default=""),
            ]
        )

        field = schema.get_field("draft")
        assert field is not None
        assert field.name == "draft"
        assert field.type == StateFieldType.STRING

        assert schema.get_field("nonexistent") is None

    def test_state_schema_validation(self):
        """Test StateSchema validation."""
        # Must have at least one field
        with pytest.raises(ValueError):
            StateSchema(fields=[])


class TestSimulationResult:
    """Test SimulationResult model."""

    def test_simulation_result_creation(self):
        """Test creating a SimulationResult."""
        steps = [
            SimulationStep(
                step_number=1,
                step_type=SimulationStepType.ENTER_NODE,
                node_id="generator",
                description="Enter generator node",
                state_snapshot={"iteration_count": 0},
            ),
            SimulationStep(
                step_number=2,
                step_type=SimulationStepType.EXIT_NODE,
                node_id="generator",
                description="Exit generator node",
                state_snapshot={"iteration_count": 0, "draft": "Hello"},
            ),
        ]

        result = SimulationResult(
            success=True,
            total_steps=2,
            steps=steps,
            issues=[],
            final_state={"is_finished": True},
            execution_trace="Step 1: Enter generator\nStep 2: Exit generator",
        )

        assert result.success is True
        assert result.total_steps == 2
        assert len(result.steps) == 2
        assert result.has_errors() is False
        assert result.has_warnings() is False

    def test_simulation_result_with_issues(self):
        """Test SimulationResult with issues."""
        issues = [
            SimulationIssue(
                issue_type="infinite_loop",
                severity="error",
                description="Detected infinite loop",
                affected_nodes=["generator", "critic"],
                suggestion="Add iteration_count check",
            ),
            SimulationIssue(
                issue_type="unreachable_node",
                severity="warning",
                description="Node never visited",
                affected_nodes=["unused_node"],
            ),
        ]

        result = SimulationResult(
            success=False,
            total_steps=10,
            steps=[],
            issues=issues,
            execution_trace="Simulation failed due to infinite loop",
        )

        assert result.success is False
        assert result.has_errors() is True
        assert result.has_warnings() is True
        assert len(result.get_issues_by_type("infinite_loop")) == 1
        assert len(result.get_issues_by_type("unreachable_node")) == 1


class TestProjectMetaExtensions:
    """Test ProjectMeta extensions for PM dual-brain mode."""

    def test_project_meta_with_execution_plan(self):
        """Test ProjectMeta with execution plan."""
        plan = [
            ExecutionStep(
                step=1, role="Architect", goal="Design system architecture"
            ),
            ExecutionStep(step=2, role="Coder", goal="Implement core logic"),
            ExecutionStep(step=3, role="Tester", goal="Write and run tests"),
        ]

        meta = ProjectMeta(
            agent_name="TestAgent",
            description="Test agent",
            user_intent_summary="Build a test agent",
            status="ready",
            complexity_score=7,
            execution_plan=plan,
        )

        assert meta.status == "ready"
        assert meta.complexity_score == 7
        assert len(meta.execution_plan) == 3
        assert meta.execution_plan[0].role == "Architect"

    def test_project_meta_clarifying_status(self):
        """Test ProjectMeta with clarifying status."""
        meta = ProjectMeta(
            agent_name="TestAgent",
            description="Test agent",
            user_intent_summary="Build something",
            status="clarifying",
            clarification_questions=[
                "What should the agent do?",
                "What data sources are needed?",
            ],
        )

        assert meta.status == "clarifying"
        assert len(meta.clarification_questions) == 2


class TestGraphStructureExtensions:
    """Test GraphStructure extensions for three-step design."""

    def test_graph_structure_with_pattern_and_state(self):
        """Test GraphStructure with pattern and state schema."""
        pattern = PatternConfig(
            pattern_type=PatternType.REFLECTION, max_iterations=3
        )

        state_schema = StateSchema(
            fields=[
                StateField(
                    name="messages", type=StateFieldType.LIST_MESSAGE, reducer="add_messages"
                ),
                StateField(name="draft", type=StateFieldType.STRING, default=""),
                StateField(
                    name="iteration_count", type=StateFieldType.INT, default=0
                ),
            ]
        )

        graph = GraphStructure(
            pattern=pattern,
            state_schema=state_schema,
            nodes=[
                NodeDef(
                    id="generator",
                    type="llm",
                    role_description="Generate initial content",
                ),
                NodeDef(id="critic", type="llm", role_description="Review content"),
            ],
            edges=[EdgeDef(source="generator", target="critic")],
            conditional_edges=[
                ConditionalEdgeDef(
                    source="critic",
                    condition="should_continue",
                    condition_logic="if state['iteration_count'] < 3: return 'generator'\nelse: return 'end'",
                    branches={"generator": "generator", "end": "END"},
                )
            ],
            entry_point="generator",
        )

        assert graph.pattern.pattern_type == PatternType.REFLECTION
        assert len(graph.state_schema.fields) == 3
        assert graph.nodes[0].role_description == "Generate initial content"
        assert graph.conditional_edges[0].condition_logic is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
