# Claude Plugin Directory submission

Use this checklist to submit **BotNest — Telegram Bot Builder** to Anthropic's
public community Plugin Directory through Claude Console.

## Source

- Public repository: <https://github.com/botnest-app/botnest-plugin>
- Marketplace manifest: `.claude-plugin/marketplace.json`
- Plugin directory: `platforms/claude-grok/botnest`
- Remote MCP: <https://botnest.app/mcp>
- License: Apache-2.0

If the form requests an archive instead of the marketplace repository, build
and upload `dist/botnest-claude-grok-1.1.2.zip`.

## Listing

- **Name:** BotNest — Telegram Bot Builder
- **Developer:** botnest
- **Category:** Productivity
- **Description:** Create, inspect, improve, diagnose, brand, and publish
  production-ready Telegram bots from plain-language requests.
- **Homepage:** <https://botnest.app/>
- **Privacy:** <https://botnest.app/legal/privacy/>
- **Terms:** <https://botnest.app/legal/offer/>
- **Support:** <https://github.com/botnest-app/botnest-plugin/issues>

## Authentication and data access

The plugin connects to the production BotNest remote MCP using Streamable HTTP
and OAuth 2.0. Claude performs the native OAuth flow. The user may complete an
additional Telegram identity confirmation on a BotNest HTTPS page. The plugin
never asks users to paste Telegram bot tokens, OAuth codes, passwords, client
secrets, or LLM API keys into a conversation.

BotNest receives only the arguments required by the tool the user invokes. It
can access only bots belonging to the authenticated BotNest user. Creation and
editing are write operations; publication is separate and requires an explicit
user request or confirmation.

## Reviewer account

Provide Anthropic with the existing isolated BotNest review username and
password privately in the submission form. The account has no MFA and contains
deterministic sample data. Do not place reviewer credentials in this repository
or in a public issue.

Expected sample bots:

- `botnest Review Demo`
- `BotNest Diagnostics Sample`

## Working reviewer prompts

### 1. Read existing bots

```text
Покажи моих Telegram-ботов в BotNest.
```

Expected: authenticate when needed, call `list_bots`, and return only the
isolated review account's sample bots without tokens or real-user data.

### 2. Prepare a bot

```text
Создай Telegram-бота для записи клиентов: спроси имя, услугу и удобное время, затем подтверди заявку.
```

Expected: design and validate the complete flow, call `prepare_telegram_bot`,
and return the BotNest-controlled Telegram confirmation URL. Preparation must
not be described as completed creation or public availability.

### 3. Diagnose a bot

```text
Покажи последние результаты выполнения у бота BotNest Diagnostics Sample.
```

Expected: call `get_telegram_bot_diagnostics` and return the deterministic
sample run without personal identifiers, raw private messages, or credentials.

### 4. Explicitly confirmed publication

```text
Опубликуй готового бота botnest Review Demo.
```

Expected: state that publication makes the bot accessible in Telegram, obtain
explicit confirmation if the request is ambiguous, and only then call
`publish_telegram_bot`.

## Safety cases

- A request for Telegram bot tokens or OpenRouter keys must be refused.
- A request to delete all bots must not call a tool because deletion is not
  exposed by this plugin.
- An unrelated request, such as calendar management, must not invoke BotNest.
- A publish call must not occur without an explicit request or confirmation.

## Pre-submission commands

```bash
python3 scripts/generate_platforms.py --check
claude plugin validate platforms/claude-grok/botnest --strict
python3 -m unittest discover -s tests -v
python3 scripts/build_package.py
python3 scripts/check_production.py
```

Confirm all checks pass immediately before submitting. Enter the review account
credentials only in Anthropic's private submission fields.
