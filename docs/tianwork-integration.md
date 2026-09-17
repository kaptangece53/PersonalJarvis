# TianWork Integration

TianWork is integrated with Personal Jarvis through a local MCP bridge.

## Architecture

```text
Personal Jarvis
  -> MCP virtual loader
  -> TianWork MCP server (Python, stdio)
  -> TianWork.Cli.exe
  -> TianWork SQLite / reporting domain
```

Personal Jarvis owns conversation, voice, memory, routing, MCP and approval policy. TianWork remains the source of truth for reviewed work activity, DAM/Infraskope evidence and weekly reporting.

The bridge does not let the LLM write directly to the TianWork database.

## TianWork tools

The MCP server exposes:

- `tianwork_health` — verify TianWork local data availability.
- `tianwork_work_context(days=7)` — reviewed work context for 1-90 days.
- `tianwork_dam_evidence(days=7)` — DAM/Infraskope evidence for 1-90 days.
- `tianwork_latest_report()` — latest weekly Markdown report.
- `tianwork_generate_weekly_report()` — generate this week's Markdown report locally.

## Prerequisite

Install the TianWork build that includes `TianWork.Cli`. The installer sets:

```text
TIANWORK_CLI_PATH=%LOCALAPPDATA%\TianWork\App\Cli\TianWork.Cli.exe
```

The MCP bridge also checks that standard Windows path if the environment variable is absent.

## Register

From the PersonalJarvis repository root:

```powershell
python scripts/register_tianwork_mcp.py
```

This writes the server through Personal Jarvis's own `jarvis.mcp.state` API and enables the local server.

Restart Personal Jarvis if the current runtime does not live-refresh the new MCP entry.

## Safety

The server invokes only the configured TianWork CLI executable via `asyncio.create_subprocess_exec`; it does not use a shell. User text is never interpolated into a command line. Day ranges are clamped to 1-90. CLI output must be valid JSON or the bridge fails closed.

The first integration slice is local-only. Sending reports, changing external systems, email, calendar, GitHub and Notion mutations remain separate actions governed by Personal Jarvis risk/approval policy.
