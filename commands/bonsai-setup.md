---
description: Install or remove the bonsai statusline
argument-hint: "[install|remove|status]"
allowed-tools: Bash, Read, Edit, Write
---

Set up the bonsai statusline. Argument: `$1` (default `install`).

Paths:

- Renderer: `${CLAUDE_PLUGIN_ROOT}/bin/bonsai.py`
- Statusline entry: `${CLAUDE_PLUGIN_ROOT}/bin/bonsai-statusline.sh`
- Settings: `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json`
- Chain script: `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/bonsai-chain.sh`
- Config: `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/bonsai-config.json`

## install

1. Back up `settings.json` to `settings.json.bak.pre-bonsai`.
2. If `statusLine.command` is already set and does **not** point at
   `bonsai-statusline.sh`, preserve it: write it into `bonsai-chain.sh` as
   `#!/bin/bash` plus `exec <old command>`, and `chmod +x` it. The bonsai
   statusline runs it afterwards, so both render. Tell the user this happened.
3. Set `statusLine` to:
   ```json
   {"type": "command", "command": "<plugin root>/bin/bonsai-statusline.sh", "padding": 1, "refreshInterval": 5}
   ```
   Resolve `<plugin root>` to a real absolute path — do not leave a variable in
   the JSON, because Claude Code does not expand it.
4. Verify by piping sample hook JSON into the script and showing the output.
5. Tell the user to restart Claude Code.

## remove

1. Restore `statusLine` from `bonsai-chain.sh` if present, otherwise from the
   backup; if neither exists, drop the `statusLine` key.
2. Delete `bonsai-chain.sh`.
3. Leave `bonsai-config.json` alone and say so.

## status

Print the current `statusLine.command`, whether a chain script exists, and the
contents of `bonsai-config.json` if present.
