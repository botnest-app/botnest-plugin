#!/usr/bin/env python3
"""Generate platform-specific BotNest packages from one canonical source."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "botnest.plugin.json"
CODEX_PLUGIN = ROOT / "plugins" / "botnest"
CLAUDE_GROK_PLUGIN = ROOT / "platforms" / "claude-grok" / "botnest"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def codex_manifest(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": config["name"],
        "version": config["version"],
        "description": config["description"],
        "author": config["author"],
        "homepage": config["homepage"],
        "repository": config["repository"],
        "keywords": config["keywords"],
        "skills": "./skills/",
        "mcpServers": "./.mcp.json",
        "interface": config["codex"]["interface"],
    }


def claude_manifest(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": config["name"],
        "version": config["version"],
        "description": config["description"],
        "author": config["author"],
        "homepage": config["homepage"],
        "repository": config["repository"],
    }


def codex_mcp(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "mcpServers": {
            "botnest": {
                "title": "botnest",
                "description": (
                    "Create and manage Telegram bots with callback-free "
                    "Telegram authorization."
                ),
                "command": "python3",
                "args": ["./scripts/botnest_mcp_proxy.py"],
                "cwd": ".",
                "startup_timeout_sec": 15,
                "tool_timeout_sec": 90,
            }
        }
    }


def remote_mcp(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "mcpServers": {
            "botnest": {
                "type": "http",
                "url": config["service"]["mcp_url"],
            }
        }
    }


def codex_marketplace(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": config["codex"]["marketplace_name"],
        "interface": {"displayName": config["codex"]["interface"]["displayName"]},
        "plugins": [
            {
                "name": config["name"],
                "source": {"source": "local", "path": "./plugins/botnest"},
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": config["codex"]["category"],
            }
        ],
    }


def claude_marketplace(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": config["claude"]["marketplace_name"],
        "owner": config["author"],
        "metadata": {
            "description": config["claude"]["marketplace_description"],
            "version": config["version"],
        },
        "plugins": [
            {
                "name": config["name"],
                "description": config["description"],
                "source": "./platforms/claude-grok/botnest",
                "category": config["claude"]["category"],
            }
        ],
    }


def runtime_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": config["version"],
        **config["service"],
    }


def chatgpt_connector(config: dict[str, Any]) -> dict[str, Any]:
    base_url = config["service"]["base_url"]
    return {
        "platform": "chatgpt",
        "distribution": config["chatgpt"]["distribution"],
        "directory": config["chatgpt"]["directory"],
        "mcp_server_url": config["service"]["mcp_url"],
        "oauth": {
            "protected_resource_metadata": (
                f"{base_url}/.well-known/oauth-protected-resource/mcp"
            ),
            "authorization_server_metadata": (
                f"{base_url}/.well-known/oauth-authorization-server"
            ),
        },
        "submission_file": config["chatgpt"]["submission_file"],
        "skill_archive": config["chatgpt"]["skill_archive"],
    }


def alice_publication(config: dict[str, Any]) -> dict[str, Any]:
    alice = config["alice"]
    return {
        "name": alice["name"],
        "activation_names": alice["activation_names"],
        "description": alice["description"],
        "access": "public",
        "webhook_url": alice["webhook_url"],
        "account_linking": alice["oauth"],
        "required_interfaces": ["account_linking"],
        "icon": "../../plugins/botnest/assets/logo.png",
    }


def alice_runtime(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": config["version"],
        "base_url": config["service"]["base_url"],
        "mcp_url": config["service"]["mcp_url"],
        "request_timeout_seconds": 3.0,
    }


def claude_readme(config: dict[str, Any]) -> bytes:
    text = f"""# botnest for Claude and Grok

This package is generated from the shared BotNest source in
`plugins/botnest`. Do not edit generated files here.

It connects {config['name']} directly to `{config['service']['mcp_url']}`.
Claude handles the remote MCP OAuth flow natively. Grok uses the same package
through its Claude Code compatibility layer.

See the repository root README for installation and release instructions.
"""
    return text.encode("utf-8")


def generated_files(config: dict[str, Any]) -> dict[Path, bytes]:
    result = {
        CODEX_PLUGIN / ".codex-plugin" / "plugin.json": json_bytes(
            codex_manifest(config)
        ),
        CODEX_PLUGIN / ".mcp.json": json_bytes(codex_mcp(config)),
        CODEX_PLUGIN / "runtime.json": json_bytes(runtime_config(config)),
        ROOT / ".agents" / "plugins" / "marketplace.json": json_bytes(
            codex_marketplace(config)
        ),
        ROOT / "platforms" / "chatgpt" / "connector.json": json_bytes(
            chatgpt_connector(config)
        ),
        ROOT / ".claude-plugin" / "marketplace.json": json_bytes(
            claude_marketplace(config)
        ),
        CLAUDE_GROK_PLUGIN / ".claude-plugin" / "plugin.json": json_bytes(
            claude_manifest(config)
        ),
        CLAUDE_GROK_PLUGIN / ".mcp.json": json_bytes(remote_mcp(config)),
        CLAUDE_GROK_PLUGIN / "README.md": claude_readme(config),
        ROOT / "adapters" / "alice" / "publication.json": json_bytes(
            alice_publication(config)
        ),
        ROOT / "adapters" / "alice" / "runtime.json": json_bytes(
            alice_runtime(config)
        ),
    }
    for source_root_name in ("assets", "skills"):
        source_root = CODEX_PLUGIN / source_root_name
        for source in sorted(source_root.rglob("*")):
            if source.is_file() and "__pycache__" not in source.parts:
                target = CLAUDE_GROK_PLUGIN / source.relative_to(CODEX_PLUGIN)
                result[target] = source.read_bytes()
    return result


def write_files(files: dict[Path, bytes]) -> None:
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_bytes() != content:
            path.write_bytes(content)
            print(path.relative_to(ROOT))


def check_files(files: dict[Path, bytes]) -> int:
    drift = []
    for path, expected in files.items():
        if not path.is_file() or path.read_bytes() != expected:
            drift.append(path.relative_to(ROOT))
    if not drift:
        print("Generated platform files are up to date.")
        return 0
    print("Generated platform files are stale or missing:", file=sys.stderr)
    for path in drift:
        print(f"  {path}", file=sys.stderr)
    print("Run: python3 scripts/generate_platforms.py", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail when tracked platform packages differ from canonical source.",
    )
    args = parser.parse_args()
    files = generated_files(load_config())
    if args.check:
        return check_files(files)
    write_files(files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
