from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_PLUGIN = ROOT / "plugins" / "botnest"
CLAUDE_PLUGIN = ROOT / "platforms" / "claude" / "botnest"
PERPLEXITY_PLUGIN = ROOT / "platforms" / "perplexity" / "botnest"


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
            load_json(CLAUDE_PLUGIN / ".claude-plugin" / "plugin.json")[
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
            CLAUDE_PLUGIN,
            PERPLEXITY_PLUGIN,
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

    def test_claude_uses_remote_mcp_package(self):
        marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual(marketplace["plugins"][0]["source"], "./platforms/claude/botnest")
        mcp = load_json(CLAUDE_PLUGIN / ".mcp.json")
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
            (CLAUDE_PLUGIN / "skills" / "create-telegram-bot" / "SKILL.md").read_bytes(),
            (CODEX_PLUGIN / "skills" / "create-telegram-bot" / "SKILL.md").read_bytes(),
        )
        self.assertFalse((CLAUDE_PLUGIN / "scripts" / "botnest_mcp_proxy.py").exists())

    def test_perplexity_uses_remote_mcp_oauth_and_shared_skill(self):
        connector = load_json(PERPLEXITY_PLUGIN / "connector.json")
        self.assertEqual(connector["distribution"], "custom-remote-connector")
        self.assertEqual(connector["mcp_server_url"], "https://botnest.app/mcp")
        self.assertEqual(connector["transport"], "Streamable HTTP")
        authentication = connector["authentication"]
        self.assertEqual(authentication["type"], "OAuth 2.0")
        self.assertTrue(authentication["dynamic_client_registration"])
        self.assertEqual(
            authentication["redirect_urls"],
            [
                "https://www.perplexity.ai/rest/connections/oauth_callback",
                "https://enterprise.perplexity.ai/rest/connections/oauth_callback",
            ],
        )
        self.assertEqual(
            (PERPLEXITY_PLUGIN / "skills" / "create-telegram-bot" / "SKILL.md").read_bytes(),
            (CODEX_PLUGIN / "skills" / "create-telegram-bot" / "SKILL.md").read_bytes(),
        )
        self.assertLessEqual((PERPLEXITY_PLUGIN / "icon.png").stat().st_size, 128 * 1024)
        self.assertTrue((ROOT / connector["submission_file"]).is_file())
        readme = (PERPLEXITY_PLUGIN / "README.md").read_text(encoding="utf-8")
        self.assertIn("Account settings → Connectors", readme)
        self.assertIn("Customize → Skills", readme)
        self.assertIn("public self-service marketplace submission", readme)

    def test_claude_package_is_ready_for_directory_submission(self):
        manifest = load_json(
            CLAUDE_PLUGIN / ".claude-plugin" / "plugin.json"
        )
        self.assertEqual(manifest["displayName"], "BotNest — Telegram Bot Builder")
        self.assertEqual(manifest["license"], "Apache-2.0")
        self.assertIn("botnest", manifest["keywords"])
        self.assertEqual(
            (CLAUDE_PLUGIN / "LICENSE").read_bytes(),
            (ROOT / "LICENSE").read_bytes(),
        )
        setup = (CLAUDE_PLUGIN / "SETUP.md").read_text(encoding="utf-8")
        self.assertIn("https://botnest.app/mcp", setup)
        self.assertIn("Never ask the user to paste", setup)
        readme = (CLAUDE_PLUGIN / "README.md").read_text(encoding="utf-8")
        self.assertIn("https://botnest.app/legal/privacy/", readme)
        self.assertIn("https://botnest.app/legal/offer/", readme)
        self.assertIn("support", readme.lower())
        self.assertTrue((ROOT / "CLAUDE_SUBMISSION.md").is_file())


if __name__ == "__main__":
    unittest.main()
