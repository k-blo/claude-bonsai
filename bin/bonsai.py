#!/usr/bin/env python3
"""Colorful ASCII tree, sized by Claude Code context and usage.

Full-grown tree by Joris Bellenger (b'ger), https://asciiart.website/art/3809
Smaller growth stages drawn in the same style.
"""

import argparse
import datetime
import json
import os
import random
import sys

CONFIG_PATH = os.path.join(
    os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude"),
    "bonsai-config.json",
)

DEFAULTS = {
    "cols": 0,
    "blossoms": True,
    "blossomChars": ["❀", "✿"],
    "blossomChance": 0.05,
    "align": "center",
    "indentChar": "\u2800",
    "ground": True,
    "showStats": True,
    "growth": "sum",
    "costFull": 10.0,
    "curve": 1.0,
    "seed": None,
    "palette": "verdant",
    "stage": None,
}

GROUND = r" _________/)#(_____________"

STAGES = [
    [
        r"           ,%%,",
        r"           %%%%",
        r"            \|",
    ],
    [
        r"          ,%%%%%,",
        r"         %%%*%%%%",
        r"          \\%|%*",
        r"            \|",
    ],
    [
        r"        ,%%%%%%%%,",
        r"       %%%*%%%%%%%%",
        r'      ;%%%\\-*%%%%"',
        r"         %%\(_.*%%",
        r"           )\|,%%",
        r"           \/ #)",
    ],
    [
        r"       %%%,%%%%%%%",
        r"      ,'%% \\-*%%%%%%",
        r'  ;%%%%*%   _%%%%"',
        r"   ,%%%      \(_.*%%%",
        r"    *%%, ,%%%%*(   '",
        r"      ,*%%% )\|,%%*%",
        r'         \/ #).-"*%',
        r"         _.) ,/ *%",
    ],
    [
        r"       %%%,%%%%%%%",
        r"       ,'%% \\-*%%%%%%%",
        r' ;%%%%%*%   _%%%%"',
        r"  ,%%%       \(_.*%%%%.",
        r"  % *%%, ,%%%%*(    '",
        r"%^     ,*%%% )\|,%%*%,_",
        r'     *%    \/ #).-"*%%*',
        r"         _.) ,/ *%,",
    ],
]

PALETTES = {
    "verdant": {
        "wood": ["#a87b3f", "#8f6631", "#c19553"],
        "old": ["#3f7a2a", "#356a24", "#2d5c1f"],
        "new": ["#79c142", "#8fd14f", "#66ad38"],
        "edge": ["#a8e063", "#bdea7f"],
        "blossom": ["#ff8fb1", "#ffb3c9"],
        "ground": "#8a7f6d",
    },
    "autumn": {
        "wood": ["#8f6631", "#a87b3f", "#6f4f26"],
        "old": ["#a8511a", "#8f4416", "#c1651b"],
        "new": ["#e8973a", "#f2b134", "#d4772b"],
        "edge": ["#ffd166", "#ffdf8f"],
        "blossom": ["#e63946", "#ff6b6b"],
        "ground": "#8a7458",
    },
    "sakura": {
        "wood": ["#8a6f5a", "#6f5847", "#a2836a"],
        "old": ["#b3708f", "#9c5f7c"],
        "new": ["#ffaecb", "#ffc0d9"],
        "edge": ["#ffd6e6", "#ffe6f0"],
        "blossom": ["#fff0f5", "#ffe1ec"],
        "ground": "#a89f96",
    },
    "mono": {
        "wood": ["#a8a8a8", "#8f8f8f", "#c0c0c0"],
        "old": ["#6f6f6f", "#5f5f5f"],
        "new": ["#c9c9c9", "#b5b5b5"],
        "edge": ["#e8e8e8"],
        "blossom": ["#ffffff"],
        "ground": "#6a6a6a",
    },
}

FOLIAGE = set("%*")
EDGE = set(",';^\"")
WOOD = set("\\/|()#_-.")

RESET = "\033[0m"


