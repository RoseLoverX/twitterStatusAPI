import datetime as dtm
from typing import Union, cast
import pytz
from hyphen.textwrap2 import fill
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path
from hyphen import Hyphenator
from PIL import Image, ImageFont

PATH_PREFIX = "../" if Path("../headers").is_dir() else ""

TEMPLATE_DIRECTORY = f"{PATH_PREFIX}templates"
HEADER_TEMPLATE = f"{TEMPLATE_DIRECTORY}/header.png"
FOOTER_TEMPLATE = f"{TEMPLATE_DIRECTORY}/footer.png"
BODY_TEMPLATE = f"{TEMPLATE_DIRECTORY}/body.png"
VERIFIED_TEMPLATE = f"{TEMPLATE_DIRECTORY}/verified.png"
VERIFIED_IMAGE = Image.open(VERIFIED_TEMPLATE)
VERIFIED_IMAGE.thumbnail((27, 27))
BACKGROUND = "#16202cff"
TEXT_MAIN = "#ffffff"
TEXT_SECONDARY = "#8d99a5ff"
FONTS_DIRECTORY = f"{PATH_PREFIX}fonts"
FONT_HEAVY = f"{FONTS_DIRECTORY}/seguibl.ttf"
FONT_SEMI_BOLD = f"{FONTS_DIRECTORY}/seguisb.ttf"
FALLBACK_PROFILE_PICTURE = "logo/TwitterStatusBot-rectangle.png"
HEADERS_DIRECTORY = f"{PATH_PREFIX}headers"
FOOTER_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 24)
USER_NAME_FONT = ImageFont.truetype(FONT_HEAVY, 24)
USER_HANDLE_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 23)
BIG_TEXT_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 70)
SMALL_TEXT_FONT = ImageFont.truetype(FONT_SEMI_BOLD, 36)
HYPHENATOR = Hyphenator("en_US")


from http.server import BaseHTTPRequestHandler
import json
 
class handler(BaseHTTPRequestHandler):
 
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return

    def do_POST(self):
        # extract data from the request
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        j = json.loads(post_data)
        sticker_file = build_sticker(j.get("text", "Hi"), j.get("name", "N/A"), j.get("username", j.get("name", "N/A")), j.get("user_id", "123456"), j.get('timezone', 'UTC'))
        b = sticker_file.tobytes()
        self.send_response(200)
        self.send_header('Content-type','image/png')
        self.end_headers()
        self.wfile.write(b)
        return





def mask_circle_transparent(image: Union[Image.Image, str]) -> Image.Image:
    if isinstance(image, str):
        image = Image.open(image)
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)
    mask = mask.filter(ImageFilter.DETAIL())
    result = image.copy()
    result.putalpha(mask)
    return result


def shorten_text(text: str, max_width: int, font: ImageFont.ImageFont) -> str:
    (width, _), _ = font.font.getsize(text)
    i = 0
    short_text = text
    while width > max_width:
        i += 1
        short_text = f"{text[:-i]}..."
        (width, _), _ = font.font.getsize(short_text)
    return short_text


def build_footer(timezone: str = "UTC") -> Image.Image:
    now = dtm.datetime.now(tz=pytz.timezone(timezone))
    date_string = " ".join(
        [now.strftime("%I:%M %p"), "•", now.strftime("%b %d, %Y")])
    # Offsets
    top = 28
    left = 27
    image = Image.open(FOOTER_TEMPLATE)
    draw = ImageDraw.Draw(image)
    draw.text((left, top), date_string, fill=TEXT_SECONDARY, font=FOOTER_FONT)
    image.save("nib.png", "PNG")
    return image


