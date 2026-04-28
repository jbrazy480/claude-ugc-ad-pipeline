---
name: ugc-ad-pipeline-install
description: First-time install — clone the skill, install ffmpeg + Python deps, register with Claude Code so the user can start editing UGC ads.
---

# Install

You're setting up the UGC Ad Pipeline skill on a new machine. After install, the user drops a raw AI UGC clip into a folder, runs Claude there, and says "edit this for Meta." You handle the rest by reading `SKILL.md`.

## Three things that must exist on this machine

1. The repo cloned somewhere stable (`~/Developer/claude-ugc-ad-pipeline` is the default).
2. `ffmpeg` + `ffprobe` on `$PATH` (Node 20+ for the Hyperframes transcribe shim is also nice but optional).
3. Python 3.9+ with `Pillow` installed (`pip install Pillow` or use any venv with PIL).

And one thing must be true about the agent:

4. It can discover `SKILL.md` — typically via a symlink at `~/.claude/skills/ugc-ad-pipeline`.

## Steps

### 1. Clone

```bash
test -d ~/Developer/claude-ugc-ad-pipeline || \
  git clone https://github.com/jbrazy480/claude-ugc-ad-pipeline ~/Developer/claude-ugc-ad-pipeline
```

If already cloned, `cd ~/Developer/claude-ugc-ad-pipeline && git pull --ff-only`.

### 2. Install deps

```bash
# macOS
command -v ffmpeg >/dev/null || brew install ffmpeg
python3 -m pip install --user Pillow

# Debian / Ubuntu
# sudo apt-get update && sudo apt-get install -y ffmpeg python3-pil
```

If `brew` / `apt` requires a sudo prompt, tell the user the exact command and wait. Don't invent a password.

### 3. Register with Claude Code

```bash
mkdir -p ~/.claude/skills
ln -sfn ~/Developer/claude-ugc-ad-pipeline ~/.claude/skills/ugc-ad-pipeline
```

For Codex / Hermes / other agents with skills directories, symlink to that agent's skills directory under the name `ugc-ad-pipeline` instead.

### 4. Verify

```bash
python3 -c "from PIL import Image; print('PIL OK')"
ffmpeg -version | head -1
ls ~/.claude/skills/ugc-ad-pipeline/SKILL.md && echo "skill registered"
```

If all three checks pass, install is done. Don't transcribe a real video at install time — that wastes Whisper compute.

### 5. Hand off

Tell the user:
- Where the skill is installed (`~/Developer/claude-ugc-ad-pipeline`).
- They can `cd` into any folder containing a raw UGC clip and start a Claude session.
- A good first message is: *"edit this UGC clip for Meta — 9:16, captions in upper third, brand colors orange/green."*
- All outputs land alongside the source — `final.mp4`, `transcript.json`, `build/` build artifacts.

## Updating

```bash
cd ~/Developer/claude-ugc-ad-pipeline && git pull --ff-only
```

The symlink auto-picks up changes. If `make_overlays.py` changes shape, the user's existing `config.json` may need a tweak — check `config.example.json` for new fields.

## Cold-start reminders

- **Symlink the WHOLE directory**, not just `SKILL.md`. `helpers/` must sit next to it.
- **Pillow is the only Python dep.** Don't install anything else unless future helper scripts require it.
- **Hyperframes CLI is optional** — only needed if you use `helpers/transcribe.sh`. The user can also bring their own transcript if they have one.
