from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_GIF = ROOT / "portfolio-rebalancing-neon-dataviz.gif"
OUT_POSTER = ROOT / "portfolio-rebalancing-neon-dataviz-poster.png"
OUT_STORYBOARD = ROOT / "portfolio-rebalancing-neon-dataviz-storyboard.png"

W = H = 1200
OUTPUT_SIZE = (1080, 1080)
FPS = 8
DURATION = 14.0

BG = "#030506"
WHITE = "#EDF1F2"
MUTED = "#96A1A6"
GRID = "#26343B"
CYAN = "#54D9FF"
ORANGE = "#FFB348"
GREEN = "#00E887"
PURPLE = "#C459E8"
RED = "#FF6173"
YELLOW = "#F7DB6A"

FONT_HAND_CN = Path(r"C:\Windows\Fonts\FZSTK.TTF")
FONT_BODY_CN = Path(r"C:\Windows\Fonts\simkai.ttf")
FONT_HAND_EN = Path(r"C:\Windows\Fonts\Inkfree.ttf")
FONT_NUM = Path(r"C:\Windows\Fonts\comicbd.ttf")


def fnt(size: int, kind: str = "body") -> ImageFont.FreeTypeFont:
    path = {
        "hand": FONT_HAND_CN,
        "body": FONT_BODY_CN,
        "english": FONT_HAND_EN,
        "number": FONT_NUM,
    }[kind]
    return ImageFont.truetype(str(path), size)


def rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def ease(value: float) -> float:
    value = clamp(value)
    return value * value * (3 - 2 * value)


def progress(t: float, start: float, end: float) -> float:
    return ease((t - start) / (end - start))


def center_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    value: str,
    font: ImageFont.FreeTypeFont,
    fill: str | tuple[int, int, int, int],
) -> None:
    draw.text(xy, value, font=font, fill=fill, anchor="mm")


def text(
    base: Image.Image,
    xy: tuple[int, int],
    value: str,
    size: int,
    color: str = WHITE,
    kind: str = "body",
    anchor: str = "la",
) -> None:
    ImageDraw.Draw(base).text(xy, value, font=fnt(size, kind), fill=color, anchor=anchor)


def neon_line(
    base: Image.Image,
    points: Sequence[tuple[float, float]],
    color: str,
    width: int = 4,
    glow: int = 10,
    alpha: int = 235,
) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.line(points, fill=rgba(color, alpha), width=width, joint="curve")
    blur = layer.filter(ImageFilter.GaussianBlur(glow))
    base.alpha_composite(blur)
    base.alpha_composite(blur)
    base.alpha_composite(layer)


def neon_round_rect(
    base: Image.Image,
    box: tuple[int, int, int, int],
    color: str,
    fill: str,
    radius: int = 24,
    width: int = 3,
) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(box, radius=radius, fill=rgba(fill, 215), outline=rgba(color, 220), width=width)
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(10)))
    base.alpha_composite(layer)


def partial_polyline(points: Sequence[tuple[float, float]], p: float) -> list[tuple[float, float]]:
    p = clamp(p)
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points[:-1], points[1:])]
    total = sum(lengths)
    target = total * p
    walked = 0.0
    result = [points[0]]
    for (a, b), length in zip(zip(points[:-1], points[1:]), lengths):
        if walked + length <= target:
            result.append(b)
            walked += length
            continue
        local = 0.0 if length == 0 else (target - walked) / length
        result.append((a[0] + (b[0] - a[0]) * local, a[1] + (b[1] - a[1]) * local))
        break
    return result


def point_on_polyline(points: Sequence[tuple[float, float]], p: float) -> tuple[float, float]:
    return partial_polyline(points, p)[-1]


def moving_dot(base: Image.Image, points: Sequence[tuple[float, float]], p: float, color: str) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for index in range(7, -1, -1):
        local = max(0.0, p - index * 0.028)
        x, y = point_on_polyline(points, local)
        radius = max(3, 8 - index // 2)
        alpha = 35 + (7 - index) * 27
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=rgba(color, alpha))
    glow = layer.filter(ImageFilter.GaussianBlur(14))
    base.alpha_composite(glow)
    base.alpha_composite(glow)
    base.alpha_composite(layer)


def series_y(value: float, endpoint_offset: int = 0) -> float:
    return 500 - (value - 50) * 1.8 + endpoint_offset


