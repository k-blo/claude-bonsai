#!/usr/bin/env python3
"""Wires the bonsai statusline into settings.json.

Deterministic on purpose: this edits the user's settings.json, so it is a
script and not a prose command for the model to improvise.

settings.json does not expand ${CLAUDE_PLUGIN_ROOT}, and the plugin cache path
carries the version (.../claude-bonsai/0.1.0/bin/...), so pointing settings.json
straight at the plugin leaves every existing user on a dead path at the next
release. Instead settings.json points at a stable shim in the config dir, and
the shim resolves the newest install at run time.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

CFG_DIR = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR") or (pathlib.Path.home() / ".claude"))
SETTINGS = CFG_DIR / "settings.json"
BACKUP = CFG_DIR / "settings.json.bak.pre-bonsai"
CHAIN = CFG_DIR / "bonsai-chain.sh"
SHIM = CFG_DIR / "bonsai-statusline.sh"
CONFIG = CFG_DIR / "bonsai-config.json"

PLUGIN_ROOT = pathlib.Path(
    os.environ.get("CLAUDE_PLUGIN_ROOT") or pathlib.Path(__file__).resolve().parent.parent
).resolve()

SHIM_TEMPLATE = """#!/bin/bash
# Stable entry point for the bonsai statusline -- written by bonsai-setup.py.
# Resolves the newest installed plugin version, so a plugin update does not
# leave settings.json pointing at a deleted version directory.
set -uo pipefail
cfg_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
root=$(ls -d "$cfg_dir"/plugins/cache/*/claude-bonsai/*/ 2>/dev/null | sort -V |
  while read -r d; do [ -x "$d/bin/bonsai-statusline.sh" ] && echo "$d"; done | tail -1)
[ -n "$root" ] || root=%(fallback)s
exec "$root/bin/bonsai-statusline.sh"
"""

SAMPLE = {
    "session_id": "bonsai-setup-check",
    "transcript_path": "",
    "model": {"id": "claude-opus-5", "display_name": "Opus 5"},
    "workspace": {"current_dir": str(pathlib.Path.cwd())},
    "rate_limits": {"five_hour": {"used_percentage": 61.0, "resets_at": time.time() + 11160}},
}


def load_settings():
    if not SETTINGS.exists():
        return {}
    try:
        return json.loads(SETTINGS.read_text() or "{}")
    except ValueError as exc:
        sys.exit("settings.json is not valid JSON (%s); fix it before running setup." % exc)


def save_settings(data):
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS.with_suffix(".json.bonsai-tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(SETTINGS)


def statusline_command(settings):
    entry = settings.get("statusLine")
    if isinstance(entry, dict):
        return entry.get("command")
    return entry if isinstance(entry, str) else None


def is_bonsai(command):
    return bool(command) and "bonsai" in command


def install():
    settings = load_settings()
    notes = []

    # Only ever back up the genuinely pre-bonsai file; a second install must not
    # overwrite it with a bonsai-modified copy.
    if SETTINGS.exists() and not BACKUP.exists():
        shutil.copy2(SETTINGS, BACKUP)
        notes.append("backed up settings.json -> %s" % BACKUP.name)

    old = statusline_command(settings)
    if old and not is_bonsai(old):
        CHAIN.write_text("#!/bin/bash\nexec %s\n" % old)
        CHAIN.chmod(0o755)
        notes.append("kept your previous statusline in %s; it renders under the tree" % CHAIN.name)

    SHIM.write_text(SHIM_TEMPLATE % {"fallback": json.dumps(str(PLUGIN_ROOT))})
    SHIM.chmod(0o755)

    settings["statusLine"] = {
        "type": "command",
        "command": str(SHIM),
        "padding": 1,
        "refreshInterval": 5,
    }
    save_settings(settings)
    notes.append("statusLine -> %s" % SHIM)

    for note in notes:
        print("  " + note)
    print("\nPreview:")
    try:
        out = subprocess.run([str(SHIM)], input=json.dumps(SAMPLE), capture_output=True,
                             text=True, timeout=15)
        sys.stdout.write(out.stdout)
        if out.returncode != 0:
            print("  shim exited %d: %s" % (out.returncode, out.stderr.strip()))
    except OSError as exc:
        print("  could not run the shim: %s" % exc)
    print("\nRestart Claude Code to pick it up.")


def remove():
    settings = load_settings()
    restored = None

    if CHAIN.exists():
        for line in CHAIN.read_text().splitlines():
            if line.startswith("exec "):
                restored = line[len("exec "):].strip()
    if restored is None and BACKUP.exists():
        try:
            restored = statusline_command(json.loads(BACKUP.read_text() or "{}"))
        except ValueError:
            restored = None

    if restored and not is_bonsai(restored):
        settings["statusLine"] = {"type": "command", "command": restored}
        print("  restored your previous statusline: %s" % restored)
    else:
        settings.pop("statusLine", None)
        print("  removed the statusLine entry")
    save_settings(settings)

    for path in (CHAIN, SHIM):
        if path.exists():
            path.unlink()
            print("  deleted %s" % path.name)
    print("  left %s alone" % CONFIG.name)
    print("\nRestart Claude Code to pick it up.")


def status():
    command = statusline_command(load_settings())
    print("  config dir:  %s" % CFG_DIR)
    print("  statusLine:  %s" % (command or "(not set)"))
    print("  wired:       %s" % ("yes" if is_bonsai(command) else "no"))
    print("  shim:        %s" % (SHIM if SHIM.exists() else "(absent)"))
    print("  chain:       %s" % (CHAIN if CHAIN.exists() else "(none)"))
    print("  plugin root: %s" % PLUGIN_ROOT)
    if CONFIG.exists():
        print("  %s:" % CONFIG.name)
        for line in CONFIG.read_text().splitlines():
            print("    " + line)
    else:
        print("  %s: (none, using defaults)" % CONFIG.name)


def main():
    action = (sys.argv[1] if len(sys.argv) > 1 else "install").lower()
    if action == "install":
        install()
    elif action == "remove":
        remove()
    elif action == "status":
        status()
    else:
        sys.exit("usage: bonsai-setup.py [install|remove|status]")


if __name__ == "__main__":
    main()
