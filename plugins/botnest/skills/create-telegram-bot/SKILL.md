---
name: create-telegram-bot
description: Create, inspect, edit, brand, check, list, or publish BotNest Telegram bots from a plain-language request, including arbitrary custom block graphs, runtime LLM credentials, stateful behavior, Telegram profile text, commands, menu settings, and generated avatars. Use whenever the user asks to make or change a Telegram bot, add AI or an LLM block to a bot, change how a bot looks in Telegram, generate or set a bot avatar, asks about BotNest bots, or wants to publish a prepared BotNest bot.
---

# Create a Telegram bot with BotNest

Turn the user's description into a working BotNest-managed Telegram bot with
as little friction as possible.

## Creating a bot

1. If a BotNest tool returns `authorization_required`, show its HTTPS
   `authorization_url` as a clickable primary action. Tell the user to confirm
   with Telegram and return to this conversation. Never ask them to copy or
   paste a localhost callback, authorization code, device code, password, API
   key, or Telegram bot token.
2. When the user continues after Telegram confirmation, retry the original
   BotNest tool with the same arguments. The host connection completes and
   stores the OAuth session automatically. If authorization is still pending,
   keep showing the same HTTPS URL; do not start a duplicate flow.
3. Treat the user's original description as the source of truth. Preserve all
   requested behavior, questions, tone, data to collect, and success criteria.
4. Ask a follow-up only when the request does not contain enough information to
   infer a useful bot. If a reasonable first version can be made, proceed
   immediately and explain that it can be refined later. When two or more
   materially different implementations are reasonable, briefly state the
   trade-offs and the option you will use by default. Do not make the user
   discover those options only after something fails.
5. Create one stable `idempotency_key` for this creation attempt and keep using
   that exact value for every retry in the conversation.
6. Call `get_flow_builder_context` without a `bot_id`. Design a complete flow
   from the returned `flow_format`, `block_catalog`, constraints, and reaction
   catalog. Do not invent block kinds or fields. If the graph uses an `llm`
   block, follow **LLM runtime credentials** below before preparing the bot.
7. Call `prepare_telegram_bot` with the complete goal, stable key, and complete
   flow. If the user did not choose a name, pass a short neutral
   purpose-based `suggested_name`, such as “Собеседник”, “Помощник записи”, or
   “Поддержка”; never use a fragment of the raw instruction as a name. The host
   model designs the graph; BotNest validates and stores it, so designing a
   custom graph does not depend on the BotNest runtime LLM key.
   Executing an `llm` block does require a runtime credential as described
   below.
   If validation fails, repair every returned detail and retry with the same
   key. Never remove a requirement merely to make validation pass.
8. Present the suggested name and a compact summary of the proposed behavior.
   Give the returned `telegram_creation_url` as the primary next action and ask
   the user to open it and confirm the creation in Telegram.
9. Never ask the user to paste a Telegram bot token. Never display, request, or
   infer bot tokens, OAuth credentials, or other secrets.
10. Do not claim that the bot is ready just because preparation succeeded.
   After the user confirms in Telegram, call `get_bot_creation_status` with the
   returned `setup_id`.
11. If the status is `pending`, `telegram_linked`, or `provisioning`, say what
   is still happening and check again when the user asks or confirms the
   Telegram step is complete.
12. When the status is `ready`, show the bot username and Telegram URL. Briefly
   explain what the generated bot does and give one concrete message or command
   that tests the complete path. Then follow **Optional profile polish** once.

## Creation quality bar

Before preparing or updating a bot, perform a preflight over the complete
runtime path:

1. Every required credential, provider, model, table, output field, and
   downstream placeholder must be selected and compatible. A block merely
   existing in the graph is not enough.
2. For the simplest conversational bot, prefer the minimal path
   `Telegram message → LLM → Telegram reply`. Do not add history, tables, or
   parallel branches unless the request needs them.
3. Use the reliable model returned by `llm_runtime.recommended_model`. Do not
   use `openrouter/free` as an invisible default: it is an experimental
   zero-cost option that may return no text.
4. When useful, tell the user the available choices in one compact sentence:
   for example, reliable/cheap, free/experimental, or higher-quality/more
   expensive. Choose the reliable/cheap option unless the user says otherwise.
5. Do not call a bot “working” until BotNest accepted the complete graph and
   Telegram reports the setup as ready. If the user reports no reply, inspect
   diagnostics before changing the graph or model.

## Publishing

