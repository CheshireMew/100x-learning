from __future__ import annotations

import math
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUT = ROOT / "ai-copy-comparison-4-panel-v2-light.png"

W, H = 2400, 3600
BG_TOP = (247, 250, 255)
BG_BOTTOM = (232, 240, 252)

FONT_REGULAR = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"


CARDS = [
    {
        "number": "01",
        "brand": "ChatGPT 5.6-sol",
        "mode": "高智能",
        "logo": "chatgpt-openai-dark.png",
        "accent": (92, 231, 190),
        "text": """Vibe coding 最容易露馅的地方，就是动画。

大多数 AI 写出来的动效还停留在淡入淡出，能动，但没有质感。

GreenSock 官方开源的 GSAP Skills，直接教 Codex、Cursor 和 Claude Code 用专业方式写时间轴、滚动触发、视差、SVG 变形、页面转场和微交互，还包含框架适配与性能规范。

装上之后，AI 终于不只是“让页面动起来”，而是知道动画该怎么设计。

🔗 https://github.com/greensock/gsap-skills""",
    },
    {
        "number": "02",
        "brand": "Gemini 3.1 pro",
        "mode": "拓展思考",
        "logo": "gemini.png",
        "accent": (139, 111, 255),
        "text": """Vibecoding 的 UI 动画短板被直接补齐了！

以前 AI 写前端动效，很多时候只会简单的淡入淡出，确实是能动但不高级。现在 GreenSock 官方开源了 AI 技能包，直接让 AI 真正学会写专业级的 GSAP 动画。

装上这个技能包之后，AI 不再凭感觉写代码，而是开始遵循专业规范。无论是时间轴动画、滚动触发、视差效果，还是 SVG 变形和复杂的页面转场，它都能处理得非常细腻。

有了它，做官网可以让页面滚动更有层次，产品页的卡片和按钮出现更加自然，落地页的转场视差也能直接对标真实的商业网站。

AI 生成页面的速度已经越来越快了，但真正拉开质感差距的往往就是动画和细节。

开源项目 greensock/gsap-skills 的地址我已经放在评论区了。""",
    },
    {
        "number": "03",
        "brand": "DeepSeek",
        "mode": "专家模式 · 深度思考",
        "logo": "deepseek.png",
        "accent": (65, 145, 255),
        "text": """Vibecoding / Live Coding 做页面的动画短板，被彻底终结了！
就是这个开源技能包 GSAP Skills，绿袜（GreenSock）官方出品。

以前 AI 写前端动效，只会简单淡入淡出，“能动但不高级”。
而 GSAP 本就是专业动画方案，时间轴、滚动触发、视差、SVG 变形、转场、微交互都能做得极细。

这个技能包把 GSAP 的写法、插件和规范直接变成 AI 可调用的能力，让 AI 按专业方式生成动效。
官网的层次滚动、产品卡片的自然出现、落地页的视差转场，质感差距瞬间拉开。

项目地址我放评论区了。""",
    },
    {
        "number": "04",
        "brand": "豆包",
        "mode": "专家模式",
        "logo": "doubao-user-reference.png",
        "accent": (242, 104, 211),
        "text": """AI写前端动画的硬伤，被官方直接根治了
格林索克（GreenSock）官方开源的这套 GSAP AI技能包，直接让AI写出专业级GSAP动画。

以前AI做前端动效，永远只会淡入淡出，“能动但不高级”。而GSAP本就是前端动画领域的成熟方案，时间轴、滚动触发、视差滚动、SVG变形、页面转场、微交互，精细效果全能实现。

这套技能包把GSAP的写法、插件用法、动画模式、性能规范全部整理成AI可调用的能力，装上之后AI不再凭感觉瞎写，严格按专业标准生成动效代码。

官网做滚动层次感、产品页元素自然出场、落地页首屏转场视差，随手拉满商业网站质感。毕竟AI生成页面越来越快，真正拉开质感差距的，就是动画和细节。

项目地址：https://github.com/greensock/gsap-skills""",
    },
]


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(lerp(top[i], bottom[i], t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return img


def cover(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    ratio = max(size[0] / img.width, size[1] / img.height)
    resized = img.resize((round(img.width * ratio), round(img.height * ratio)), Image.Resampling.LANCZOS)
    left = (resized.width - size[0]) // 2
    top = (resized.height - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))


def alpha_fade_bottom(img: Image.Image, fade_start: int) -> Image.Image:
    rgba = img.convert("RGBA")
    alpha = Image.new("L", rgba.size, 255)
    ad = ImageDraw.Draw(alpha)
    for y in range(fade_start, rgba.height):
        t = (y - fade_start) / max(1, rgba.height - fade_start)
        a = round(255 * (1 - t) ** 1.7)
        ad.line((0, y, rgba.width, y), fill=a)
    rgba.putalpha(alpha)
    return rgba


def add_glow_line(base: Image.Image, points: list[tuple[int, int]], color: tuple[int, int, int], width: int = 6) -> None:
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for extra, alpha in ((30, 35), (16, 70), (6, 190)):
        gd.line(points, fill=(*color, alpha), width=width + extra, joint="curve")
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    base.alpha_composite(glow)
    ImageDraw.Draw(base).line(points, fill=(*color, 220), width=width, joint="curve")


def rounded_card_layer(size: tuple[int, int], radius: int, accent: tuple[int, int, int]) -> Image.Image:
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    header = tuple(round(255 * 0.90 + c * 0.10) for c in accent)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=(255, 255, 255, 252), outline=(*accent, 150), width=3)
    d.rounded_rectangle((3, 3, w - 4, 175), radius=radius - 3, fill=(*header, 255))
    d.rectangle((3, 112, w - 4, 175), fill=(*header, 255))
    d.line((56, 178, w - 56, 178), fill=(*accent, 105), width=2)
    return layer


def resize_logo(path: Path, box: int) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    bbox = logo.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    ratio = min(box / logo.width, box / logo.height)
    return logo.resize((max(1, round(logo.width * ratio)), max(1, round(logo.height * ratio))), Image.Resampling.LANCZOS)


def text_width(draw: ImageDraw.ImageDraw, value: str, fnt: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(value, font=fnt)


def wrap_paragraph(draw: ImageDraw.ImageDraw, paragraph: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    if not paragraph:
        return [""]
    lines: list[str] = []
    current = ""
    tokens = re.findall(r"https?://\S+|[A-Za-z0-9][A-Za-z0-9./:+-]*|[ \t]+|.", paragraph)
    closing_punctuation = "，。！？、；：”’）】》」』"
    for token in tokens:
        candidate = current + token
        if not current and token.isspace():
            continue
        if text_width(draw, candidate, fnt) <= max_width:
            current = candidate
            continue
        if token in closing_punctuation and current:
            current = candidate
            continue
        if current:
            lines.append(current.rstrip())
            current = token.lstrip()
        else:
            current = token.lstrip()

        # Only very long unbroken strings (normally URLs) may be split character-by-character.
        while current and text_width(draw, current, fnt) > max_width:
            cut = 1
            while cut < len(current) and text_width(draw, current[: cut + 1], fnt) <= max_width:
                cut += 1
            lines.append(current[:cut])
            current = current[cut:]
    if current or not lines:
        lines.append(current.rstrip())
    return lines


def layout_text(draw: ImageDraw.ImageDraw, value: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str | None]:
    lines: list[str | None] = []
    paragraphs = value.split("\n")
    for paragraph in paragraphs:
        if paragraph == "":
            lines.append(None)
        else:
            lines.extend(wrap_paragraph(draw, paragraph, fnt, max_width))
    return lines


def draw_rich_line(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    line: str,
    body_font: ImageFont.FreeTypeFont,
    emoji_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int, int],
) -> None:
    x, y = xy
    if line.startswith("🔗"):
        draw.text((x, y - 2), "🔗", font=emoji_font, fill=fill, embedded_color=True)
        emoji_w = round(draw.textlength("🔗", font=emoji_font))
        draw.text((x + emoji_w + 8, y), line[1:].lstrip(), font=body_font, fill=fill)
    else:
        draw.text((x, y), line, font=body_font, fill=fill)


def draw_pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, accent: tuple[int, int, int]) -> None:
    fnt = font(FONT_BOLD, 27)
    x, y = xy
    pad_x, pad_y = 22, 11
    bbox = draw.textbbox((0, 0), label, font=fnt)
    w = bbox[2] - bbox[0] + pad_x * 2
    h = bbox[3] - bbox[1] + pad_y * 2
    tinted_light = tuple(round(250 * 0.78 + c * 0.22) for c in accent)
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=(*tinted_light, 255), outline=(*accent, 255), width=2)
    draw.text((x + w / 2, y + h / 2 - 1), label, font=fnt, fill=(28, 39, 58, 255), anchor="mm")


