#!/usr/bin/env python3
"""Build a deterministic plugin archive for local testing and review."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "botnest"
CLAUDE_PLUGIN = ROOT / "platforms" / "claude" / "botnest"
PERPLEXITY_PLUGIN = ROOT / "platforms" / "perplexity" / "botnest"
SKILL = PLUGIN / "skills" / "create-telegram-bot"
DIST = ROOT / "dist"


def write_archive(output: Path, base: Path, files: list[Path]) -> None:
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(base)
            info = ZipInfo(str(Path(base.name) / relative), (2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (0o755 if path.suffix == ".py" else 0o644) << 16
            archive.writestr(info, path.read_bytes())


def main() -> None:
    generator_path = ROOT / "scripts" / "generate_platforms.py"
    spec = importlib.util.spec_from_file_location("generate_platforms", generator_path)
    generator = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(generator)
    config = generator.load_config()
    if generator.check_files(generator.generated_files(config)):
        raise SystemExit(1)

    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    version = manifest["version"]
    codex_output = DIST / f"botnest-codex-{version}.zip"
    claude_output = DIST / f"botnest-claude-{version}.zip"
    perplexity_output = DIST / f"botnest-perplexity-{version}.zip"
    perplexity_skill_output = DIST / f"botnest-perplexity-skill-{version}.zip"
    skill_output = DIST / "create-telegram-bot-skill.zip"
    DIST.mkdir(exist_ok=True)

    codex_files = sorted(
        path
        for path in PLUGIN.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    claude_files = sorted(
        path
        for path in CLAUDE_PLUGIN.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    perplexity_files = sorted(
        path
        for path in PERPLEXITY_PLUGIN.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    skill_files = sorted(path for path in SKILL.rglob("*") if path.is_file())
    write_archive(codex_output, PLUGIN, codex_files)
    write_archive(claude_output, CLAUDE_PLUGIN, claude_files)
    write_archive(perplexity_output, PERPLEXITY_PLUGIN, perplexity_files)
    write_archive(skill_output, SKILL, skill_files)
    write_archive(perplexity_skill_output, SKILL, skill_files)

    print(codex_output.relative_to(ROOT))
    print(claude_output.relative_to(ROOT))
    print(perplexity_output.relative_to(ROOT))
    print(skill_output.relative_to(ROOT))
    print(perplexity_skill_output.relative_to(ROOT))


if __name__ == "__main__":
    main()