Creation and publication are separate actions. Do not call
`publish_telegram_bot` unless the user explicitly asks to publish the ready bot
or clearly confirms a publication proposal. Before calling it, state that the
bot will become publicly accessible in Telegram. After success, return the
public Telegram URL.

## Editing an existing bot

1. Use `list_bots` to resolve a referenced name, username, “last bot”, or other
   natural-language reference to an owned `bot_id`.
2. Call `get_flow_builder_context` with that `bot_id`. Use `current_flow` as
   the starting point and the returned catalog as the only supported block
   contract. If the resulting graph uses an `llm` block, follow **LLM runtime
   credentials** below before updating the bot.
3. Treat the user's edit request as the complete desired behavior after the
   update. Preserve every requirement, including ordering, state scope, tone,
   and success criteria. Preserve unrelated current behavior unless the user
   explicitly replaces it.
4. Design the complete resulting flow and call `update_telegram_bot` with the
   resolved `bot_id`, complete goal, and complete flow. An explicit user request
   to change that bot is sufficient confirmation. If validation fails, repair
   the graph from the returned details and retry.
5. The update keeps the same Telegram bot and creates a recoverable flow
   snapshot before replacing its behavior. Do not create a replacement bot
   unless the user explicitly asks for one.
6. After success, return the existing username and Telegram URL, summarize the
   new behavior, and give a concrete test action.

## LLM runtime credentials

Treat graph generation and graph execution as separate concerns. The assistant
can design a graph without a BotNest AI subscription, but every runtime `llm`
block must reference a usable BotNest credential.

1. Read `llm_runtime` from the latest `get_flow_builder_context` result before
   preparing or updating any graph that contains an `llm` block.
2. If `llm_runtime.available` is true, put the exact
   `llm_runtime.recommended_credential_id`,
   `llm_runtime.recommended_provider`, and
   `llm_runtime.recommended_model` into each `llm` block unless the user
   explicitly selected another compatible entry. Never invent an ID and never
   leave `credential_id` empty.
3. OpenRouter is the product default. When
   `llm_runtime.openrouter.connected` is false, present
   `llm_runtime.openrouter.connect_url` as the primary clickable authorization
   action and explain that OpenRouter will return them to BotNest automatically.
   If another provider is already available, mention it as the immediate
   alternative instead of hiding that choice.
4. If no credential is available, do not call `prepare_telegram_bot` or
   `update_telegram_bot` with the LLM graph. Keep the complete requested graph
   in the conversation while the user authorizes OpenRouter. Never ask the user
   to paste an API key into any chat or conversation.
5. After authorization, call `get_flow_builder_context` again. Proceed only
   from the fresh response and confirm that the exact selected credential,
   provider, and model are compatible.
6. `openrouter/free` is allowed only when the user explicitly chooses the
   free/experimental trade-off; in that case also set
   `config.allow_experimental_model: true`. For a normal conversational bot, use
   `llm_runtime.openrouter.reliable_default_model` or the selected credential's
   `recommended_model`.
7. Treat `llm_credential_required` as a deterministic missing-key result, not a
   temporary BotNest outage. Treat `llm_credential_invalid` as a stale or
   inaccessible ID: refresh the context and rebuild every LLM block with a
   currently returned ID.
8. Never expose or request credential secrets. The context contains only safe
   labels and opaque IDs; that is sufficient to wire the flow.

## Optional profile polish

After a newly created bot reaches `ready`, mention profile customization once,
without blocking the user from testing the bot:

1. Offer three concise, purpose-specific directions that combine a visible
   name, short description tone, and avatar idea. Prefer the host's interactive
   choice controls when available; otherwise present numbered choices `1–3`
   that can be selected with a one-character reply.
2. Include a quiet escape such as “оставить как есть”. Do not ask a chain of
   separate questions for name, description, and avatar.
3. If the user chooses a direction, call `get_telegram_bot_profile`, generate
   the avatar when requested, and apply the name, short description,
   description, and avatar in one cohesive workflow.
4. Do not repeat the offer after the user declines or continues with another
   task. Never imply that the generated Telegram username can be renamed.

## Editing the Telegram profile

Profile edits are independent from behavior edits. Do not rebuild or replace a
flow when the user only asks to change the bot's name, avatar, descriptions,
commands, menu button, language versions, or suggested administrator rights.

1. Use `list_bots` to resolve the referenced bot. Call
   `get_telegram_bot_profile` before editing so unspecified profile fields stay
   unchanged.
