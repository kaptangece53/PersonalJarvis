"""Register and enable the built-in TianWork MCP bridge.

Usage from the PersonalJarvis repository root:
    python scripts/register_tianwork_mcp.py

This uses Personal Jarvis's own mcp.json state writer rather than editing the
file by hand.
"""
from __future__ import annotations

import sys

from jarvis.mcp import state as mcp_state

SERVER_NAME = "tianwork"


def main() -> int:
    spec = {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "jarvis.integrations.tianwork_mcp"],
        "env": {},
        "enabled": True,
        "description": (
            "Local TianWork work-context, DAM evidence and weekly-report bridge. "
            "Uses TIANWORK_CLI_PATH and never moves TianWork's evidence source-of-truth into the LLM."
        ),
    }

    mcp_state.upsert_server(SERVER_NAME, spec)
    mcp_state.set_enabled(SERVER_NAME, True)

    saved = mcp_state.get_server_entry(SERVER_NAME)
    if not saved or not saved.get("enabled"):
        raise RuntimeError("TianWork MCP kaydı doğrulanamadı.")

    print("TianWork MCP registered and enabled.")
    print(f"Server: {SERVER_NAME}")
    print(f"Command: {sys.executable} -m jarvis.integrations.tianwork_mcp")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
