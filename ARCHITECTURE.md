# Cross-platform architecture

## Decision

Keep every client integration in this repository and keep the BotNest backend
in its existing service repository.

Splitting ChatGPT, Codex, Claude, and Grok into separate repositories
would duplicate manifests, release versions, brand assets, safety rules, and
the agent workflow. Moving the backend into this repository would couple
distribution packages to secrets, database migrations, and service deployment.
The chosen boundary keeps both sides independently deployable.

## Layers

```text
botnest.plugin.json + shared skill/assets
                    |
          generate_platforms.py
                    |
   +----------------+--------------------+
   |                |                    |
ChatGPT          Codex             Claude + Grok
remote MCP       local bridge      remote MCP package
   |                |                    |
   +----------------+--------------------+
                    |
          https://botnest.app/mcp
                    |
              BotNest backend
```

The shared layer contains product metadata, natural-language workflow rules,
tool semantics, safety requirements, and assets. Adapters contain only what the
host platform forces us to vary: transport, manifests, catalog data,
authorization handoff, and conversational protocol.

## Platform boundaries

### ChatGPT

ChatGPT is submitted as a remote MCP integration with OAuth metadata. It does
not need the Codex local proxy. OpenAI-only review cases and policy
justifications remain in `chatgpt-app-submission.json` because other catalogs
do not use that schema.

### Codex

Codex installs `plugins/botnest`. Its local stdio proxy implements callback-free
device authorization and forwards the shared tool contract to production.

### Claude and Grok

Claude installs `platforms/claude-grok/botnest`, which contains the generated
copy of the shared skill/assets and a remote HTTP MCP definition. Grok consumes
the same package through Claude Code compatibility; a separate Grok fork would
have no platform-specific behavior today.

## Ownership and generation rules

- Edit version, URLs, listing metadata, or common platform settings only in
  `botnest.plugin.json`.
- Edit agent behavior only in
  `plugins/botnest/skills/create-telegram-bot/SKILL.md`.
- Do not manually edit files under `platforms/claude-grok/botnest`, generated
  manifests, or `runtime.json`.
- Platform policy/review forms and executable adapters remain hand-maintained
  because they contain genuinely platform-specific logic.
- Run `python3 scripts/generate_platforms.py --check` in CI before tests and
  packaging.

## Adding another platform

Add a thin adapter only after identifying the platform's transport,
authorization, manifest/catalog format, confirmation semantics, and response
deadline. Reuse the remote MCP whenever the platform supports it. Do not fork
the shared skill unless the host cannot run agent instructions.
