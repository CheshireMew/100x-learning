from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "content2-static-sample-reset.png"

W, H = 800, 540
BG = "#F4F0E7"
INK = "#19242B"
MUTED = "#69757A"
GRID = "#D8D1C4"
ASSET_A = "#287A96"
ASSET_B = "#E87945"
POSITIVE = "#31775D"
POSITIVE_BG = "#DCECE3"
PAPER_DOT = "#E8E1D5"

FONT_REGULAR = Path(r"C:\Windows\Fonts\Deng.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\Dengb.ttf")
FONT_NUM = Path(r"C:\Windows\Fonts\arialbd.ttf")


def font(size: int, bold: bool = False, number: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_NUM if number else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(str(path), size)


def centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int, fill: str, bold: bool = False, number: bool = False) -> None:
    draw.text(xy, value, font=font(size, bold, number), fill=fill, anchor="mm")


def line_chart(draw: ImageDraw.ImageDraw) -> None:
    left, right = 64, 585
    top, bottom = 118, 270

    def y(value: float) -> float:
        return bottom - (value - 50) * 1.0

    for value in (50, 100, 200):
        yy = y(value)
        draw.line((left, yy, right, yy), fill=GRID, width=1)
        draw.text((52, yy), str(value), font=font(14, number=True), fill=MUTED, anchor="rm")

    xs = [90, 323, 556]
    labels = ["开始", "第一年", "第二年"]
    for x, label in zip(xs, labels):
        draw.line((x, bottom, x, bottom + 5), fill=MUTED, width=1)
        centered(draw, (x, 286), label, 14, MUTED)

    a_points = [(xs[0], y(100)), (xs[1], y(200)), (xs[2], y(100))]
    b_points = [(xs[0], y(100)), (xs[1], y(50)), (xs[2], y(100))]
    draw.line(a_points, fill=ASSET_A, width=4, joint="curve")
    draw.line(b_points, fill=ASSET_B, width=4, joint="curve")

    for x, yy in a_points:
        draw.ellipse((x - 5, yy - 5, x + 5, yy + 5), fill=BG, outline=ASSET_A, width=3)
    for x, yy in b_points:
        draw.ellipse((x - 5, yy - 5, x + 5, yy + 5), fill=BG, outline=ASSET_B, width=3)

    draw.line((556, y(100) - 3, 612, 177), fill=ASSET_A, width=2)
    draw.ellipse((625, 164, 637, 176), fill=ASSET_A)
    draw.text((648, 162), "资产A  100→200→100", font=font(14, bold=True), fill=ASSET_A)
    draw.text((648, 184), "最终收益 0%", font=font(13), fill=MUTED)

    draw.line((556, y(100) + 3, 612, 227), fill=ASSET_B, width=2)
    draw.ellipse((625, 214, 637, 226), fill=ASSET_B)
    draw.text((648, 212), "资产B  100→50→100", font=font(14, bold=True), fill=ASSET_B)
    draw.text((648, 234), "最终收益 0%", font=font(13), fill=MUTED)


def stacked_bars(draw: ImageDraw.ImageDraw) -> None:
    baseline = 466
    scale = 0.72
    width = 82
    centers = [125, 315, 505, 695]
    states = [
        ("初始", "50 / 50", 50.0, 50.0, "100"),
        ("第一年", "80 / 20", 100.0, 25.0, "125"),
        ("再平衡后", "50 / 50", 62.5, 62.5, "125"),
        ("第二年", "20 / 80", 31.25, 125.0, "156.25"),
    ]

    for value in (50, 100, 150):
        yy = baseline - value * scale
        draw.line((72, yy, 744, yy), fill=GRID, width=1)
        draw.text((61, yy), str(value), font=font(12, number=True), fill=MUTED, anchor="rm")

    for center_x, (label, weights, a_value, b_value, total) in zip(centers, states):
        a_height = a_value * scale
        b_height = b_value * scale
        x0, x1 = center_x - width // 2, center_x + width // 2
        draw.rectangle((x0, baseline - b_height, x1, baseline), fill=ASSET_B)
        draw.rectangle((x0, baseline - b_height - a_height, x1, baseline - b_height), fill=ASSET_A)
        draw.rectangle((x0, baseline - b_height - a_height, x1, baseline), outline=INK, width=1)
        centered(draw, (center_x, int(baseline - b_height - a_height - 16)), total, 17, INK, bold=True, number=True)
        centered(draw, (center_x, 486), label, 14, INK, bold=True)
        centered(draw, (center_x, 507), weights, 13, MUTED, number=True)

    # Rebalancing annotation stays inside the same data scene.
    draw.line((358, 397, 410, 374, 462, 397), fill=POSITIVE, width=2)
    centered(draw, (410, 356), "转移 37.5", 13, POSITIVE, bold=True)
    centered(draw, (410, 416), "总额不变", 12, MUTED)


def main() -> None:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)

    # Very light paper texture, intentionally unrelated to all previous treatments.
    random.seed(11)
    for _ in range(1100):
        x = random.randrange(W)
        y = random.randrange(H)
        draw.point((x, y), fill=PAPER_DOT)

    draw.text((28, 19), "两个资产都回到原点，组合却变成 156.25", font=font(27, bold=True), fill=INK)
    draw.text((29, 57), "再平衡示例｜所有变化始终发生在同一张画布上", font=font(15), fill=MUTED)

    draw.rounded_rectangle((629, 18, 771, 70), radius=14, fill=POSITIVE_BG)
    centered(draw, (700, 35), "+56.25%", 23, POSITIVE, bold=True, number=True)
    centered(draw, (700, 58), "两年累计变化", 11, POSITIVE)

    draw.line((28, 88, 772, 88), fill=INK, width=2)
    draw.text((29, 99), "单独持有", font=font(17, bold=True), fill=INK)
    line_chart(draw)

    draw.line((28, 303, 772, 303), fill=INK, width=2)
    draw.text((29, 314), "50/50组合：第一年结束时恢复目标权重", font=font(17, bold=True), fill=INK)
    stacked_bars(draw)

    draw.text((28, 523), "理想化交替涨跌案例；未计交易成本、税费和流动性。", font=font(12), fill=MUTED)
    draw.text((772, 523), "再平衡恢复配置，不预测赢家。", font=font(12, bold=True), fill=POSITIVE, anchor="ra")

    image.save(OUT, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