def build_header(name, username, user_id, user_picture: Image.Image = None) -> Image.Image:
    # Get Background
    background: Image = Image.open(HEADER_TEMPLATE)
    up_left = 25
    up_top = 25
    if not user_picture:
        user_picture = mask_circle_transparent(FALLBACK_PROFILE_PICTURE)
    # crop a centered square
    if not user_picture.width == user_picture.height:
        side = min(user_picture.width, user_picture.height)
        left = (user_picture.width - side) // 2
        upper = (user_picture.height - side) // 2
        user_picture = user_picture.crop(
            (left, upper, left + side, upper + side))
    # make it a circle an small
    user_picture = mask_circle_transparent(user_picture)
    user_picture.thumbnail((78, 78))
    background.alpha_composite(user_picture, (up_left, up_top))
    draw = ImageDraw.Draw(background)
    # Add user name
    un_left = 118
    un_top = 30
    user_name = shorten_text(cast(str, name), 314, USER_NAME_FONT)
    draw.text((un_left, un_top), user_name,
              fill=TEXT_MAIN, font=USER_NAME_FONT)
    # Add user handle
    uh_left = 118
    uh_top = 62
    user_handle = shorten_text(
        f"@{username}", 370, USER_HANDLE_FONT
    )
    draw.text((uh_left, uh_top), user_handle,
              fill=TEXT_SECONDARY, font=USER_HANDLE_FONT)
    # Add verified symbol
    (un_width, _), _ = USER_NAME_FONT.font.getsize(user_name)
    v_left = un_left + un_width + 4
    v_top = 34
    background.alpha_composite(VERIFIED_IMAGE, (v_left, v_top))
    # Save for later use
    background.save(f"{HEADERS_DIRECTORY}/{user_id}.png")
    return background


def build_body(text: str, text_direction: str) -> Image.Image:
    max_chars_per_line = 26
    max_pixels_per_line = 450
    kwargs = {"direction": text_direction}
    left = 27 if text_direction == "ltr" else 512 - 27
    kwargs["anchor"] = "la" if text_direction == "ltr" else "ra"
    kwargs["align"] = "left" if text_direction == "ltr" else "right"
    kwargs["fill"] = TEXT_MAIN

    def single_line_text(position, text_, font, background_):  # type: ignore
        _, height = font.getsize(text_)
        background_ = background_.resize((background_.width, height + top + 1))
        draw = ImageDraw.Draw(background_)
        draw.text(position, text_, font=font, **kwargs)
        return background_

    def multiline_text(position, text_, background_):  # type: ignore
        spacing = 4
        _, height = SMALL_TEXT_FONT.getsize_multiline(text_, spacing=spacing)
        background_ = background_.resize((background_.width, height - spacing))
        draw = ImageDraw.Draw(background_)
        draw.multiline_text(
            position, text_, font=SMALL_TEXT_FONT, spacing=spacing, **kwargs)
        return background_
    background = Image.open(BODY_TEMPLATE)
    if "\n" in text:
        top = -12
        lines = text.split("\n")
        try:
            text = "\n".join(
                [fill(line, max_chars_per_line, use_hyphenator=HYPHENATOR)
                 for line in lines]
            )
        except BaseException as exc:
            print(exc)
        background = multiline_text((left, top), text, background)
    else:
        width, _ = BIG_TEXT_FONT.getsize(text)
        top = -12
        if width > max_pixels_per_line:
            width, _ = SMALL_TEXT_FONT.getsize(text)
            if width > max_pixels_per_line:
                try:
                    text = fill(text, max_chars_per_line,
                                use_hyphenator=HYPHENATOR)
                except Exception as exc:
                    print(exc)
                background = multiline_text((left, top), text, background)
            else:
                background = single_line_text(
                    (left, top), text, SMALL_TEXT_FONT, background)
        else:
            top = -26
            background = single_line_text(
                (left, top), text, BIG_TEXT_FONT, background)
    return background


def build_sticker(text: str, name, username, user_id, timezone) -> Image.Image:
    header = build_header(name, username, user_id)
    body = build_body(text, text_direction="ltr")
    footer = build_footer(timezone=timezone)
    sticker = Image.new(
        "RGBA", (512, header.height + body.height + footer.height))
    sticker.paste(header, (0, 0))
    sticker.paste(body, (0, header.height))
    sticker.paste(footer, (0, header.height + body.height))
    sticker.thumbnail((512, 512))
    return sticker

