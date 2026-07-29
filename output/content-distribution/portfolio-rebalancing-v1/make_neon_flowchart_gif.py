from __future__ import annotations

import math
from pathlib import Path
from typing import Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
OUT_GIF = ROOT / "portfolio-rebalancing-neon-flowchart.gif"
OUT_POSTER = ROOT / "portfolio-rebalancing-neon-flowchart-poster.png"
OUT_STORYBOARD = ROOT / "portfolio-rebalancing-neon-flowchart-storyboard.png"

W, H = 1400, 1200
OUTPUT_SIZE = (1080, 926)
FPS = 8
DURATION = 14.0

BG = "#030506"
WHITE = "#E9EEF1"
MUTED = "#9DA8AD"
BLUE = "#2CA7F4"
GREEN = "#00E887"
MINT = "#79E4D2"
PURPLE = "#C356E6"
ORANGE = "#FFB44A"
RED = "#FF5E70"
CYAN = "#5CD9FF"

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
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str | tuple[int, int, int, int],
) -> None:
    draw.text(xy, text, font=font, fill=fill, anchor="mm")


def glow_composite(base: Image.Image, layer: Image.Image, radius: int = 12, strength: int = 2) -> Image.Image:
    blurred = layer.filter(ImageFilter.GaussianBlur(radius))
    result = base
    for _ in range(strength):
        result = Image.alpha_composite(result, blurred)
    return Image.alpha_composite(result, layer)


def neon_round_rect(
    base: Image.Image,
    box: tuple[int, int, int, int],
    color: str,
    fill: str | tuple[int, int, int, int] = (4, 12, 18, 220),
    radius: int = 24,
    width: int = 3,
    glow: int = 10,
) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=rgba(color, 220), width=width)
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(glow)))
    base.alpha_composite(layer)


def neon_line(
    base: Image.Image,
    points: Sequence[tuple[float, float]],
    color: str = WHITE,
    width: int = 3,
    glow: int = 7,
    alpha: int = 210,
) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.line(points, fill=rgba(color, alpha), width=width, joint="curve")
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(glow)))
    base.alpha_composite(layer)


def arrow_head(base: Image.Image, p1: tuple[float, float], p2: tuple[float, float], color: str = WHITE) -> None:
    angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    length = 18
    spread = 0.7
    a = (
        p2[0] - length * math.cos(angle - spread),
        p2[1] - length * math.sin(angle - spread),
    )
    b = (
        p2[0] - length * math.cos(angle + spread),
        p2[1] - length * math.sin(angle + spread),
    )
    neon_line(base, [a, p2, b], color=color, width=3, glow=5)


def route(base: Image.Image, points: Sequence[tuple[float, float]], color: str = WHITE, dashed: bool = False) -> None:
    if not dashed:
        neon_line(base, points, color=color, width=3, glow=5, alpha=180)
        arrow_head(base, points[-2], points[-1], color)
        return

    for start, end in zip(points[:-1], points[1:]):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        ux, uy = dx / length, dy / length
        cursor = 0.0
        while cursor < length:
            seg_end = min(length, cursor + 14)
            neon_line(
                base,
                [(start[0] + ux * cursor, start[1] + uy * cursor), (start[0] + ux * seg_end, start[1] + uy * seg_end)],
                color=color,
                width=3,
                glow=4,
                alpha=155,
            )
            cursor += 26
    arrow_head(base, points[-2], points[-1], color)


def text(base: Image.Image, xy: tuple[int, int], value: str, size: int, color: str = WHITE, kind: str = "body", anchor: str = "la") -> None:
    ImageDraw.Draw(base).text(xy, value, font=fnt(size, kind), fill=color, anchor=anchor)


