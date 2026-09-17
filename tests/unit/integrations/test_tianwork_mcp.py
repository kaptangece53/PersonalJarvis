from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.integrations import tianwork_mcp


def test_cli_path_prefers_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cli = tmp_path / "TianWork.Cli.exe"
    monkeypatch.setenv("TIANWORK_CLI_PATH", str(cli))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "other"))

    assert tianwork_mcp._default_cli_path() == cli


def test_cli_path_falls_back_to_localappdata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TIANWORK_CLI_PATH", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    assert tianwork_mcp._default_cli_path() == (
        tmp_path / "TianWork" / "App" / "Cli" / "TianWork.Cli.exe"
    )


@pytest.mark.asyncio
async def test_missing_cli_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    missing = tmp_path / "missing.exe"
    monkeypatch.setenv("TIANWORK_CLI_PATH", str(missing))

    with pytest.raises(RuntimeError, match="TianWork CLI bulunamadı"):
        await tianwork_mcp._invoke_cli("health")


@pytest.mark.asyncio
async def test_work_context_clamps_days(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[tuple[str, tuple[str, ...]]] = []

    async def fake_invoke(command: str, *args: str):
        captured.append((command, args))
        return {"ok": True}

    monkeypatch.setattr(tianwork_mcp, "_invoke_cli", fake_invoke)

    result = await tianwork_mcp.tianwork_work_context(999)

    assert result == {"ok": True}
    assert captured == [("work-context", ("90",))]
