# UGC Ad Pipeline

> Drop a raw AI UGC clip in a folder, say *"edit this for Meta"*, get a converting paid-social ad out.

A Claude Code skill that turns one AI UGC talking-head clip into a Meta-Ads-ready vertical video. Word-synced captions with color-coded highlights on pain/money words, 2–4 motion-graphic beats at the right moments, CTA endcard, all driven by one config file.

Built for AI UGC characters (HeyGen, Arcads, Captions.ai, AI Studios, etc.). For human-recorded talking heads with filler words to cut, use [video-use](https://github.com/browser-use/video-use) instead.

---

## What you get

| Stage | What it produces |
|---|---|
| Transcribe | Word-level timestamps via local Whisper (no API key) |
| Caption frames | 2-word UPPERCASE chunks, white default, **orange on pain words**, **green on money/proof words** |
| Motion graphics | 3 built-in patterns: `list_chip` (corner credibility chip), `money_stamp` (center result stamp), `cta_endcard` (bottom slide-up CTA) |
| Composite | One ffmpeg pass — speed-adjusts the source (`atempo` preserves pitch), overlays MGs at their cue points, captions on top with auto-suppression during MG windows |

You configure: pain words, money words, MG copy, MG cue points, brand colors, speed, CTA text. Everything else is automatic.

---

## Install

```bash
git clone https://github.com/jbrazy480/claude-ugc-ad-pipeline ~/Developer/claude-ugc-ad-pipeline
cd ~/Developer/claude-ugc-ad-pipeline

# Deps
brew install ffmpeg                              # macOS — or apt-get install ffmpeg
python3 -m pip install --user Pillow

# Register with Claude Code
mkdir -p ~/.claude/skills
ln -sfn ~/Developer/claude-ugc-ad-pipeline ~/.claude/skills/ugc-ad-pipeline
```

Verify: `ls ~/.claude/skills/ugc-ad-pipeline/SKILL.md`. Full install notes in [install.md](install.md).

## Use it

```bash
mkdir -p ~/Movies/my-ad && cd ~/Movies/my-ad
cp ~/Downloads/your-ai-ugc-clip.mp4 raw.mp4
cp ~/Developer/claude-ugc-ad-pipeline/config.example.json config.json
# Edit config.json — pain_words, money_words, motion_graphics for your script

claude
# Then: "edit this UGC clip for Meta"
```

Claude reads `SKILL.md` from your skills directory and runs the pipeline:
1. Transcribes the source video (`helpers/transcribe.sh`)
2. Generates motion-graphic overlays from `config.json` (`helpers/make_overlays.py`)
3. Generates caption frames synced to the transcript (`helpers/make_captions.py`)
4. Composites everything in one ffmpeg pass (`helpers/compose.sh`)
5. Verifies the render at every cue point before declaring it done

Output: `final.mp4` next to your source.

## Manual mode (no Claude needed)

If you'd rather skip the agent and just run the pipeline:

```bash
cd ~/Movies/my-ad
bash   ~/.claude/skills/ugc-ad-pipeline/helpers/transcribe.sh raw.mp4 transcript.json
python ~/.claude/skills/ugc-ad-pipeline/helpers/make_overlays.py
python ~/.claude/skills/ugc-ad-pipeline/helpers/make_captions.py
bash   ~/.claude/skills/ugc-ad-pipeline/helpers/compose.sh
```

---

## Why this exists (and what it isn't)

**This isn't a video editor.** It's a templating engine for one specific creative pattern: AI UGC talking-head + word-synced captions + 2–4 MG beats + CTA card. That pattern converts on Meta Ads when the script is good. This skill makes the production step nearly free.

**The opinionated parts:**
- Two accent colors max (orange = pain, green = money). More colors → lower conversion.
- Captions in upper-third — never on the speaker's face.
- AI UGC defaults to `speed: 1.15` because the source is always too slow to feel human.
- CTA card holds to the last frame, points at the platform's CTA button.
- No music. The AI voice carries it.

**Things you'll outgrow:**
- The 3 built-in MG types cover ~80% of cases. For anything else, write a new builder in `make_overlays.py` (~50 lines next to the existing ones).
- For multi-take human-recorded UGC where you need to remove filler words and pick best-take cuts, use [video-use](https://github.com/browser-use/video-use) — it's the right tool for that.

## Built on top of

- **[video-use](https://github.com/browser-use/video-use)** by Browser Use — the conversation-driven editor whose render contract (per-segment extract, 30ms audio fades, PTS-shifted overlays, captions LAST) influenced the composite step.
- **[Hyperframes](https://github.com/heygen-com/hyperframes)** by HeyGen — the local Whisper transcribe is a thin wrapper around `hyperframes transcribe`.

## License

MIT. See [LICENSE](LICENSE). Use it, fork it, sell videos with it.

## Credits

Built by James Hill. PRs welcome — keep helpers small and config-driven, no extra Python deps beyond Pillow.