def draw_card(base: Image.Image, card: dict[str, object], xy: tuple[int, int], size: tuple[int, int]) -> dict[str, int]:
    x, y = xy
    w, h = size
    accent = card["accent"]
    assert isinstance(accent, tuple)

    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x + 5, y + 16, x + w + 5, y + h + 16), radius=42, fill=(62, 88, 132, 58))
    shadow = shadow.filter(ImageFilter.GaussianBlur(32))
    base.alpha_composite(shadow)
    base.alpha_composite(rounded_card_layer(size, 42, accent), (x, y))

    d = ImageDraw.Draw(base)
    logo_chip = (x + 48, y + 42, x + 144, y + 138)
    d.rounded_rectangle(logo_chip, radius=28, fill=(255, 255, 255, 255), outline=(*accent, 255), width=2)
    logo = resize_logo(ASSETS / str(card["logo"]), 70)
    lx = logo_chip[0] + (96 - logo.width) // 2
    ly = logo_chip[1] + (96 - logo.height) // 2
    base.alpha_composite(logo, (lx, ly))

    brand_font = font(FONT_BOLD, 45)
    d.text((x + 170, y + 48), str(card["brand"]), font=brand_font, fill=(22, 31, 48, 255))
    draw_pill(d, (x + 170, y + 105), str(card["mode"]), accent)

    num_font = font(FONT_BOLD, 55)
    num = str(card["number"])
    num_w = d.textlength(num, font=num_font)
    d.text((x + w - 50 - num_w, y + 49), num, font=num_font, fill=(*accent, 255))

    body_font = font(FONT_REGULAR, 37)
    emoji_font = font(FONT_EMOJI, 37)
    max_width = w - 104
    lines = layout_text(d, str(card["text"]), body_font, max_width)
    line_h = 59
    para_gap = 24
    tx = x + 52
    ty = y + 216
    start_y = ty
    for line in lines:
        if line is None:
            ty += para_gap
            continue
        draw_rich_line(d, (tx, ty), line, body_font, emoji_font, (45, 56, 76, 255))
        ty += line_h

    bottom = y + h - 44
    if ty > bottom:
        raise RuntimeError(f"Text overflow in {card['brand']}: used to {ty}, limit {bottom}")
    return {"text_top": start_y, "text_bottom": ty, "limit": bottom, "line_count": sum(line is not None for line in lines)}