def draw_static() -> Image.Image:
    base = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(base)

    # Header and title borrow the visual language only: blackboard, handwriting and neon.
    draw.rectangle((40, 31, 49, 99), fill=PURPLE)
    text(base, (66, 29), "再平衡的反直觉结果", 48, WHITE, "hand", "la")
    text(base, (66, 93), "两个资产都回到原点，组合为什么变成 156.25？", 23, MUTED, "body", "la")
    neon_round_rect(base, (793, 28, 1148, 105), GREEN, "#14372F", radius=20, width=2)
    center_text(draw, (970, 65), "Rebalancing", fnt(46, "english"), GREEN)
    draw.line((40, 129, 1160, 129), fill=rgba("#596167", 160), width=2)

    # Upper data visualization: two return paths, not a flowchart.
    text(base, (72, 157), "单独持有：两条路径最终都回到 100", 32, WHITE, "hand", "la")
    text(base, (1125, 165), "各自收益 0%", 24, GREEN, "body", "ra")

    chart_left, chart_right = 135, 915
    for value in (50, 100, 200):
        y = series_y(value)
        draw.line((chart_left, y, chart_right, y), fill=rgba(GRID, 170), width=2)
        text(base, (113, int(y)), str(value), 20, MUTED, "number", "rm")
    draw.line((chart_left, 225, chart_left, 510), fill=rgba("#79858A", 160), width=2)
    draw.line((chart_left, 510, chart_right, 510), fill=rgba("#79858A", 160), width=2)

    x_points = [180, 525, 870]
    for x, label in zip(x_points, ["开始", "第一年", "第二年"]):
        draw.line((x, 510, x, 521), fill=rgba("#79858A", 180), width=2)
        center_text(draw, (x, 545), label, fnt(21, "body"), MUTED)

    # Dim guide paths show the structure before animated lines are drawn.
    a_path = [(180, series_y(100, -6)), (525, series_y(200)), (870, series_y(100, -6))]
    b_path = [(180, series_y(100, 6)), (525, series_y(50)), (870, series_y(100, 6))]
    draw.line(a_path, fill=rgba(CYAN, 60), width=3, joint="curve")
    draw.line(b_path, fill=rgba(ORANGE, 60), width=3, joint="curve")

    draw.line((870, series_y(100, -6), 937, 375), fill=rgba(CYAN, 160), width=2)
    draw.ellipse((946, 363, 966, 383), fill=CYAN)
    text(base, (980, 361), "A  100 · 0%", 23, CYAN, "number", "la")
    draw.line((870, series_y(100, 6), 937, 441), fill=rgba(ORANGE, 160), width=2)
    draw.ellipse((946, 429, 966, 449), fill=ORANGE)
    text(base, (980, 427), "B  100 · 0%", 23, ORANGE, "number", "la")

    # Lower data visualization: stacked columns across time.
    draw.line((40, 565, 1160, 565), fill=rgba("#596167", 130), width=2)
    text(base, (72, 594), "50/50 组合：同样的涨跌，结果不同", 34, WHITE, "hand", "la")
    text(base, (1127, 604), "+56.25%", 40, GREEN, "number", "ra")
    text(base, (1127, 646), "两年累计变化", 20, MUTED, "body", "ra")

    base_y = 1040
    draw.line((92, base_y, 1112, base_y), fill=rgba("#79858A", 170), width=2)
    for value in (50, 100, 150):
        y = base_y - value * 2.15
        draw.line((92, y, 1068, y), fill=rgba(GRID, 130), width=2)
        text(base, (79, int(y)), str(value), 18, MUTED, "number", "rm")

    centers = [180, 430, 680, 930]
    labels = ["初始", "第一年", "再平衡后", "第二年"]
    subtitles = ["50 / 50", "80 / 20", "50 / 50", "20 / 80"]
    for x, label, subtitle in zip(centers, labels, subtitles):
        center_text(draw, (x, 1081), label, fnt(22, "body"), WHITE)
        center_text(draw, (x, 1113), subtitle, fnt(20, "number"), MUTED)

    # A curved transfer annotation, styled like a hand-drawn note rather than a process arrow.
    arc = [(493, 885), (550, 837), (618, 885)]
    draw.line(arc, fill=rgba(YELLOW, 100), width=2, joint="curve")
    center_text(draw, (555, 818), "转移 37.5", fnt(20, "body"), YELLOW)
    text(base, (505, 912), "总额仍是 125", 18, MUTED, "body", "la")

    text(base, (72, 1161), "理想化交替涨跌 · 未计交易成本和税费 · 不是“再平衡必赚”的证明", 20, RED, "body", "la")
    text(base, (1128, 1161), "恢复目标配置，不是预测赢家", 20, GREEN, "body", "ra")
    return base


def draw_path(base: Image.Image, points: Sequence[tuple[float, float]], p: float, color: str) -> None:
    partial = partial_polyline(points, p)
    if len(partial) > 1:
        neon_line(base, partial, color, width=5, glow=10)
        moving_dot(base, points, p, color)


