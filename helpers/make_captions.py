#!/usr/bin/env python3
"""
Generate caption frames as PNG sequence from a word-level transcript + config.json.

Each PNG is a full-frame transparent overlay showing the active 2-word UPPERCASE chunk.
Pain words → orange, money words → green, everything else → white.
Suppression windows (where motion graphics own the screen) auto-derived from MG cue points.

Usage:
  python make_captions.py [--config config.json] [--project-dir /path/to/project]
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def normalize(word: str) -> str:
    return re.sub(r"^[^\w$&-]+|[^\w$&-]+$", "", word).upper()


def color_for(word_norm: str, pain_words: set, money_words: set,
               default_color, pain_color, money_color) -> tuple:
    if word_norm in pain_words:
        return pain_color
    if word_norm in money_words:
        return money_color
    if "$" in word_norm:
        return money_color
    return default_color


def build_chunks(words):
    """Group consecutive words into 2-word chunks, breaking on sentence punctuation."""
    chunks = []
    cur = []
    for w in words:
        cur.append(w)
        ends_sentence = bool(re.search(r"[.!?,]$", w["text"]))
        if len(cur) >= 2 or ends_sentence:
            chunks.append({
                "start": cur[0]["start"],
                "end": cur[-1]["end"],
                "words": cur[:],
            })
            cur = []
    if cur:
        chunks.append({
            "start": cur[0]["start"],
            "end": cur[-1]["end"],
            "words": cur,
        })
    # Pad each chunk to ~0.45s minimum readability
    for i, c in enumerate(chunks):
        if c["end"] - c["start"] < 0.45:
            c["end"] = c["start"] + 0.45
        if i + 1 < len(chunks):
            c["end"] = min(c["end"], chunks[i + 1]["start"])
    return chunks


def render_chunk_image(chunk, font_obj, W, H, y_position, outline_px,
                        pain_words, money_words,
                        default_color, pain_color, money_color):
    """Render one full-frame transparent PNG of the chunk's text."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    word_data = []
    for w in chunk["words"]:
        txt = w["text"].upper()
        clean = re.sub(r"[.,!?]$", "", txt)
        punct = txt[len(clean):]
        color = color_for(clean, pain_words, money_words,
                           default_color, pain_color, money_color)
        word_data.append((clean + punct, color))

    space_w = d.textlength(" ", font=font_obj)
    widths = [d.textlength(w, font=font_obj) for w, _ in word_data]
    total_w = sum(widths) + space_w * (len(word_data) - 1)
    x_start = (W - total_w) // 2
    y = y_position

    cursor_x = x_start
    for (w, color), w_width in zip(word_data, widths):
        # Black outline pass
        for dx in range(-outline_px, outline_px + 1):
            for dy in range(-outline_px, outline_px + 1):
                if dx * dx + dy * dy > outline_px * outline_px:
                    continue
                d.text((cursor_x + dx, y + dy), w, font=font_obj, fill=(0, 0, 0, 255))
        # Color fill pass
        d.text((cursor_x, y), w, font=font_obj, fill=tuple(color) + (255,))
        cursor_x += w_width + space_w

    return img


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--project-dir", default=".")
    args = parser.parse_args()

    proj = Path(args.project_dir).resolve()
    cfg = json.loads((proj / args.config).read_text())

    speed = cfg.get("speed", 1.0)
    fps = cfg.get("fps", 30)
    W = cfg.get("width", 1080)
    H = cfg.get("height", 1920)
    tail = cfg.get("tail_seconds", 4.0)

    cap = cfg.get("captions", {})
    font_path = cap.get("font_path", "/System/Library/Fonts/HelveticaNeue.ttc")
    font_index = cap.get("font_index", 1)
    font_size = cap.get("size", 90)
    outline_px = cap.get("outline_px", 6)
    y_position = cap.get("y_position", 380)

    default_color = cap.get("default_color", [255, 255, 255])
    pain_color = cap.get("pain_color", [255, 90, 0])
    money_color = cap.get("money_color", [0, 255, 133])

    pain_words = set(w.upper() for w in cap.get("pain_words", []))
    money_words = set(w.upper() for w in cap.get("money_words", []))

    transcript_path = proj / cfg.get("transcript", "transcript.json")
    out_dir = proj / "build" / "overlays" / "captions"

    # Suppression windows derived from MG cue points (output time = original / speed)
    suppress_windows = []
    for mg in cfg.get("motion_graphics", []):
        st = mg["start_t"] / speed
        en = (mg["start_t"] + mg["duration"]) / speed
        suppress_windows.append((st, en))

    # Total output duration: scaled raw + tail
    raw_dur = cfg.get("raw_duration_s")
    if raw_dur is None:
        # Fall back to transcript end
        words = json.loads(transcript_path.read_text())
        raw_dur = words[-1]["end"]
    total_dur = raw_dur / speed + tail
    n_frames = int(total_dur * fps)

    print(f"[captions] speed={speed}× | output_dur={total_dur:.2f}s | frames={n_frames}")
    print(f"[captions] suppress windows: {[(round(s,2),round(e,2)) for s,e in suppress_windows]}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    words = json.loads(transcript_path.read_text())
    # Rescale word timestamps to output time
    for w in words:
        w["start"] = w["start"] / speed
        w["end"] = w["end"] / speed

    chunks = build_chunks(words)
    font_obj = ImageFont.truetype(font_path, font_size, index=font_index)

    chunk_images = [
        render_chunk_image(c, font_obj, W, H, y_position, outline_px,
                            pain_words, money_words,
                            default_color, pain_color, money_color)
        for c in chunks
    ]

    blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    def is_suppressed(t: float) -> bool:
        return any(s <= t < e for s, e in suppress_windows)

    for fi in range(n_frames):
        t = fi / fps
        if is_suppressed(t):
            blank.save(out_dir / f"{fi:04d}.png")
            continue
        active = None
        for ci, c in enumerate(chunks):
            if c["start"] <= t < c["end"]:
                active = ci
                break
        (chunk_images[active] if active is not None else blank).save(
            out_dir / f"{fi:04d}.png"
        )
        if fi % 300 == 0:
            print(f"  {fi}/{n_frames}", flush=True)

    print(f"✓ captions: {n_frames} frames → {out_dir} ({len(chunks)} unique chunks)")


if __name__ == "__main__":
    main()
