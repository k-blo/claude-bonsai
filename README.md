# claude-bonsai

A colorful ASCII tree for the Claude Code statusline. It starts as a sapling and
grows through five stages as you burn through your usage limits.

![The tree rendered in the Claude Code statusline](docs/statusline.png)

Full-grown, it looks like this:

```
       %%%,%%%%%%%
       ,'%% \\-*%%%%%%%
 ;%%%%%*%   _%%%%"
  ,%%%       \(_.*%%%%.
  % *%%, ,%%%%*(    '
%^     ,*%%% )\|,%%*%,_
     *%    \/ #).-"*%%*
         _.) ,/ *%,
 _________/)#(_____________
19% ctx · 61% session (resets in 3h 6m) · weekly 23%
```

## Credit

The full-grown tree is ASCII art by **Joris Bellenger** (`b'ger`), from
[asciiart.website/art/3809](https://asciiart.website/art/3809). The four smaller
growth stages are drawn in the same style. The art is reproduced unmodified; this
plugin only colors it and picks a stage.

## Requirements

- `python3` (stdlib only — no packages to install)
- A truecolor terminal

## Install

```bash
claude plugin marketplace add k-blo/claude-bonsai
claude plugin install claude-bonsai@claude-bonsai
```

Then, inside Claude Code:

```
/bonsai-setup install
```

That points `statusLine` at `~/.claude/bonsai-statusline.sh`, a small shim that
resolves the newest installed version at run time — `settings.json` cannot
expand `${CLAUDE_PLUGIN_ROOT}`, so a literal path there would break on the next
plugin update. If you already had a statusline, it is preserved and rendered
underneath the tree, so nothing is lost.

`/bonsai-setup status` shows what is wired up; `/bonsai-setup remove` undoes it
and puts your old statusline back.

If the tree does not appear, the statusline says why on one line
(`bonsai: ...`) rather than rendering blank.

Upgrading from 0.1.0: re-run `/bonsai-setup install` once — 0.1.0 wrote a
version-pinned path into `settings.json` that the update leaves behind.

## Commands

| Command | Does |
|---|---|
| `/bonsai` | Print the full-grown tree |
| `/bonsai palette autumn` | Switch palette: `verdant`, `autumn`, `sakura`, `mono` |
| `/bonsai stage <0-4>` | Pin a stage instead of following the session |
| `/bonsai growth <mode>` | Grow on `max`, `avg`, `session`, `weekly`, or `cost` |
| `/bonsai align left\|center` | Move the tree and stats line together |
| `/bonsai ground on\|off` | Toggle the ground line |
| `/bonsai stats on\|off` | Toggle the `19% ctx · 61% session` line |
| `/bonsai status` | Print the tree from the newest usage any session saw |
| `/bonsai reset` | Delete the config |
| `/bonsai-setup install\|remove\|status` | Manage the statusline wiring |

## How growth works

Five hand-drawn stages, from a two-leaf sapling to the full tree. Every stage
shares the same ground line and trunk column, so the tree grows in place instead
of jumping around.

Growth comes from your **rate limits**: by default whichever of the 5-hour
session window and the weekly window is fuller, so a full tree means you are at
a limit. Context does not feed the tree.

| Mode | Tree follows |
|---|---|
| `max` (default) | The higher of session and weekly |
| `avg` | The mean of the two |
| `session` | 5-hour window only |
| `weekly` | 7-day windows only |
| `cost` | Session dollars against `costFull` |

Both come from `rate_limits` on the statusline payload: `61% session` is the 5-hour
session window and `(resets in 3h 5m)` is when it clears; `weekly 23%` is the
busiest 7-day window (including per-model ones). Context is still shown as
`19% ctx`, read from the last assistant message in the transcript.

## Freshness

The statusline only re-runs when the conversation updates, so an idle terminal
keeps whatever it last drew. The 5-hour window is account-wide, so every render
writes its reading to `~/.claude/bonsai-usage.json` and every render prefers the
newer of that file and its own payload — a terminal you come back to after an
hour picks up the numbers a busier one recorded.

To check without spending a turn (it works while you are rate-limited, since no
request is made), run it from bash mode:

```
!~/.claude/bonsai-statusline.sh --status
```

```
61% session (resets in 3h 5m) · weekly 23% · 4m ago
```

The countdown is recomputed at print time, so it stays right however old the
reading is; `4m ago` is the age of the percentages themselves.

Colors are applied per character: `%` and `*` become foliage, `,' ^ ; "` become
lighter leaf edges, and `\ / | ( ) # _ - .` become wood. A small share of leaves
turn into blossoms. The pattern is seeded from the session ID, so each session
gets its own coloring and it stays stable across statusline refreshes.

## Config

`~/.claude/bonsai-config.json`. Anything left out falls back to the default.

> **Why `indentChar`:** the statusline trims leading whitespace from every line,
> which flattens ASCII art. Plain spaces and `U+00A0` are both stripped, so the
> tree is indented with `U+2800` (braille blank) — blank, one column wide, and
> not classed as whitespace.

| Key | Default | Meaning |
|---|---|---|
| `align` | `"center"` | `center` or `left`; moves the tree and the stats line together |
| `cols` | `0` | Width to centre in; `0` follows the terminal (30–80) |
| `palette` | `"verdant"` | `verdant`, `autumn`, `sakura`, `mono` |
| `blossoms` | `true` | Scatter blossoms in the foliage |
| `blossomChars` | `["❀","✿"]` | Blossom characters |
| `blossomChance` | `0.05` | Share of leaves that blossom |
| `indentChar` | `"\u2800"` | Blank used for indentation; see note below |
| `ground` | `true` | Draw the ground line |
| `showStats` | `true` | Show the `19% ctx · 61% session` line |
| `growth` | `"max"` | `max`, `avg`, `session`, `weekly`, or `cost` |
| `costFull` | `10.0` | Dollars that count as a full tree |
| `curve` | `1.0` | Below 1 reaches the bigger stages sooner |
| `stage` | `null` | Pin a stage `0`–`4`; `null` follows the session |
| `seed` | `null` | Pin the coloring; `null` means per-session |

## Standalone use

```bash
python3 bin/bonsai.py --stage 4 --palette sakura
python3 bin/bonsai.py --progress 0.5 --cols 60
python3 bin/bonsai.py --status
```

## License

MIT for the plugin code. The full-grown tree art is by Joris Bellenger, credited
above — please keep the attribution if you redistribute it.
