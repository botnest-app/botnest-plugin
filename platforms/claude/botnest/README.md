# BotNest for Claude

Create, inspect, improve, diagnose, brand, and publish Telegram bots from a
plain-language request. This package bundles the BotNest workflow skill with a
remote MCP connector to `https://botnest.app/mcp`.

## Connect

1. Install and enable **BotNest**.
2. Select **Connect** or **Authorize** when Claude prompts for the BotNest
   connector.
3. Complete the BotNest HTTPS sign-in flow. BotNest may ask you to confirm your
   identity in Telegram, then returns you to Claude.
4. Retry the original request after authorization completes.

Never paste Telegram bot tokens, OAuth codes, passwords, or LLM API keys into a
Claude conversation. See `SETUP.md` for recovery steps.

## Example prompts

- `Покажи моих Telegram-ботов в BotNest.`
- `Создай Telegram-бота для записи клиентов: спроси имя, услугу и время.`
- `Проверь последние ошибки моего бота и объясни, что исправить.`

Bot creation remains private until the user completes the Telegram confirmation
step. Publishing a ready bot is a separate action and requires an explicit user
request or confirmation.

## Data and permissions

The connector sends only the arguments needed for the selected BotNest tool to
the production BotNest service. OAuth access is limited to reading, creating,
updating, and publishing bots owned by the authenticated user. The package has
no local hooks, background processes, telemetry, or bundled executable code.

- Privacy policy: https://botnest.app/legal/privacy/
- Terms of service: https://botnest.app/legal/offer/
- Support and issue reporting: https://github.com/botnest-app/botnest-plugin/issues
- Source: https://github.com/botnest-app/botnest-plugin

## Troubleshooting

- If Claude reports that authorization is required, open the HTTPS authorization
  action again and finish the Telegram confirmation before retrying.
- If a bot is still being provisioned, ask for its creation status instead of
  starting another creation flow.
- If a tool fails, keep the returned error code and contact support without
  sharing tokens, credentials, or private bot data.

This package is generated from the shared BotNest source. Do not edit generated
files under `platforms/claude/botnest` directly.

Licensed under the Apache License 2.0. See `LICENSE`.
