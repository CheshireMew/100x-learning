from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
GIF_PATH = ROOT / "portfolio-rebalancing.gif"
COVER_PATH = ROOT / "portfolio-rebalancing-cover.png"
STORYBOARD_PATH = ROOT / "portfolio-rebalancing-storyboard.png"

W = H = 1200
FPS = 12
DURATION = 15.5

BG = "#09111F"
PANEL = "#111D30"
PANEL_2 = "#17253A"
TEXT = "#F4F7FB"
MUTED = "#A9B6C9"
GRID = "#2A3A52"
CYAN = "#37C6E8"
ORANGE = "#FFB14E"
GREEN = "#51D39A"
RED = "#FF6B78"
YELLOW = "#F5D76E"

FONT_REGULAR = Path(r"C:\Windows\Fonts\Deng.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\Dengb.ttf")
FONT_NUMBER = Path(r"C:\Windows\Fonts\arialbd.ttf")


def font(size: int, bold: bool = False, number: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_NUMBER if number else (FONT_BOLD if bold else FONT_REGULAR)
    return ImageFont.truetype(str(path), size)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def ease(value: float) -> float:
    value = clamp(value)
    return 1 - (1 - value) ** 3


def between(t: float, start: float, end: float) -> float:
    return ease((t - start) / (end - start))


def lerp(start: float, end: float, progress: float) -> float:
    return start + (end - start) * progress


def money(value: float) -> str:
    if abs(value - round(value)) < 0.005:
        return f"{int(round(value))}"
    if abs(value * 10 - round(value * 10)) < 0.005:
        return f"{value:.1f}"
    return f"{value:.2f}"


def centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    value: str,
    text_font: ImageFont.FreeTypeFont,
    fill: str,
    anchor: str = "mm",
) -> None:
    draw.text(xy, value, font=text_font, fill=fill, anchor=anchor)


def rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: str = PANEL,
    outline: str | None = GRID,
    radius: int = 30,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def pill(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    value: str,
    fill: str,
    text_fill: str = BG,
    text_size: int = 28,
) -> None:
    text_font = font(text_size, bold=True)
    left, top, right, bottom = draw.textbbox((0, 0), value, font=text_font)
    width = right - left + 34
    height = bottom - top + 22
    x, y = xy
    draw.rounded_rectangle((x, y, x + width, y + height), radius=height // 2, fill=fill)
    centered_text(draw, (x + width / 2, y + height / 2 - 1), value, text_font, text_fill)


def draw_header(draw: ImageDraw.ImageDraw, stage: str, accent: str) -> None:
    pill(draw, (68, 55), "MIT 18.S096 · PORTFOLIO MANAGEMENT", PANEL_2, TEXT, 24)
    pill(draw, (963, 55), stage, accent, BG, 24)
    draw.text((68, 132), "两个资产都回到原点，", font=font(53, bold=True), fill=TEXT)
    draw.text((68, 198), "组合为什么变成 156.25？", font=font(53, bold=True), fill=TEXT)
    draw.line((68, 278, 1132, 278), fill=GRID, width=2)


def draw_asset_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: float,
    accent: str,
    movement: str,
    movement_color: str,
) -> None:
    x0, y0, x1, y1 = box
    rounded_panel(draw, box)
    draw.ellipse((x0 + 34, y0 + 34, x0 + 68, y0 + 68), fill=accent)
    draw.text((x0 + 84, y0 + 27), f"资产 {label}", font=font(34, bold=True), fill=TEXT)
    if movement:
        right = x1 - 34
        movement_font = font(27, bold=True)
        width = draw.textbbox((0, 0), movement, font=movement_font)[2]
        draw.text((right - width, y0 + 33), movement, font=movement_font, fill=movement_color)

    draw.text((x0 + 34, y0 + 104), "当前价值", font=font(26), fill=MUTED)
    draw.text((x0 + 34, y0 + 142), money(value), font=font(72, number=True), fill=TEXT)

    base_y = y1 - 56
    max_height = 190
    bar_height = max(8, max_height * value / 125)
    draw.rounded_rectangle(
        (x0 + 310, base_y - bar_height, x0 + 405, base_y),
        radius=18,
        fill=accent,
    )
    draw.line((x0 + 270, base_y, x1 - 38, base_y), fill=GRID, width=3)
    draw.text((x0 + 334, base_y + 14), "价值", font=font(23), fill=MUTED)


