from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "rebalancing-sketch-style-sample.png"

W, H = 800, 600
BG = "#020303"
WHITE = "#D9DADD"
MUTED = "#92969C"
GREEN = "#00CF77"
BLUE = "#2C9EDA"
CYAN = "#79DDD2"
ORANGE = "#EBAA4A"
PURPLE = "#A94BC1"
PINK = "#D95876"

FONT_CN = Path(r"C:\Windows\Fonts\simkai.ttf")
FONT_EN = Path(r"C:\Windows\Fonts\Inkfree.ttf")
FONT_NUM = Path(r"C:\Windows\Fonts\comicbd.ttf")

rng = random.Random(27)


def font(size: int, kind: str = "cn") -> ImageFont.FreeTypeFont:
    path = {"cn": FONT_CN, "en": FONT_EN, "num": FONT_NUM}[kind]
    return ImageFont.truetype(str(path), size)


def rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def composite_glow(base: Image.Image, layer: Image.Image, radius: int = 7, repeats: int = 1) -> None:
    glow = layer.filter(ImageFilter.GaussianBlur(radius))
    for _ in range(repeats):
        base.alpha_composite(glow)
    base.alpha_composite(layer)


def rough_line(
    base: Image.Image,
    start: tuple[float, float],
    end: tuple[float, float],
    color: str,
    width: int = 2,
    jitter: float = 1.4,
    glow: int = 0,
) -> None:
    length = max(1.0, math.dist(start, end))
    count = max(2, int(length / 13))
    points = []
    for i in range(count + 1):
        p = i / count
        x = start[0] + (end[0] - start[0]) * p
        y = start[1] + (end[1] - start[1]) * p
        if 0 < i < count:
            x += rng.uniform(-jitter, jitter)
            y += rng.uniform(-jitter, jitter)
        points.append((x, y))

    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for dx, dy, alpha in [(-0.6, 0.2, 90), (0.7, -0.4, 75), (0, 0, 205)]:
        draw.line([(x + dx, y + dy) for x, y in points], fill=rgba(color, alpha), width=width, joint="curve")
    if glow:
        base.alpha_composite(layer.filter(ImageFilter.GaussianBlur(glow)))
    base.alpha_composite(layer)


def rough_round_rect(
    base: Image.Image,
    box: tuple[int, int, int, int],
    color: str,
    fill: str,
    radius: int = 18,
    width: int = 2,
    glow: int = 0,
) -> None:
    fill_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(fill_layer).rounded_rectangle(box, radius=radius, fill=rgba(fill, 220))
    base.alpha_composite(fill_layer)

    line_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(line_layer)
    x0, y0, x1, y1 = box
    for offset, alpha in [((-1, 0, 1, 0), 85), ((1, 1, 0, 1), 70), ((0, 0, 0, 0), 205)]:
        a, b, c, d = offset
        draw.rounded_rectangle((x0 + a, y0 + b, x1 + c, y1 + d), radius=radius, outline=rgba(color, alpha), width=width)
    if glow:
        base.alpha_composite(line_layer.filter(ImageFilter.GaussianBlur(glow)))
    base.alpha_composite(line_layer)


