# Perplexity connector distribution

BotNest is ready for Perplexity as a custom remote MCP connector with OAuth and
an optional Perplexity Computer skill. Perplexity does not currently document
an open public catalogue submission flow for third-party developers, so this
file covers both the working custom-connector path and the information to send
Perplexity when requesting a built-in connector tile.

## Working custom connector

| Field | Value |
| --- | --- |
| Name | BotNest — Telegram Bot Builder |
| MCP Server URL | https://botnest.app/mcp |
| Description | Create, inspect, improve, diagnose, brand, and publish Telegram bots with BotNest. |
| Authentication | OAuth 2.0 |
| Transport | Streamable HTTP |
| Icon | `platforms/perplexity/botnest/icon.png` |

BotNest supports OAuth discovery, PKCE, refresh tokens, and dynamic client
registration. Perplexity therefore does not need a static client ID or client
secret. BotNest accepts the documented Perplexity callback URLs:

- `https://www.perplexity.ai/rest/connections/oauth_callback`
- `https://enterprise.perplexity.ai/rest/connections/oauth_callback`

After connecting the MCP, upload
`dist/botnest-perplexity-skill-1.1.5.zip` in **Customize → Skills**. The skill
improves tool selection and safety; it does not replace the connector.

## Built-in catalogue request

Perplexity support: <support@perplexity.ai>

Include the repository, production MCP URL, privacy policy, terms, support URL,
OAuth metadata URLs, the two callback URLs above, and a request for the partner
or connector-review process. Ask whether BotNest can receive a public connector
tile with per-user OAuth rather than requiring every user to enter the MCP URL.

## Review information

- Repository: <https://github.com/botnest-app/botnest-plugin>
- Homepage: <https://botnest.app/>
- Privacy: <https://botnest.app/legal/privacy/>
- Terms: <https://botnest.app/legal/offer/>
- Support: <https://github.com/botnest-app/botnest-plugin/issues>
- Protected-resource metadata:
  <https://botnest.app/.well-known/oauth-protected-resource/mcp>
- Authorization-server metadata:
  <https://botnest.app/.well-known/oauth-authorization-server>

Provide the existing isolated BotNest reviewer credentials only through a
private Perplexity review channel. Never commit them to this repository or send
them in a public issue.

## Suggested reviewer prompts

1. `Покажи моих Telegram-ботов в BotNest.`
2. `Создай Telegram-бота для записи клиентов: спроси имя, услугу и время.`
3. `Покажи последние результаты выполнения у бота BotNest Diagnostics Sample.`

Publication remains a separate consequential action and requires an explicit
user request or confirmation.
