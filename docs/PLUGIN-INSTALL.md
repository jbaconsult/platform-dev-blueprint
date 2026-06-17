# Installing the skills as a Claude Desktop plugin

The lifecycle skills in `skills/` are packaged as a **Claude plugin** via the
`.claude-plugin/plugin.json` manifest at the repo root. This is how they become
*triggering* skills in a Claude Desktop session (concept work), not just files
in the repo.

> **Two different skill systems — pick the right one.** Claude Code loads skills
> from a `~/.claude/skills/` (or project `.claude/skills/`) directory. Claude
> **Desktop** (the GUI app) does **not** reliably use that path — it installs
> skills/plugins via a **ZIP upload** through the Customize UI. The two
> mechanisms are separate. For Desktop, use the plugin ZIP described here; the
> `~/.claude/skills/` directory is the Claude Code path.

## What gets packaged

A plugin is a directory with this shape (only `plugin.json` lives inside
`.claude-plugin/`; everything else sits at the plugin root):

```
<plugin-name>/
├── .claude-plugin/
│   └── plugin.json        ← the manifest (name, version, description)
└── skills/
    ├── session-start/SKILL.md
    ├── solve-problem/SKILL.md
    ├── session-closure/SKILL.md
    ├── code-handover/SKILL.md
    ├── adr-author/SKILL.md
    └── fs-write/SKILL.md
```

This repo already has both pieces: `.claude-plugin/plugin.json` and `skills/`.
A derived instance should give its plugin a unique `name` in `plugin.json`
(e.g. `forgenesis-platform-dev`, `kumbuka-platform-dev`) so two instances'
plugins do not collide in the same Desktop account.

## Build the plugin ZIP

Stage just the manifest and `skills/` (never zip the whole repo — it carries
submodules and chat-context). Build the ZIP with the **plugin folder as the ZIP
root** (verified working form):

```bash
# stage a clean plugin dir (manifest + skills only)
rm -rf /tmp/<plugin-name>
mkdir -p /tmp/<plugin-name>
cp -R <workspace_root>/.claude-plugin /tmp/<plugin-name>/
cp -R <workspace_root>/skills         /tmp/<plugin-name>/

# sanity-check the shape
find /tmp/<plugin-name> -maxdepth 2

# zip with the plugin folder AS the ZIP root
cd /tmp
zip -r ~/Desktop/<plugin-name>.zip <plugin-name>
```

The ZIP then contains `<plugin-name>/.claude-plugin/plugin.json` and
`<plugin-name>/skills/...`. (Add `-x "*.DS_Store"` to keep macOS metadata out.)

## Install in Claude Desktop

1. Customize → Skills → **+** → **Create skill**.
2. Select the ZIP. Desktop reads the manifest and lists the bundled skills.
3. Toggle the plugin **on** (off = ignored).
4. The skills trigger automatically by their `description`; verify with
   "Which skills are available?" in a new session.

## Updating

Desktop plugins are account-bound copies, not a live link to the repo — there is
no git-tracked auto-update. When a `SKILL.md` changes, **rebuild the ZIP and
re-upload** (remove the old plugin first, or overwrite). Keep the repo as the
source of truth; the uploaded plugin is a snapshot.
