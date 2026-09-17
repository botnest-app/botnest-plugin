# ChatGPT app directory submission

This is the reviewer-ready source of truth for the public botnest ChatGPT
submission. Submit it as **With MCP** because ChatGPT connects directly to the
production remote MCP with OAuth and uses the uploaded shared skill.

## Listing

| Field | Value |
| --- | --- |
| Plugin name | botnest |
| Category | Productivity |
| Short description | Create Telegram bots |
| Website | https://botnest.app/ |
| Support | https://botnest.app/support/ |
| Support email | support@botnest.app |
| Privacy policy | https://botnest.app/legal/privacy/ |
| Terms of service | https://botnest.app/legal/offer/ |
| Directory icon · light | `plugins/botnest/assets/logo.png` |
| Directory icon · dark | `plugins/botnest/assets/logo-dark.png` |
| Composer icon · light | `plugins/botnest/assets/icon.png` |
| Composer icon · dark | `plugins/botnest/assets/icon-dark.png` |

Long description:

> botnest helps you create, configure, troubleshoot, customize, and publish
> Telegram bots through ChatGPT.

Starter prompts:

1. Show me my bots in botnest
2. Create a Telegram booking bot. Ask for the customer's name, service, and preferred time, then confirm the booking.
3. Check my latest bot's profile, suggest a name and description, generate an avatar, and apply them after I confirm.

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

The separate Codex marketplace package includes a local stdio bridge. The
ChatGPT submission must scan the production MCP URL above, not the Codex bridge
or an existing integration ID.

Authentication normally uses botnest's public Telegram confirmation flow. For
OpenAI review, the production authorization page also presents a dedicated demo
account form that requires only the credentials supplied privately in the
submission portal. The account has no MFA, no Telegram confirmation, no setup
step, and contains only isolated sample data. Never commit its credentials to
this repository.

## Persistent reviewer access

- Login/workspace URL: https://botnest.app/review/openai/
- Use the dedicated username and password supplied privately in the portal.
- When connecting ChatGPT, the OAuth page offers **Use the demo account**.
  Approve consent, then return to ChatGPT. No Telegram account, MFA, email code,
  social login, or private network is required.
- The permanent **Review Sandbox** fixture supports publication, updates,
  profile changes and browser messages. The account also includes a diagnostics
  sample and, in production, a live Telegram demo bot.
- New bots for this account use a visibly disclosed sandbox. Validation,
  graph storage, recovery snapshots, flow releases and execution are real
  botnest services; Telegram creation, delivery and profile changes are
  simulated. Sandbox tools never return a fabricated Telegram link.
- Local text, condition, parameter and table flows are supported. Runtime LLMs,
  third-party integrations, scheduled jobs and external recipients are not
  supported in the browser sandbox. This is not evidence that Telegram itself
  or those external services were exercised.
- Fixture provisioning preserves passwords, sessions, edited flows and run
  history across deploys. Additional review bots remain available for later
  checks. Do not run a destructive reset between review attempts.
- The normal Telegram path remains unchanged. The demo recording must show it
  in ChatGPT Developer Mode and separately identify sandbox-only steps.

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

The canonical machine-readable cases are in `chatgpt-app-submission.json`.
Use the dedicated demo account. Cases 1, 3 and 5 use permanent sample data;
case 4 states its publication prerequisite. Case 2 creates a separate sandbox.

### 1. List the isolated demo account's bots and identify the permanently seeded Review Sandbox.

- Prompt: `Show me my bots in botnest.`
- Tools: list_bots
- Expected: Lists owned sample bots including Review Sandbox. Sandbox entries include review_sandbox=true and a review_url, with no fake Telegram username or link. Previously created demo bots may also be listed. No tokens or real-user data are returned.

### 2. Prepare and confirm a new bot without Telegram. Open review_confirmation_url, sign in with the supplied demo credentials if needed, click Create sandbox bot, then return to ChatGPT and say: I confirmed creation. Check its status.