def draw_stack(
    base: Image.Image,
    center_x: int,
    a_value: float,
    b_value: float,
    p: float,
    total_label: str,
    pulse: float = 0.0,
) -> None:
    p = clamp(p)
    width = 132
    base_y = 1040
    scale = 2.15
    b_h = b_value * scale * p
    a_h = a_value * scale * p
    x0, x1 = center_x - width // 2, center_x + width // 2

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle((x0, base_y - b_h, x1, base_y), radius=13, fill=rgba(ORANGE, 230))
    draw.rounded_rectangle((x0, base_y - b_h - a_h, x1, base_y - b_h + 13), radius=13, fill=rgba(CYAN, 230))
    if b_h > 13:
        draw.rectangle((x0, base_y - b_h, x1, base_y - 13), fill=rgba(ORANGE, 230))
    if a_h > 13:
        draw.rectangle((x0, base_y - b_h - a_h + 13, x1, base_y - b_h), fill=rgba(CYAN, 230))
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(8 + int(7 * pulse))))
    base.alpha_composite(layer)

    if p > 0.72:
        draw = ImageDraw.Draw(base)
        top = base_y - a_h - b_h
        center_text(draw, (center_x, top - 29), total_label, fnt(26, "number"), GREEN if center_x == 930 else WHITE)
        if a_h > 45:
            center_text(draw, (center_x, top + a_h / 2), f"A {a_value:g}", fnt(18, "number"), BG)
        if b_h > 45:
            center_text(draw, (center_x, base_y - b_h / 2), f"B {b_value:g}", fnt(18, "number"), BG)


def draw_transfer_particles(base: Image.Image, p: float) -> None:
    curve = [(495, 883), (550, 836), (618, 883)]
    moving_dot(base, curve, p, YELLOW)


def render_frame(static: Image.Image, t: float) -> Image.Image:
    frame = static.copy()

    a_path = [(180, series_y(100, -6)), (525, series_y(200)), (870, series_y(100, -6))]
    b_path = [(180, series_y(100, 6)), (525, series_y(50)), (870, series_y(100, 6))]
    draw_path(frame, a_path, progress(t, 0.0, 2.4), CYAN)
    draw_path(frame, b_path, progress(t, 0.6, 3.0), ORANGE)

    p0 = progress(t, 2.6, 4.0)
    p1 = progress(t, 3.8, 5.4)
    p2 = progress(t, 5.2, 7.3)
    p3 = progress(t, 7.1, 9.2)

    draw_stack(frame, 180, 50, 50, p0, "100")
    draw_stack(frame, 430, 100, 25, p1, "125")
    draw_stack(frame, 680, 62.5, 62.5, p2, "125", pulse=math.sin(math.pi * p2))
    draw_stack(frame, 930, 31.25, 125, p3, "156.25", pulse=max(0.0, math.sin(math.pi * progress(t, 8.0, 11.0))))

    if 5.1 <= t <= 7.5:
        draw_transfer_particles(frame, progress(t, 5.1, 7.2))

    # A restrained pulse on the final result, without changing the chart structure.
    if 8.7 <= t <= 12.5:
        pulse = (math.sin((t - 8.7) * math.pi * 1.1) + 1) / 2
        layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        draw.ellipse((1058 - 7, 622 - 7, 1058 + 7, 622 + 7), fill=rgba(GREEN, int(120 + pulse * 120)))
        frame.alpha_composite(layer.filter(ImageFilter.GaussianBlur(15)))
        frame.alpha_composite(layer)

    return frame.convert("RGB")


def build_storyboard(static: Image.Image) -> Image.Image:
    board = Image.new("RGB", (1200, 1200), "#010203")
    for index, sample_time in enumerate([1.7, 3.8, 5.1, 6.7, 8.5, 10.5]):
        sample = render_frame(static, sample_time).resize((600, 400), Image.Resampling.LANCZOS)
        board.paste(sample, ((index % 2) * 600, (index // 2) * 400))
    return board


def main() -> None:
    static = draw_static()
    frames = []
    for index in range(int(FPS * DURATION)):
        rgb = render_frame(static, index / FPS).resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)
        frames.append(rgb.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))

    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=0,
        disposal=2,
        optimize=True,
    )
    render_frame(static, 10.5).save(OUT_POSTER, optimize=True)
    build_storyboard(static).save(OUT_STORYBOARD, optimize=True)
    print(OUT_GIF)
    print(OUT_POSTER)
    print(OUT_STORYBOARD)


if __name__ == "__main__":
    main()
