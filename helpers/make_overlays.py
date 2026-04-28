#!/usr/bin/env python3
"""
Generate motion graphic overlays as PNG sequences from a config.json.

Three built-in overlay types:
  - list_chip      → corner credibility chip (carrier logos, stack badges, etc.)
  - money_stamp    → center money/result stamp (e.g. "$12,000 CASH UPFRONT")
  - cta_endcard    → bottom slide-up CTA card with risk reversal + arrow

Each type accepts simple config — see config.example.json. Output is RGBA PNG seq
ready for ffmpeg to overlay on the base video.

Usage:
  python make_overlays.py [--config config.json] [--project-dir /path/to/project]
"""
import argparse
import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ────────────────── easing functions ──────────────────

def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_back_out(t: float, overshoot: float = 1.4) -> float:
    c1 = overshoot
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


# ────────────────── shared utilities ──────────────────

def font_at(path: str, size: int, index: int = 0):
    return ImageFont.truetype(path, size, index=index)


def text_size(draw, text, font_obj):
    bbox = draw.textbbox((0, 0), text, font=font_obj)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_text_outlined(draw, xy, text, font_obj, fill, outline=(0, 0, 0, 255),
                        ow=4, anchor="lt"):
    x, y = xy
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx == 0 and dy == 0:
                continue
            if dx * dx + dy * dy > ow * ow:
                continue
            draw.text((x + dx, y + dy), text, font=font_obj, fill=outline, anchor=anchor)
    draw.text((x, y), text, font=font_obj, fill=fill, anchor=anchor)


def reset_dir(p: Path):
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)


# ────────────────── overlay builders ──────────────────

