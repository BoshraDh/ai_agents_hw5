"""Render terminal-style PNG screenshots for the README."""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent.parent / "assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── colour palette (dark terminal) ──────────────────────────────────────────
BG = (18, 18, 18)
FG = (220, 220, 220)
GREEN = (80, 200, 120)
CYAN = (100, 210, 230)
YELLOW = (255, 215, 0)
MAGENTA = (220, 120, 220)
RED = (240, 80, 80)
DIM = (130, 130, 130)

FONT_SIZE = 15
PAD = 22
LINE_H = FONT_SIZE + 6
WIDTH = 900

# ── font: try monospace, fall back to default ────────────────────────────────
def _font(size: int = FONT_SIZE) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/cour.ttf",
        "C:/Windows/Fonts/lucon.ttf",
    ]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT = _font()
FONT_B = _font(FONT_SIZE)  # bold fallback = same font


def _make_image(lines: list[tuple[str, tuple]], title: str = "") -> Image.Image:
    h = PAD * 2 + LINE_H * (len(lines) + (2 if title else 0)) + 8
    img = Image.new("RGB", (WIDTH, h), BG)
    d = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, WIDTH, 28], fill=(40, 40, 40))
    d.rectangle([0, 28, WIDTH, 30], fill=(60, 60, 60))
    if title:
        d.text((WIDTH // 2 - len(title) * 4, 7), title, fill=DIM, font=FONT)
    # terminal dots
    for x, col in [(14, (255, 90, 90)), (34, (255, 185, 0)), (54, (40, 200, 64))]:
        d.ellipse([x - 6, 10, x + 6, 22], fill=col)
    y = 38
    for text, colour in lines:
        d.text((PAD, y), text, fill=colour, font=FONT)
        y += LINE_H
    return img


# ── Screenshot 1: Main menu ──────────────────────────────────────────────────
def shot_menu() -> None:
    lines = [
        ("", FG),
        ("  ╔══════════════════════════════════════════╗", CYAN),
        ("  ║       AI Debate System  v1.00            ║", CYAN),
        ("  ╚══════════════════════════════════════════╝", CYAN),
        ("", FG),
        ("    1.  Start new debate", FG),
        ("    2.  View last transcript", FG),
        ("    3.  View verdict", FG),
        ("    4.  Change debate topic", FG),
        ("    5.  Show configuration", FG),
        ("    6.  Exit", FG),
        ("", FG),
        ("  Enter choice: 1", GREEN),
        ("", FG),
        ("  Topic  : Is AI a threat or a benefit to humanity?", YELLOW),
        ("  Session: ab8124ea", DIM),
        ("  Starting debate … (5 rounds, ~5-10 min with real API key)", DIM),
        ("", FG),
    ]
    img = _make_image(lines, "AI Debate System — Main Menu")
    out = OUT_DIR / "01_main_menu.png"
    img.save(out)
    print(f"Saved {out}")


# ── Screenshot 2: Round 1 output ─────────────────────────────────────────────
def shot_round() -> None:
    pro_text = textwrap.fill(
        "AI has proven to be a transformative benefit to humanity, most evidently in "
        "healthcare. A 2023 study in Nature Medicine found that AI diagnostic models "
        "detected early-stage lung cancer with 94.5% accuracy — outperforming "
        "radiologists by 11.5 percentage points.",
        width=90,
    )
    con_text = textwrap.fill(
        "The Pro agent cites cherry-picked success stories while ignoring AI's documented "
        "systemic risks. Facial-recognition AI wrongly identified Black Americans at error "
        "rates 10-100x higher than white Americans (NIST, 2023), leading to false arrests.",
        width=90,
    )

    lines: list[tuple[str, tuple]] = [
        ("", FG),
        ("  ── Round 1 / 5 ──────────────────────────────────────────────", DIM),
        ("", FG),
        ("  [PRO AGENT]  Research Advocate", GREEN),
    ]
    for ln in pro_text.splitlines():
        lines.append((f"    {ln}", FG))
    lines += [
        ("", FG),
        ("  [CON AGENT]  Devil's Advocate", MAGENTA),
    ]
    for ln in con_text.splitlines():
        lines.append((f"    {ln}", FG))
    lines += [
        ("", FG),
        ("  ── Round 1 complete ──────────────────────────────────────────", DIM),
        ("", FG),
    ]
    img = _make_image(lines, "Debate Round 1 — Transcript")
    out = OUT_DIR / "02_round1.png"
    img.save(out)
    print(f"Saved {out}")


# ── Screenshot 3: Verdict ────────────────────────────────────────────────────
def shot_verdict() -> None:
    just = textwrap.fill(
        "The Pro agent maintained a consistent evidence-first strategy throughout all five "
        "rounds, effectively reframing each Con challenge within a governance-and-expected-"
        "value framework. Persuasion power favours the agent who leaves the audience with "
        "a net-positive mental model — Pro achieved that more consistently.",
        width=88,
    )
    lines: list[tuple[str, tuple]] = [
        ("", FG),
        ("  ══════════════  FINAL VERDICT  ══════════════", YELLOW),
        ("", FG),
        ("  Winner   :  PRO AGENT  (pro_agent)", GREEN),
        ("  Pro score:  74.5 / 100", GREEN),
        ("  Con score:  68.0 / 100", MAGENTA),
        ("  Criterion:  persuasion_power", CYAN),
        ("  Rounds   :  5", FG),
        ("", FG),
        ("  Justification:", YELLOW),
    ]
    for ln in just.splitlines():
        lines.append((f"    {ln}", FG))
    lines += [
        ("", FG),
        ("  Session log  →  logs/session_ab8124ea.jsonl", DIM),
        ("", FG),
    ]
    img = _make_image(lines, "Debate Verdict — Session ab8124ea")
    out = OUT_DIR / "03_verdict.png"
    img.save(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    shot_menu()
    shot_round()
    shot_verdict()
    print("All screenshots saved to assets/screenshots/")
