#!/usr/bin/env python3
"""Minimal production HTTP server for the BotNest Alice webhook."""

from __future__ import annotations

import json
import logging
import os
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from handler import handler as alice_handler


HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", str(64 * 1024)))
WEBHOOK_PATH = "/alice/webhook/"


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def _fallback_response() -> dict[str, object]:
    return {
        "response": {
            "text": "botnest сейчас не отвечает. Попробуйте ещё раз через минуту.",
            "end_session": False,
        },
        "version": "1.0",
    }


class AliceWebhookRequestHandler(BaseHTTPRequestHandler):
    server_version = "BotNestAlice/1.0"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if urlsplit(self.path).path != "/healthz":
            self._send_json({"error": "not_found"}, status=404)
            return
        self._send_json({"status": "ok"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if urlsplit(self.path).path != WEBHOOK_PATH:
            self._send_json({"error": "not_found"}, status=404)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json({"error": "invalid_content_length"}, status=400)
            return
        if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json({"error": "invalid_request_size"}, status=413)
            return

        body = self.rfile.read(content_length)
        event = {
            "body": body.decode("utf-8", errors="strict"),
            "headers": {key: value for key, value in self.headers.items()},
        }
        try:
            response = alice_handler(event)
        except (UnicodeDecodeError, ValueError):
            self._send_json({"error": "invalid_json"}, status=400)
            return
        except Exception:  # pragma: no cover - defensive production boundary
            logging.exception("Unhandled Alice webhook error")
            response = _fallback_response()
        self._send_json(response)

    def _send_json(self, payload: object, *, status: int = 200) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        logging.info("Alice webhook request: " + format, *args)


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    server = ThreadingHTTPServer((HOST, PORT), AliceWebhookRequestHandler)
    server.daemon_threads = True
    server.timeout = 0.5
    stopping = threading.Event()

    def stop(_signum: int, _frame: object) -> None:
        stopping.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    logging.info("Alice webhook listening on %s:%s", HOST, PORT)
    try:
        while not stopping.is_set():
            server.handle_request()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
