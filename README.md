<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="plugins/botnest/assets/logo-dark.png">
    <img src="plugins/botnest/assets/logo.png" width="128" height="128" alt="botnest logo">
  </picture>
</p>

<h1 align="center">botnest integrations</h1>

<p align="center">
  One product source for ChatGPT and Codex, Claude, and Perplexity.
</p>

This repository is the distribution monorepo for **botnest**. Product metadata,
the agent workflow, brand assets, and the production MCP contract are maintained
once and rendered into the platform packages that need them.

The BotNest application backend remains a separate service and repository. It
owns user data, OAuth grants, Telegram credentials, and the production MCP at
`https://botnest.app/mcp`; none of those secrets are copied into a plugin.

## Platform model

| Platform | Distribution | Runtime connection |
| --- | --- | --- |
| ChatGPT | ChatGPT app directory submission | Direct remote MCP + native OAuth; works on mobile |
| Codex | OpenAI plugin marketplace package | Local stdio bridge + Telegram device authorization |
| Claude | Claude plugin marketplace package | Direct remote MCP + native OAuth |
| Perplexity | Custom remote connector + uploaded skill | Direct remote MCP + native OAuth |

OpenAI intentionally has two adapters. ChatGPT uses the remote MCP/OAuth path,
while the installable Codex plugin keeps the local bridge path. They share the
same BotNest tools and workflow rather than maintaining separate product logic.

## Source of truth

- `botnest.plugin.json` is the canonical version, listing, service URL, and
  platform configuration.
- `plugins/botnest/skills/create-telegram-bot/SKILL.md` is the shared agent
  workflow used by ChatGPT, Codex, Claude, and Perplexity.
- `plugins/botnest/assets/` contains the shared brand assets.
- `plugins/botnest/scripts/botnest_mcp_proxy.py` is Codex-specific transport.
- `chatgpt-app-submission.json` contains OpenAI-specific review cases and tool
  policy justifications.

`scripts/generate_platforms.py` renders the Codex manifest and marketplace, the
ChatGPT remote-connector descriptor, the Claude package and marketplace, the
Perplexity connector bundle, and the runtime configuration. Generated drift is
a CI error, so generated platform copies cannot silently diverge.

See [ARCHITECTURE.md](ARCHITECTURE.md) for boundaries and release rules.

## Install and publish

### ChatGPT

Submit `https://botnest.app/mcp` as the remote MCP server using the data in
`chatgpt-app-submission.json` and `SUBMISSION.md`. ChatGPT performs the OAuth
flow against BotNest directly; the standalone skill archive is produced for the
submission flow when needed.

### Codex

Python 3.10 or newer is required for the bundled local MCP bridge.

```bash
codex plugin marketplace add botnest-app/botnest-plugin --ref main
codex plugin add botnest@botnest
```

Restart the app, enable **botnest**, and start a new conversation.

### Claude

```text
/plugin marketplace add botnest-app/botnest-plugin
/plugin install botnest@botnest
```

The generated package under `platforms/claude/botnest` connects directly
to the production MCP and lets Claude handle OAuth.

For public-directory review, submit this repository through Claude Console and
use the reviewer information in `CLAUDE_SUBMISSION.md`. The generated package
is also available as `dist/botnest-claude-<version>.zip` when an archive is
requested.

### Perplexity

Add BotNest from **Account settings → Connectors → + Custom connector → Remote**
using `https://botnest.app/mcp`, OAuth, and Streamable HTTP. Then upload
`dist/botnest-perplexity-skill-<version>.zip` under **Customize → Skills** in
Perplexity Computer. Exact field values and current availability constraints
are documented in `platforms/perplexity/botnest/README.md` and
`PERPLEXITY_SUBMISSION.md`.

Perplexity currently exposes this as a custom connector, not an open public
marketplace submission. A built-in catalogue tile requires separate
coordination with Perplexity.

## Change once, release everywhere

1. Edit `botnest.plugin.json`, the shared skill/assets, or a genuinely
   platform-specific adapter.
2. Regenerate tracked platform artifacts.
3. Run tests, build archives, and check the production MCP.

```bash
python3 scripts/generate_platforms.py
python3 scripts/generate_platforms.py --check
python3 -m unittest discover -s tests -v
python3 scripts/build_package.py
python3 scripts/check_production.py
```

The package command creates:

- `dist/botnest-codex-<version>.zip`
- `dist/botnest-claude-<version>.zip`
- `dist/botnest-perplexity-<version>.zip`
- `dist/botnest-perplexity-skill-<version>.zip`
- `dist/create-telegram-bot-skill.zip`

## Security and privacy

The Codex bridge stores OAuth credentials inside the plugin's private data
directory with restrictive permissions. Remote-MCP platforms keep OAuth in
their native connector flow. No adapter asks users to paste Telegram bot tokens
or LLM API keys into a conversation.

- Privacy: <https://botnest.app/legal/privacy/>
- Terms: <https://botnest.app/legal/offer/>
- Support: <https://github.com/botnest-app/botnest-plugin/issues>
- Vulnerability reporting: [SECURITY.md](SECURITY.md)

## License

The plugin distributions and their source in this repository are licensed
under the [Apache License 2.0](LICENSE).
