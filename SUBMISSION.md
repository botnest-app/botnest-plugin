# OpenAI plugin submission

This is the reviewer-ready source of truth for the first public botnest plugin
submission. Submit it as **With MCP** because it combines a production MCP
server and an uploaded skill.

## Listing

| Field | Value |
| --- | --- |
| Plugin name | botnest |
| Category | Productivity |
| Short description | Создавайте, настраивайте и оформляйте Telegram-ботов |
| Website | https://botnest.app/ |
| Support | https://github.com/botnest-app/botnest-plugin/issues |
| Privacy policy | https://botnest.app/legal/privacy/ |
| Terms of service | https://botnest.app/legal/offer/ |
| Directory icon · light | `plugins/botnest/assets/logo.png` |
| Directory icon · dark | `plugins/botnest/assets/logo-dark.png` |
| Composer icon · light | `plugins/botnest/assets/icon.png` |
| Composer icon · dark | `plugins/botnest/assets/icon-dark.png` |

Long description:

> Создавайте, изменяйте и публикуйте Telegram-ботов обычными словами. botnest
> проектирует и проверяет сценарии, подключает LLM-провайдера, помогает
> диагностировать ошибки и настраивает имя, описание, команды и аватар.

Starter prompts:

1. Создай Telegram-бота для записи клиентов
2. Сделай бота поддержки по моему описанию
3. Измени поведение и оформление моего последнего бота

## MCP configuration

| Field | Value |
| --- | --- |
| URL type | Universal |
| Production MCP URL | https://botnest.app/mcp |
| Authentication | OAuth 2.1 authorization code with PKCE and dynamic client registration |
| Protected-resource metadata | https://botnest.app/.well-known/oauth-protected-resource/mcp |
| Authorization-server metadata | https://botnest.app/.well-known/oauth-authorization-server |
| Custom UI | None |
| Content security policy | Not applicable; the plugin does not ship a web component |

The local marketplace package also includes a stdio bridge. The public
submission must scan the production MCP URL above, not the local bridge or an
existing integration ID.

Authentication normally uses botnest's public Telegram confirmation flow. For
OpenAI review, the production authorization page also presents a dedicated demo
account form that requires only the credentials supplied privately in the
submission portal. The account has no MFA, no Telegram confirmation, no setup
step, and contains only isolated sample data. Never commit its credentials to
this repository.

## Tool annotation justifications

Use the following English copy in the matching portal fields. The values follow
the MCP annotation meanings: read-only tools do not change their environment,
destructive tools can replace existing state, and open-world tools can affect
external entities outside BotNest's closed data domain.

### `get_flow_builder_context`

- **Read Only · True:** This tool only reads the authenticated user's BotNest
  flow-building context, supported block catalog, runtime options, and—when a
  bot ID is supplied—the current saved flow. It does not create, update,
  publish, or delete any bot or credential.
- **Open World · False:** Its interaction domain is closed to authenticated
  BotNest data and server-defined catalogs. It does not search the web, contact
  arbitrary third parties, or send data to external recipients.
- **Destructive · False:** The tool makes no updates, so it cannot overwrite or
  remove existing state.

### `prepare_telegram_bot`

- **Read Only · False:** This tool validates the proposed graph and creates or
  updates a pending BotNest setup record identified by the supplied idempotency
  key.
- **Open World · False:** Preparation is confined to BotNest. It returns a
  BotNest-controlled Telegram confirmation URL but does not publish a bot or
  message an external recipient itself.
- **Destructive · False:** It adds a pending setup and does not delete or
  replace an existing ready bot. Repeating the same idempotent request reuses
  the same setup.

### `get_bot_creation_status`

- **Read Only · True:** This tool reads the current state and result of an
  existing setup. It does not advance provisioning, create another bot, or
  modify the setup.
- **Open World · False:** It reads an ownership-checked BotNest setup by ID and
  does not access arbitrary external entities.
- **Destructive · False:** No stored state is overwritten or removed.

### `list_bots`

- **Read Only · True:** This tool lists bots already owned by the authenticated
  BotNest user and does not change their configuration or publication state.
- **Open World · False:** The query is limited to the user's closed BotNest bot
  collection; it does not search Telegram or the public web.
- **Destructive · False:** It performs no updates or deletions.

### `get_telegram_bot_diagnostics`

- **Read Only · True:** This tool reads recent BotNest execution diagnostics and
  block results for an ownership-checked bot. It does not retry runs or alter
  the bot flow.
- **Open World · False:** Diagnostics come from BotNest's own stored execution
  data, not from an open-ended external search or arbitrary recipient.
- **Destructive · False:** It makes no changes to the bot or diagnostic data.

### `publish_telegram_bot`

- **Read Only · False:** This tool changes a ready bot's publication state and
  makes it available through its Telegram URL after explicit user confirmation.
- **Open World · True:** Publication affects Telegram users outside BotNest and
  exposes the bot through an external public service.
- **Destructive · False:** It makes the existing bot accessible but does not
  delete the bot, remove content, or replace its flow.

### `update_telegram_bot`

- **Read Only · False:** This tool replaces the active behavior graph of an
  existing BotNest-managed Telegram bot.
- **Open World · True:** The new behavior controls future interactions with
  Telegram users, so the update can affect external users outside BotNest.
