---
description: Install or remove the bonsai statusline
argument-hint: "[install|remove|status]"
allowed-tools: Bash
---

Run exactly this, with `$1` (default `install`):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/bonsai-setup.py" "${1:-install}"
```

The script owns every step — backup, chaining a previous statusline, the
stable shim, the `settings.json` edit, the preview. Do not edit
`settings.json` yourself, and do not reimplement any of it if the script
reports a problem; show the output and stop.

Print the output verbatim, tree included. On `install`, remind the user to
restart Claude Code.
