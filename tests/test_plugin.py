from __future__ import annotations

import importlib.util
import json
import struct
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "botnest"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_proxy():
    path = PLUGIN / "scripts" / "botnest_mcp_proxy.py"
    spec = importlib.util.spec_from_file_location("botnest_mcp_proxy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError(f"{path} is not a valid PNG")
    return struct.unpack(">II", data[16:24])


class PluginPackageTests(unittest.TestCase):
    def test_repository_contains_exactly_one_plugin(self):
        plugin_names = sorted(path.name for path in (ROOT / "plugins").iterdir() if path.is_dir())
        self.assertEqual(plugin_names, ["botnest"])

    def test_manifest_is_production_ready(self):
        manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        self.assertEqual(manifest["name"], "botnest")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")
        self.assertEqual(
            manifest["repository"],
            "https://github.com/botnest-app/botnest-plugin",
        )
        interface = manifest["interface"]
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        self.assertTrue(all(len(prompt) <= 128 for prompt in interface["defaultPrompt"]))
        self.assertEqual(interface["websiteURL"], "https://botnest.app/")
        self.assertEqual(
            interface["privacyPolicyURL"],
            "https://botnest.app/legal/privacy/",
        )
        self.assertEqual(
            interface["termsOfServiceURL"],
            "https://botnest.app/legal/offer/",
        )

    def test_marketplace_is_standalone(self):
        marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")
        self.assertEqual(marketplace["name"], "botnest")
        self.assertEqual(marketplace["interface"]["displayName"], "botnest")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "botnest")
        self.assertEqual(entry["source"]["path"], "./plugins/botnest")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")

    def test_brand_assets_are_valid_square_pngs(self):
        manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        for field in ("composerIcon", "logo"):
            path = PLUGIN / manifest["interface"][field]
            width, height = png_size(path)
            self.assertEqual(width, height)
            self.assertGreaterEqual(width, 48)
            self.assertLessEqual(width, 4096)
            self.assertLessEqual(path.stat().st_size, 5 * 1024 * 1024)

    def test_bundle_has_no_stage_or_lmn_tools_references(self):
        forbidden = ("stage.botnest.app", "codex-lmn-tools", "LMN Tools")
        for path in PLUGIN.rglob("*"):
            if not path.is_file() or path.suffix in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".pyc",
            }:
                continue
            text = path.read_text(encoding="utf-8")
            for value in forbidden:
                self.assertNotIn(value, text, f"{value!r} found in {path}")

    def test_skill_frontmatter_and_core_safety_rules(self):
        skill = (PLUGIN / "skills" / "create-telegram-bot" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertTrue(skill.startswith("---\nname: create-telegram-bot\n"))
        self.assertIn("Never ask the user to paste a Telegram bot token", skill)
        self.assertIn("explicitly asks to publish", skill)
        self.assertIn("get_telegram_bot_diagnostics", skill)


class McpBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proxy = load_proxy()

    def test_bridge_targets_production(self):
        self.assertEqual(self.proxy.BASE_URL, "https://botnest.app")
        self.assertEqual(self.proxy.MCP_URL, "https://botnest.app/mcp")

    def test_mcp_manifest_uses_the_production_bridge(self):
        config = load_json(PLUGIN / ".mcp.json")
        self.assertEqual(list(config["mcpServers"]), ["botnest"])
        server = config["mcpServers"]["botnest"]
        self.assertEqual(server["command"], "python3")
        self.assertEqual(server["args"], ["./scripts/botnest_mcp_proxy.py"])
        self.assertNotIn("url", server)

    def test_every_tool_has_review_annotations_and_output_schema(self):
        response = self.proxy.dispatch(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        )
        tools = response["result"]["tools"]
        self.assertGreaterEqual(len(tools), 10)
        for tool in tools:
            self.assertEqual(tool["inputSchema"]["type"], "object")
            self.assertEqual(tool["outputSchema"]["type"], "object")
            annotations = tool["annotations"]
            for name in ("readOnlyHint", "destructiveHint", "openWorldHint"):
                self.assertIs(type(annotations[name]), bool, f"{tool['name']}.{name}")

    def test_manifest_and_skill_paths_exist(self):
        manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
        self.assertTrue((PLUGIN / manifest["skills"]).is_dir())
        self.assertTrue((PLUGIN / manifest["mcpServers"]).is_file())


if __name__ == "__main__":
    unittest.main()