def draw_allocation_bar(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    width: int,
    height: int,
    a_value: float,
    b_value: float,
) -> None:
    total = a_value + b_value
    a_ratio = a_value / total if total else 0.5
    split = x0 + int(width * a_ratio)
    draw.rounded_rectangle((x0, y0, x0 + width, y0 + height), radius=height // 2, fill=ORANGE)
    draw.rounded_rectangle((x0, y0, split + height // 2, y0 + height), radius=height // 2, fill=CYAN)
    draw.rectangle((split, y0, split + height // 2, y0 + height), fill=ORANGE)
    centered_text(draw, (x0 + (split - x0) / 2, y0 + height / 2), f"A {a_ratio:.0%}", font(24, bold=True), BG)
    centered_text(draw, (split + (x0 + width - split) / 2, y0 + height / 2), f"B {1-a_ratio:.0%}", font(24, bold=True), BG)


def draw_total_panel(
    draw: ImageDraw.ImageDraw,
    a_value: float,
    b_value: float,
    note: str,
) -> None:
    total = a_value + b_value
    rounded_panel(draw, (68, 821, 1132, 1080), fill=PANEL_2)
    draw.text((104, 853), "组合总额", font=font(28), fill=MUTED)
    draw.text((104, 891), money(total), font=font(74, number=True), fill=TEXT)
    change = (total / 100 - 1) * 100
    change_text = f"{change:+.2f}%" if abs(change) > 0.004 else "0.00%"
    draw.text((340, 919), change_text, font=font(34, number=True), fill=GREEN if change > 0 else MUTED)
    draw.text((104, 996), note, font=font(27, bold=True), fill=YELLOW)
    draw_allocation_bar(draw, 630, 877, 454, 58, a_value, b_value)
    centered_text(draw, (857, 995), "实时权重", font(25), MUTED)


def draw_transfer(draw: ImageDraw.ImageDraw, progress: float) -> None:
    if progress <= 0:
        return
    x0, x1, y = 520, 680, 603
    current = lerp(x0, x1, progress)
    draw.line((x0, y, current, y), fill=YELLOW, width=10)
    if progress > 0.85:
        draw.polygon(((x1, y), (x1 - 24, y - 17), (x1 - 24, y + 17)), fill=YELLOW)
    centered_text(draw, (600, 555), "转移 37.5", font(28, bold=True), YELLOW)


def draw_main_scene(t: float) -> Image.Image:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)

    if t < 1.8:
        stage, accent = "1 / 4  初始", CYAN
        a, b = 50.0, 50.0
        a_move = b_move = ""
        note = "目标权重：A 50% / B 50%"
    elif t < 4.5:
        stage, accent = "2 / 4  第一年", GREEN
        p = between(t, 1.8, 4.2)
        a, b = lerp(50, 100, p), lerp(50, 25, p)
        a_move, b_move = "+100%", "-50%"
        note = "价格变化后，权重从 50/50 漂移到 80/20"
    elif t < 7.2:
        stage, accent = "3 / 4  再平衡", YELLOW
        p = between(t, 4.5, 6.8)
        a, b = lerp(100, 62.5, p), lerp(25, 62.5, p)
        a_move, b_move = "卖出一部分", "补回仓位"
        note = "总额不变，只把组合重新拉回 50/50"
    else:
        stage, accent = "4 / 4  第二年", ORANGE
        p = between(t, 7.2, 9.5)
        a, b = lerp(62.5, 31.25, p), lerp(62.5, 125, p)
        a_move, b_move = "-50%", "+100%"
        note = "第二年涨跌互换，组合再增长 25%"

    draw_header(draw, stage, accent)
    draw_asset_card(draw, (68, 318, 558, 782), "A", a, CYAN, a_move, GREEN if "+" in a_move else RED if "-" in a_move else YELLOW)
    draw_asset_card(draw, (642, 318, 1132, 782), "B", b, ORANGE, b_move, GREEN if "+" in b_move else RED if "-" in b_move else YELLOW)
    if 4.5 <= t < 7.2:
        draw_transfer(draw, between(t, 4.7, 6.2))
    draw_total_panel(draw, a, b, note)
    centered_text(draw, (600, 1147), "每一次数值变化都基于上一期的新金额", font(24), MUTED)
    return image


def draw_result_scene() -> Image.Image:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    pill(draw, (68, 55), "结果", GREEN, BG, 26)
    draw.text((68, 133), "两项资产单独持有都回到原点", font=font(49, bold=True), fill=TEXT)
    draw.text((68, 195), "再平衡组合却从 100 变成 156.25", font=font(49, bold=True), fill=TEXT)

    rounded_panel(draw, (68, 305, 1132, 660), fill=PANEL_2)
    centered_text(draw, (600, 397), "+56.25%", font(108, number=True), GREEN)
    centered_text(draw, (600, 505), "再平衡组合的两年累计变化", font(31, bold=True), MUTED)

    steps = [
        (120, "100", "初始 50/50", CYAN),
        (470, "125", "第一年结束", YELLOW),
        (820, "156.25", "第二年结束", GREEN),
    ]
    for index, (x, value, label, color) in enumerate(steps):
        draw.ellipse((x, 735, x + 86, 821), fill=color)
        centered_text(draw, (x + 43, 778), str(index + 1), font(29, number=True), BG)
        centered_text(draw, (x + 43, 866), value, font(45, number=True), TEXT)
        centered_text(draw, (x + 43, 917), label, font(25), MUTED)
        if index < 2:
            draw.line((x + 100, 778, x + 316, 778), fill=GRID, width=8)
            draw.polygon(((x + 316, 778), (x + 288, 758), (x + 288, 798)), fill=GRID)

    rounded_panel(draw, (68, 1001, 1132, 1101), fill=PANEL)
    centered_text(draw, (600, 1051), "关键动作：第一年结束时，把 80/20 恢复为 50/50", font(30, bold=True), YELLOW)
    centered_text(draw, (600, 1151), "A：100→200→100 ｜ B：100→50→100 ｜ 单独持有均为 0%", font(23), MUTED)
    return image


def draw_caveat_scene() -> Image.Image:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    pill(draw, (68, 55), "重要边界", RED, TEXT, 26)
    draw.text((68, 142), "这不是“再平衡必赚”的证明", font=font(55, bold=True), fill=TEXT)
    draw.text((68, 216), "它只是一个刻意构造的教学示例", font=font(38), fill=MUTED)

    items: Iterable[tuple[str, str]] = [
        ("01", "示例假设两项资产的涨跌完全交替"),
        ("02", "没有计入交易成本、税费和流动性问题"),
        ("03", "单边下跌或共同暴跌时，结果可能完全不同"),
    ]
    for index, (number, value) in enumerate(items):
        top = 353 + index * 180
        rounded_panel(draw, (68, top, 1132, top + 137), fill=PANEL_2)
        draw.ellipse((104, top + 32, 177, top + 105), fill=RED if index == 2 else YELLOW)
        centered_text(draw, (140, top + 69), number, font(25, number=True), BG)
        draw.text((215, top + 44), value, font=font(32, bold=True), fill=TEXT)

    rounded_panel(draw, (68, 934, 1132, 1098), fill="#123329", outline="#2E7A61")
    centered_text(draw, (600, 987), "再平衡的主要作用", font(27), GREEN)
    centered_text(draw, (600, 1049), "恢复目标配置，而不是预测下一位赢家", font(37, bold=True), TEXT)
    centered_text(draw, (600, 1151), "教学示例 · 不构成投资建议", font(24), MUTED)
    return image


def render_frame(t: float) -> Image.Image:
    if t < 9.7:
        return draw_main_scene(t)
    if t < 12.4:
        return draw_result_scene()
    return draw_caveat_scene()


def main() -> None:
    frames: list[Image.Image] = []
    frame_count = int(DURATION * FPS)
    for index in range(frame_count):
        frame = render_frame(index / FPS)
        frames.append(frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))

    frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / FPS),
        loop=0,
        disposal=2,
        optimize=True,
    )
    draw_result_scene().save(COVER_PATH, optimize=True)
    storyboard = Image.new("RGB", (1200, 1800), "#050A12")
    sample_times = [0.8, 4.35, 7.0, 9.6, 10.6, 13.6]
    for index, sample_time in enumerate(sample_times):
        sample = render_frame(sample_time).resize((600, 600), Image.Resampling.LANCZOS)
        storyboard.paste(sample, ((index % 2) * 600, (index // 2) * 600))
    storyboard.save(STORYBOARD_PATH, optimize=True)
    print(GIF_PATH)
    print(COVER_PATH)
    print(STORYBOARD_PATH)


if __name__ == "__main__":
    main()
