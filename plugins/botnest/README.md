# botnest plugin

The installable plugin package for creating and managing Telegram bots with
[botnest](https://botnest.app/).

It bundles one focused skill and a local stdio bridge to the production botnest
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

See the [public repository](https://github.com/botnest-app/botnest-plugin) for
capabilities, security notes, testing, and OpenAI submission materials.
