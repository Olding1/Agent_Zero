"""Execution result schema."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ExecutionStatus(str, Enum):
    """Execution status enumeration."""

    PASS = "pass"
    FAIL = "fail"
    FAILED = "failed" # Alias for FAIL
    ERROR = "error"
    TIMEOUT = "timeout"
    SUCCESS = "success"  # Alias for PASS if needed, or simply map PASS. Wait, Runner uses SUCCESS?
    SKIPPED = "skipped"


class TestResult(BaseModel):
    """Single test execution result.
    
    Contains the outcome of running one test case.
    """

    test_id: str = Field(..., description="Test case ID")
    status: ExecutionStatus = Field(..., description="Execution status")
    actual_output: Optional[str] = Field(default=None, description="Actual output")
    error_message: Optional[str] = Field(default=None, description="Error message if any")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    token_usage: Optional[int] = Field(default=None, description="Token usage count")


class ExecutionResult(BaseModel):
    """Complete execution result.
    
    Aggregates results from all test cases in a test run.
    """

    overall_status: ExecutionStatus = Field(..., description="Overall execution status")
    test_results: List[TestResult] = Field(..., description="Individual test results")
    stderr: Optional[str] = Field(default=None, description="Standard error output")
    feedback: Optional[str] = Field(
        default=None, description="Feedback for improvement"
    )
    total_token_usage: int = Field(default=0, description="Total token usage")
    executed_at: datetime = Field(
        default_factory=datetime.now, description="Execution timestamp"
    )

model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overall_status": "pass",
                "test_results": [
                    {
                        "test_id": "test_001",
                        "status": "pass",
                        "actual_output": "The net profit is 5 million with 20% growth",
                        "duration_ms": 1500,
                        "token_usage": 250,
                    }
                ],
                "total_token_usage": 250,
            }
        }
    )
