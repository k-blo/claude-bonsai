#!/bin/bash
# Statusline entry point. Chains a previous statusline if configured.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cfg_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
chain_file="$cfg_dir/bonsai-chain.sh"
input=$(cat)

# Claude Code does not export COLUMNS; work it out for centring.
if [ -z "${COLUMNS:-}" ] || ! [ "$COLUMNS" -eq "$COLUMNS" ] 2>/dev/null; then
  COLUMNS=$(stty size 2>/dev/null </dev/tty | awk '{print $2}')
fi
case "${COLUMNS:-}" in "" | *[!0-9]*) COLUMNS=80 ;; esac
export COLUMNS

# Never swallow the failure: a blank statusline with no reason is unfixable.
if ! command -v python3 >/dev/null 2>&1; then
  echo "bonsai: python3 not found on PATH"
else
  err="${TMPDIR:-/tmp}/bonsai-err.$$"
  if out=$(python3 "$here/bonsai.py" --statusline <<<"$input" 2>"$err"); then
    [ -n "$out" ] && printf '%s\n' "$out"
  else
    printf 'bonsai: %s\n' "$(tail -n 1 "$err" | cut -c1-160)"
  fi
  rm -f "$err"
fi

# Run the statusline bonsai replaced.
if [ -x "$chain_file" ]; then
  cache="${TMPDIR:-/tmp}/bonsai-chain.cache"
  now=$(date +%s)
  # GNU form first: on Linux `stat -f %m F` treats %m as a second FILE, exits 1
  # but still prints "  File: ..." on stdout, so the fallback's number gets
  # prefixed with junk and $(( )) below dies with "File: unbound variable".
  then_=$(stat -c %Y "$cache" 2>/dev/null || stat -f %m "$cache" 2>/dev/null || echo 0)
  case "$then_" in "" | *[!0-9]*) then_=0 ;; esac
  if [ ! -s "$cache" ] || [ $((now - then_)) -ge 5 ]; then
    "$chain_file" <<<"$input" >"$cache.tmp" 2>/dev/null && mv -f "$cache.tmp" "$cache"
  fi
  cat "$cache" 2>/dev/null
fi
