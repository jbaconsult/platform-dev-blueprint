#!/usr/bin/env bash
#
# @mcp-tool: gitstatus
# @mcp-desc: Git ground-truth for the superrepo and every submodule — branch, upstream ahead/behind, short working-tree status, latest commit, and submodule pointer alignment.
# @mcp-arg: verbose | boolean | optional | include the full per-repo `git status` (not just -sb short form)
#
# Run by the script-runner MCP server with the working directory set to the
# superrepo root (the server resolves it via `git rev-parse --show-toplevel`).
# Reports, for the superrepo and each submodule: current branch, ahead/behind
# vs. upstream, short status, and the latest commit. Submodule pointer alignment
# is shown via `git submodule status` (leading '+' = checked-out commit differs
# from the recorded pointer; '-' = uninitialized submodule).
#
# Exit: 0 on success; 1 if the working directory is not a git work tree.

set -u

# --- argument parsing (tolerate unknown args; the server may pass others) ---
VERBOSE=0
for arg in "$@"; do
  case "$arg" in
    verbose|--verbose|verbose=true) VERBOSE=1 ;;
    *) : ;;  # ignore anything we don't understand
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "not a git work tree: $(pwd)" >&2
  exit 1
fi

# --- helper: report the repo at the current directory ---
report_here() {
  local label="$1"

  local branch
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '(detached)')"
  echo "[$label] branch: $branch"

  local upstream
  if upstream="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)"; then
    local counts behind ahead
    counts="$(git rev-list --left-right --count "${upstream}...HEAD" 2>/dev/null)"
    if [ -n "$counts" ]; then
      behind="$(echo "$counts" | awk '{print $1}')"
      ahead="$(echo "$counts" | awk '{print $2}')"
      echo "  upstream: $upstream  (ahead $ahead, behind $behind)"
    fi
  else
    echo "  upstream: (none)"
  fi

  echo "  status:"
  if [ "$VERBOSE" -eq 1 ]; then
    git status 2>/dev/null | sed 's/^/    /'
  else
    git status -sb 2>/dev/null | sed 's/^/    /'
  fi

  echo "  HEAD: $(git log --oneline -1 2>/dev/null)"
}

# --- superrepo ---
report_here "superrepo"
echo

# --- submodules (if any) ---
if [ -f .gitmodules ]; then
  echo "[submodules] pointer alignment:"
  git submodule status --recursive 2>/dev/null | sed 's/^/  /'
  echo

  git submodule foreach --recursive --quiet '
    echo "--- submodule: $name ($sm_path) ---"
    branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "(detached)")"
    echo "  branch: $branch"
    echo "  status:"
    git status -sb 2>/dev/null | sed "s/^/    /"
    echo "  HEAD: $(git log --oneline -1 2>/dev/null)"
  '
else
  echo "[submodules] none (.gitmodules absent)"
fi
