# Set up BotNest

Use these instructions when the BotNest plugin is installed but its remote MCP
connector is not yet authenticated or a BotNest tool returns
`authorization_required`.

1. Confirm that the configured connector URL is exactly
   `https://botnest.app/mcp`.
2. Start Claude's native **Connect** or **Authorize** action for BotNest.
3. Open only the HTTPS BotNest authorization page shown by Claude. Complete the
   sign-in and Telegram confirmation there.
4. Return to the same conversation and retry the original request with the same
   arguments. For bot creation, preserve the original idempotency key.
5. Verify the connection with a read-only request such as listing the user's
   bots before continuing a write workflow.

Never ask the user to paste a Telegram bot token, OAuth authorization code,
device code, password, client secret, or LLM API key. Do not replace the
configured MCP URL with localhost, a tunnel, or another domain. If the HTTPS
authorization page or connector remains unavailable, stop and direct the user
to https://github.com/botnest-app/botnest-plugin/issues.
