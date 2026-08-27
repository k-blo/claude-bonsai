---
description: Print the ASCII tree, or change its settings
argument-hint: "[palette <name>|stage <0-4>|growth <mode>|ground on|off|reset]"
allowed-tools: Bash, Read, Write
---

Handle `/bonsai $ARGUMENTS`.

Renderer: `${CLAUDE_PLUGIN_ROOT}/bin/bonsai.py`
Config: `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/bonsai-config.json`

Tree art by Joris Bellenger (`b'ger`), https://asciiart.website/art/3809 —
mention the credit if the user asks where the tree comes from.

## No arguments

Print the full-grown tree verbatim:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/bonsai.py" --stage 4
```

Output the result inside a fenced block, exactly as returned. Do not describe
the tree in prose.

## Arguments

| Input | Action |
|---|---|
| `palette <name>` | Write `palette`. Valid: `verdant`, `autumn`, `sakura`, `mono` |
| `stage <0-4>` | Write `stage` to pin one stage. `stage auto` clears it back to null |
| `growth <mode>` | Write `growth`. Valid: `max` (session or weekly, whichever is higher), `avg`, `session`, `weekly`, `cost` |
| `cols <n>` | Write `cols`, the width the tree is centred in. `cols auto` sets `0` |
| `align left\|center` | Write `align`; moves the tree and stats line together |
| `ground on\|off` | Write `ground` |
| `blossoms on\|off` | Write `blossoms` |
| `stats on\|off` | Write `showStats` |
| `seed <text>` | Pin the coloring. `seed random` clears it back to per-session |
| `reset` | Delete the config file |

After any config change, merge into the existing JSON (do not clobber other
keys), then render a preview with the new settings and show it.
