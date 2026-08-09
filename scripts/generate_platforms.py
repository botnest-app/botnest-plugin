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
    interface = {
        **config["codex"]["interface"],
        "privacyPolicyURL": config["legal"]["privacy_policy_url"],
        "termsOfServiceURL": config["legal"]["terms_of_service_url"],
    }
    return {
        "name": config["name"],
        "version": config["version"],
        "description": config["description"],
        "author": config["author"],
        "homepage": config["homepage"],
        "repository": config["repository"],
        "license": config["license"],
        "keywords": config["keywords"],
        "skills": "./skills/",
        "mcpServers": "./.mcp.json",
        "interface": interface,
    }


def claude_manifest(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": config["name"],
        "displayName": config["claude"]["display_name"],
        "version": config["version"],
        "description": config["description"],
        "author": config["author"],
        "homepage": config["homepage"],
        "repository": config["repository"],
        "license": config["license"],
        "keywords": config["keywords"],
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
    legal = config["legal"]
    text = f"""# BotNest for Claude and Grok

Create, inspect, improve, diagnose, brand, and publish Telegram bots from a
plain-language request. This package bundles the BotNest workflow skill with a
remote MCP connector to `{config['service']['mcp_url']}`.

## Connect

1. Install and enable **BotNest**.
2. Select **Connect** or **Authorize** when Claude prompts for the BotNest
   connector.
3. Complete the BotNest HTTPS sign-in flow. BotNest may ask you to confirm your
   identity in Telegram, then returns you to Claude.
4. Retry the original request after authorization completes.

Never paste Telegram bot tokens, OAuth codes, passwords, or LLM API keys into a
Claude conversation. See `SETUP.md` for recovery steps.

## Example prompts

- `Покажи моих Telegram-ботов в BotNest.`
- `Создай Telegram-бота для записи клиентов: спроси имя, услугу и время.`
- `Проверь последние ошибки моего бота и объясни, что исправить.`

Bot creation remains private until the user completes the Telegram confirmation
step. Publishing a ready bot is a separate action and requires an explicit user
request or confirmation.

## Data and permissions

The connector sends only the arguments needed for the selected BotNest tool to
the production BotNest service. OAuth access is limited to reading, creating,
updating, and publishing bots owned by the authenticated user. The package has
no local hooks, background processes, telemetry, or bundled executable code.

- Privacy policy: {legal['privacy_policy_url']}
- Terms of service: {legal['terms_of_service_url']}
- Support and issue reporting: {legal['support_url']}
- Source: {config['repository']}

## Troubleshooting

- If Claude reports that authorization is required, open the HTTPS authorization
  action again and finish the Telegram confirmation before retrying.
- If a bot is still being provisioned, ask for its creation status instead of
  starting another creation flow.
- If a tool fails, keep the returned error code and contact support without
  sharing tokens, credentials, or private bot data.

This package is generated from the shared BotNest source. Do not edit generated
files under `platforms/claude-grok/botnest` directly. Grok Build uses the same
package through its Claude Code compatibility layer.

Licensed under the Apache License 2.0. See `LICENSE`.
"""
    return text.encode("utf-8")


def claude_setup(config: dict[str, Any]) -> bytes:
    text = f"""# Set up BotNest

Use these instructions when the BotNest plugin is installed but its remote MCP
connector is not yet authenticated or a BotNest tool returns
`authorization_required`.

1. Confirm that the configured connector URL is exactly
   `{config['service']['mcp_url']}`.
2. Start Claude's native **Connect** or **Authorize** action for BotNest.
3. Open only the HTTPS BotNest authorization page shown by Claude. Complete the
   sign-in and Telegram confirmation there.
4. Return to the same conversation and retry the original request with the same
   arguments. For bot creation, preserve the original idempotency key.
5. Verify the connection with a read-only request such as listing the user's
   bots before continuing a write workflow.

Never ask the user to paste a Telegram bot token, OAuth authorization code,
device code, password, client secret, or LLM API key. Do not replace the
configured MCP URL with localhost, a tunnel, or another domain. If the HTTPS
authorization page or connector remains unavailable, stop and direct the user
to {config['legal']['support_url']}.
"""
    return text.encode("utf-8")


def generated_files(config: dict[str, Any]) -> dict[Path, bytes]:
    license_bytes = (ROOT / "LICENSE").read_bytes()
    result = {
        CODEX_PLUGIN / ".codex-plugin" / "plugin.json": json_bytes(
            codex_manifest(config)
        ),
        CODEX_PLUGIN / ".mcp.json": json_bytes(codex_mcp(config)),
        CODEX_PLUGIN / "runtime.json": json_bytes(runtime_config(config)),
        CODEX_PLUGIN / "LICENSE": license_bytes,
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
        CLAUDE_GROK_PLUGIN / "SETUP.md": claude_setup(config),
        CLAUDE_GROK_PLUGIN / "LICENSE": license_bytes,
        ROOT / "adapters" / "alice" / "publication.json": json_bytes(
            alice_publication(config)
        ),
        ROOT / "adapters" / "alice" / "runtime.json": json_bytes(
            alice_runtime(config)
        ),
        ROOT / "adapters" / "alice" / "LICENSE": license_bytes,
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
