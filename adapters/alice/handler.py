#!/usr/bin/env python3
"""Yandex Alice webhook adapter for the shared BotNest MCP service."""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _load_runtime() -> dict[str, Any]:
    path = Path(__file__).with_name("runtime.json")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


RUNTIME = _load_runtime()
MCP_URL = str(RUNTIME.get("mcp_url") or "https://botnest.app/mcp")
BASE_URL = str(RUNTIME.get("base_url") or "https://botnest.app").rstrip("/")
PLUGIN_VERSION = str(RUNTIME.get("version") or "dev")
REQUEST_TIMEOUT_SECONDS = float(RUNTIME.get("request_timeout_seconds") or 3.0)
USER_AGENT = f"BotNest-Alice/{PLUGIN_VERSION}"


class BotNestUnavailable(RuntimeError):
    """The remote service did not return a usable response in time."""


class BotNestUnauthorized(RuntimeError):
    """Alice needs to start or renew account linking."""


class BotNestToolError(RuntimeError):
    """A BotNest tool rejected a valid authenticated request."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class BotNestMcpClient:
    def __init__(
        self,
        url: str = MCP_URL,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.url = url
        self.timeout = timeout

    def call_tool(
        self,
        access_token: str,
        name: str,
        arguments: dict[str, Any],
        *,
        request_id: object,
    ) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }
        request = urllib.request.Request(
            self.url,
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
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise BotNestUnauthorized from exc
            raise BotNestUnavailable from exc
        except (
            json.JSONDecodeError,
            OSError,
            TimeoutError,
            UnicodeDecodeError,
            urllib.error.URLError,
        ) as exc:
            raise BotNestUnavailable from exc
        if not isinstance(result, dict):
            raise BotNestUnavailable
        if isinstance(result.get("error"), dict):
            raise BotNestUnavailable
        tool_result = result.get("result")
        if not isinstance(tool_result, dict):
            raise BotNestUnavailable
        structured = tool_result.get("structuredContent")
        structured = structured if isinstance(structured, dict) else {}
        if tool_result.get("isError"):
            raise BotNestToolError(str(structured.get("error") or "tool_error"))
        return structured


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _event_payload(event: object) -> tuple[dict[str, Any], dict[str, str]]:
    if not isinstance(event, dict):
        return {}, {}
    headers = {
        str(key).lower(): str(value)
        for key, value in _dict(event.get("headers")).items()
    }
    if "session" in event or "version" in event:
        return event, headers
    body = event.get("body")
    if event.get("isBase64Encoded") and isinstance(body, str):
        try:
            body = base64.b64decode(body).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return {}, headers
    if isinstance(body, str):
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return {}, headers
        return (_dict(payload), headers)
    return (_dict(body), headers)


def _state(payload: dict[str, Any], scope: str) -> dict[str, Any]:
    return dict(_dict(_dict(payload.get("state")).get(scope)))


def _button(
    title: str,
    *,
    action: str | None = None,
    url: str | None = None,
    values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {"title": title[:64], "hide": True}
    if url:
        result["url"] = url[:1024]
    payload = dict(values or {})
    if action:
        payload["action"] = action
    if payload:
        result["payload"] = payload
    return result


def _reply(
    text: str,
    *,
    buttons: list[dict[str, Any]] | None = None,
    directives: dict[str, Any] | None = None,
    session_state: dict[str, Any] | None = None,
    user_state: dict[str, Any] | None = None,
    application_state: dict[str, Any] | None = None,
    end_session: bool = False,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "text": text.strip()[:1024],
        "end_session": end_session,
    }
    if buttons:
        response["buttons"] = buttons
    if directives:
        response["directives"] = directives
    result: dict[str, Any] = {"response": response, "version": "1.0"}
    if session_state is not None:
        result["session_state"] = session_state
    if user_state is not None:
        result["user_state_update"] = user_state
    if application_state is not None:
        result["application_state"] = application_state
    return result


def _request_command(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    request = _dict(payload.get("request"))
    button_payload = _dict(request.get("payload"))
    command = str(request.get("command") or request.get("original_utterance") or "")
    normalized = " ".join(command.lower().replace("ё", "е").split())
    return normalized, button_payload


def _access_token(payload: dict[str, Any], headers: dict[str, str]) -> str:
    session_user = _dict(_dict(payload.get("session")).get("user"))
    token = str(session_user.get("access_token") or "").strip()
    if token:
        return token
    authorization = headers.get("authorization", "")
    scheme, separator, value = authorization.partition(" ")
    if separator and scheme.lower() == "bearer":
        return value.strip()
    return ""


def _needs_authorization(
    payload: dict[str, Any],
    command: str,
    application_state: dict[str, Any],
) -> dict[str, Any]:
    if command:
        application_state["pending_command"] = command[:700]
    interfaces = _dict(_dict(payload.get("meta")).get("interfaces"))
    if "account_linking" in interfaces:
        return _reply(
            "Свяжите аккаунт botnest, чтобы я могла работать с вашими ботами.",
            directives={"start_account_linking": {}},
            application_state=application_state,
        )
    return _reply(
        "Для этой команды нужна связка аккаунта botnest. Откройте навык на телефоне и авторизуйтесь.",
        buttons=[_button("Открыть botnest", url=f"{BASE_URL}/")],
        application_state=application_state,
    )


def _help() -> dict[str, Any]:
    return _reply(
        "Я управляю Telegram-ботами в botnest. Скажите: «покажи моих ботов», «создай бота для записи клиентов», «статус создания» или «диагностика бота 12».",
        buttons=[
            _button("Мои боты", action="list_bots"),
            _button("Статус создания", action="creation_status"),
        ],
    )


def _tool_error_text(code: str) -> str:
    messages = {
        "bot_limit_reached": "Достигнут лимит ботов в вашем тарифе botnest.",
        "telegram_identity_required": "Сначала подключите Telegram к аккаунту botnest.",
        "managed_bot_not_found": "Не нашла такого бота в вашем аккаунте botnest.",
        "managed_bot_setup_not_found": "Не нашла эту заявку на создание бота.",
        "managed_bot_publish_failed": "Не удалось опубликовать бота. Попробуйте ещё раз позже.",
        "bot_update_generation_failed": "Не удалось подготовить новое поведение бота. Уточните описание.",
        "goal_too_short": "Опишите задачу бота чуть подробнее.",
    }
    return messages.get(code, "botnest не смог выполнить эту команду. Проверьте данные и попробуйте ещё раз.")


def _integer(command: str, button_payload: dict[str, Any]) -> int | None:
    raw = button_payload.get("bot_id")
    if raw is None:
        match = re.search(r"\b(\d+)\b", command)
        raw = match.group(1) if match else None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _format_bots(result: dict[str, Any]) -> dict[str, Any]:
    bots = result.get("bots") if isinstance(result.get("bots"), list) else []
    if not bots:
        return _reply("У вас пока нет Telegram-ботов в botnest.")
    lines = [f"Нашла ботов: {len(bots)}."]
    buttons = []
    for item in bots[:8]:
        bot = _dict(item)
        bot_id = bot.get("id")
        name = str(bot.get("name") or bot.get("username") or f"Бот {bot_id}")
        username = str(bot.get("username") or "")
        status = "активен" if bot.get("is_active") else "остановлен"
        lines.append(f"{bot_id}: {name}, {status}.")
        if username:
            buttons.append(_button(name, url=f"https://t.me/{username}"))
    return _reply("\n".join(lines), buttons=buttons[:5])


def _format_diagnostics(result: dict[str, Any]) -> dict[str, Any]:
    bot = _dict(result.get("bot"))
    runs = result.get("runs") if isinstance(result.get("runs"), list) else []
    if not runs:
        return _reply(f"У бота {bot.get('name') or bot.get('id')} пока нет запусков для диагностики.")
    successful = sum(1 for run in runs if _dict(run).get("success") is True)
    failed = sum(1 for run in runs if _dict(run).get("success") is False)
    latest = _dict(runs[0])
    latest_status = "успешно" if latest.get("success") is True else "с ошибкой"
    text = (
        f"Диагностика бота {bot.get('name') or bot.get('id')}: "
        f"проверено запусков {len(runs)}, успешных {successful}, с ошибкой {failed}. "
        f"Последний запуск завершился {latest_status}."
    )
    return _reply(text)


def _call(
    client: BotNestMcpClient,
    token: str,
    payload: dict[str, Any],
    name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    session = _dict(payload.get("session"))
    request_id = f"alice:{session.get('session_id', '')}:{session.get('message_id', 0)}"
    return client.call_tool(token, name, arguments, request_id=request_id)


def handle_request(
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    client: BotNestMcpClient | None = None,
) -> dict[str, Any]:
    headers = headers or {}
    client = client or BotNestMcpClient()
    command, button_payload = _request_command(payload)
    action = str(button_payload.get("action") or "")
    session = _dict(payload.get("session"))
    session_state = _state(payload, "session")
    user_state = _state(payload, "user")
    application_state = _state(payload, "application")

    if "account_linking_complete_event" in payload:
        command = str(application_state.pop("pending_command", ""))
        if not command:
            return _reply(
                "Аккаунт botnest подключён. Теперь можно управлять вашими Telegram-ботами.",
                application_state=application_state,
            )

    if action in {"help", ""} and command in {
        "",
        "помощь",
        "что ты умеешь",
        "что умеешь",
    }:
        return _help()
    if session.get("new") and not command and not action:
        return _help()

    pending_action = str(session_state.get("pending_action") or "")
    confirmation = command in {"да", "подтверждаю", "подтвердить"} or action.startswith(
        "confirm_"
    )
    cancellation = command in {"нет", "отмена", "отменить"} or action == "cancel"
    if pending_action and cancellation:
        return _reply("Отменила действие.", session_state={})

    token = _access_token(payload, headers)
    if not token:
        return _needs_authorization(payload, command, application_state)

    try:
        if pending_action == "publish" and confirmation:
            bot_id = int(session_state["bot_id"])
            result = _call(client, token, payload, "publish_telegram_bot", {"bot_id": bot_id})
            username = str(result.get("username") or "")
            return _reply(
                f"Бот {username or bot_id} опубликован и доступен пользователям.",
                buttons=[_button("Открыть бота", url=str(result.get("telegram_url") or ""))],
                session_state={},
            )
        if action == "list_bots" or any(
            phrase in command for phrase in ("мои боты", "покажи ботов", "список ботов")
        ):
            return _format_bots(_call(client, token, payload, "list_bots", {}))

        if action == "creation_status" or "статус" in command:
            setup_id = str(button_payload.get("setup_id") or user_state.get("last_setup_id") or "")
            if not setup_id:
                return _reply("Сначала создайте бота или укажите идентификатор заявки.")
            result = _call(
                client,
                token,
                payload,
                "get_bot_creation_status",
                {"setup_id": setup_id},
            )
            status = str(result.get("status") or "неизвестен")
            text = f"Статус создания: {status}."
            buttons = []
            if result.get("telegram_url"):
                buttons.append(_button("Открыть бота", url=str(result["telegram_url"])))
            return _reply(text, buttons=buttons)

        if action == "diagnostics" or command.startswith("диагност"):
            bot_id = _integer(command, button_payload)
            if not bot_id:
                return _reply("Назовите номер бота, например: «диагностика бота 12».")
            result = _call(
                client,
                token,
                payload,
                "get_telegram_bot_diagnostics",
                {"bot_id": bot_id, "limit": 5},
            )
            return _format_diagnostics(result)

        if action == "publish" or command.startswith("опубликуй"):
            bot_id = _integer(command, button_payload)
            if not bot_id:
                return _reply("Назовите номер бота, который нужно опубликовать.")
            return _reply(
                f"Опубликовать бота {bot_id} и открыть его для пользователей?",
                buttons=[
                    _button("Подтвердить", action="confirm_publish"),
                    _button("Отмена", action="cancel"),
                ],
                session_state={"pending_action": "publish", "bot_id": bot_id},
            )

        if command.startswith(("измени", "обнови")):
            return _reply(
                "Сложное редактирование сценария пока доступно через ChatGPT, Claude, Grok или Codex. В Алисе можно создать, проверить и опубликовать бота.",
            )

        create_match = re.match(
            r"^(?:создай|сделай)(?:\s+(?:мне\s+)?(?:телеграм[- ]?бота|бота))?\s*(.*)$",
            command,
        )
        if create_match:
            goal = create_match.group(1).strip()
            if len(goal) < 8:
                return _reply("Опишите, что должен делать новый Telegram-бот.")
            request_id = f"alice:{session.get('session_id', '')}:{session.get('message_id', 0)}"
            result = _call(
                client,
                token,
                payload,
                "prepare_telegram_bot",
                {"goal": goal[:1000], "idempotency_key": request_id},
            )
            setup_id = str(result.get("setup_id") or "")
            if setup_id:
                user_state["last_setup_id"] = setup_id
            return _reply(
                "Подготовила бота. Откройте Telegram и подтвердите его создание.",
                buttons=[
                    _button(
                        "Продолжить в Telegram",
                        url=str(result.get("telegram_creation_url") or ""),
                    )
                ],
                user_state=user_state,
            )

        return _help()
    except BotNestUnauthorized:
        return _needs_authorization(payload, command, application_state)
    except BotNestToolError as exc:
        return _reply(_tool_error_text(exc.code))
    except BotNestUnavailable:
        return _reply("botnest сейчас не отвечает. Попробуйте ещё раз через минуту.")


def handler(event: object, context: object = None) -> dict[str, Any]:
    """Yandex Cloud Functions-compatible entry point."""

    del context
    payload, headers = _event_payload(event)
    if not payload:
        return _reply("Не удалось прочитать запрос Алисы. Попробуйте ещё раз.")
    return handle_request(payload, headers)


if __name__ == "__main__":
    raise SystemExit("Deploy adapters.alice.handler:handler as an HTTPS webhook.")