2. Map the user's language precisely:
   - `name` is the visible bot name, up to 64 characters;
   - `short_description` is shown on the profile and when the bot link is
     shared, up to 120 characters;
   - `description` is the longer “What can this bot do?” text shown in an empty
     chat before the first message, up to 512 characters;
   - username is not editable through the Bot API. Never imply that changing
     `name` changes `@username`.
3. If the user supplies exact copy, preserve it. If they ask BotNest to invent
   the copy, write concise, specific text derived from the bot's current goal
   and behavior. Do not add capabilities the bot does not have.
4. Call `update_telegram_bot_profile` with only the fields the user asked to
   change. An explicit request to edit that bot is sufficient confirmation.
   The tool keeps the same Telegram bot.
5. Commands use lowercase English letters, digits, and underscores. Preserve
   their order. Mark `is_ephemeral: true` only when the user wants the command
   and its response visible solely to its sender.
6. A Web App menu button requires a public HTTPS URL. Do not invent a URL.
7. Suggested administrator rights are only proposed by Telegram when the bot
   is added as an administrator; the user still approves them in Telegram.
8. After success, report the existing username and Telegram link, then
   summarize exactly what changed. Never claim an edit succeeded before the
   update tool returns success.

## Generating and setting an avatar

1. When the user asks to generate an avatar, use the available image generation
   capability first. Generate a square, icon-like composition with a clear
   central subject, generous edge padding, no tiny details, no watermark, and
   no text unless the user explicitly requests text.
2. Inspect the exposed input schema for `update_telegram_bot_profile`; different
   hosts transport image data differently. Use only an image field that the
   current schema actually exposes.
3. When the schema exposes `avatar_base64`, pass the actual generated PNG,
   JPEG, or WebP bytes as base64 together with the matching
   `avatar_mime_type`. The decoded image must be at most 10 MB. Never print or
   paste the encoded bytes into the conversation.
4. When the schema exposes `avatar_path`, pass the actual absolute saved path
   returned by the image tool. Use only a supported PNG, JPEG, or WebP inside
   the host's permitted generated-image directory. Never invent a path or use
   an unrelated local file.
5. If the current host cannot supply either accepted input form, do not claim
   that the avatar was installed. Return the generated image and explain the
   exact transport limitation.
6. If the user asked to generate and install the avatar, do both in the same
   workflow without asking them to upload it manually. Show the final image and
   Telegram bot link only after Telegram accepts it.
7. Remove an avatar only when the user explicitly asks, using
   `remove_avatar: true`.

## Reactions and stateful behavior

- Use only values returned in `telegram_reaction_emojis`. Telegram supports one
  standard reaction per message.
- Read `action_results` and the output block's `result_shape` before reasoning
  about message IDs. A successful `mode: copy` action exposes the copied
  Telegram message as `${<output_field>.message.message_id}` and its destination
  chat as `${<output_field>.chat.id}`. Never say that the copied message ID is
  unavailable when the live context documents these paths.
- To mirror reactions between correlated copies, store two directional rows in
  a bot-scoped message-link table after every successful copy. Key each row by
  source `chat_id + message_id` and store the peer `chat_id + message_id`.
  Route the input block's `reaction` event through a lookup, then use a normal
  `mode: react` output with `target_chat_id`, `reaction_message_id`, and dynamic
  `reaction_emoji: ${reaction.new_emoji}`. On
  `${reaction.removed} == true`, use a separate react output with
  `remove_reaction: true`.
- Build cycles and other state machines by composing general blocks from the
  current catalog. For a per-chat cycle: increment a chat-scoped parameter,
  calculate modulo N with a math block, store the bounded position, branch with
  conditions, and connect each branch to a normal `mode: react` output block.
- Do not invent a reaction-sequence field or another one-off runtime feature.
  Never discard an emoji, shorten an order, or substitute a reaction.

## Data flow integrity

- Give every producing block a unique, simple `output_field`; never reuse a
  default such as `table_result`, `member_result`, or `bot_action`.
- Reference the exact result name only where its producer runs earlier on every
  possible path to the consumer; a merely connected side branch is not enough.
  For stateful branches, use role-based names such as `current_member`,
  `waiting_candidates`, `selected_candidate`, and `relay_partner`.
- Treat every validation detail as blocking. Repair and retry the same request;
  never assume BotNest will rename fields or repair references.
- Apply a filter based on an optional value, such as `last_partner_user_id`,
  only on the branch where that value exists.
- If a bot does not behave as requested, call
  `get_telegram_bot_diagnostics` before explaining the cause. Use the returned
  executed block names and details as evidence; do not invent runtime logs.

