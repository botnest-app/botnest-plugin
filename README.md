<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="plugins/botnest/assets/logo-dark.png">
    <img src="plugins/botnest/assets/logo.png" width="128" height="128" alt="botnest logo">
  </picture>
</p>

<h1 align="center">botnest for ChatGPT and Codex</h1>

<p align="center">
  Create, improve, diagnose, brand, and publish Telegram bots using plain language.
</p>

This repository contains one production plugin: **botnest**. It combines a
focused workflow skill with a local MCP bridge to the production service at
`https://botnest.app/mcp`.

## What it does

- Designs complete Telegram bot flows from a natural-language brief.
- Creates and updates bot behavior without asking users for Telegram tokens.
- Connects compatible LLM credentials through a guided OpenRouter flow.
- Diagnoses failed flow runs before proposing changes.
- Updates bot names, descriptions, commands, menus, localizations, and avatars.
- Publishes a ready bot only after explicit user confirmation.

## Install

Python 3.10 or newer is required for the bundled local MCP bridge.

```bash
codex plugin marketplace add botnest-app/botnest-plugin --ref main
codex plugin add botnest@botnest
```

Restart the ChatGPT desktop app, enable **botnest** in Plugins, and start a new
conversation. Authentication happens through botnest's HTTPS Telegram flow;
never paste a bot token, API key, callback URL, or authorization code into the
conversation.

## Repository layout

```text
.
├── .agents/plugins/marketplace.json  # standalone botnest marketplace
├── plugins/botnest/                  # the only plugin package
│   ├── .codex-plugin/plugin.json
│   ├── .mcp.json
│   ├── assets/
│   ├── scripts/
│   └── skills/
├── scripts/                          # validation and packaging helpers
├── tests/
├── chatgpt-app-submission.json       # upload-ready OpenAI review form data
└── SUBMISSION.md                     # OpenAI review form copy and test cases
```

## Validate and package

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_package.py
python3 scripts/check_production.py
```

The package command creates `dist/botnest-<version>.zip` and the standalone
`dist/create-telegram-bot-skill.zip` accepted by the OpenAI submission form.
The production check verifies the MCP endpoint, OAuth discovery, and public
legal/support pages used by the OpenAI submission.

For the exact listing copy, MCP configuration, reviewer scenarios, and final
portal checklist, see [SUBMISSION.md](SUBMISSION.md).

## Security and privacy

The local bridge stores OAuth credentials inside the plugin's private
`PLUGIN_DATA` directory with restrictive filesystem permissions. It never asks
for Telegram bot tokens or LLM API keys in chat. Avatar uploads are limited to
supported images in Codex-generated image directories.

- Privacy: <https://botnest.app/legal/privacy/>
- Terms: <https://botnest.app/legal/offer/>
- Support: <https://github.com/botnest-app/botnest-plugin/issues>
- Vulnerability reporting: [SECURITY.md](SECURITY.md)