def main() -> None:
    base = vertical_gradient((W, H), BG_TOP, BG_BOTTOM).convert("RGBA")

    # Keep the IP interaction as supporting context: small, brightened, and secondary to the four cards.
    hero = cover(Image.open(ASSETS / "four-way-ai-hero.png").convert("RGB"), (1320, 860))
    hero = ImageEnhance.Brightness(hero).enhance(1.28)
    hero = Image.blend(hero, Image.new("RGB", hero.size, (238, 245, 255)), 0.34).convert("RGBA")
    left_mask = Image.new("L", hero.size, 255)
    lm = ImageDraw.Draw(left_mask)
    for x in range(280):
        lm.line((x, 0, x, hero.height), fill=round(255 * (x / 280) ** 1.25))
    bottom_mask = Image.new("L", hero.size, 255)
    bm = ImageDraw.Draw(bottom_mask)
    for y in range(610, hero.height):
        bm.line((0, y, hero.width, y), fill=round(255 * (1 - (y - 610) / (hero.height - 610)) ** 1.45))
    hero.putalpha(ImageChops.multiply(left_mask, bottom_mask))
    base.alpha_composite(hero, (1080, 0))

    d = ImageDraw.Draw(base)
    kicker_font = font(FONT_BOLD, 30)
    title_font = font(FONT_BOLD, 76)
    subtitle_font = font(FONT_REGULAR, 31)
    d.rounded_rectangle((92, 70, 460, 127), radius=28, fill=(226, 237, 252, 255), outline=(105, 139, 187, 255), width=2)
    d.text((121, 79), "GSAP SKILLS · 文案横评", font=kicker_font, fill=(50, 73, 109, 255))
    d.text((88, 173), "同一提示词，4 个 AI", font=title_font, fill=(21, 35, 58, 255))
    d.text((88, 270), "写出了什么差别？", font=title_font, fill=(21, 35, 58, 255))
    d.text((94, 388), "同一套内容 · 同一提示词 · 四段输出原文完整保留", font=subtitle_font, fill=(78, 99, 132, 255))

    # The small label explains the character's action while keeping the comparison itself dominant.
    note_font = font(FONT_BOLD, 27)
    note = "拉动一次 → 四路输出"
    note_bbox = d.textbbox((0, 0), note, font=note_font)
    note_w = note_bbox[2] - note_bbox[0] + 46
    note_x = 1320
    d.rounded_rectangle((note_x, 545, note_x + note_w, 606), radius=30, fill=(255, 255, 255, 245), outline=(111, 142, 186, 255), width=2)
    d.text((note_x + 23, 556), note, font=note_font, fill=(51, 75, 111, 255))

    # A compact four-color key visually hands the hero's outputs to the four comparison cards.
    key_y = 635
    key_font = font(FONT_BOLD, 26)
    key_items = [("01", 92), ("02", 660), ("03", 1228), ("04", 1796)]
    for (label, x), card in zip(key_items, CARDS, strict=True):
        accent = card["accent"]
        assert isinstance(accent, tuple)
        d.rounded_rectangle((x, key_y, x + 490, key_y + 12), radius=6, fill=(*accent, 255))
        d.text((x, key_y - 42), f"{label}  {card['brand']}", font=key_font, fill=(52, 66, 88, 255))

    card_w, card_h = 1125, 1310
    positions = [(55, 720), (1220, 720), (55, 2070), (1220, 2070)]
    metrics = []
    for card, pos in zip(CARDS, positions, strict=True):
        metrics.append(draw_card(base, card, pos, (card_w, card_h)))

    # Footer/source marker. The two outputs that include the URL keep it verbatim inside their own cards.
    footer_font = font(FONT_REGULAR, 27)
    footer_bold = font(FONT_BOLD, 28)
    d = ImageDraw.Draw(base)
    d.text((70, 3494), "对比说明：", font=footer_bold, fill=(49, 66, 91, 255))
    d.text((210, 3494), "仅重新排版，不删改、不概括四个 AI 的输出内容。", font=footer_font, fill=(91, 111, 142, 255))
    source = "github.com/greensock/gsap-skills"
    sw = d.textlength(source, font=footer_font)
    d.text((W - 70 - sw, 3494), source, font=footer_font, fill=(91, 111, 142, 255))

    base.convert("RGB").save(OUT, quality=96, optimize=True)
    print(f"saved={OUT}")
    for card, metric in zip(CARDS, metrics, strict=True):
        print(f"{card['brand']}: {metric}")


if __name__ == "__main__":
    main()
