# Example — AI UGC Meta Ad

A real ad shipped through this pipeline. AI UGC talking-head clip + caption highlights + 3 motion graphic beats + CTA endcard. 75s total.

The raw clip is not committed (it's the user's branded creative — not redistributable). What's here:

| File | What it is |
|---|---|
| [config.json](config.json) | The exact config used to generate the ad |
| [verify/](verify/) | Frame stills from the rendered output — what each MG beat looks like in context |

## Reproduce it

If you have your own AI UGC clip and want to mimic this ad's structure:

1. Drop your clip in this folder as `raw.mp4`
2. Run `bash ../../helpers/transcribe.sh raw.mp4 transcript.json`
3. Edit `config.json`:
   - Replace `pain_words` / `money_words` with terms from your script
   - Adjust `motion_graphics` cue points (`start_t`) to land on your script's beats
   - Update `motion_graphics[*].header / amount / main / sub` to your copy
4. Run `python ../../helpers/make_overlays.py && python ../../helpers/make_captions.py && bash ../../helpers/compose.sh`

## What each frame shows

### `00-pain-caption.jpg`
Caption highlight on pain words: **11PM** and **LOSING** in orange.

### `01-carrier-chip.jpg`
`list_chip` overlay landing on "AT&T, Verizon, T-Mobile" in the script. Top-right credibility chip with three carrier pills, slides in/out.

### `02-money-stamp.jpg`
`money_stamp` overlay at the proof beat: "$12,000 CASH UPFRONT — CLOSED LAST WEEK." Bounce-in scale, holds 1.5s, fades.

### `03-cta-endcard.jpg`
`cta_endcard` overlay during the close: "BOOK THE CALL" + risk reversal + pulsing chevron pointing at the platform's CTA button. Held to last frame.

### `04-fridge-opening.jpg`
The pattern-interrupt opening (the AI character is filmed inside a fridge — the camera is *in* the fridge looking out). Caption "LAST WEEK," anchors the viewer's eye while the visual settles. Don't underestimate weird framing in AI UGC — it's often the strongest scroll-stopper you have.

## Conversion-relevant decisions in this config

- **`speed: 1.15`** — AI UGC voices default to a too-slow pace that screams "I'm AI." 1.15× preserves pitch (`atempo`) but tightens delivery to feel human.
- **Two accent colors only** — orange for pain/agitation (`LOST`, `30 DAYS`, `YOUTUBE TUTORIAL`), green for money/proof (`$12K`, `CASH`, `REVENUE ENGINE`). The eye reads an emotional arc: agitation → reward.
- **CTA points at the platform button**, not a URL. On Meta Ads, the "Learn More" button below the video is the click destination — the in-video CTA just says "TAP BELOW ↓."
- **Risk reversal beats price**. The CTA card emphasizes "$200 IF WE WASTE YOUR TIME" over the offer itself. People click on the safety net.
