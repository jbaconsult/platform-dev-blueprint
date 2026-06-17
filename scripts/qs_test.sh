#!/usr/bin/env bash
#
# qs_test.sh — OFFLINE TEST HELPER. Not the production path.
#
# In production, the script-runner MCP server (scripts/mcp-server/) discovers
# the tool scripts and exposes each as its own MCP tool. This helper exists only
# to run those same scripts locally — to smoke-test a script before the server
# picks it up, without going through MCP.
#
# It discovers every *.sh in this directory that carries a valid `@mcp-tool:`
# header (the same opt-in the server uses), runs each from the superrepo root
# with all arguments forwarded verbatim, and prints a labelled report. It is a
# convenience, not a contract: the server is the authority on what becomes a
# tool.
#
# Exit: number of scripts that exited non-zero (0 if all succeeded).

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Superrepo root, independent of the caller's CWD — scripts run from here.
if REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
cd "$REPO_ROOT" || { echo "qs_test: cannot cd to repo root: $REPO_ROOT" >&2; exit 255; }

# Discover tool scripts: top-level *.sh in scripts/ with an @mcp-tool: header.
# (Same opt-in rule as the server. Files without the header — libs, this helper
#  itself — are skipped. Not recursive, so scripts/mcp-server/ is untouched.)
shopt -s nullglob
CANDIDATES=("$SCRIPT_DIR"/*.sh)
shopt -u nullglob

TOOLS=()
for f in "${CANDIDATES[@]}"; do
  [ "$(basename "$f")" = "qs_test.sh" ] && continue
  if grep -qE '^[[:space:]]*#[[:space:]]*@mcp-tool:' "$f"; then
    TOOLS+=("$f")
  fi
done

if [ "${#TOOLS[@]}" -eq 0 ]; then
  echo "qs_test: no @mcp-tool scripts found in $SCRIPT_DIR" >&2
  exit 0
fi

FAILED=0
TOTAL=0
for tool in "${TOOLS[@]}"; do
  name="$(basename "$tool")"
  TOTAL=$((TOTAL + 1))
  echo "=== ${name} ==="
  if [ -x "$tool" ]; then "$tool" "$@"; else bash "$tool" "$@"; fi
  rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "--- ${name}: exit ${rc} ---" >&2
    FAILED=$((FAILED + 1))
  fi
  echo
done

echo "=== qs_test summary ==="
echo "tool scripts run: ${TOTAL} · failed: ${FAILED}"
exit "$FAILED"
