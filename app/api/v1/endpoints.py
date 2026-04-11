# API v1 - Log Analysis Endpoints
import time
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    AnalyzeLogRequest,
    AnalyzeLogResponse,
    LogStats,
    HealthResponse,
    ErrorResponse,
    ParseLogRequest,
)
from app.services.llm_service import get_llm_service
from app.services.log_parser import get_log_parser
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["Log Analysis"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="ai-log-analyzer",
        version="1.0.0",
        llm_provider=settings.llm.provider,
        timestamp=datetime.now().isoformat(),
    )


@router.post("/analyze", response_model=AnalyzeLogResponse)
async def analyze_logs(request: AnalyzeLogRequest):
    """
    Analyze Apache logs and generate an AI-based diagnosis.

    - **access_logs**: Access log lines (access.log)
    - **error_logs**: Error log lines (error.log)
    - **include_stats**: Include statistics in the response
    """
    start_time = time.time()

    try:
        # Initialize services
        llm_service = get_llm_service()
        log_parser = get_log_parser()

        # Format logs for AI processing
        formatted = log_parser.format_logs_for_ai(
            access_logs=request.access_logs,
            error_logs=request.error_logs,
            max_lines=50,
        )

        # Run AI analysis
        analysis = llm_service.analyze_apache_logs(
            access_logs=formatted["access_logs_sample"],
            error_logs=formatted["error_logs_sample"],
            context=formatted["context"],
        )

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Build response
        stats = None
        if request.include_stats:
            stats = LogStats(**formatted["summary"])

        return AnalyzeLogResponse(
            analysis=analysis,
            stats=stats,
            model_used=settings.llm.gemini.model,
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.now().isoformat(),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.post("/analyze/stream")
async def analyze_logs_stream(request: AnalyzeLogRequest):
    """
    Analyze Apache logs with streaming response (SSE).

    Returns results using Server-Sent Events.
    """
    async def generate_stream():
        import asyncio
        start_time = time.time()

        try:
            llm_service = get_llm_service()
            log_parser = get_log_parser()

            formatted = log_parser.format_logs_for_ai(
                access_logs=request.access_logs,
                error_logs=request.error_logs,
                max_lines=50,
            )

            # Format context
            context_str = f"Total requests: {formatted['summary']['total_requests']}, "
            context_str += f"Error rate: {formatted['context']['error_rate']}"

            # Yield stats first
            yield f"data: {{\"type\": \"stats\", \"data\": {formatted['summary']}}}\n\n"
            yield f"data: {{\"type\": \"status\", \"data\": \"Analyzing logs...\"}}\n\n"

            # Run AI analysis and stream the result
            analysis = llm_service.analyze_apache_logs(
                access_logs=formatted["access_logs_sample"],
                error_logs=formatted["error_logs_sample"],
                context=formatted["context"],
            )

            processing_time = round((time.time() - start_time) * 1000, 2)

            # Yield complete result
            yield f"data: {{\"type\": \"complete\", \"analysis\": {repr(analysis)}, \"processing_time_ms\": {processing_time}}}\n\n"

        except Exception as e:
            yield f"data: {{\"type\": \"error\", \"error\": {repr(str(e))}}}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/parse", response_model=Dict)
async def parse_logs_only(request: ParseLogRequest):
    """
    Parse and summarize logs only (without calling AI).

    Useful for verifying that logs are parsed correctly.
    """
    parser = get_log_parser()
    stats = parser.get_statistics(request.access_logs, request.error_logs)

    return {
        "stats": stats.to_dict(),
        "access_entries": len(parser.parse_access_log(request.access_logs)),
        "error_entries": len(parser.parse_error_log(request.error_logs)),
    }
