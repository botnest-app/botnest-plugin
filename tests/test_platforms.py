from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import time
import unittest
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_PLUGIN = ROOT / "plugins" / "botnest"
CLAUDE_GROK_PLUGIN = ROOT / "platforms" / "claude-grok" / "botnest"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class GeneratedPlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = load_module(
            "generate_platforms",
            ROOT / "scripts" / "generate_platforms.py",
        )
        cls.config = load_json(ROOT / "botnest.plugin.json")

    def test_generated_files_match_canonical_source(self):
        files = self.generator.generated_files(self.config)
        self.assertEqual(self.generator.check_files(files), 0)

    def test_every_manifest_uses_the_canonical_version(self):
        version = self.config["version"]
        self.assertEqual(
            load_json(CODEX_PLUGIN / ".codex-plugin" / "plugin.json")["version"],
            version,
        )
        self.assertEqual(
            load_json(CLAUDE_GROK_PLUGIN / ".claude-plugin" / "plugin.json")[
                "version"
            ],
            version,
        )
        self.assertEqual(
            load_json(CODEX_PLUGIN / "runtime.json")["version"],
            version,
        )

    def test_standalone_distributions_include_the_repository_license(self):
        expected = (ROOT / "LICENSE").read_bytes()
        for distribution in (
            CODEX_PLUGIN,
            CLAUDE_GROK_PLUGIN,
            ROOT / "adapters" / "alice",
        ):
            self.assertEqual((distribution / "LICENSE").read_bytes(), expected)

    def test_chatgpt_uses_direct_remote_mcp_and_oauth(self):
        connector = load_json(ROOT / "platforms" / "chatgpt" / "connector.json")
        self.assertEqual(connector["distribution"], "remote-mcp")
        self.assertEqual(connector["mcp_server_url"], "https://botnest.app/mcp")
        self.assertEqual(
            connector["oauth"]["protected_resource_metadata"],
            "https://botnest.app/.well-known/oauth-protected-resource/mcp",
        )
        self.assertTrue((ROOT / connector["submission_file"]).is_file())

    def test_claude_and_grok_share_remote_mcp_package(self):
        marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual(marketplace["plugins"][0]["source"], "./platforms/claude-grok/botnest")
        mcp = load_json(CLAUDE_GROK_PLUGIN / ".mcp.json")
        self.assertEqual(
            mcp,
            {
                "mcpServers": {
                    "botnest": {
                        "type": "http",
                        "url": "https://botnest.app/mcp",
                    }
                }
            },
        )
        self.assertEqual(
            (CLAUDE_GROK_PLUGIN / "skills" / "create-telegram-bot" / "SKILL.md").read_bytes(),
            (CODEX_PLUGIN / "skills" / "create-telegram-bot" / "SKILL.md").read_bytes(),
        )
        self.assertFalse((CLAUDE_GROK_PLUGIN / "scripts" / "botnest_mcp_proxy.py").exists())

    def test_claude_package_is_ready_for_directory_submission(self):
        manifest = load_json(
            CLAUDE_GROK_PLUGIN / ".claude-plugin" / "plugin.json"
        )
        self.assertEqual(manifest["displayName"], "BotNest — Telegram Bot Builder")
        self.assertEqual(manifest["license"], "Apache-2.0")
        self.assertIn("botnest", manifest["keywords"])
        self.assertEqual(
            (CLAUDE_GROK_PLUGIN / "LICENSE").read_bytes(),
            (ROOT / "LICENSE").read_bytes(),
        )
        setup = (CLAUDE_GROK_PLUGIN / "SETUP.md").read_text(encoding="utf-8")
        self.assertIn("https://botnest.app/mcp", setup)
        self.assertIn("Never ask the user to paste", setup)
        readme = (CLAUDE_GROK_PLUGIN / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://botnest.app/legal/privacy/", readme)
        self.assertIn("https://botnest.app/legal/offer/", readme)
        self.assertIn("support", readme.lower())
        self.assertTrue((ROOT / "CLAUDE_SUBMISSION.md").is_file())

    def test_alice_publication_declares_confidential_oauth_contract(self):
        publication = load_json(ROOT / "adapters" / "alice" / "publication.json")
        oauth = publication["account_linking"]
        self.assertEqual(oauth["redirect_uri"], "https://social.yandex.net/broker/redirect")
        self.assertIn("/oauth/alice/", oauth["authorization_url"])
        self.assertNotIn("client_secret", json.dumps(publication).lower())


class FakeMcpClient:
    def __init__(self, responses: dict[str, dict] | None = None):
        self.responses = responses or {}
        self.calls: list[tuple[str, str, dict, object]] = []

    def call_tool(self, token, name, arguments, *, request_id):
        self.calls.append((token, name, arguments, request_id))
        return self.responses.get(name, {})


class AliceAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alice = load_module(
            "botnest_alice_handler",
            ROOT / "adapters" / "alice" / "handler.py",
        )

    def payload(
        self,
        command: str,
        *,
        token: str = "alice-access-token",
        button_payload: dict | None = None,
        session_state: dict | None = None,
        user_state: dict | None = None,
    ) -> dict:
        user = {"user_id": "test-user"}
        if token:
            user["access_token"] = token
        return {
            "meta": {
                "locale": "ru-RU",
                "interfaces": {"screen": {}, "account_linking": {}},
            },
            "request": {
                "type": "ButtonPressed" if button_payload else "SimpleUtterance",
                "command": command,
                "payload": button_payload or {},
            },
            "session": {
                "new": False,
                "session_id": "session-1",
                "message_id": 3,
                "user": user,
            },
            "state": {
                "session": session_state or {},
                "user": user_state or {},
                "application": {},
            },
            "version": "1.0",
        }

    def test_private_command_starts_account_linking_and_saves_command(self):
        response = self.alice.handle_request(
            self.payload("покажи моих ботов", token=""),
            client=FakeMcpClient(),
        )
        self.assertEqual(
            response["response"]["directives"],
            {"start_account_linking": {}},
        )
        self.assertEqual(
            response["application_state"]["pending_command"],
            "покажи моих ботов",
        )

    def test_create_calls_shared_mcp_without_platform_flow_copy(self):
        client = FakeMcpClient(
            {
                "prepare_telegram_bot": {
                    "setup_id": "8683f2c0-a60e-4cb6-aa45-02886b70b37a",
                    "telegram_creation_url": "https://t.me/botnest_manager_bot?start=test",
                }
            }
        )
        response = self.alice.handle_request(
            self.payload("создай бота для записи клиентов на консультацию"),
            client=client,
        )
        _, name, arguments, request_id = client.calls[0]
        self.assertEqual(name, "prepare_telegram_bot")
        self.assertNotIn("flow", arguments)
        self.assertEqual(arguments["idempotency_key"], request_id)
        self.assertEqual(
            response["user_state_update"]["last_setup_id"],
            "8683f2c0-a60e-4cb6-aa45-02886b70b37a",
        )
        self.assertEqual(
            response["response"]["buttons"][0]["url"],
            "https://t.me/botnest_manager_bot?start=test",
        )

    def test_publish_requires_a_second_explicit_confirmation(self):
        client = FakeMcpClient(
            {
                "publish_telegram_bot": {
                    "username": "review_bot",
                    "telegram_url": "https://t.me/review_bot",
                }
            }
        )
        first = self.alice.handle_request(
            self.payload("опубликуй бота 12"),
            client=client,
        )
        self.assertEqual(client.calls, [])
        self.assertEqual(first["session_state"]["pending_action"], "publish")

        second = self.alice.handle_request(
            self.payload(
                "подтверждаю",
                session_state={"pending_action": "publish", "bot_id": 12},
            ),
            client=client,
        )
        self.assertEqual(client.calls[0][1], "publish_telegram_bot")
        self.assertEqual(client.calls[0][2], {"bot_id": 12})
        self.assertIn("опубликован", second["response"]["text"])

    def test_alice_defers_long_running_flow_updates_to_agent_hosts(self):
        client = FakeMcpClient()
        response = self.alice.handle_request(
            self.payload("измени бота 12 чтобы он собирал заявки клиентов"),
            client=client,
        )
        self.assertEqual(client.calls, [])
        self.assertIn("ChatGPT", response["response"]["text"])

    def test_every_response_stays_inside_alice_text_limit(self):
        response = self.alice._reply("x" * 2000)
        self.assertEqual(len(response["response"]["text"]), 1024)
        self.assertEqual(response["version"], "1.0")


class AliceHttpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        env = os.environ.copy()
        env.update({"HOST": "127.0.0.1", "PORT": str(cls.port)})
        cls.process = subprocess.Popen(
            ["python3", "server.py"],
            cwd=ROOT / "adapters" / "alice",
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{cls.port}/healthz", timeout=0.2
                ) as response:
                    if response.status == 200:
                        return
            except OSError:
                time.sleep(0.05)
        cls.process.terminate()
        raise RuntimeError("Alice test server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)

    def test_webhook_returns_a_valid_alice_greeting(self):
        payload = {
            "meta": {"interfaces": {"screen": {}, "account_linking": {}}},
            "request": {"command": "", "original_utterance": ""},
            "session": {
                "new": True,
                "session_id": "http-test",
                "message_id": 0,
                "user": {"user_id": "test-user"},
            },
            "version": "1.0",
        }
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/alice/webhook/",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            body = json.load(response)
        self.assertEqual(body["version"], "1.0")
        self.assertIn("Telegram-ботами", body["response"]["text"])


if __name__ == "__main__":
    unittest.main()