def node(
    base: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    main: str,
    detail: str,
    color: str,
) -> None:
    neon_round_rect(base, box, color, fill=rgba("#07131D", 235), radius=20, width=3, glow=7)
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(base)
    draw.ellipse((x0 + 22, y0 + 22, x0 + 42, y0 + 42), fill=color)
    center_text(draw, ((x0 + x1) / 2 + 8, y0 + 42), title, fnt(27, "hand"), WHITE)
    center_text(draw, ((x0 + x1) / 2, y0 + 101), main, fnt(31, "number"), color)
    center_text(draw, ((x0 + x1) / 2, y0 + 149), detail, fnt(21, "body"), MUTED)


def draw_static() -> Image.Image:
    base = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(base)

    # Header: deliberately asymmetric, handwritten and spacious like the reference.
    draw.rectangle((42, 28, 50, 91), fill=PURPLE)
    text(base, (66, 30), "组合再平衡", 48, WHITE, "hand", "la")
    text(base, (66, 90), "价格改变权重，再平衡恢复目标", 22, MUTED, "body", "la")
    neon_round_rect(base, (500, 24, 900, 105), GREEN, fill=rgba("#173A32", 220), radius=20, width=2, glow=7)
    center_text(draw, (700, 62), "Rebalancing Loop", fnt(47, "english"), GREEN)
    text(base, (1318, 55), "MIT 18.S096", 23, WHITE, "english", "ra")
    text(base, (1318, 87), "52:22—55:48", 19, MUTED, "number", "ra")

    neon_round_rect(base, (38, 127, 1362, 1162), "#62666B", fill=rgba("#000000", 40), radius=34, width=2, glow=4)

    # Trigger / premise box.
    neon_round_rect(base, (330, 158, 1070, 335), GREEN, fill=rgba("#061610", 215), radius=20, width=3, glow=9)
    center_text(draw, (700, 190), "两个资产，单独持有都回到原点", fnt(31, "hand"), WHITE)
    text(base, (410, 240), "A", 30, CYAN, "number", "mm")
    text(base, (465, 240), "100  >  200  >  100", 29, WHITE, "number", "lm")
    text(base, (915, 240), "0%", 29, GREEN, "number", "mm")
    text(base, (410, 291), "B", 30, ORANGE, "number", "mm")
    text(base, (465, 291), "100  >  50  >  100", 29, WHITE, "number", "lm")
    text(base, (915, 291), "0%", 29, GREEN, "number", "mm")

    # Central loop panel.
    neon_round_rect(base, (72, 386, 1328, 842), BLUE, fill=rgba("#031321", 230), radius=28, width=3, glow=10)
    center_text(draw, (700, 417), "再平衡循环", fnt(34, "hand"), WHITE)
    text(base, (1074, 419), "所有节点一直可见，信号沿路径移动", 18, MUTED, "body", "mm")

    node(base, (105, 485, 302, 672), "初始", "50 / 50", "总额 100", CYAN)
    node(base, (356, 485, 584, 672), "第一年", "100 / 25", "权重 80/20 · 总额 125", ORANGE)

    # Decision diamond.
    diamond = [(697, 483), (781, 578), (697, 673), (613, 578)]
    neon_line(base, diamond + [diamond[0]], GREEN, width=3, glow=9)
    center_text(draw, (697, 550), "权重", fnt(26, "hand"), WHITE)
    center_text(draw, (697, 589), "80 / 20", fnt(26, "number"), GREEN)
    center_text(draw, (697, 625), "偏离目标", fnt(20, "body"), MUTED)

    node(base, (810, 485, 1036, 672), "再平衡", "62.5 / 62.5", "总额 125（不变）", GREEN)
    node(base, (1090, 485, 1295, 672), "第二年", "31.25 / 125", "总额 156.25", PURPLE)

    # Connectors in central loop.
    route(base, [(302, 578), (356, 578)], WHITE)
    route(base, [(584, 578), (613, 578)], WHITE)
    route(base, [(781, 578), (810, 578)], WHITE)
    route(base, [(1036, 578), (1090, 578)], WHITE)

    # Return loop.
    loop_path = [(1192, 672), (1192, 758), (205, 758), (205, 672)]
    route(base, loop_path, GREEN, dashed=True)
    center_text(draw, (700, 790), "下一次检查：继续把漂移的权重拉回目标", fnt(21, "body"), MUTED)

    # Bottom summary blocks.
    neon_round_rect(base, (78, 890, 425, 1118), GREEN, fill=rgba("#04160E", 225), radius=20, width=3, glow=8)
    text(base, (103, 921), "再平衡规则", 31, GREEN, "hand", "la")
    text(base, (109, 978), "① 权重偏离目标", 23, WHITE, "body", "la")
    text(base, (109, 1021), "② 卖出相对上涨者", 23, WHITE, "body", "la")
    text(base, (109, 1064), "③ 补回低配资产", 23, WHITE, "body", "la")

    neon_round_rect(base, (476, 890, 925, 1118), PURPLE, fill=rgba("#16051A", 225), radius=20, width=3, glow=8)
    center_text(draw, (700, 924), "数字轨迹", fnt(31, "hand"), WHITE)
    center_text(draw, (700, 990), "100  >  125  >  156.25", fnt(35, "number"), WHITE)
    center_text(draw, (700, 1053), "+56.25%", fnt(49, "number"), GREEN)
    center_text(draw, (700, 1091), "教学示例中的两年累计变化", fnt(18, "body"), MUTED)

    neon_round_rect(base, (976, 890, 1322, 1118), RED, fill=rgba("#17070B", 225), radius=20, width=3, glow=8)
    text(base, (1001, 921), "必要边界", 31, RED, "hand", "la")
    text(base, (1007, 978), "① 涨跌被刻意安排成交替", 21, WHITE, "body", "la")
    text(base, (1007, 1021), "② 未计交易成本和税费", 21, WHITE, "body", "la")
    text(base, (1007, 1064), "③ 不是“再平衡必赚”公式", 21, WHITE, "body", "la")

    route(base, [(270, 842), (270, 890)], GREEN)
    route(base, [(700, 842), (700, 890)], PURPLE)
    route(base, [(1149, 842), (1149, 890)], RED)
    route(base, [(700, 335), (700, 386)], GREEN)

    # Small chalk-like decorations.
    for x, y, color in [(87, 349, GREEN), (1262, 350, PURPLE), (460, 355, CYAN), (940, 355, GREEN), (448, 1142, PURPLE), (944, 1142, GREEN)]:
        text(base, (x, y), "+", 35, color, "english", "mm")
    center_text(draw, (700, 1143), "恢复目标配置，而不是预测下一位赢家", fnt(21, "body"), MUTED)
    return base