def make_list_chip(mg, out_dir, W, H, fps, font_path, font_index, accent, fill):
    duration = mg["duration"]
    n = int(duration * fps)
    header = mg.get("header", "")
    items = mg.get("items", [])
    position = mg.get("position", "top-right")

    f_label = font_at(font_path, 56, font_index)
    f_header = font_at(font_path, 38, font_index)

    pill_w, pill_h, gap, header_h = 460, 88, 16, 60
    panel_w = pill_w + 60
    panel_h = header_h + len(items) * pill_h + (len(items) - 1) * gap + 60

    if position == "top-right":
        final_x, final_y = W - panel_w - 40, 80
    elif position == "top-left":
        final_x, final_y = 40, 80
    elif position == "bottom-right":
        final_x, final_y = W - panel_w - 40, H - panel_h - 80
    else:
        final_x, final_y = (W - panel_w) // 2, 80

    off_x = W

    for i in range(n):
        t = i / fps
        if t < 0.6:
            p = ease_out_cubic(t / 0.6)
            x = int(off_x + (final_x - off_x) * p)
            alpha = int(255 * p)
        elif t < duration - 0.8:
            x = final_x
            alpha = 255
        else:
            p = (t - (duration - 0.8)) / 0.8
            x = final_x
            alpha = int(255 * (1 - p))

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if alpha <= 0:
            img.save(out_dir / f"{i:04d}.png")
            continue

        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle(
            [(x, final_y), (x + panel_w, final_y + panel_h)],
            radius=24, fill=(10, 10, 10, int(alpha * 0.85)),
            outline=tuple(accent) + (alpha,), width=3,
        )
        hw, _ = text_size(d, header, f_header)
        d.text(
            (x + panel_w // 2 - hw // 2, final_y + 24),
            header, font=f_header, fill=tuple(accent) + (alpha,),
        )
        py = final_y + header_h + 30
        for name in items:
            px = x + (panel_w - pill_w) // 2
            d.rounded_rectangle(
                [(px, py), (px + pill_w, py + pill_h)],
                radius=16, fill=(255, 255, 255, int(alpha * 0.95)),
            )
            tw, th = text_size(d, name, f_label)
            d.text(
                (px + pill_w // 2 - tw // 2, py + pill_h // 2 - th // 2 - 6),
                name, font=f_label, fill=(10, 10, 10, alpha),
            )
            py += pill_h + gap
        img = Image.alpha_composite(img, layer)
        img.save(out_dir / f"{i:04d}.png")


def make_money_stamp(mg, out_dir, W, H, fps, font_path, font_index, money_color):
    duration = mg["duration"]
    n = int(duration * fps)
    header = mg.get("header", "")
    amount = mg.get("amount", "")
    subtitle = mg.get("subtitle", "")

    f_amount = font_at(font_path, 220, font_index)
    f_sub = font_at(font_path, 70, font_index)
    f_micro = font_at(font_path, 38, font_index)

    stamp_w, stamp_h = 980, 540
    stamp = Image.new("RGBA", (stamp_w, stamp_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(stamp)
    d.rounded_rectangle(
        [(0, 0), (stamp_w, stamp_h)],
        radius=32, fill=(8, 8, 8, 240),
        outline=tuple(money_color) + (255,), width=6,
    )
    if header:
        mw, _ = text_size(d, header, f_micro)
        d.text(
            (stamp_w // 2 - mw // 2, 36),
            header, font=f_micro, fill=(160, 160, 160, 255),
        )
    draw_text_outlined(
        d, (stamp_w // 2, 110), amount, f_amount,
        fill=tuple(money_color) + (255,), outline=(0, 0, 0, 255),
        ow=2, anchor="mt",
    )
    if subtitle:
        sw, _ = text_size(d, subtitle, f_sub)
        d.text(
            (stamp_w // 2 - sw // 2, 380),
            subtitle, font=f_sub, fill=(255, 255, 255, 255),
        )

    final_cx, final_cy = W // 2, H // 2 + 60

    for i in range(n):
        t = i / fps
        if t < 0.4:
            p = t / 0.4
            scale = max(0.01, ease_back_out(p, overshoot=1.4))
            alpha = int(255 * min(1.0, p * 2.0))
        elif t < duration - 0.5:
            scale, alpha = 1.0, 255
        else:
            p = (t - (duration - 0.5)) / 0.5
            scale = 1.0 + 0.05 * p
            alpha = int(255 * (1 - p))

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if alpha <= 0:
            img.save(out_dir / f"{i:04d}.png")
            continue

        sw_s = int(stamp_w * scale)
        sh_s = int(stamp_h * scale)
        scaled = stamp.resize((sw_s, sh_s), Image.LANCZOS)
        if alpha < 255:
            a = scaled.split()[3].point(lambda p: int(p * alpha / 255))
            scaled.putalpha(a)
        x = final_cx - sw_s // 2
        y = final_cy - sh_s // 2
        img.alpha_composite(scaled, (x, y))
        img.save(out_dir / f"{i:04d}.png")


def make_cta_endcard(mg, out_dir, W, H, fps, font_path, font_index,
                      money_color, accent):
    duration = mg["duration"]
    n = int(duration * fps)
    main = mg.get("main", "BOOK THE CALL")
    sub = mg.get("sub", "")
    micro = mg.get("micro", "")
    show_arrow = mg.get("show_arrow", True)

    f_main = font_at(font_path, 110, font_index)
    f_sub = font_at(font_path, 64, font_index)
    f_micro = font_at(font_path, 42, font_index)

    card_h = 800
    final_y = H - card_h
    start_y = H

    for i in range(n):
        t = i / fps
        if t < 0.6:
            p = ease_out_cubic(t / 0.6)
            y = int(start_y + (final_y - start_y) * p)
            alpha = int(255 * min(1.0, p * 1.5))
        else:
            y = final_y
            alpha = 255

        # Pulsing arrow loop
        pulse = 1.0
        if t > 0.6:
            ct = (t - 0.6) % 1.0
            pulse = 1.0 + 0.15 * (ct / 0.5) if ct < 0.5 else 1.15 - 0.15 * ((ct - 0.5) / 0.5)

        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rectangle(
            [(0, y), (W, H)],
            fill=(8, 8, 8, int(225 * alpha / 255)),
        )
        d.rectangle(
            [(0, y), (W, y + 8)],
            fill=tuple(money_color) + (alpha,),
        )
        draw_text_outlined(
            d, (W // 2, y + 90), main, f_main,
            fill=tuple(money_color) + (alpha,), outline=(0, 0, 0, 255),
            ow=3, anchor="mt",
        )
        if sub:
            sw, _ = text_size(d, sub, f_sub)
            d.text(
                (W // 2 - sw // 2, y + 270),
                sub, font=f_sub, fill=(255, 255, 255, alpha),
            )
            d.rectangle(
                [(W // 2 - 200, y + 380), (W // 2 + 200, y + 384)],
                fill=tuple(accent) + (alpha,),
            )
        if micro:
            d.text(
                (W // 2, y + 460),
                micro, font=f_micro, fill=(200, 200, 200, alpha), anchor="mt",
            )
        if show_arrow:
            ax, ay = W // 2, y + 560
            aw = int(120 * pulse)
            ah = int(70 * pulse)
            stroke = max(8, int(14 * pulse))
            green_a = tuple(money_color) + (alpha,)
            d.line([(ax - aw // 2, ay), (ax, ay + ah)], fill=green_a, width=stroke)
            d.line([(ax + aw // 2, ay), (ax, ay + ah)], fill=green_a, width=stroke)
            r = stroke // 2
            for cx, cy in [(ax - aw // 2, ay), (ax + aw // 2, ay), (ax, ay + ah)]:
                d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=green_a)
        img = Image.alpha_composite(img, layer)
        img.save(out_dir / f"{i:04d}.png")


# ────────────────── dispatcher ──────────────────

OVERLAY_TYPES = {
    "list_chip": make_list_chip,
    "money_stamp": make_money_stamp,
    "cta_endcard": make_cta_endcard,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--project-dir", default=".")
    args = parser.parse_args()

    proj = Path(args.project_dir).resolve()
    cfg = json.loads((proj / args.config).read_text())

    fps = cfg.get("fps", 30)
    W = cfg.get("width", 1080)
    H = cfg.get("height", 1920)

    cap = cfg.get("captions", {})
    font_path = cap.get("font_path", "/System/Library/Fonts/HelveticaNeue.ttc")
    font_index = cap.get("font_index", 1)
    accent = cap.get("pain_color", [255, 90, 0])
    money_color = cap.get("money_color", [0, 255, 133])

    overlays_root = proj / "build" / "overlays"
    overlays_root.mkdir(parents=True, exist_ok=True)

    for mg in cfg.get("motion_graphics", []):
        mg_id = mg["id"]
        mg_type = mg["type"]
        out_dir = overlays_root / mg_id
        reset_dir(out_dir)

        builder = OVERLAY_TYPES.get(mg_type)
        if builder is None:
            print(f"⚠ unknown overlay type: {mg_type} — skipping {mg_id}")
            continue

        if mg_type == "list_chip":
            builder(mg, out_dir, W, H, fps, font_path, font_index, accent, money_color)
        elif mg_type == "money_stamp":
            builder(mg, out_dir, W, H, fps, font_path, font_index, money_color)
        elif mg_type == "cta_endcard":
            builder(mg, out_dir, W, H, fps, font_path, font_index, money_color, accent)

        n = int(mg["duration"] * fps)
        print(f"✓ {mg_id} ({mg_type}): {n} frames → {out_dir}")


if __name__ == "__main__":
    main()
