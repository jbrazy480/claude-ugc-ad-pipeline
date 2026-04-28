---
name: ugc-ad-pipeline
description: Convert raw AI UGC talking-head videos into Meta-Ads-ready vertical clips with conversion-optimized captions (color-coded pain/money words), motion-graphic overlays at key beats, and a CTA endcard. Use when the user has an AI UGC clip (HeyGen, Arcads, Captions.ai, etc.) and wants it edited for paid social — not for filler-word removal of human takes (use video-use for that). Triggers on "edit my UGC ad," "make this Meta-ready," "add captions and graphics," "convert this for Reels/TikTok ads."
---

# UGC Ad Pipeline

Turn one AI UGC clip into a converting paid-social ad. Captions sync to the words. Pain words turn orange, money/proof words turn green. Three motion graphic moments land at the right beats. CTA endcard hits the close. All driven by one `config.json`.

## Hard rules (production correctness)

These cause silent failures or broken output if you skip them. Memorize.

1. **Captions go on the LAST overlay layer** so they're never hidden by motion graphics — but they auto-suppress during MG windows (derived from cue points) so the two never collide.
2. **All motion graphic cue points are in ORIGINAL video time** (not output time after speed-up). The pipeline rescales cues by `1 / speed` automatically.
3. **`atempo` for audio speed-up, never raw playback rate.** atempo preserves pitch — the voice doesn't sound chipmunked. Use `setpts=PTS/SPEED` for video.
4. **Source AI UGC clips are usually too slow** (~0.85–0.9× of natural speech). Default to `speed: 1.15` for AI UGC. Real-human UGC uses `speed: 1.0`.
5. **The CTA endcard must hold to the last frame.** Compute `tail_seconds` so `cta.start_t + cta.duration ≥ raw_duration / speed + tail_seconds`.
6. **Captions must NOT cover the speaker's face.** Default `y_position` is upper-third (380px on 1920 frame). Adjust per shot if framing differs.
7. **Verify before delivery.** Pull frames at every cue point AND scattered through the timeline. Read each PNG into context — don't trust filenames.

## When to use this skill

- User has an AI UGC clip (HeyGen, Arcads, Captions.ai, AI Studios, etc.) and wants paid-social-ready output.
- They want captions, color highlights on key phrases, and 1–4 motion graphic beats.
- They're running this on **Meta Ads, TikTok Ads, YouTube Shorts, or organic Reels**.

**When NOT to use:** human-recorded talking head with filler words / messy takes — use the `video-use` skill instead. That skill cuts on word boundaries and removes "um"s. This one assumes clean AI audio and focuses on the conversion overlay.

## Conversation flow

1. **Inventory.** `ffprobe` the source. Run `bash helpers/transcribe.sh raw.mp4 transcript.json` (free, local Whisper). Pull 6–8 frames evenly across the timeline and read them into context.
2. **Read the script.** Pack the transcript into phrases and identify the structural beats: hook, pain, reframe, solution, proof, CTA. The user's `config.json` is built around these beats.
3. **Propose strategy in plain English.** What's the ad selling? Who's the ICP? What's the CTA? Which words deserve color highlights? Where should the 2–4 MG beats land? **Wait for confirmation.**
4. **Build `config.json`** based on the agreed plan. Use `config.example.json` as the template.
5. **Generate overlays in this order:**
   ```bash
   python helpers/make_overlays.py        # MG PNG sequences
   python helpers/make_captions.py        # caption frames (auto-derives suppression windows from MG cues)
   bash   helpers/compose.sh              # final.mp4
   ```
6. **Verify the render.** Pull frames at every MG cue + a few scattered. Read each one into context. Look for: caption/MG collision (shouldn't happen with suppression), face cropping, off-cue MG timing, blank frames.
7. **Iterate.** Most edits are one config change + one re-render. Speed feels off → change `speed`. Color wrong → swap `pain_color`/`money_color`. Word missing the highlight → add to `pain_words`/`money_words`. MG cue late → adjust `start_t`.

## Config schema (copy `config.example.json`)

| Field | What it controls |
|---|---|
| `speed` | Speed-up factor. AI UGC: 1.15. Real human UGC: 1.0. |
| `tail_seconds` | Held-frame seconds at the end (CTA breathing room). Default 4. |
| `captions.pain_words` | UPPERCASE list. These words render in `pain_color`. |
| `captions.money_words` | UPPERCASE list. These render in `money_color`. Any word with `$` auto-classifies as money. |
| `captions.y_position` | Y pixel position from top. 380 = upper-third (above face). Increase if face is high in frame. |
| `motion_graphics[].start_t` | When the MG enters, in **original** video time (pre-speedup). |
| `motion_graphics[].duration` | How long it stays on screen. |
| `motion_graphics[].type` | One of `list_chip`, `money_stamp`, `cta_endcard`. |

## Caption color theory (why two colors, not five)

This pipeline is opinionated: **two accent colors max** — orange for pain/agitation, green for money/proof/safety. The emotional arc on viewer eyes goes "see the problem (orange) → see the proof + reward (green)."

More colors = visual noise = lower conversion. Resist the urge to add a third.

## Motion graphic patterns (built-in)

### `list_chip`
Top-corner credibility badge. Use for: carrier names, logo lists, certifications, stack badges. Slides in, holds, fades.

### `money_stamp`
Center-screen money/result hit. Use for: revenue claims, deal sizes, ROI numbers. Bounce-in scale, holds, fades.

### `cta_endcard`
Bottom slide-up CTA card. Always include this as the final MG. Has main headline + risk-reversal line + arrow pointing at the platform's CTA button. **Tune `duration` so it covers from `start_t` to the end of the video.**

If you need a pattern not covered here, write the new builder in `helpers/make_overlays.py` (~50 lines). Pattern lives next to the others.

## Common edits and what to change

| User says | What to change |
|---|---|
| "Too slow / too AI-sounding" | Increase `speed` 0.05 at a time. 1.15 → 1.20 → 1.25. Cap at 1.30. |
| "Captions cover her face" | Increase `captions.y_position` (move up). |
| "I want the $X to pop more" | Add the exact numeric token (e.g. `"$500"`) to `money_words`. |
| "Move the carrier chip earlier" | Decrease `motion_graphics[i].start_t`. |
| "Different brand colors" | Update `pain_color` and/or `money_color` (RGB arrays). |

## Anti-patterns (don't do these)

- **Don't run video-use first.** AI UGC clips don't have filler words to cut. Re-encoding twice degrades quality.
- **Don't use 3+ accent colors in captions.** Visual noise tanks conversion.
- **Don't burn captions inside the speaker's face area.** Always upper-third or above-shoulder.
- **Don't add music/SFX for AI UGC.** The voice carries the ad. Music competes for the same emotional channel.
- **Don't extend the video to >90s for paid social.** 60–80s is the conversion sweet spot. If the script is longer, cut something.
- **Don't ask the user for ElevenLabs.** Free local Whisper via `transcribe.sh` is good enough for AI UGC (clean audio).
- **Don't render at quality `draft` and ship.** Always `crf 18` minimum for paid social.