def hand_text(
    base: Image.Image,
    xy: tuple[int, int],
    value: str,
    size: int,
    color: str = WHITE,
    kind: str = "cn",
    spacing: int = 0,
) -> None:
    x, y = xy
    face = font(size, kind)
    for character in value:
        if character == " ":
            x += max(8, size // 3)
            continue
        bbox = face.getbbox(character)
        char_w = max(1, bbox[2] - bbox[0])
        char_h = max(1, bbox[3] - bbox[1])
        tile = Image.new("RGBA", (char_w + 24, char_h + 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(tile)
        draw.text((12 - bbox[0], 12 - bbox[1]), character, font=face, fill=rgba(color, 235))
        angle = rng.uniform(-1.8, 1.8)
        tile = tile.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        base.alpha_composite(tile, (int(x + rng.uniform(-1, 1)), int(y + rng.uniform(-1, 1))))
        x += char_w + spacing + rng.uniform(-0.6, 0.9)


def centered_text(base: Image.Image, xy: tuple[int, int], value: str, size: int, color: str, kind: str = "cn") -> None:
    ImageDraw.Draw(base).text(xy, value, font=font(size, kind), fill=color, anchor="mm")


def glow_dot(base: Image.Image, xy: tuple[int, int], color: str, radius: int = 4) -> None:
    x, y = xy
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=rgba(color, 235))
    glow = layer.filter(ImageFilter.GaussianBlur(11))
    base.alpha_composite(glow)
    base.alpha_composite(glow)
    base.alpha_composite(layer)


def draw_balance(base: Image.Image) -> None:
    # A deliberately imperfect balance illustration: no polished chart geometry.
    rough_line(base, (236, 290), (568, 252), WHITE, width=3, jitter=1.7)
    rough_line(base, (402, 270), (402, 377), MUTED, width=3, jitter=1.2)
    rough_line(base, (402, 377), (352, 419), MUTED, width=3, jitter=1.0)
    rough_line(base, (402, 377), (452, 419), MUTED, width=3, jitter=1.0)
    rough_line(base, (352, 419), (452, 419), MUTED, width=3, jitter=1.0)

    # Left and right hanging pans.
    rough_line(base, (252, 288), (252, 337), CYAN, width=2)
    rough_line(base, (211, 358), (293, 358), CYAN, width=2)
    rough_line(base, (211, 358), (228, 337), CYAN, width=2)
    rough_line(base, (293, 358), (276, 337), CYAN, width=2)

    rough_line(base, (548, 254), (548, 304), ORANGE, width=2)
    rough_line(base, (507, 325), (589, 325), ORANGE, width=2)
    rough_line(base, (507, 325), (524, 304), ORANGE, width=2)
    rough_line(base, (589, 325), (572, 304), ORANGE, width=2)

    # Hand-drawn asset tokens.
    rough_round_rect(base, (190, 368, 314, 431), CYAN, "#07171D", radius=12)
    centered_text(base, (252, 389), "资产 A", 20, CYAN)
    centered_text(base, (252, 416), "100", 27, WHITE, "num")
    rough_round_rect(base, (486, 335, 610, 398), ORANGE, "#191207", radius=12)
    centered_text(base, (548, 356), "资产 B", 20, ORANGE)
    centered_text(base, (548, 383), "25", 27, WHITE, "num")

    # A light signal trail suggests motion without making this a flowchart.
    curve = [(294, 321), (345, 308), (396, 295), (448, 281), (500, 267)]
    for a, b in zip(curve[:-1], curve[1:]):
        rough_line(base, a, b, GREEN, width=2, jitter=1.0, glow=2)
    for point, radius in zip(curve[1:-1], [3, 4, 5]):
        glow_dot(base, point, GREEN, radius)


def main() -> None:
    image = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(image)

    # The sample intentionally mimics the reference's visual grammar, not its flowchart layout.
    draw.rectangle((34, 28, 42, 91), fill=PURPLE)
    hand_text(image, (58, 28), "再平衡", 45, WHITE, "cn", spacing=1)
    hand_text(image, (59, 86), "把 80/20 拉回 50/50", 18, MUTED, "cn")

    rough_round_rect(image, (470, 27, 754, 104), GREEN, "#17372F", radius=19, width=2, glow=3)
    centered_text(image, (612, 64), "Rebalancing", 42, GREEN, "en")

    rough_round_rect(image, (33, 126, 767, 558), "#686C70", "#000000", radius=27, width=2)
    rough_round_rect(image, (67, 160, 733, 468), BLUE, "#03121C", radius=24, width=2, glow=2)
    centered_text(image, (400, 190), "组合现在偏向资产 A", 26, WHITE, "cn")

    draw_balance(image)

    rough_round_rect(image, (88, 488, 333, 539), GREEN, "#04150D", radius=13, width=2, glow=2)
    centered_text(image, (210, 513), "目标：恢复 50 / 50", 21, GREEN, "cn")
    rough_round_rect(image, (466, 488, 711, 539), PURPLE, "#150519", radius=13, width=2, glow=2)
    centered_text(image, (588, 513), "总额 125（不变）", 21, WHITE, "cn")

    for x, y, color in [(77, 112, GREEN), (368, 137, CYAN), (720, 137, PURPLE), (448, 566, GREEN), (337, 568, PURPLE)]:
        centered_text(image, (x, y), "+", 29, color, "en")

    image.convert("RGB").save(OUT, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
