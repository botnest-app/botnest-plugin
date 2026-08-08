# Alice adapter

This directory contains the platform-specific webhook for Yandex Alice. It is
the only BotNest distribution that does not run the shared agent skill: Alice
sends deterministic webhook requests rather than hosting an MCP-aware model.

The adapter calls the same production MCP tools as ChatGPT, Claude, Grok, and
Codex. It supports account linking, bot creation from a brief, listing bots,
creation status, diagnostics, and confirmed publication. Complex flow editing
stays in the agent hosts because Alice's webhook has a strict response budget.

## Deploy

1. Run `python3 scripts/generate_platforms.py` from the repository root.
2. Deploy `handler.py`, `runtime.json`, and its standard-library Python runtime
   behind the HTTPS URL in `publication.json`.
3. Configure the Yandex Dialog with the values from `publication.json`.
4. Deploy the BotNest backend's dedicated confidential Alice OAuth endpoints,
   configure `BOTNEST_ALICE_OAUTH_CLIENT_ID` and
   `BOTNEST_ALICE_OAUTH_CLIENT_SECRET`, and enter the same values in Yandex
   Dialogs. Do not reuse the public MCP clients or the Codex device client.
5. Test account linking, the 4.5-second response budget, confirmation flows,
   and every example utterance before catalog submission.

The target Alice OAuth endpoints in `publication.json` are a backend contract.
They must exist in production before the public skill is submitted. Client
secrets belong only in backend/Dialogs configuration and are never committed
to this repository.
