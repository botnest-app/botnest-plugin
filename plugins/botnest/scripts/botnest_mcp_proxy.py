#!/usr/bin/env python3
"""Local stdio MCP bridge with callback-free Telegram device authorization."""

from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def _runtime_config() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "runtime.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


RUNTIME = _runtime_config()
OAUTH = RUNTIME.get("oauth") if isinstance(RUNTIME.get("oauth"), dict) else {}
BASE_URL = str(RUNTIME.get("base_url") or "https://botnest.app").rstrip("/")
MCP_URL = str(RUNTIME.get("mcp_url") or f"{BASE_URL}/mcp")
TOKEN_URL = str(OAUTH.get("token_url") or f"{BASE_URL}/oauth/token")
DEVICE_URL = str(
    OAUTH.get("device_authorization_url") or f"{BASE_URL}/oauth/device"
)
RESOURCE = str(OAUTH.get("resource") or MCP_URL)
CLIENT_ID = str(OAUTH.get("device_client_id") or "botnest-codex-device")
DEVICE_GRANT_TYPE = str(
    OAUTH.get("device_grant_type")
    or "urn:ietf:params:oauth:grant-type:device_code"
)
SCOPES = str(OAUTH.get("scopes") or "bots:read bots:create bots:publish")
PLUGIN_VERSION = str(RUNTIME.get("version") or "dev")
USER_AGENT = f"BotNest-Plugin/{PLUGIN_VERSION}"
PROTOCOL_VERSION = "2025-11-25"
MAX_AVATAR_BYTES = 10 * 1024 * 1024


