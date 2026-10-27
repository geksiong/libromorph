"""
libromorph.cover: Ebook cover image generator and handler.
Loads custom cover images or dynamically renders typographic covers
matching book genre themes using Pillow.
"""

import os
from PIL import Image, ImageDraw, ImageFont


THEME_PALETTES = {
    "classic-novel": {
        "bg": (245, 240, 230),
        "primary": (40, 30, 20),
        "accent": (160, 50, 45),
        "border": (190, 165, 130),
        "sub": (90, 80, 70),
    },
    "technical": {
        "bg": (26, 32, 44),
        "primary": (255, 255, 255),
        "accent": (79, 140, 255),
        "border": (45, 55, 72),
        "sub": (160, 174, 192),
    },
    "cjk-vertical": {
        "bg": (248, 244, 236),
        "primary": (30, 30, 32),
        "accent": (198, 40, 40),
        "border": (198, 40, 40),
        "sub": (100, 95, 90),
    },
    "modern-minimal": {
        "bg": (255, 255, 255),
        "primary": (17, 24, 39),
        "accent": (14, 165, 233),
        "border": (229, 231, 235),
        "sub": (107, 114, 128),
    },
    "fantasy-vintage": {
        "bg": (44, 30, 22),
        "primary": (230, 215, 175),
        "accent": (212, 175, 55),
        "border": (170, 130, 60),
        "sub": (185, 170, 140),
    }
}


def _get_font(size: int, bold: bool = False):
    """Attempt to load a system TTF font, fallback to default font."""
    font_candidates = [
        # Linux standard fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_cover_image(
    output_path: str,
    title: str,
    subtitle: str = "",
    author: str = "",
    theme: str = "classic-novel",
    width: int = 1600,
    height: int = 2400
) -> str:
    """
    Generates a 1600x2400 standard high-resolution ebook cover image
    styled with decorative borders and typography matching the chosen theme.
    """
    palette = THEME_PALETTES.get(theme, THEME_PALETTES["classic-novel"])
    img = Image.new("RGB", (width, height), color=palette["bg"])
    draw = ImageDraw.Draw(img)

    # Outer decorative frame
    margin = 80
    border_width = 8
    draw.rectangle(
        [(margin, margin), (width - margin, height - margin)],
        outline=palette["border"],
        width=border_width
    )
    # Inner thin border
    inner_margin = margin + 24
    draw.rectangle(
        [(inner_margin, inner_margin), (width - inner_margin, height - inner_margin)],
        outline=palette["border"],
        width=2
    )

    # Corner ornaments
    corner_len = 60
    for cx, cy in [
        (inner_margin, inner_margin),
        (width - inner_margin, inner_margin),
        (inner_margin, height - inner_margin),
        (width - inner_margin, height - inner_margin)
    ]:
        draw.ellipse([(cx - 10, cy - 10), (cx + 10, cy + 10)], fill=palette["accent"])

    # Fonts
    font_title = _get_font(size=110, bold=True)
    font_sub = _get_font(size=55, bold=False)
    font_author = _get_font(size=65, bold=True)
    font_badge = _get_font(size=40, bold=False)

    # Accent decorative bar
    center_y = int(height * 0.38)
    draw.line([(width // 4, center_y - 180), (3 * width // 4, center_y - 180)], fill=palette["accent"], width=4)

    # Draw Title (with word-wrap)
    words = title.split()
    lines = []
    current_line = []
    for w in words:
        current_line.append(w)
        test_str = " ".join(current_line)
        bbox = draw.textbbox((0, 0), test_str, font=font_title)
        if (bbox[2] - bbox[0]) > (width - 2 * margin - 160):
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [w]
    if current_line:
        lines.append(" ".join(current_line))

    y_text = center_y - 120
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        w_line = bbox[2] - bbox[0]
        x_text = (width - w_line) // 2
        draw.text((x_text, y_text), line, font=font_title, fill=palette["primary"])
        y_text += (bbox[3] - bbox[1]) + 40

    # Draw Subtitle
    if subtitle:
        y_text += 20
        draw.line([(width // 3, y_text), (2 * width // 3, y_text)], fill=palette["accent"], width=3)
        y_text += 50
        bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
        x_sub = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x_sub, y_text), subtitle, font=font_sub, fill=palette["sub"])

    # Center emblem / diamond
    emblem_y = int(height * 0.62)
    draw.polygon([
        (width // 2, emblem_y - 40),
        (width // 2 + 40, emblem_y),
        (width // 2, emblem_y + 40),
        (width // 2 - 40, emblem_y)
    ], fill=palette["accent"])

    # Draw Author at bottom
    if author:
        author_y = int(height * 0.82)
        bbox = draw.textbbox((0, 0), author, font=font_author)
        x_author = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x_author, author_y), author, font=font_author, fill=palette["primary"])

        badge_text = "EDITION · LIBROMORPH"
        bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
        x_b = (width - (bbox_b[2] - bbox_b[0])) // 2
        draw.text((x_b, author_y + 90), badge_text, font=font_badge, fill=palette["sub"])

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    return output_path