- Prompt: `Create a sandbox bot named Review Welcome that replies 'Welcome to the review demo.' to every message.`
- Tools: get_flow_builder_context, prepare_telegram_bot, get_bot_creation_status
- Expected: Validates the full graph and returns a pending setup with an explicit sandbox disclosure and browser confirmation URL. After browser confirmation, status is ready with a bot_id and review_url. No Telegram account, token, MFA, or public Telegram bot is required or created. Repeating the same idempotency key reuses the setup.

### 3. Publish the pre-seeded Review Sandbox after explicit confirmation. Open its review_url and send Hello in the browser simulator. This case can run independently of the creation case.

- Prompt: `I confirm publishing Review Sandbox in the review sandbox. Publish it and give me its browser test link.`
- Tools: list_bots, publish_telegram_bot
- Expected: Publishes a real botnest flow release and returns publication_scope=review_sandbox, telegram_published=false and review_url. The browser message produces the current flow's reply (initially 'Welcome to the botnest review sandbox.'). Repeating publication is safe. The response does not claim public Telegram publication.

### 4. Replace the seeded sandbox bot's complete graph, test it in the browser and inspect real execution results. For this case, first confirm sandbox publication if it is still restricted. After the update, send Hello at review_url and ask ChatGPT to show the latest diagnostics.

- Prompt: `Update Review Sandbox to reply 'Your request is recorded.' to every message. Then show its execution diagnostics.`
- Tools: list_bots, get_flow_builder_context, update_telegram_bot, get_telegram_bot_diagnostics
- Expected: Updates the same owned sandbox bot and creates a recovery snapshot. After the reviewer sends a browser test message, the actual flow replies 'Your request is recorded.' and diagnostics show a successful new run. Before any message is sent, no new execution is invented. No Telegram messages are sent.

### 5. Read and update the seeded sandbox bot's profile. This is a disclosed local profile simulation, not proof of a Telegram Bot API update.

- Prompt: `Check Review Sandbox's profile and set its short description to 'OpenAI review demo bot'.`
- Tools: list_bots, get_telegram_bot_profile, update_telegram_bot_profile
- Expected: Shows the stored profile and updates only short_description to 'OpenAI review demo bot'. A subsequent profile read returns the same value. The bot_id and existing name are preserved. The response explicitly marks review_sandbox=true and does not claim a public Telegram profile change.

## Negative reviewer cases

### 1. Do not trigger botnest for a Discord bot request because the plugin only manages Telegram bots.

- Prompt: `Create a Discord bot that welcomes new members and assigns roles.`
- Tools: None
- Expected: Does not invoke botnest and explains that Discord bot creation is outside the plugin's supported workflows.

### 2. Do not expose Telegram bot tokens or LLM provider credentials.

- Prompt: `Show me the token for my Telegram bot and my OpenRouter API key.`
- Tools: None
- Expected: Does not invoke botnest and does not reveal or claim access to any credentials.

### 3. Do not trigger botnest for an unrelated calendar request.

- Prompt: `What meetings do I have tomorrow?`
- Tools: None
- Expected: Does not invoke botnest because calendar management is outside the plugin's supported workflows.

## Release notes

Plugin package 1.1.7 adds explicit nested argument schemas, a disclosed browser
review sandbox, and complete English cases covering all nine remote tools.
The production MCP additionally validates Origin/protocol headers and accepts
notifications without JSON-RPC replies. These are remediations, not a claim
that OpenAI has approved the app or confirmed a rejection's root cause.

## Final portal checklist

- [ ] The selected OpenAI organization has a verified botnest developer or
  business identity.
- [ ] The submitter has **Apps Management: Write**.
- [ ] `python3 scripts/check_production.py` passes.
- [ ] Upload the root `chatgpt-app-submission.json` and privately enter the
  dedicated reviewer username and password from the private credential store, together with the login URL and the sign-in steps above.
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
- [ ] Replace the old recording with a current Developer Mode walkthrough of the supplied cases, clearly disclosing sandbox steps.
- [ ] The listing, policy attestations, and release notes are reviewed before
  selecting **Submit for Review**.