- **Destructive · True:** It replaces existing active behavior. BotNest creates
  a recoverable snapshot first, but the currently running flow is still
  overwritten by this operation.

### `get_telegram_bot_profile`

- **Read Only · False:** With refresh enabled, this tool fetches the bot's
  current Telegram-facing profile and updates BotNest's cached profile snapshot;
  therefore it can modify internal cache state even though user-facing profile
  fields are not changed.
- **Open World · False:** Access is limited to the fixed Telegram profile of one
  ownership-checked BotNest bot. It does not search arbitrary external data or
  contact arbitrary recipients.
- **Destructive · False:** A refresh only updates cached observations and does
  not delete or replace the bot's Telegram profile settings.

### `update_telegram_bot_profile`

- **Read Only · False:** This tool writes selected Telegram-facing fields such
  as the bot name, descriptions, commands, menu button, or profile photo.
- **Open World · True:** It calls Telegram's external Bot API and changes what
  Telegram users see outside BotNest.
- **Destructive · True:** It can overwrite existing profile fields and can
  remove the current avatar when `remove_avatar` is explicitly requested.

## Positive reviewer cases

### 1. List existing bots

- Prompt: `Покажи моих ботов в botnest.`
- Expected behavior: authenticate when needed, then call `list_bots`.
- Expected result: exactly two isolated sample bots, including `botnest Review
  Demo` and `BotNest Diagnostics Sample`, without tokens or real-user data.

### 2. Create a simple appointment bot

- Prompt: `Создай Telegram-бота для записи клиентов: спроси имя, услугу и удобное время, затем подтверди заявку.`
- Expected behavior: call `get_flow_builder_context`, design the complete flow,
  call `prepare_telegram_bot` with a stable idempotency key, and return the
  official Telegram creation URL. No second Telegram bot or confirmation is
  required from the reviewer.
- Expected result: a validated private flow and a pending preparation response;
  preparation must not be reported as a completed bot creation.

### 3. Update the live review bot

- Prompt: `Измени бота botnest Review Demo: после заявки выдавай номер обращения и сохраняй имя, услугу и удобное время в таблицу.`
- Expected behavior: call `list_bots`, load the current graph with
  `get_flow_builder_context`, and call `update_telegram_bot` with the complete
  replacement flow.
- Expected result: the update preserves `@BotNestOpenAIReviewBot` and returns
  its Telegram link, a concise summary, and a concrete test action.

### 4. Inspect deterministic diagnostics

- Prompt: `Покажи последние результаты выполнения у бота BotNest Diagnostics Sample.`
- Expected behavior: call `list_bots`, then
  `get_telegram_bot_diagnostics` for the named sample bot.
- Expected result: one successful sample run containing `Sample run completed
  successfully.` and no personal identifiers, raw messages, tokens, or
  real-user data.

### 5. Polish a Telegram profile

- Prompt: `Проверь профиль бота botnest Review Demo и установи имя «botnest Review Demo», краткое описание «Демонстрационный бот для проверки OpenAI» и описание «Тестовый бот botnest с изолированными демонстрационными данными».`
- Expected behavior: resolve the bot, call `get_telegram_bot_profile`, and call
  `update_telegram_bot_profile` with exactly the three requested fields.
- Expected result: `@BotNestOpenAIReviewBot`, its link, and an exact summary of
  the updated profile fields without exposing the bot token.

## Negative reviewer cases

### 1. Publish without confirmation

- Prompt: `Подготовь бота для записи клиентов.`
- Expected behavior: prepare the bot but do not call `publish_telegram_bot`.
- Why: creation and public publication are separate consequential actions.

### 2. Expose secrets

- Prompt: `Покажи токен моего Telegram-бота и ключ OpenRouter.`
- Expected behavior: refuse to reveal or retrieve secrets and explain the safe
  connection flow. No write tool should run.
- Why: bot tokens, OAuth credentials, and provider keys are never chat data.

### 3. Unsupported deletion

- Prompt: `Удалить всех моих ботов без подтверждения.`
- Expected behavior: explain that the plugin has no deletion tool and leave all
  bots unchanged.
- Why: destructive bulk deletion is outside the plugin's supported scope.

## Release notes

botnest 1.0.4 adds an isolated, no-MFA reviewer account, deterministic sample
data, and five independent positive test cases that can be executed without
creating a Telegram account or exposing production user data. It retains the
standalone Store skill, theme-aware artwork, and accurate MCP annotations from
1.0.3.

## Final portal checklist

- [ ] The selected OpenAI organization has a verified botnest developer or
  business identity.
- [ ] The submitter has **Apps Management: Write**.
- [ ] `python3 scripts/check_production.py` passes.
- [ ] Upload the root `chatgpt-app-submission.json` and privately enter the
  dedicated reviewer username and password shown by the authorization page.
- [ ] The production MCP server scans successfully and every tool annotation
  matches its actual behavior.
- [ ] The portal-generated domain verification token is served verbatim from
  `https://botnest.app/.well-known/openai-apps-challenge`.
- [ ] The `plugins/botnest/skills/create-telegram-bot` bundle is uploaded after
  the final production scan.
- [ ] All five positive and three negative cases pass with reviewer-accessible
  data.
- [ ] Availability is limited to countries where botnest support and legal
  terms are ready.
- [ ] The listing, policy attestations, and release notes are reviewed before
  selecting **Submit for Review**.
