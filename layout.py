from PIL import Image, ImageDraw, ImageFont
import textwrap


BG_COLOR = (245, 247, 252)
PANEL_COLOR = (17, 24, 39)
ACCENT_COLOR = (96, 165, 250)
MUTED_COLOR = (170, 184, 206)
TEXT_COLOR = (244, 247, 252)
CARD_COLOR = (31, 41, 55)

TITLE_FONT_SIZE = 20
META_FONT_SIZE = 14
BODY_FONT_SIZE = 16
LINE_HEIGHT = 22
CARD_GAP = 10
PANEL_PADDING = 16


def _safe_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _format_summary_blocks(summary_text):
    summary_text = " ".join((summary_text or "").split())
    if not summary_text:
        return []

    sentence_like = summary_text.replace(". ", ".|").replace("? ", "?|").replace("! ", "!|")
    parts = [part.strip() for part in sentence_like.split("|") if part.strip()]

    blocks = []
    current = ""
    for part in parts:
        candidate = f"{current} {part}".strip()
        if current and len(candidate) > 85:
            blocks.append(current)
            current = part
        else:
            current = candidate

    if current:
        blocks.append(current)

    if not blocks:
        blocks = textwrap.wrap(summary_text, width=70)

    return blocks[:4]


def _wrap_blocks(summary_text, vertical):
    blocks = _format_summary_blocks(summary_text)
    wrap_width = 24 if vertical else 62
    return [textwrap.wrap(block, width=wrap_width) or [block] for block in blocks]


def _measure_panel_size(summary_text, frame_w, frame_h, vertical):
    wrapped_blocks = _wrap_blocks(summary_text, vertical)

    header_height = 14 + 28 + 16 + 30 + 24
    empty_height = header_height + 30

    if not wrapped_blocks:
        needed_height = empty_height
    else:
        body_height = 0
        for lines in wrapped_blocks:
            card_height = 18 + (len(lines) * LINE_HEIGHT)
            body_height += card_height + CARD_GAP
        needed_height = header_height + body_height + 16

    if vertical:
        panel_w = max(int(frame_w * 0.28), 280)
        panel_h = max(frame_h, needed_height)
    else:
        min_panel_h = int(frame_h * 0.32)
        panel_h = max(min_panel_h, needed_height)
        panel_w = frame_w

    return panel_w, panel_h, wrapped_blocks


def _draw_summary_content(draw, panel_box, timestamp, wrapped_blocks, vertical):
    left, top, right, bottom = panel_box

    title_font = _safe_font(TITLE_FONT_SIZE)
    meta_font = _safe_font(META_FONT_SIZE)
    body_font = _safe_font(BODY_FONT_SIZE)

    chip_w = 110 if vertical else 120
    chip_h = 28
    chip_x = left + PANEL_PADDING
    chip_y = top + 14
    draw.rounded_rectangle(
        [chip_x, chip_y, chip_x + chip_w, chip_y + chip_h],
        radius=12,
        fill=(42, 56, 86),
    )
    draw.text((chip_x + 12, chip_y + 7), f"Time: {int(timestamp)}s", fill=MUTED_COLOR, font=meta_font)

    title_y = chip_y + chip_h + 16
    draw.text((left + PANEL_PADDING, title_y), "AI Study Notes", fill=TEXT_COLOR, font=title_font)

    accent_y = title_y + 30
    draw.rounded_rectangle(
        [left + PANEL_PADDING, accent_y, left + PANEL_PADDING + 60, accent_y + 5],
        radius=3,
        fill=ACCENT_COLOR,
    )

    if not wrapped_blocks:
        draw.text(
            (left + PANEL_PADDING, accent_y + 18),
            "No summary available for this slide.",
            fill=MUTED_COLOR,
            font=body_font,
        )
        return

    body_y = accent_y + 24
    for lines in wrapped_blocks:
        card_height = 18 + (len(lines) * LINE_HEIGHT)
        draw.rounded_rectangle(
            [left + 14, body_y, right - 14, body_y + card_height],
            radius=14,
            fill=CARD_COLOR,
        )

        bullet_x = left + 28
        bullet_y = body_y + 13
        draw.ellipse([bullet_x, bullet_y, bullet_x + 8, bullet_y + 8], fill=ACCENT_COLOR)

        text_x = bullet_x + 18
        text_y = body_y + 8
        for line in lines:
            draw.text((text_x, text_y), line, fill=TEXT_COLOR, font=body_font)
            text_y += LINE_HEIGHT

        body_y += card_height + CARD_GAP


def create_frame_with_summary(pil_image, summary_text, timestamp, position="right"):
    """
    Takes a frame and summary text.
    Returns a new image with the summary panel placed around the frame.
    """
    frame_w, frame_h = pil_image.size
    position = (position or "right").lower()

    if position not in {"top", "right", "left", "bottom"}:
        position = "right"

    vertical = position in {"left", "right"}
    panel_w, panel_h, wrapped_blocks = _measure_panel_size(summary_text, frame_w, frame_h, vertical)

    if vertical:
        total_w = frame_w + panel_w
        total_h = max(frame_h, panel_h)
        canvas = Image.new("RGB", (total_w, total_h), color=BG_COLOR)
        panel_box = (0, 0, panel_w, total_h) if position == "left" else (frame_w, 0, total_w, total_h)
        frame_pos = (panel_w, 0) if position == "left" else (0, 0)
        divider = [panel_w, 0, panel_w, total_h] if position == "left" else [frame_w, 0, frame_w, total_h]
    else:
        total_w = frame_w
        total_h = frame_h + panel_h
        canvas = Image.new("RGB", (total_w, total_h), color=BG_COLOR)
        panel_box = (0, 0, frame_w, panel_h) if position == "top" else (0, frame_h, frame_w, total_h)
        frame_pos = (0, panel_h) if position == "top" else (0, 0)
        divider = [0, panel_h, frame_w, panel_h] if position == "top" else [0, frame_h, frame_w, frame_h]

    canvas.paste(pil_image, frame_pos)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle(panel_box, fill=PANEL_COLOR)
    draw.line(divider, fill=(79, 94, 122), width=2)
    _draw_summary_content(draw, panel_box, timestamp, wrapped_blocks, vertical)

    return canvas


if __name__ == "__main__":
    test_frame = Image.new("RGB", (1280, 720), color=(100, 149, 237))
    summary = (
        "The lecture explains how red blood cells are produced rapidly in the body. "
        "It also compares that rate with how much garbage the world creates every minute. "
        "The idea is to make biological scale easier to understand."
    )
    result = create_frame_with_summary(test_frame, summary, timestamp=5, position="top")
    result.save("test_layout.jpg")
    print("Saved test_layout.jpg")