def point_on_polyline(points: Sequence[tuple[float, float]], p: float) -> tuple[float, float]:
    lengths = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points[:-1], points[1:])]
    total = sum(lengths)
    target = clamp(p) * total
    walked = 0.0
    for (a, b), length in zip(zip(points[:-1], points[1:]), lengths):
        if walked + length >= target:
            local = 0 if length == 0 else (target - walked) / length
            return (a[0] + (b[0] - a[0]) * local, a[1] + (b[1] - a[1]) * local)
        walked += length
    return points[-1]


def moving_signal(base: Image.Image, points: Sequence[tuple[float, float]], p: float, color: str = GREEN, size: int = 7) -> None:
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    for index in range(5, -1, -1):
        trail_p = max(0.0, p - index * 0.035)
        x, y = point_on_polyline(points, trail_p)
        alpha = int(45 + (5 - index) * 28)
        radius = max(3, size - index // 2)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=rgba(color, alpha))
    blurred = glow.filter(ImageFilter.GaussianBlur(13))
    base.alpha_composite(blurred)
    base.alpha_composite(blurred)
    base.alpha_composite(glow)


def active_box(base: Image.Image, box: tuple[int, int, int, int], color: str, pulse: float) -> None:
    if pulse <= 0:
        return
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    alpha = int(90 + 100 * pulse)
    draw.rounded_rectangle(box, radius=22, outline=rgba(color, alpha), width=5)
    base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(10 + int(6 * pulse))))
    base.alpha_composite(layer)


