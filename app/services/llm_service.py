# LLM Service - Gemini Integration
import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import google.generativeai as genai
from loguru import logger

from app.core.config import settings


@dataclass
class LLMResponse:
    """LLM response container."""
    content: str
    raw_response: Optional[Any] = None
    usage: Optional[Dict[str, int]] = None


class LLMService:
    """LLM service supporting Gemini, OpenAI, Anthropic, and Ollama."""

    def __init__(self):
        self.provider = settings.llm.provider
        self._init_provider()

    def _init_provider(self):
        """Initialize provider from configuration."""
        if self.provider == "gemini":
            api_key = settings.llm.gemini.api_key
            if not api_key or api_key == "your-gemini-api-key-here":
                raise ValueError("GEMINI_API_KEY is not configured in .env")
            genai.configure(api_key=api_key)
            logger.info(f"Initialized Gemini with model: {settings.llm.gemini.model}")
        else:
            logger.warning(f"Provider {self.provider} is not fully supported yet")

    def analyze_apache_logs(
        self,
        access_logs: List[str],
        error_logs: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Analyze Apache logs and provide an incident diagnosis.

        Args:
            access_logs: Access log lines (access.log)
            error_logs: Error log lines (error.log)
            context: Additional metadata (time, tags, etc.)

        Returns:
            str: AI-generated analysis and diagnosis
        """
        if self.provider == "gemini":
            return self._analyze_with_gemini(access_logs, error_logs, context)
        else:
            raise NotImplementedError(f"Provider {self.provider} is not supported")

    def _analyze_with_gemini(
        self,
        access_logs: List[str],
        error_logs: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Analyze logs with Gemini."""
        model = genai.GenerativeModel(settings.llm.gemini.model)

        # Build detailed prompt
        prompt = self._build_analysis_prompt(access_logs, error_logs, context)

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.llm.gemini.temperature,
                    max_output_tokens=settings.llm.gemini.max_tokens,
                )
            )
            logger.info("Log analysis completed")
            return response.text
        except Exception as e:
            logger.error(f"Gemini call failed: {e}")
            raise

    def _build_analysis_prompt(
        self,
        access_logs: List[str],
        error_logs: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build prompt for log analysis."""
        prompt_parts = [
            "# Task: Analyze and diagnose Apache log issues",
            "",
            "## Requirements",
            "You are an Apache log analysis expert. Your tasks are:",
            "1. Read and analyze access logs (access.log) and error logs (error.log)",
            "2. Identify errors, warnings, and current issues",
            "3. Provide root cause analysis",
            "4. Propose concrete remediation steps",
            "5. Assess severity (Critical/High/Medium/Low)",
            "",
            "## Response format",
            "Respond in Markdown with this structure:",
            "",
            "### Summary",
            "- Number of failed requests (4xx, 5xx)",
            "- Number of warnings/errors in error.log",
            "",
            "### Error details",
            "List each issue with:",
            "- Error code (if available)",
            "- Occurrence time",
            "- Short description",
            "",
            "### Root cause",
            "Analyze the primary causes behind the issues",
            "",
            "### Recommended fixes",
            "Provide concrete remediation steps (numbered)",
            "",
            "### Severity",
            "Critical | High | Medium | Low with explanation",
            "",
            "## Access Log (first 10 lines):"
        ]

        if access_logs:
            prompt_parts.extend([f"```\n{log}\n```" for log in access_logs[:50]])
        else:
            prompt_parts.append("*No access log provided*")

        prompt_parts.extend([
            "",
            "## Error Log (first 10 lines):"
        ])

        if error_logs:
            prompt_parts.extend([f"```\n{log}\n```" for log in error_logs[:50]])
        else:
            prompt_parts.append("*No error log provided*")

        if context:
            prompt_parts.extend([
                "",
                "## Additional context:",
                f"```json\n{json.dumps(context, indent=2, default=str)}\n```"
            ])

        prompt_parts.extend([
            "",
            "---",
            "Please analyze and provide a detailed diagnosis."
        ])

        return "\n".join(prompt_parts)


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get singleton instance of the LLM service."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
