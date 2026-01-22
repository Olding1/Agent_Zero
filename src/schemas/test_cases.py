"""Test cases schema."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum


class TestType(str, Enum):
    """Type of test case."""

    FACT_BASED = "fact_based"
    LOGIC_BASED = "logic_based"
    BOUNDARY = "boundary"


class TestCase(BaseModel):
    """Single test case definition.
    
    Represents one test scenario for validating agent behavior.
    """

    id: str = Field(..., description="Test case ID")
    type: TestType = Field(..., description="Test type")
    input: str = Field(..., description="Input content")
    expected_keywords: Optional[List[str]] = Field(
        default=None, description="Expected keywords in output"
    )
    expected_tone: Optional[str] = Field(
        default=None, description="Expected tone (e.g., 'friendly', 'professional')"
    )
    expected_not_contain: Optional[List[str]] = Field(
        default=None, description="Content that should not appear in output"
    )
    timeout_seconds: int = Field(default=30, description="Timeout in seconds")


class TestSuite(BaseModel):
    """Test suite containing multiple test cases.
    
    Groups related test cases together.
    """

    cases: List[TestCase] = Field(..., description="List of test cases")

model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cases": [
                    {
                        "id": "test_001",
                        "type": "fact_based",
                        "input": "What is the net profit mentioned in the report?",
                        "expected_keywords": ["5 million", "growth"],
                        "timeout_seconds": 30,
                    },
                    {
                        "id": "test_002",
                        "type": "logic_based",
                        "input": "Hello",
                        "expected_tone": "friendly",
                        "timeout_seconds": 30,
                    },
                ]
            }
        }
    )