def pulse_at(t: float, start: float, end: float) -> float:
    if t < start or t > end:
        return 0.0
    local = (t - start) / (end - start)
    return math.sin(math.pi * local) ** 0.7


def render_frame(static: Image.Image, t: float) -> Image.Image:
    frame = static.copy()

    top_a = [(512, 239), (760, 239), (905, 239)]
    top_b = [(512, 290), (760, 290), (905, 290)]
    down = [(700, 335), (700, 386), (205, 485)]
    p1 = [(302, 578), (356, 578)]
    p2 = [(584, 578), (613, 578)]
    p3 = [(781, 578), (810, 578)]
    p4 = [(1036, 578), (1090, 578)]
    loop = [(1192, 672), (1192, 758), (205, 758), (205, 672)]

    # Signals traverse the entire map; the diagram itself never disappears.
    if t < 1.6:
        p = progress(t, 0.0, 1.5)
        moving_signal(frame, top_a, p, CYAN)
        moving_signal(frame, top_b, p, ORANGE)
    elif t < 2.4:
        moving_signal(frame, down, progress(t, 1.6, 2.3), GREEN)
    elif t < 3.6:
        moving_signal(frame, p1, progress(t, 2.4, 3.5), GREEN)
    elif t < 4.7:
        moving_signal(frame, p2, progress(t, 3.6, 4.6), GREEN)
    elif t < 5.9:
        moving_signal(frame, p3, progress(t, 4.7, 5.8), GREEN)
    elif t < 7.1:
        moving_signal(frame, p4, progress(t, 5.9, 7.0), PURPLE)
    elif t < 9.3:
        moving_signal(frame, loop, progress(t, 7.1, 9.2), GREEN)
    elif t < 11.0:
        p = progress(t, 9.3, 10.8)
        moving_signal(frame, [(270, 842), (270, 890)], p, GREEN)
        moving_signal(frame, [(700, 842), (700, 890)], p, PURPLE)
        moving_signal(frame, [(1149, 842), (1149, 890)], p, RED)
    else:
        moving_signal(frame, loop, (t - 11.0) / 3.0, GREEN)

    active_box(frame, (330, 158, 1070, 335), GREEN, pulse_at(t, 0.0, 2.0))
    active_box(frame, (105, 485, 302, 672), CYAN, pulse_at(t, 1.6, 3.0))
    active_box(frame, (356, 485, 584, 672), ORANGE, pulse_at(t, 2.7, 4.2))
    active_box(frame, (613, 483, 781, 673), GREEN, pulse_at(t, 3.8, 5.2))
    active_box(frame, (810, 485, 1036, 672), GREEN, pulse_at(t, 4.8, 6.5))
    active_box(frame, (1090, 485, 1295, 672), PURPLE, pulse_at(t, 6.0, 7.8))
    active_box(frame, (476, 890, 925, 1118), PURPLE, pulse_at(t, 8.5, 11.8))
    active_box(frame, (976, 890, 1322, 1118), RED, pulse_at(t, 9.5, 12.5))

    return frame.convert("RGB")


def build_storyboard(static: Image.Image) -> Image.Image:
    board = Image.new("RGB", (1400, 1200), "#010203")
    times = [0.9, 3.1, 5.3, 6.6, 8.2, 10.1]
    for index, sample_time in enumerate(times):
        sample = render_frame(static, sample_time).resize((700, 400), Image.Resampling.LANCZOS)
        board.paste(sample, ((index % 2) * 700, (index // 2) * 400))
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
    static.convert("RGB").save(OUT_POSTER, optimize=True)
    build_storyboard(static).save(OUT_STORYBOARD, optimize=True)
    print(OUT_GIF)
    print(OUT_POSTER)
    print(OUT_STORYBOARD)


if __name__ == "__main__":
    main()
