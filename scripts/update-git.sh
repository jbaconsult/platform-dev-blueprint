#!/usr/bin/env bash
#
# @mcp-tool: updategit
# @mcp-desc: Pull the superrepo and every submodule. Default --branches mode pulls each repo on its own branch (--ff-only), skipping dirty/detached/no-origin. --pointers mode runs `git submodule update --remote` instead. Never commits, pushes, or forces; pointer changes are left uncommitted for an operator-gated git block.
# @mcp-arg: mode | string | optional | "branches" (default) or "pointers"
#
# Run by the script-runner MCP server with the working directory set to the
# superrepo root (the server resolves it via `git rev-parse --show-toplevel`).
# Read-and-pull only — the writing git work (commit/push/pointer-bump) stays
# operator-gated and is NOT done here.
#
# Exit: 0 if nothing failed; 1 on any failed pull or if not a git work tree.

set -u

# --- argument parsing (tolerate unknown args; the server may pass others) ---
MODE="branches"
for arg in "$@"; do
  case "$arg" in
    branches|--branches|mode=branches) MODE="branches" ;;
    pointers|--pointers|mode=pointers) MODE="pointers" ;;
    *) : ;;  # ignore anything we don't understand
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "not a git work tree: $(pwd)" >&2
  exit 1
fi

green=$'\e[32m'; yellow=$'\e[33m'; red=$'\e[31m'; bold=$'\e[1m'; reset=$'\e[0m'
ok=(); skipped=(); failed=()

# --- pull the repo at the current directory; $1 = label (used in branches mode
#     for the superrepo root) ---
pull_here() {
  local name="$1"
  printf '%s==> %s%s\n' "$bold" "$name" "$reset"

  local branch
  if ! branch="$(git symbolic-ref --quiet --short HEAD)"; then
    printf '  %sskip%s — detached HEAD\n' "$yellow" "$reset"
    skipped+=("$name (detached)"); return
  fi
  if [ -n "$(git status --porcelain)" ]; then
    printf '  %sskip%s — uncommitted changes on %s\n' "$yellow" "$reset" "$branch"
    skipped+=("$name (dirty)"); return
  fi
  if ! git remote get-url origin >/dev/null 2>&1; then
    printf '  %sskip%s — no origin remote\n' "$yellow" "$reset"
    skipped+=("$name (no origin)"); return
  fi
  if git pull --ff-only --quiet; then
    printf '  %sok%s — %s up to date\n' "$green" "$reset" "$branch"
    ok+=("$name")
  else
    printf '  %sFAIL%s — pull on %s did not fast-forward\n' "$red" "$reset" "$branch"
    failed+=("$name")
  fi
}

if [ "$MODE" = "pointers" ]; then
  # --- idiomatic submodule sync: pull the superrepo branch, then move each
  #     submodule to its remote-tracking branch via update --remote ---
  printf '%smode: pointers%s\n\n' "$bold" "$reset"
  pull_here "superrepo (root)"
  echo
  printf '%s==> submodules (update --remote --recursive)%s\n' "$bold" "$reset"
  if git submodule update --remote --recursive; then
    printf '  %sok%s — submodules synced to remote-tracking branches\n' "$green" "$reset"
    ok+=("submodules (--remote)")
    # surface any resulting pointer drift so the operator knows a commit is due
    pointer_changes="$(git status --porcelain | grep -E '^[ M]M ' || true)"
    if [ -n "$pointer_changes" ]; then
      printf '  %sNOTE%s — submodule pointers changed; uncommitted in superrepo:\n' "$yellow" "$reset"
      printf '%s\n' "$pointer_changes" | sed 's/^/    /'
    fi
  else
    printf '  %sFAIL%s — submodule update --remote did not complete\n' "$red" "$reset"
    failed+=("submodules (--remote)")
  fi
else
  # --- branches mode (default): pull every repo on its own branch ---
  printf '%smode: branches%s\n\n' "$bold" "$reset"
  pull_here "superrepo (root)"
  echo
  if [ -f .gitmodules ]; then
    # `git submodule foreach` runs each iteration in a subshell, so array
    # mutations there cannot reach this shell. Instead each iteration emits a
    # machine-parseable OK::/SKIP::/FAIL:: line on stdout, which the parent loop
    # below tallies. Human-readable lines pass through unchanged.
    while IFS= read -r line; do
      case "$line" in
        OK::*)   ok+=("${line#OK::}") ;;
        SKIP::*) skipped+=("${line#SKIP::}") ;;
        FAIL::*) failed+=("${line#FAIL::}") ;;
        *)       printf '%s\n' "$line" ;;
      esac
    done < <(git submodule foreach --recursive --quiet '
      printf "%s==> %s%s\n" "'"$bold"'" "$name" "'"$reset"'"
      if ! b="$(git symbolic-ref --quiet --short HEAD)"; then
        printf "  %sskip%s — detached HEAD\n" "'"$yellow"'" "'"$reset"'"
        echo "SKIP::$name (detached)"; exit 0
      fi
      if [ -n "$(git status --porcelain)" ]; then
        printf "  %sskip%s — uncommitted changes on %s\n" "'"$yellow"'" "'"$reset"'" "$b"
        echo "SKIP::$name (dirty)"; exit 0
      fi
      if ! git remote get-url origin >/dev/null 2>&1; then
        printf "  %sskip%s — no origin remote\n" "'"$yellow"'" "'"$reset"'"
        echo "SKIP::$name (no origin)"; exit 0
      fi
      if git pull --ff-only --quiet; then
        printf "  %sok%s — %s up to date\n" "'"$green"'" "'"$reset"'" "$b"
        echo "OK::$name"
      else
        printf "  %sFAIL%s — pull on %s did not fast-forward\n" "'"$red"'" "'"$reset"'" "$b"
        echo "FAIL::$name"
      fi
    ')
  fi
fi

printf '\n%ssummary:%s  %d ok · %d skipped · %d failed\n' \
  "$bold" "$reset" "${#ok[@]}" "${#skipped[@]}" "${#failed[@]}"
[ "${#skipped[@]}" -gt 0 ] && printf '  skipped: %s\n' "${skipped[*]}"
[ "${#failed[@]}"  -gt 0 ] && printf '  failed:  %s\n' "${failed[*]}"

[ "${#failed[@]}" -eq 0 ]
