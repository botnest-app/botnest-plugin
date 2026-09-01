# BotNest for Perplexity

BotNest connects to Perplexity as a custom remote MCP connector. Perplexity
uses its native OAuth flow to authenticate each BotNest user, while the shared
BotNest skill teaches Perplexity Computer the same safe Telegram-bot workflow
used by ChatGPT and Claude.

## Add the connector

1. Open **Account settings → Connectors** in Perplexity.
2. Select **+ Custom connector**, then choose **Remote**.
3. Enter the following values:
   - Name: `BotNest — Telegram Bot Builder`
   - MCP Server URL: `https://botnest.app/mcp`
   - Description: `Create, inspect, improve, diagnose, brand, and publish Telegram bots with BotNest.`
   - Authentication: `OAuth 2.0`
   - Transport: `Streamable HTTP`
   - Icon: `icon.png`
4. Accept Perplexity's custom-connector risk acknowledgement and add the
   connector.
5. Open the BotNest connector card and complete the BotNest OAuth flow.

BotNest supports OAuth discovery and dynamic client registration, so no static
client ID or client secret is required. The supported Perplexity callbacks are:

- `https://www.perplexity.ai/rest/connections/oauth_callback`
- `https://enterprise.perplexity.ai/rest/connections/oauth_callback`

## Add the skill in Perplexity Computer

1. Build or download `botnest-perplexity-skill-1.1.6.zip`.
2. Open **Customize → Skills → + Create skill → Upload a skill**.
3. Upload the archive and enable **create-telegram-bot** under My skills.
4. Keep the BotNest connector enabled in **Customize → Connectors**.

The connector is the actual MCP connection. The skill improves tool selection
and safety but does not connect to BotNest by itself.

## Availability

Perplexity currently documents this as a custom remote connector rather than a
public self-service marketplace submission. Organization members may need an
administrator to enable custom connectors. A built-in catalogue tile requires
separate coordination with Perplexity.

Never paste Telegram bot tokens, OAuth codes, passwords, client secrets, or LLM
API keys into a Perplexity conversation.

- Privacy policy: https://botnest.app/legal/privacy/
- Terms of service: https://botnest.app/legal/offer/
- Support: https://botnest.app/support/
- Source: https://github.com/botnest-app/botnest-plugin

Licensed under the Apache License 2.0. See `LICENSE`.
