# botnest for Codex

The installable plugin package for creating and managing Telegram bots with
[botnest](https://botnest.app/).

It bundles the shared BotNest skill and a Codex-specific local stdio bridge to the production botnest
MCP service at `https://botnest.app/mcp`. The bridge keeps OAuth credentials in
the plugin's private `PLUGIN_DATA` directory, refreshes them automatically, and
requires Python 3.10 or newer.

Install the public marketplace:

```bash
codex plugin marketplace add botnest-app/botnest-plugin --ref main
codex plugin add botnest@botnest
```

Restart the ChatGPT desktop app, enable **botnest** in Plugins, and start a new
conversation.

This is one of several adapters generated from the same repository. ChatGPT
uses the production remote MCP directly, Claude uses its native remote-MCP
package, and Perplexity uses a custom remote connector plus the shared skill. See the
[public repository](https://github.com/botnest-app/botnest-plugin) for the
cross-platform architecture, security notes, and release workflow.