def hex_to_ansi(color, bold=False):
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)
    return "%s\033[38;2;%d;%d;%dm" % ("\033[1m" if bold else "", r, g, b)


def indent_for(cfg, width):
    """Left padding that centres a block, or none when aligned left."""
    if cfg["align"] == "left":
        return 0
    return max(0, (canvas_width(cfg) - width) // 2)


def canvas_width(cfg):
    """Width the tree is centred in; follows the terminal by default."""
    if cfg["cols"]:
        return cfg["cols"]
    try:
        return max(30, min(80, int(os.environ.get("COLUMNS", 0))))
    except ValueError:
        return 60


def paint(art, cfg, pal, seed, color=True):
    """Colours one stage and centres it over the ground line."""
    width = max([len(GROUND)] + [len(row) for row in art])
    pad = indent_for(cfg, width)
    out = []

    rows = list(art) + ([GROUND] if cfg["ground"] else [])
    for ry, row in enumerate(rows):
        is_ground = cfg["ground"] and ry == len(rows) - 1
        line = []
        for cx, ch in enumerate(row):
            if ch == " ":
                line.append(" ")
                continue
            rng = random.Random("%s:%d:%d" % (seed, ry, cx))
            if is_ground:
                hexcol, bold = pal["ground"], False
            elif ch in FOLIAGE:
                if cfg["blossoms"] and rng.random() < cfg["blossomChance"]:
                    ch = rng.choice(cfg["blossomChars"])
                    hexcol, bold = rng.choice(pal["blossom"]), True
                else:
                    pool = pal["new"] if rng.random() < 0.55 else pal["old"]
                    hexcol, bold = rng.choice(pool), rng.random() < 0.3
            elif ch in EDGE:
                hexcol, bold = rng.choice(pal["edge"]), rng.random() < 0.4
            elif ch in WOOD:
                hexcol, bold = rng.choice(pal["wood"]), rng.random() < 0.3
            else:
                hexcol, bold = rng.choice(pal["new"]), False
            line.append(hex_to_ansi(hexcol, bold) + ch + RESET if color else ch)
        # The statusline trims whitespace; braille blanks survive it.
        text = (" " * pad + "".join(line)).rstrip()
        out.append(text.replace(" ", cfg["indentChar"]))
    return out


def read_context(transcript_path, model_id):
    """Returns (used_tokens, limit) from the tail of the transcript."""
    limit = 1_000_000 if "[1m]" in (model_id or "") else 200_000
    if not transcript_path or not os.path.exists(transcript_path):
        return 0, limit
    try:
        size = os.path.getsize(transcript_path)
        with open(transcript_path, "rb") as fh:
            fh.seek(max(0, size - 262144))
            chunk = fh.read().decode("utf-8", "replace")
    except OSError:
        return 0, limit
    for raw in reversed(chunk.splitlines()):
        if '"usage"' not in raw:
            continue
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        if rec.get("isSidechain") or rec.get("type") != "assistant":
            continue
        usage = (rec.get("message") or {}).get("usage") or {}
        used = (
            usage.get("input_tokens", 0)
            + usage.get("output_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
        )
        if used:
            return used, limit
    return 0, limit


def read_usage(payload):
    """Busiest rate-limit window as (fraction, resets_at)."""
    limits = payload.get("rate_limits") or {}
    seen = []
    for key in ("five_hour", "seven_day"):
        win = limits.get(key) or {}
        pct = win.get("used_percentage")
        if isinstance(pct, (int, float)):
            seen.append((pct, win.get("resets_at")))
    for entry in limits.get("model_scoped") or []:
        pct = (entry or {}).get("utilization")
        if isinstance(pct, (int, float)):
            seen.append((pct, (entry or {}).get("resets_at")))
    if not seen:
        return None, None
    pct, resets = max(seen, key=lambda p: p[0])
    if not resets:
        # Busiest window gave no stamp; take one from any window.
        resets = next((r for _, r in seen if r), None)
    return max(0.0, min(1.0, pct / 100.0)), resets


def until(resets_at):
    """Formats an ISO reset stamp as 3h 6m."""
    if not isinstance(resets_at, str) or not resets_at:
        return None
    try:
        when = datetime.datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=datetime.timezone.utc)
    mins = int((when - datetime.datetime.now(datetime.timezone.utc)).total_seconds() // 60)
    if mins <= 0:
        return "now"
    if mins < 60:
        return "%dm" % mins
    hours, mins = divmod(mins, 60)
    if hours < 24:
        return "%dh %dm" % (hours, mins)
    days, hours = divmod(hours, 24)
    return "%dd %dh" % (days, hours)


def load_config(overrides=None):
    cfg = dict(DEFAULTS)
    try:
        with open(CONFIG_PATH) as fh:
            cfg.update(json.load(fh))
    except (OSError, ValueError):
        pass
    if overrides:
        cfg.update({k: v for k, v in overrides.items() if v is not None})
    return cfg


def main():
    ap = argparse.ArgumentParser(description="Colorful ASCII tree for Claude Code.")
    ap.add_argument("--statusline", action="store_true", help="read hook JSON on stdin")
    ap.add_argument("--progress", type=float, help="growth 0..1, overrides live data")
    ap.add_argument("--stage", type=int, help="force a growth stage")
    ap.add_argument("--cols", type=int, help="centre within this width")
    ap.add_argument("--palette", choices=sorted(PALETTES))
    ap.add_argument("--seed")
    ap.add_argument("--curve", type=float)
    ap.add_argument("--growth", choices=("sum", "context", "usage", "cost"))
    ap.add_argument("--align", choices=("center", "left"))
    ap.add_argument("--indentChar", help="character used for blank space")
    ap.add_argument("--no-ground", dest="ground", action="store_false", default=None)
    ap.add_argument("--no-stats", dest="showStats", action="store_false", default=None)
    ap.add_argument("--no-color", dest="color", action="store_false", default=True)
    args = ap.parse_args()

    payload = {}
    if args.statusline and not sys.stdin.isatty():
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            payload = {}

    keys = ("cols", "palette", "ground", "showStats", "seed", "curve", "growth",
            "stage", "indentChar", "align")
    cfg = load_config({k: getattr(args, k) for k in keys})

    model_id = ((payload.get("model") or {}).get("id")) or ""
    used, limit = read_context(payload.get("transcript_path"), model_id)
    ctx = used / limit if limit else 0.0
    use, resets = read_usage(payload)
    cost = (payload.get("cost") or {}).get("total_cost_usd", 0.0) or 0.0
    cost_pct = min(1.0, cost / max(0.01, cfg["costFull"]))

    if args.progress is not None:
        progress = args.progress
    elif cfg["growth"] == "context":
        progress = ctx
    elif cfg["growth"] == "usage":
        progress = use if use is not None else ctx
    elif cfg["growth"] == "cost":
        progress = cost_pct
    else:
        # Context + usage together: 100% + 100% is a full tree.
        progress = (ctx + use) / 2 if use is not None else ctx
    progress = max(0.0, min(1.0, progress)) ** max(0.1, cfg["curve"])

    if cfg["stage"] is not None:
        idx = max(0, min(len(STAGES) - 1, int(cfg["stage"])))
    else:
        idx = int(round(progress * (len(STAGES) - 1)))

    pal = PALETTES.get(cfg["palette"], PALETTES["verdant"])
    seed = cfg.get("seed") or payload.get("session_id") or "tree"
    lines = paint(STAGES[idx], cfg, pal, seed, color=args.color)

    if cfg["showStats"] and args.statusline:
        tint = hex_to_ansi(pal["new"][0]) if args.color else ""
        end = RESET if args.color else ""
        parts = ["%d%% ctx" % round(ctx * 100)]
        if use is not None:
            left = until(resets)
            parts.append("%d%% use%s" % (round(use * 100),
                                         " (resets in %s)" % left if left else ""))
        text = " · ".join(parts)
        # Line up with the tree above it.
        pad = cfg["indentChar"] * indent_for(cfg, len(text))
        lines.append("%s%s%s%s" % (pad, tint, text, end))

    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