## Semantic composite blocks

- Read `graph_design` from `get_flow_builder_context` before designing or
  materially editing a graph. On a flow with roughly 15 or more blocks, or
  whenever four or more blocks form one named business stage, actively look for
  a semantic `composite` boundary instead of leaving every implementation block
  on the top-level canvas.
- Keep input triggers top-level. Good composites describe one purpose such as
  command routing, partner search, relay, stop, or report handling. Do not wrap
  a single action or an ordinary two-block sequence merely to reduce the visible
  count.
- Treat the overview and every component interior as separate visual levels.
  Keep top-level `ui_x`/`ui_y` positions compact in roughly three or four
  columns; never reserve overview space for hidden children. Lay out children
  compactly inside their own level, using three columns or four for a large
  component rather than one long vertical or horizontal strip.
- A condition chain that classifies one input is a router. Give its composite
  one input and named outcome outputs such as `start`, `help`, `next`, `stop`,
  `report`, and `message`; never expose `true`, `false`, or `default` as its
  public business vocabulary.
- Follow `graph_design.composite_contract` exactly. Set `group` on every child,
  add the composite-to-child entry bridge for every used input, add a
  child-to-composite exit bridge for every used output, and use the same named
  port on the composite's external connection. Do not invent shorthand or omit
  a bridge because the canvas can visually infer one.
- A terminal composite may finish with internal Telegram or table side effects
  and have `ports.outputs: []`. Do not add a fake `done` port or connection.
- Composite nesting and input triggers inside a composite are unsupported.
  Keep the top level small with several sibling purpose components instead.
- Before updating the bot, read the collapsed graph as a user would: its block
  names and port labels must explain the complete high-level flow without
  opening a component. Then expand each composite mentally and verify that every
  context producer dominates every consumer on all routes to that output.

## Composing platform behavior

- Treat `get_flow_builder_context` as the live source of truth about BotNest,
  not prior assumptions about its internals. Read `runtime_guarantees` and use
  `action_results`, output `result_shape` entries, and an applicable entry from
  `recipes` before claiming that the platform needs a new block or cannot
  implement a request. Missing recollection is not evidence of a platform
  limitation.
- Prefer a graph made from general blocks over a use-case-specific runtime
  primitive. Tables model queues and state machines; conditions route events;
  random choice selects from rows; hashes create opaque session keys; normal
  Telegram actions perform side effects.
- For an anonymous chat or chat roulette, follow the returned
  `anonymous_chat_roulette` recipe. Do not propose or invent
  `anonymous_matchmaking`, `anonymous_relay`, or `anonymous_moderation` block
  kinds. Use bot-scoped participant/report tables and `output` mode `copy` so
  text and media arrive without Telegram forward attribution.
- Keep identity data server-side. Never place `message.from_user_id`,
  `message.from_username`, `message.from_name`, or `raw_update` in a message
  sent to the partner. Explain accurately that users are anonymous to each
  other, not to Telegram or BotNest.
- For any multi-row state transition, design idempotent recovery from an
  interrupted write as described by the recipe. Do not use an ordinary `send`
  action to imitate media relay and do not call an external Telegram API with
  a bot token.

## Integrity rule

Never silently apply a partial interpretation. Only after checking the live
block catalog, action result paths, runtime guarantees, and applicable recipes,
if the complete requested behavior still cannot be represented, do not mutate
the bot. Explain the exact unsupported requirement and keep the existing bot
unchanged. Do not revert to an older behavior unless the user explicitly asks.

## Existing bots and errors

- Use `list_bots` when the user asks what bots they have or when a bot ID must
  be resolved before publication.
- Use `get_telegram_bot_profile` for current Telegram-facing settings. A
  `telegram_profile_refresh_failed` warning means cached settings were returned;
  do not treat it as a successful live refresh.
- For `avatar_file_unavailable` on a host that exposes `avatar_path`, verify
  that the image exists at the actual absolute saved path inside the permitted
  generated-image directory. Do not request a bot token or send an arbitrary
  local file.
- If botnest requests authentication, tell the user to connect through the
  returned production HTTPS Telegram authorization screen. Do not invoke native
  loopback OAuth or suggest Google login, passwords, API keys, callback
  copying, or manual token entry.
- Translate tool error codes into a short useful explanation. Preserve privacy:
  a missing or foreign setup is simply “not found”.
- If creation is temporarily unavailable, keep the user's full description in
  the conversation so the operation can be retried with the same
  `idempotency_key`.
