"""TianWork MCP bridge for Personal Jarvis.

This module exposes TianWork's local evidence/reporting CLI through MCP without
moving TianWork's source of truth into the LLM. Personal Jarvis remains the
agent/runtime layer; TianWork remains the domain/evidence layer.

Run with:
    python -m jarvis.integrations.tianwork_mcp

The TianWork installer publishes ``TIANWORK_CLI_PATH``. On Windows, the bridge
also falls back to the standard per-user install path.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("tianwork")

_DEFAULT_TIMEOUT_SECONDS = 45


def _default_cli_path() -> Path:
    configured = os.environ.get("TIANWORK_CLI_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()

    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data) / "TianWork" / "App" / "Cli" / "TianWork.Cli.exe"

    return Path.home() / ".local" / "share" / "TianWork" / "App" / "Cli" / "TianWork.Cli"


async def _invoke_cli(command: str, *args: str) -> dict[str, Any]:
    """Invoke the trusted TianWork CLI directly and decode its JSON response."""
    cli_path = _default_cli_path()
    if not cli_path.is_file():
        raise RuntimeError(
            "TianWork CLI bulunamadı. TianWork bridge build/install işlemini tamamlayın "
            "ve TIANWORK_CLI_PATH değişkenini doğrulayın. "
            f"Beklenen yol: {cli_path}"
        )

    process = await asyncio.create_subprocess_exec(
        str(cli_path),
        command,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=_DEFAULT_TIMEOUT_SECONDS
        )
    except TimeoutError:
        process.kill()
        await process.communicate()
        raise RuntimeError(f"TianWork CLI zaman aşımına uğradı: {command}") from None

    output_text = stdout.decode("utf-8", errors="replace").strip()
    error_text = stderr.decode("utf-8", errors="replace").strip()

    if process.returncode != 0:
        detail = error_text or output_text or f"exit code {process.returncode}"
        raise RuntimeError(f"TianWork CLI başarısız oldu ({command}): {detail}")

    if not output_text:
        raise RuntimeError(f"TianWork CLI boş yanıt döndürdü: {command}")

    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"TianWork CLI geçersiz JSON döndürdü ({command}): {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"TianWork CLI beklenmeyen yanıt tipi döndürdü: {command}")

    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))

    return payload


@mcp.tool()
async def tianwork_health() -> dict[str, Any]:
    """Check whether TianWork's local database and report environment are available."""
    return await _invoke_cli("health")


@mcp.tool()
async def tianwork_activity_events(days: int = 30, limit: int = 500) -> dict[str, Any]:
    """Read privacy-safe raw TianWork activity events.

    Use this when reviewed work context is empty but the user wants to inspect
    collected activity. Returns timestamp, source, event type, application,
    window title and resource only; raw MetadataJson is intentionally excluded.
    Days is clamped to 1-3650 and limit to 1-1000.
    """
    bounded_days = max(1, min(int(days), 3650))
    bounded_limit = max(1, min(int(limit), 1000))
    return await _invoke_cli("activity-events", str(bounded_days), str(bounded_limit))


@mcp.tool()
async def tianwork_work_context(days: int = 7) -> dict[str, Any]:
    """Read reviewed TianWork work context for the last 1-90 days.

    Use this for questions such as what was worked on today/this week, project
    status, reviewed work items, and evidence-backed work summaries.
    """
    bounded_days = max(1, min(int(days), 90))
    return await _invoke_cli("work-context", str(bounded_days))


@mcp.tool()
async def tianwork_dam_evidence(days: int = 7) -> dict[str, Any]:
    """Read DAM/Infraskope rule, alarm and tuning evidence for the last 1-90 days.

    Returns only evidence already stored by TianWork; do not infer missing rule
    fields, test results, users, systems, queries or policy values.
    """
    bounded_days = max(1, min(int(days), 90))
    return await _invoke_cli("dam-evidence", str(bounded_days))


@mcp.tool()
async def tianwork_latest_report() -> dict[str, Any]:
    """Return the latest TianWork weekly Markdown report, including path and content."""
    return await _invoke_cli("latest-report")


@mcp.tool()
async def tianwork_generate_weekly_report() -> dict[str, Any]:
    """Generate the current week's TianWork manager-ready Markdown report locally.

    This writes only to TianWork's local Reports directory and does not send or
    publish the report to an external system.
    """
    return await _invoke_cli("generate-weekly-report")


if __name__ == "__main__":
    mcp.run("stdio")
