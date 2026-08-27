#!/usr/bin/env python3
"""Colorful ASCII tree, sized by Claude Code rate-limit usage.

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
    "growth": "max",
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
GREY = "#808080"


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


def _pct(win):
    """Window -> percentage. Statusline calls it used_percentage, the SDK utilization."""
    for key in ("used_percentage", "utilization"):
        val = (win or {}).get(key)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            return val
    return None


def read_usage(payload):
    """Session window as a fraction, when it resets, and the busiest weekly window."""
    limits = payload.get("rate_limits") or {}
    five = limits.get("five_hour") or {}
    session = _pct(five)
    weekly = [p for p in (_pct(limits.get(k)) for k in
                          ("seven_day", "seven_day_oauth_apps",
                           "seven_day_opus", "seven_day_sonnet")) if p is not None]
    # The SDK shape puts the per-model weekly limits here instead.
    weekly += [p for p in (_pct(e) for e in limits.get("model_scoped") or [])
               if p is not None]
    resets = five.get("resets_at")
    clamp = lambda p: None if p is None else max(0.0, min(1.0, p / 100.0))
    return clamp(session), resets, clamp(max(weekly) if weekly else None)


def _as_utc(resets_at):
    """Reset stamp -> aware datetime, or None.

    (resets in 3h 6m) silently vanishing means this returned None. The
    statusline payload sends Unix epoch SECONDS; the SDK/model_scoped shape
    sends an ISO 8601 string. Both land here, so handle both.
    """
    if isinstance(resets_at, bool) or resets_at is None or resets_at == "":
        return None
    if isinstance(resets_at, str):
        try:
            when = datetime.datetime.fromisoformat(resets_at.replace("Z", "+00:00"))
        except ValueError:
            try:
                resets_at = float(resets_at)
            except ValueError:
                return None
        else:
            return when if when.tzinfo else when.replace(tzinfo=datetime.timezone.utc)
    if not isinstance(resets_at, (int, float)):
        return None
    secs = float(resets_at)
    if secs > 1e11:  # milliseconds
        secs /= 1000.0
    try:
        return datetime.datetime.fromtimestamp(secs, datetime.timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def until(resets_at):
    """Formats a reset stamp as 3h 6m."""
    when = _as_utc(resets_at)
    if when is None:
        return None
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


GROWTH_MODES = ("max", "avg", "session", "weekly", "cost")


def growth_from(cfg, session, weekly, cost_pct):
    """How full the tree is: session limit, weekly limit, or a blend of both."""
    mode = cfg["growth"] if cfg["growth"] in GROWTH_MODES else DEFAULTS["growth"]
    if mode == "cost":
        return cost_pct
    if mode == "session":
        picked = [session]
    elif mode == "weekly":
        picked = [weekly]
    else:
        picked = [session, weekly]
    picked = [p for p in picked if p is not None]
    if not picked:
        return 0.0
    return sum(picked) / len(picked) if mode == "avg" else max(picked)


def main():
    ap = argparse.ArgumentParser(description="Colorful ASCII tree for Claude Code.")
    ap.add_argument("--statusline", action="store_true", help="read hook JSON on stdin")
    ap.add_argument("--progress", type=float, help="growth 0..1, overrides live data")
    ap.add_argument("--stage", type=int, help="force a growth stage")
    ap.add_argument("--cols", type=int, help="centre within this width")
    ap.add_argument("--palette", choices=sorted(PALETTES))
    ap.add_argument("--seed")
    ap.add_argument("--curve", type=float)
    ap.add_argument("--growth", choices=GROWTH_MODES)
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
    session, resets, weekly = read_usage(payload)
    cost = (payload.get("cost") or {}).get("total_cost_usd", 0.0) or 0.0
    cost_pct = min(1.0, cost / max(0.01, cfg["costFull"]))

    progress = (args.progress if args.progress is not None
                else growth_from(cfg, session, weekly, cost_pct))
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
        grey = hex_to_ansi(GREY) if args.color else ""
        end = RESET if args.color else ""
        # Kept in step: plain drives the padding, fancy carries the colours.
        plain = ["%d%% ctx" % round(ctx * 100)]
        fancy = list(plain)
        if session is not None:
            left = until(resets)
            head = "%d%% use" % round(session * 100)
            tail = " (resets in %s)" % left if left else ""
            plain.append(head + tail)
            fancy.append(head + (grey + tail + tint if tail else ""))
        if weekly is not None:
            plain.append("weekly %d%%" % round(weekly * 100))
            fancy.append(plain[-1])
        # Line up with the tree above it.
        pad = cfg["indentChar"] * indent_for(cfg, len(" · ".join(plain)))
        lines.append("%s%s%s%s" % (pad, tint, " · ".join(fancy), end))

    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