CONNECT_TOOL = {
    "name": "connect_botnest",
    "title": "Connect BotNest with Telegram",
    "description": (
        "Start or finish callback-free Telegram authorization for BotNest. "
        "Open the returned HTTPS URL; never copy a callback URL or code."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "outputSchema": {"type": "object"},
    "annotations": {
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
}

REMOTE_TOOLS = [
    {
        "name": "get_flow_builder_context",
        "title": "Get the BotNest flow builder context",
        "description": (
            "Get the current BotNest block catalog and flow format before "
            "designing custom bot behavior. Includes provider-aware LLM "
            "preflight, safe credential IDs, reliable model defaults, and a "
            "direct OpenRouter authorization action. Optionally inspect an owned bot."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "bot_id": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Owned bot to inspect before an update.",
                },
            },
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "prepare_telegram_bot",
        "title": "Prepare a Telegram bot",
        "description": (
            "Create a private BotNest setup from the user's goal and return the "
            "official Telegram creation link. This does not create or publish a "
            "Telegram bot until the user confirms in Telegram. Authorization is "
            "completed automatically after that confirmation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "minLength": 8,
                    "maxLength": 1000,
                    "description": "What the Telegram bot should do.",
                },
                "idempotency_key": {
                    "type": "string",
                    "maxLength": 160,
                    "description": "Stable key for safe retries.",
                },
                "suggested_name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 64,
                    "description": (
                        "Optional short Telegram display name. When the user did "
                        "not choose one, use a neutral purpose-based name."
                    ),
                },
                "flow": {
                    "type": "object",
                    "description": (
                        "Complete flow designed from get_flow_builder_context."
                    ),
                },
            },
            "required": ["goal"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_bot_creation_status",
        "title": "Get Telegram bot creation status",
        "description": "Check a BotNest-managed Telegram bot setup.",
        "inputSchema": {
            "type": "object",
            "properties": {"setup_id": {"type": "string", "format": "uuid"}},
            "required": ["setup_id"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "list_bots",
        "title": "List Telegram bots",
        "description": "List Telegram bots owned by the connected BotNest user.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "get_telegram_bot_diagnostics",
        "title": "Get Telegram bot diagnostics",
        "description": (
            "Read recent flow and block execution results for an owned bot. "
            "Short per-block details may include message or model-output previews "
            "from the user's own recent runs. Use this only when diagnosing bot "
            "behavior that did not work as expected."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "bot_id": {"type": "integer", "minimum": 1},
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 20,
                    "default": 5,
                },
            },
            "required": ["bot_id"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "publish_telegram_bot",
        "title": "Publish a Telegram bot",
        "description": "Publish a ready BotNest bot after explicit confirmation.",
        "inputSchema": {
            "type": "object",
            "properties": {"bot_id": {"type": "integer", "minimum": 1}},
            "required": ["bot_id"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    {
        "name": "update_telegram_bot",
        "title": "Update a Telegram bot",
        "description": (
            "Replace an existing BotNest Telegram bot's behavior from a "
            "plain-language description while keeping the same Telegram bot. "
            "The current flow is snapshotted before the replacement is applied; "
            "the change affects how the bot responds to Telegram users."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "bot_id": {"type": "integer", "minimum": 1},
                "goal": {
                    "type": "string",
                    "minLength": 8,
                    "maxLength": 1000,
                    "description": "The complete desired behavior after the update.",
                },
                "flow": {
                    "type": "object",
                    "description": (
                        "Complete replacement flow designed from "
                        "get_flow_builder_context."
                    ),
                },
            },
            "required": ["bot_id", "goal"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    {
        "name": "get_telegram_bot_profile",
        "title": "Get a Telegram bot profile",
        "description": (
            "Read the Telegram-facing name, descriptions, commands, menu "
            "button, avatar state, languages, and suggested admin rights. With "
            "refresh enabled, fetch the profile from Telegram and cache the "
            "refreshed snapshot in BotNest."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "bot_id": {"type": "integer", "minimum": 1},
                "refresh": {"type": "boolean", "default": True},
            },
            "required": ["bot_id"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    },
    {
        "name": "update_telegram_bot_profile",
        "title": "Update a Telegram bot profile",
        "description": (
            "Overwrite selected fields in an existing bot's Telegram profile. "
            "Removing the avatar deletes the current Telegram profile photo. To "
            "use a generated or local image as the avatar, pass its absolute path "
            "in avatar_path; the bridge validates and uploads it without exposing "
            "the path."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "bot_id": {"type": "integer", "minimum": 1},
                "name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 64,
                },
                "short_description": {"type": "string", "maxLength": 120},
                "description": {"type": "string", "maxLength": 512},
                "commands": {
                    "type": "array",
                    "maxItems": 100,
                    "items": {"type": "object"},
                },
                "localizations": {
                    "type": "array",
                    "maxItems": 20,
                    "items": {"type": "object"},
                },
                "menu_button": {"type": "object"},
                "admin_rights": {"type": "object"},
                "avatar_path": {
                    "type": "string",
                    "description": (
                        "Absolute path to a PNG, JPEG, or WebP image generated "
                        "by Codex under its generated-images directory."
                    ),
                },
                "remove_avatar": {"type": "boolean"},
            },
            "required": ["bot_id"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
]


class HttpFailure(RuntimeError):
    def __init__(self, status: int, payload: object) -> None:
        super().__init__(f"HTTP {status}")
        self.status = status
        self.payload = payload


def _data_dir() -> Path:
    configured = os.getenv("PLUGIN_DATA") or os.getenv("CLAUDE_PLUGIN_DATA")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".codex" / "plugin-data" / "botnest"


def _state_path() -> Path:
    return _data_dir() / "oauth-state.json"


def _load_state() -> dict[str, Any]:
    try:
        payload = json.loads(_state_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_state(state: dict[str, Any]) -> None:
    directory = _data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    try:
        directory.chmod(0o700)
    except OSError:
        pass
    handle, temporary_name = tempfile.mkstemp(
        prefix=".oauth-state-",
        suffix=".json",
        dir=directory,
        text=True,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(state, stream, ensure_ascii=False, separators=(",", ":"))
        try:
            os.chmod(temporary_name, 0o600)
        except OSError:
            pass
        os.replace(temporary_name, _state_path())
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def _decode_json(raw: bytes) -> object:
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}


def _post_form(url: str, values: dict[str, object]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(values).encode("ascii"),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = _decode_json(response.read())
    except urllib.error.HTTPError as exc:
        raise HttpFailure(exc.code, _decode_json(exc.read())) from exc
    if not isinstance(payload, dict):
        raise HttpFailure(502, {})
    return payload


def _post_mcp(access_token: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = _decode_json(response.read())
    except urllib.error.HTTPError as exc:
        raise HttpFailure(exc.code, _decode_json(exc.read())) from exc
    if not isinstance(result, dict):
        raise HttpFailure(502, {})
    return result


def _store_token(state: dict[str, Any], payload: dict[str, Any]) -> str:
    access_token = str(payload.get("access_token") or "")
    refresh_token = str(payload.get("refresh_token") or "")
    if not access_token or not refresh_token:
        raise HttpFailure(502, {})
    state["credentials"] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": int(time.time()) + int(payload.get("expires_in") or 3600),
    }
    state.pop("pending", None)
    _save_state(state)
    return access_token


def _refresh(state: dict[str, Any]) -> str | None:
    credentials = state.get("credentials")
    if not isinstance(credentials, dict):
        return None
    access_token = str(credentials.get("access_token") or "")
    expires_at = int(credentials.get("expires_at") or 0)
    if access_token and expires_at > int(time.time()) + 30:
        return access_token
    refresh_token = str(credentials.get("refresh_token") or "")
    if not refresh_token:
        state.pop("credentials", None)
        _save_state(state)
        return None
    try:
        payload = _post_form(
            TOKEN_URL,
            {
                "grant_type": "refresh_token",
                "client_id": CLIENT_ID,
                "refresh_token": refresh_token,
                "resource": RESOURCE,
            },
        )
    except HttpFailure:
        state.pop("credentials", None)
        _save_state(state)
        return None
    return _store_token(state, payload)


def _exchange_pending(state: dict[str, Any]) -> str | None:
    pending = state.get("pending")
    if not isinstance(pending, dict):
        return None
    if int(pending.get("expires_at") or 0) <= int(time.time()):
        state.pop("pending", None)
        _save_state(state)
        return None
    try:
        payload = _post_form(
            TOKEN_URL,
            {
                "grant_type": DEVICE_GRANT_TYPE,
                "device_code": str(pending.get("device_code") or ""),
                "client_id": CLIENT_ID,
                "resource": RESOURCE,
            },
        )
    except HttpFailure as exc:
        error = exc.payload.get("error") if isinstance(exc.payload, dict) else ""
        if error == "authorization_pending":
            return None
        if error in {"access_denied", "expired_token", "invalid_grant"}:
            state.pop("pending", None)
            _save_state(state)
            return None
        raise
    return _store_token(state, payload)


def _start_device_authorization(state: dict[str, Any]) -> dict[str, Any]:
    payload = _post_form(
        DEVICE_URL,
        {
            "client_id": CLIENT_ID,
            "scope": SCOPES,
            "resource": RESOURCE,
        },
    )
    device_code = str(payload.get("device_code") or "")
    authorization_url = str(payload.get("verification_uri_complete") or "")
    expires_in = int(payload.get("expires_in") or 600)
    if (
        not device_code
        or not authorization_url.startswith(f"{BASE_URL}/oauth/device/")
    ):
        raise HttpFailure(502, {})
    state["pending"] = {
        "device_code": device_code,
        "authorization_url": authorization_url,
        "expires_at": int(time.time()) + expires_in,
    }
    _save_state(state)
    return state["pending"]


def _authorization_result(state: dict[str, Any]) -> dict[str, Any]:
    pending = state.get("pending")
    if not isinstance(pending, dict):
        pending = _start_device_authorization(state)
    authorization_url = str(pending["authorization_url"])
    structured = {
        "status": "authorization_required",
        "authorization_url": authorization_url,
        "expires_at": int(pending["expires_at"]),
        "callback_required": False,
    }
    return {
        "content": [
            {
                "type": "text",
                "text": (
                    "Откройте Telegram-авторизацию BotNest: "
                    f"{authorization_url}\n"
                    "После подтверждения вернитесь в Codex. Код и callback "
                    "копировать не нужно."
                ),
            }
        ],
        "structuredContent": structured,
    }


def _access_or_authorization() -> tuple[str | None, dict[str, Any], dict[str, Any] | None]:
    state = _load_state()
    access_token = _refresh(state)
    if not access_token:
        access_token = _exchange_pending(state)
    if access_token:
        return access_token, state, None
    return None, state, _authorization_result(state)


def _connect() -> dict[str, Any]:
    access_token, _, authorization = _access_or_authorization()
    if authorization:
        return authorization
    try:
        _post_mcp(
            access_token or "",
            {"jsonrpc": "2.0", "id": "connection-check", "method": "ping"},
        )
    except HttpFailure:
        return _tool_error("botnest_connection_failed")
    return {
        "content": [{"type": "text", "text": "BotNest подключён через Telegram."}],
        "structuredContent": {
            "status": "connected",
            "callback_required": False,
        },
    }


def _call_remote(
    request_id: object,
    tool_name: str,
    arguments: object,
) -> dict[str, Any]:
    try:
        prepared_arguments = _prepare_remote_arguments(tool_name, arguments)
    except LocalAvatarError as exc:
        return _tool_error(exc.code)
    access_token, state, authorization = _access_or_authorization()
    if authorization:
        return authorization
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": prepared_arguments},
    }
    try:
        response = _post_mcp(access_token or "", payload)
    except HttpFailure as exc:
        if exc.status != 401:
            return _tool_error("botnest_unavailable")
        state.pop("credentials", None)
        _save_state(state)
        replacement, _, authorization = _access_or_authorization()
        if authorization:
            return authorization
        try:
            response = _post_mcp(replacement or "", payload)
        except HttpFailure:
            return _tool_error("botnest_unavailable")
    result = response.get("result")
    if isinstance(result, dict):
        return result
    error = response.get("error")
    if isinstance(error, dict):
        return _tool_error(str(error.get("message") or "botnest_error"))
    return _tool_error("botnest_invalid_response")


class LocalAvatarError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _prepare_remote_arguments(
    tool_name: str,
    arguments: object,
) -> object:
    if tool_name != "update_telegram_bot_profile" or not isinstance(arguments, dict):
        return arguments
    prepared = dict(arguments)
    raw_path = prepared.pop("avatar_path", None)
    if raw_path is None:
        return prepared
    avatar_path = Path(str(raw_path)).expanduser()
    if not avatar_path.is_absolute():
        raise LocalAvatarError("avatar_path_must_be_absolute")
    try:
        resolved = avatar_path.resolve(strict=True)
    except OSError as exc:
        raise LocalAvatarError("avatar_file_unavailable") from exc
    if not resolved.is_file() or not _is_allowed_avatar_path(resolved):
        raise LocalAvatarError("avatar_file_unavailable")
    try:
        size = resolved.stat().st_size
        if size <= 0 or size > MAX_AVATAR_BYTES:
            raise LocalAvatarError("invalid_avatar")
        raw = resolved.read_bytes()
    except OSError as exc:
        raise LocalAvatarError("avatar_file_unavailable") from exc
    mime_type = _avatar_mime_type(raw)
    if not mime_type:
        raise LocalAvatarError("invalid_avatar")
    prepared["avatar_base64"] = base64.b64encode(raw).decode("ascii")
    prepared["avatar_mime_type"] = mime_type
    return prepared


def _is_allowed_avatar_path(path: Path) -> bool:
    roots = [Path.cwd()]
    codex_home = Path(os.getenv("CODEX_HOME") or (Path.home() / ".codex"))
    roots.extend(
        [
            codex_home / "generated_images",
            codex_home / "attachments",
            codex_home / "visualizations",
        ]
    )
    for root in roots:
        try:
            path.relative_to(root.expanduser().resolve())
            return True
        except (OSError, ValueError):
            continue
    return False


def _avatar_mime_type(raw: bytes) -> str:
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(raw) >= 12 and raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    return ""


def _tool_error(code: str) -> dict[str, Any]:
    return {
        "isError": True,
        "content": [{"type": "text", "text": code}],
        "structuredContent": {"error": code},
    }


def _result(request_id: object, result: object) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: object, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def dispatch(message: object) -> dict[str, Any] | None:
    if not isinstance(message, dict):
        return _error(None, -32600, "Invalid Request")
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    if message.get("jsonrpc") != "2.0" or not isinstance(method, str):
        return _error(request_id, -32600, "Invalid Request")
    if method == "notifications/initialized" and "id" not in message:
        return None
    if method == "initialize":
        requested = str(params.get("protocolVersion") or PROTOCOL_VERSION)
        return _result(
            request_id,
            {
                "protocolVersion": requested,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "BotNest", "version": "0.8.0"},
                "instructions": (
                    "Use connect_botnest when authorization is required. Show "
                    "the HTTPS Telegram link; never ask for a callback URL, "
                    "authorization code, password, Google login, or bot token. "
                    "For a generated avatar, generate the image first and pass "
                    "its absolute saved path to update_telegram_bot_profile."
                ),
            },
        )
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": [CONNECT_TOOL, *REMOTE_TOOLS]})
    if method == "tools/call":
        if not isinstance(params, dict):
            return _error(request_id, -32602, "Invalid params")
        name = str(params.get("name") or "")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return _result(request_id, _tool_error("invalid_arguments"))
        try:
            if name == "connect_botnest":
                result = _connect()
            elif name in {tool["name"] for tool in REMOTE_TOOLS}:
                result = _call_remote(request_id, name, arguments)
            else:
                result = _tool_error("unknown_tool")
        except (HttpFailure, OSError, ValueError):
            result = _tool_error("botnest_unavailable")
        return _result(request_id, result)
    return _error(request_id, -32601, "Method not found")


def main() -> None:
    for raw_line in sys.stdin:
        try:
            message = json.loads(raw_line)
            response = dispatch(message)
        except json.JSONDecodeError:
            response = _error(None, -32700, "Parse error")
        if response is not None:
            sys.stdout.write(
                json.dumps(response, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            )
            sys.stdout.flush()


if __name__ == "__main__":
    main()
