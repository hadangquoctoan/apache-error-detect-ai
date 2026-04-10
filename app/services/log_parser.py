# Apache Log Parser - Apache log analysis
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from collections import Counter


@dataclass
class AccessLogEntry:
    """One Apache access log entry."""
    ip: str
    timestamp: Optional[str] = None
    method: str = ""
    path: str = ""
    status: int = 0
    size: int = 0
    referrer: str = ""
    user_agent: str = ""
    raw_line: str = ""

    @property
    def is_error(self) -> bool:
        """Check whether entry is an error (4xx, 5xx)."""
        return 400 <= self.status < 600

    @property
    def severity(self) -> str:
        """Severity level based on HTTP status."""
        if self.status >= 500:
            return "CRITICAL"
        elif self.status >= 400:
            return "WARNING"
        return "INFO"


@dataclass
class ErrorLogEntry:
    """One Apache error log entry."""
    timestamp: Optional[str] = None
    level: str = ""
    pid: str = ""
    client: str = ""
    code: str = ""
    message: str = ""
    raw_line: str = ""

    @property
    def severity(self) -> str:
        """Severity level based on Apache error code and level."""
        level_lower = (self.level or "").lower()
        critical_codes = ["00124", "00130", "00012", "00087"]
        if self.code in critical_codes:
            return "CRITICAL"
        if any(token in level_lower for token in ["emerg", "alert", "crit", "error"]):
            return "CRITICAL"
        if self.code or any(token in level_lower for token in ["warn", "notice"]):
            return "WARNING"
        return "INFO"


@dataclass
class ApacheLogStats:
    """Apache log statistics."""
    total_requests: int = 0
    success_requests: int = 0
    client_errors: int = 0  # 4xx
    server_errors: int = 0  # 5xx
    error_codes: Counter = field(default_factory=Counter)
    top_ips: Counter = field(default_factory=Counter)
    top_paths: Counter = field(default_factory=Counter)
    top_error_paths: Counter = field(default_factory=Counter)
    error_log_count: int = 0
    warning_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to a JSON-serializable dict."""
        return {
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "client_errors": self.client_errors,
            "server_errors": self.server_errors,
            "error_codes": dict(self.error_codes),
            "top_ips": dict(self.top_ips.most_common(10)),
            "top_paths": dict(self.top_paths.most_common(10)),
            "top_error_paths": dict(self.top_error_paths.most_common(10)),
            "error_log_count": self.error_log_count,
            "warning_count": self.warning_count,
        }


class ApacheLogParser:
    """Apache log parser."""

    # Pattern for Apache Combined Log Format
    ACCESS_LOG_PATTERN = re.compile(
        r'^(?P<ip>\S+)\s+\S+\s+\S+\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<method>\S+)\s+(?P<path>\S+)\s+\S+"\s+'
        r'(?P<status>\d+)\s+'
        r'(?P<size>\d+|-)\s+'
        r'"(?P<referrer>[^"]*)"\s+'
        r'"(?P<user_agent>[^"]*)"$'
    )

    # Pattern for Apache Error Log Format
    ERROR_LOG_PATTERN = re.compile(
        r'^\[(?P<timestamp>[^\]]+)\]\s+'
        r'\[(?P<level>[^\]]+)\]\s+'
        r'(?:\[pid\s+(?P<pid>[^\]]+)\]\s+)?'
        r'(?:\[client\s+(?P<client>[^\]]+)\]\s+)?'
        r'(?P<message>.*)'
    )

    # Common Apache error codes
    APACHE_ERROR_CODES = {
        "00124": "Request exceeded the limit of internal redirects",
        "00130": "Handler for (null) returned invalid result",
        "00101": "Digest: generate secret failed",
        "00087": "Could not open password file",
        "00012": "PID file not created",
        "00018": "Select pipe in filter failed",
    }

    def parse_access_log(self, lines: List[str]) -> List[AccessLogEntry]:
        """Parse access logs."""
        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            match = self.ACCESS_LOG_PATTERN.match(line)
            if match:
                size_value = match.group("size")
                entries.append(AccessLogEntry(
                    ip=match.group("ip"),
                    timestamp=match.group("timestamp"),
                    method=match.group("method"),
                    path=match.group("path"),
                    status=int(match.group("status")),
                    size=0 if size_value == "-" else int(size_value),
                    referrer=match.group("referrer"),
                    user_agent=match.group("user_agent"),
                    raw_line=line,
                ))
        return entries

    def parse_error_log(self, lines: List[str]) -> List[ErrorLogEntry]:
        """Parse error logs."""
        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try full error log pattern
            match = self.ERROR_LOG_PATTERN.match(line)
            if match:
                raw_level = match.group("level") or ""
                level = raw_level.split(":")[-1].lower()
                message = match.group("message") or ""
                ah_match = re.search(r'AH(\d+):\s*(.*)', message)
                entries.append(ErrorLogEntry(
                    timestamp=match.group("timestamp"),
                    level=level,
                    pid=match.group("pid") or "",
                    client=match.group("client") or "",
                    code=ah_match.group(1) if ah_match else "",
                    message=ah_match.group(2) if ah_match else message,
                    raw_line=line,
                ))
                continue

            # Fallback: extract AH error-code lines that do not match full format
            ah_match = re.search(r'AH(\d+):\s*(.*)', line)
            if ah_match:
                entries.append(ErrorLogEntry(
                    code=ah_match.group(1),
                    message=ah_match.group(2),
                    raw_line=line,
                    level="error",
                ))
        return entries

    def get_statistics(
        self,
        access_logs: List[str],
        error_logs: List[str]
    ) -> ApacheLogStats:
        """Compute statistics from logs."""
        access_entries = self.parse_access_log(access_logs)
        error_entries = self.parse_error_log(error_logs)

        stats = ApacheLogStats()
        stats.total_requests = len(access_entries)

        for entry in access_entries:
            if 200 <= entry.status < 300:
                stats.success_requests += 1
            elif 400 <= entry.status < 500:
                stats.client_errors += 1
            elif entry.status >= 500:
                stats.server_errors += 1
                stats.error_codes[str(entry.status)] += 1
                stats.top_error_paths[entry.path] += 1

            stats.top_ips[entry.ip] += 1
            stats.top_paths[entry.path] += 1

        stats.error_log_count = len(error_entries)
        stats.warning_count = sum(1 for e in error_entries if e.severity in ["CRITICAL", "WARNING"])

        return stats

    def format_logs_for_ai(
        self,
        access_logs: List[str],
        error_logs: List[str],
        max_lines: int = 50
    ) -> Dict[str, Any]:
        """Format logs for AI analysis."""
        stats = self.get_statistics(access_logs, error_logs)
        access_entries = self.parse_access_log(access_logs)
        error_entries = self.parse_error_log(error_logs)

        # Filter error entries from access logs
        error_access = [e for e in access_entries if e.is_error]

        return {
            "summary": stats.to_dict(),
            "access_logs_sample": [e.raw_line for e in error_access[:max_lines]],
            "error_logs_sample": [e.raw_line for e in error_entries[:max_lines]],
            "context": {
                "total_requests": stats.total_requests,
                "error_rate": f"{(stats.client_errors + stats.server_errors) / max(stats.total_requests, 1) * 100:.2f}%",
                "top_error_codes": stats.error_codes.most_common(5),
                "timestamp": datetime.now().isoformat(),
            }
        }


# Singleton instance
_parser: Optional[ApacheLogParser] = None


def get_log_parser() -> ApacheLogParser:
    """Get singleton parser instance."""
    global _parser
    if _parser is None:
        _parser = ApacheLogParser()
    return _parser
