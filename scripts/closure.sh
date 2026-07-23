#!/usr/bin/env bash
#
# @mcp-tool: closure
# @mcp-desc: Manifest-driven session closure — writes findings, sprint file, WORKLIST/STARTER/ARCHIVE consolidation, REGISTRY, handover flips and the STARTER rewrite, checks fail-closed assertions, then commits+pushes the superrepo. Use dry_run for a write-free preview (diffs + planned git block).
# @mcp-arg: manifest | string | required | path to the closure manifest (absolute, or relative to the superrepo root)
# @mcp-arg: dry_run | boolean | optional | preview only — print unified diffs and the planned git block; writes nothing, runs no git mutation
#
# Thin decorator around scripts/closure.py for the script-runner MCP server.
# The core logic lives entirely in closure.py; this wrapper only parses the
# runner's name=value argument tokens, verifies preconditions, and execs.
#
# Contract (do not weaken — the fail-closed property depends on it):
#   * Exit codes are passed through UNCHANGED via exec: 0 ok · 1 usage/I/O ·
#     2 manifest schema · 3 assertion broken (fail-closed) · 4 git blocked.
#     The MCP server surfaces a non-zero exit as isError with an
#     "[exit code: N]" + "[stderr]" block, so FAIL: … messages stay visible.
#   * stderr is NOT redirected or filtered here.
#   * Push-credential preflight (ALL push targets): a real run
#     (no dry_run) first does `git push --dry-run origin main` in the superrepo
#     AND in the spec submodule (the only submodule closure.py may push — its
#     COMMIT_WHITELIST). If the runner context cannot push either target, the
#     run refuses BEFORE closure.py starts — so a commit without push
#     capability can never happen from this entry point. dry_run skips the
#     preflight (read-only preview, works offline). closure.py repeats the
#     same preflight itself, so direct invocations are covered identically.
#
# The runner executes this with cwd = superrepo root; the cd below is a
# defensive no-op there and only matters for direct manual invocation.

set -u

MANIFEST=""
DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    manifest=*) MANIFEST="${arg#manifest=}" ;;
    dry_run|dry_run=true|--dry-run) DRY_RUN=1 ;;
    dry_run=false) : ;;
    *=*) : ;;  # unknown name=value token — tolerate (scripts/README.md convention)
    -*) : ;;   # unknown flag — tolerate
    *) [ -z "$MANIFEST" ] && MANIFEST="$arg" ;;  # bare token: manifest path (manual use)
  esac
done

if ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "$ROOT" || { echo "closure: cannot cd to repo root: $ROOT" >&2; exit 1; }
fi

if [ -z "$MANIFEST" ]; then
  echo "closure: missing required argument: manifest=<path> (add dry_run for a write-free preview)" >&2
  exit 1
fi
if [ ! -f "$MANIFEST" ]; then
  echo "closure: manifest not found: $MANIFEST (cwd: $(pwd))" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "closure: python3 not found on PATH" >&2
  exit 1
fi

if [ "$DRY_RUN" -eq 0 ]; then
  # all push targets: the superrepo plus every whitelisted submodule present
  # (mirrors COMMIT_WHITELIST in closure.py — currently only spec)
  PREFLIGHT_TARGETS="."
  [ -e "spec/.git" ] && PREFLIGHT_TARGETS=". spec"
  for repo in $PREFLIGHT_TARGETS; do
    if ! PREFLIGHT="$(git -C "$repo" push --dry-run origin main 2>&1)"; then
      {
        echo "closure: push preflight failed for '$repo' — refusing to start (a closure must never commit without push capability):"
        echo "$PREFLIGHT"
      } >&2
      exit 4
    fi
  done
fi

if [ "$DRY_RUN" -eq 1 ]; then
  exec python3 scripts/closure.py "$MANIFEST" --dry-run
else
  exec python3 scripts/closure.py "$MANIFEST"
fi
