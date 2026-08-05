#!/usr/bin/env python3
"""Build a deterministic plugin archive for local testing and review."""

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "botnest"
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
    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    version = manifest["version"]
    plugin_output = DIST / f"botnest-{version}.zip"
    skill_output = DIST / "create-telegram-bot-skill.zip"
    DIST.mkdir(exist_ok=True)

    plugin_files = sorted(
        path
        for path in PLUGIN.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    skill_files = sorted(path for path in SKILL.rglob("*") if path.is_file())
    write_archive(plugin_output, PLUGIN, plugin_files)
    write_archive(skill_output, SKILL, skill_files)

    print(plugin_output.relative_to(ROOT))
    print(skill_output.relative_to(ROOT))


if __name__ == "__main__":
    main()
