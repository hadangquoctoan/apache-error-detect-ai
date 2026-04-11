# Pydantic models for API
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AnalyzeLogRequest(BaseModel):
    """Request payload for log analysis."""
    access_logs: List[str] = Field(
        ...,
        description="List of access log lines (access.log)",
        example=[
            '127.0.0.1 - - [10/Apr/2026:10:00:00 +0700] "GET /api/users HTTP/1.1" 500 1024 "-" "Mozilla/5.0"',
            '127.0.0.1 - - [10/Apr/2026:10:01:00 +0700] "POST /api/login HTTP/1.1" 200 512 "-" "Mozilla/5.0"',
        ]
    )
    error_logs: List[str] = Field(
        default=[],
        description="List of error log lines (error.log)"
    )
    include_stats: bool = Field(
        default=True,
        description="Include statistics in the response"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for AI"
    )


class ParseLogRequest(BaseModel):
    """Request payload for log parsing only (no AI)."""
    access_logs: List[str] = Field(
        default=[],
        description="List of access log lines (access.log)"
    )
    error_logs: List[str] = Field(
        default=[],
        description="List of error log lines (error.log)"
    )


class LogStats(BaseModel):
    """Log statistics."""
    total_requests: int
    success_requests: int
    client_errors: int
    server_errors: int
    error_codes: Dict[str, int]
    top_ips: Dict[str, int]
    top_paths: Dict[str, int]
    top_error_paths: Dict[str, int]
    error_log_count: int
    warning_count: int


class AnalyzeLogResponse(BaseModel):
    """Response payload for log analysis."""
    analysis: str = Field(description="AI analysis result (Markdown)")
    stats: Optional[LogStats] = Field(
        default=None,
        description="Log statistics"
    )
    model_used: str = Field(description="AI model used")
    processing_time_ms: float = Field(description="Processing time (ms)")
    timestamp: str = Field(description="Analysis timestamp")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    llm_provider: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    timestamp: str
