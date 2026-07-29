from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "content2-copy-led-static-sample.png"

W, H = 820, 460
BG = "#FCFAF5"
INK = "#172229"
MUTED = "#758087"
LINE = "#DDD8CE"
A = "#347F9E"
B = "#E67742"
GREEN = "#31745A"
GREEN_BG = "#E2EFE8"
HIGHLIGHT = "#F1EEE5"

FONT_REGULAR = Path(r"C:\Windows\Fonts\Deng.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\Dengb.ttf")
FONT_NUMBER = Path(r"C:\Windows\Fonts\arialbd.ttf")


def font(size: int, bold: bool = False, number: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_NUMBER if number else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(str(path), size)


def centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill: str, bold: bool = False, number: bool = False) -> None:
    draw.text(xy, text, font=font(size, bold, number), fill=fill, anchor="mm")


def arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = LINE, width: int = 2) -> None:
    draw.line((start, end), fill=color, width=width)
    x, y = end
    draw.polygon(((x, y), (x - 7, y - 4), (x - 7, y + 4)), fill=color)


def mini_path(draw: ImageDraw.ImageDraw, y: int, label: str, middle: str, color: str) -> None:
    draw.ellipse((41, y - 5, 51, y + 5), fill=color)
    draw.text((63, y), label, font=font(15, bold=True), fill=color, anchor="lm")
    values = ["100", middle, "100"]
    xs = [150, 260, 370]
    for x, value in zip(xs, values):
        centered(draw, (x, y), value, 17, INK, bold=True, number=True)
    arrow(draw, (175, y), (235, y), MUTED, 1)
    arrow(draw, (285, y), (345, y), MUTED, 1)
    draw.text((417, y), "两年收益 0%", font=font(14), fill=MUTED, anchor="lm")


def stack_bar(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    a_value: float,
    b_value: float,
    total: str,
    state: str,
    weights: str,
    highlight: bool = False,
) -> None:
    baseline = 367
    scale = 0.84
    width = 76
    a_h = a_value * scale
    b_h = b_value * scale
    x0, x1 = center_x - width // 2, center_x + width // 2

    if highlight:
        draw.rounded_rectangle((center_x - 72, 183, center_x + 72, 424), radius=16, fill=GREEN_BG)

    draw.rectangle((x0, baseline - b_h, x1, baseline), fill=B)
    draw.rectangle((x0, baseline - b_h - a_h, x1, baseline - b_h), fill=A)
    draw.rectangle((x0, baseline - b_h - a_h, x1, baseline), outline=INK, width=1)

    top = int(baseline - b_h - a_h)
    centered(draw, (center_x, top - 17), total, 18, GREEN if highlight else INK, bold=True, number=True)
    if a_h >= 25:
        centered(draw, (center_x, int(top + a_h / 2)), f"A {a_value:g}", 12, BG, bold=True)
    if b_h >= 25:
        centered(draw, (center_x, int(baseline - b_h / 2)), f"B {b_value:g}", 12, BG, bold=True)

    centered(draw, (center_x, 393), state, 14, INK, bold=True)
    centered(draw, (center_x, 416), weights, 13, MUTED, number=True)


def main() -> None:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)

    draw.text((26, 18), "两个都没赚钱的资产，组合为什么反而赚钱了？", font=font(25, bold=True), fill=INK)
    draw.text((27, 52), "关键变化不在终点，而在第一年结束后的资产再平衡。", font=font(14), fill=MUTED)

    draw.rounded_rectangle((657, 17, 793, 65), radius=13, fill=GREEN_BG)
    centered(draw, (725, 34), "+56.25%", 21, GREEN, bold=True, number=True)
    centered(draw, (725, 54), "组合两年收益", 11, GREEN)

    draw.line((26, 79, 794, 79), fill=INK, width=2)
    draw.text((27, 90), "单独持有", font=font(15, bold=True), fill=INK)
    mini_path(draw, 119, "资产 A", "200", A)
    mini_path(draw, 151, "资产 B", "50", B)

    draw.rounded_rectangle((560, 94, 785, 164), radius=12, fill=HIGHLIGHT)
    draw.text((578, 112), "A：先翻倍，再腰斩", font=font(13), fill=A)
    draw.text((578, 138), "B：先腰斩，再翻倍", font=font(13), fill=B)

    draw.line((26, 176, 794, 176), fill=INK, width=2)
    draw.text((27, 187), "100元平均分配，各买50元", font=font(15, bold=True), fill=INK)

    centers = [105, 305, 515, 715]
    stack_bar(draw, centers[0], 50, 50, "100", "最初", "50 / 50")
    stack_bar(draw, centers[1], 100, 25, "125", "第一年结束", "80 / 20")
    stack_bar(draw, centers[2], 62.5, 62.5, "125", "再平衡后", "50 / 50")
    stack_bar(draw, centers[3], 31.25, 125, "156.25", "第二年结束", "20 / 80", highlight=True)

    arrow(draw, (154, 276), (246, 276), LINE, 2)
    arrow(draw, (354, 276), (446, 276), GREEN, 2)
    arrow(draw, (564, 276), (656, 276), LINE, 2)
    centered(draw, (400, 247), "卖出A，补入B", 13, GREEN, bold=True)
    centered(draw, (400, 265), "125元重新平分", 12, MUTED)

    draw.ellipse((27, 438, 35, 446), fill=A)
    draw.text((43, 442), "资产 A", font=font(12), fill=MUTED, anchor="lm")
    draw.ellipse((108, 438, 116, 446), fill=B)
    draw.text((124, 442), "资产 B", font=font(12), fill=MUTED, anchor="lm")
    draw.text((794, 442), "理想化案例；未计税费与交易成本。", font=font(12), fill=MUTED, anchor="rm")

    image.save(OUT, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
