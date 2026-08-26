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

python3 "$here/bonsai.py" --statusline <<<"$input" 2>/dev/null

# Run the statusline bonsai replaced.
if [ -x "$chain_file" ]; then
  cache="${TMPDIR:-/tmp}/bonsai-chain.cache"
  now=$(date +%s)
  then_=$(stat -f %m "$cache" 2>/dev/null || stat -c %Y "$cache" 2>/dev/null || echo 0)
  if [ ! -s "$cache" ] || [ $((now - then_)) -ge 5 ]; then
    "$chain_file" <<<"$input" >"$cache.tmp" 2>/dev/null && mv -f "$cache.tmp" "$cache"
  fi
  cat "$cache" 2>/dev/null
fi
