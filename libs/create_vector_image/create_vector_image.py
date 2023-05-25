import os
import pathlib

import numpy as np
import svgwrite
import pickle
import cv2
from PIL import Image
from svgwrite.text import TSpan
import base64

from ..manga_image_translator.manga_translator.text_rendering import fg_bg_compare, resize_regions_to_font_size
from ..manga_image_translator.manga_translator.text_rendering.text_render import calc_horizontal, \
    compact_special_symbols, put_char_horizontal, add_color, set_font

FONT = "Comic Sans MS"


def get_image(path, ctx):
    if ctx.get("base64_vector_file"):
        file_extension = pathlib.Path(path).suffix[1:]
        with open(path, 'rb') as f:  # open binary file in read mode
            image_64_encode = base64.encodebytes(f.read())

        return f"data:image/{file_extension};base64,{image_64_encode.decode('utf-8')}"
    else:
        return path


# def create_psd(psd_file, ctx):
#     from psd_tools import PSDImage
#     assert Exception("Function 'create_psd' is not work")
#     psd = PSDImage.new("rgb", (100, 100), (255, 255, 255))
#     psd.composite().save('example.png')
#     # with open("example.psd", "wb") as f_psd:
#     psd.save("example2.ps")
#     psd2 = PSDImage.open("example2.psd")
#     psd2.composite().save('example2.png')
#     for layer in psd:
#         print(layer)
#         layer_image = layer.composite()
#         layer_image.save('%s.png' % layer.name)
#
#     with open(psd_file, "w") as f_psd:
#         for reg in ctx.text_regions:
#             pass

def create_vector_file(file_path, ctx):
    create_svg(file_path, ctx)


def create_svg(svg_file, _ctx):
    ctx = dict(_ctx)
    # data = [svg_file, dict(ctx)]
    # with open(svg_file + ".ctx", "wb") as f:
    #     pickle.dump(data, f)
    img_size = ctx["input"].size
    dwg = svgwrite.Drawing(svg_file, debug=True, size=img_size)
    if ctx.get("cleaned_image_path"):
        if os.path.exists(ctx.get("cleaned_image_path")):
            dwg.add(dwg.image(get_image(ctx["cleaned_image_path"], ctx), size=img_size, id="cleaned_image"))
        else:
            dwg.add(dwg.image(get_image(ctx["original_image_path"], ctx), size=img_size, id="cleaned_image-notext"))

    if ctx["translate_vector_file"] and ctx["result"]:
        dwg.add(dwg.image(get_image(ctx["result_image_path"], ctx), size=img_size, id="translated_image"))
        img = cv2.imread(ctx["result_image_path"])
        render_translate_svg(dwg, ctx, img)
    # else:
    dwg.add(dwg.image(get_image(ctx["original_image_path"], ctx), size=img_size, id="original_image"))
    render_original_svg(dwg, ctx)

    dwg.save()


def render_svg_region_translated(dwg, region, dst_points, alignment, font_size, font):
    fg, bg = region.get_font_colors()
    fg, bg = fg_bg_compare(fg, bg)
    fg = (0, 0, 255)

    middle_pts = (dst_points[:, [1, 2, 3, 0]] + dst_points) / 2
    norm_h = np.linalg.norm(middle_pts[:, 1] - middle_pts[:, 3], axis=1)
    norm_v = np.linalg.norm(middle_pts[:, 2] - middle_pts[:, 0], axis=1)
    r_orig = np.mean(norm_h / norm_v)
    print(dst_points)
    ox, oy = dst_points[0][0]

    text = region.translation
    width = round(norm_h[0])

    text = compact_special_symbols(text)
    bg_size = int(max(font_size * 0.07, 1)) if bg is not None else 0
    spacing_y = int(font_size * 0.2)

    # calc
    # print(width)
    line_text_list, line_width_list = calc_horizontal(font_size, text, width)
    # print(line_text_list, line_width_list)

    # make large canvas
    canvas_w = max(line_width_list) + (font_size + bg_size) * 2
    canvas_h = font_size * len(line_width_list) + spacing_y * (len(line_width_list) - 1) + (font_size + bg_size) * 2
    canvas_text = np.zeros((canvas_h, canvas_w), dtype=np.uint8)
    canvas_border = canvas_text.copy()

    # pen (x, y)
    pen_orig = [ox + font_size + bg_size, oy + font_size + bg_size]
    area = svgwrite.text.Text("")
    lines = ""
    # write stuff
    for line_text, line_width in zip(line_text_list, line_width_list):
        pen_line = pen_orig.copy()
        if alignment == 'center':
            pen_line[0] += (max(line_width_list) - line_width) // 2
        elif alignment == 'right':
            pen_line[0] += max(line_width_list) - line_width
        print(pen_line, line_text)
        lines += line_text + "\n"
        area.add(TSpan(line_text, insert=pen_line,
                       font_family=font, font_size=font_size, fill=f"rgb{tuple(fg)}"))
        # for c in line_text:
        #     offset_x = put_char_horizontal(font_size, c, pen_line, canvas_text, canvas_border, border_size=bg_size)
        #     pen_line[0] += offset_x
        pen_orig[1] += spacing_y + font_size
    # area = svgwrite.text.TextArea(lines, insert=pen_orig, font_family=FONT, font_size=font_size, fill=f"rgb{tuple(fg)}")

    dwg.add(area)
    # dwg.add(dwg.text(lines, insert=pen_orig,
    #                  font_family=FONT, font_size=font_size, fill=f"rgb{tuple(fg)}"))
    # colorize
    canvas_border = np.clip(canvas_border, 0, 255)
    line_box = add_color(canvas_text, fg, canvas_border, bg)

    # rect
    x, y, width, height = cv2.boundingRect(canvas_border)
    return line_box[y:y + height, x:x + width]


def render_svg_region_original(dwg, region, font_size, font):
    color_text = "red"
    area = svgwrite.text.Text("")
    offset_y = 0 if len(region.lines) < 2 else region.lines[1][0][1] - region.lines[0][0][1]
    for line_text, poses_line in zip(region.text, region.lines):
        pos = poses_line[0][0], poses_line[0][1] + offset_y
        area.add(TSpan(line_text, insert=pos,
                       font_family=font, font_size=font_size, fill=color_text))
    dwg.add(area)


def render_translate_svg(dwg, ctx, img):
    print("Render_translate_svg")
    text_regions = ctx["text_regions"]
    set_font(ctx["font_path"])
    font_path = FONT or ctx["font_path"]
    font_size = ctx["font_size"]
    font_size_offset = ctx["font_size_offset"]
    font_size_minimum = ctx["font_size_minimum"]

    dst_points_list = resize_regions_to_font_size(img, text_regions, font_size, font_size_offset, font_size_minimum)
    group = svgwrite.container.Group(id="translated-text")
    dwg.add(group)
    for region, dst_points in zip(text_regions, dst_points_list):
        render_svg_region_translated(group, region, dst_points, region.alignment, region.font_size, font_path)
        # render_svg_region_original(dwg, region, region.font_size)


def render_original_svg(dwg, ctx):
    text_regions = ctx["original_text_regions"]
    font_path = FONT or ctx["font_path"]
    group = svgwrite.container.Group(id="original-text")
    dwg.add(group)
    for region in text_regions:
        render_svg_region_original(group, region, region.font_size, font_path)


if __name__ == '__main__':
    with open("onepunch_man_172_12.jpg.svg.ctx", "rb") as f:
        data = pickle.load(f)
    svg_file, _ctx = data
    original_file = "1.png"
    _ctx["input"].save(original_file)
    svg_file = 'onepunch_man_172_12.svg'
    image_file = "onepunch_man_172_12.jpg"

    _img_size = _ctx["input"].size
    k = 1  # 1536 / _img_size[1]
    img_size = _img_size[0] * k, _img_size[1] * k

    print(img_size)
    offset_x = 350
    dwg = svgwrite.Drawing(svg_file, debug=True, size=img_size)
    dwg.add(dwg.image(original_file, size=img_size))

    img = cv2.imread(original_file)
    render_translate_svg(dwg, _ctx, img)
    # for reg in _ctx["text_regions"]:
    #     print("reg", reg)
    #     font_size, text, width = reg[""]
    #     line_text_list, line_width_list = calc_horizontal(font_size, text, width)
    #     dwg.add(dwg.text(title, insert=(0, y),
    #                      font_family="serif", font_size=font_size, fill='black'))
    #
    # # dwg.add(dwg.line((0, 0), (10, 0), stroke=svgwrite.rgb(10, 10, 16, '%')))

    dwg.save()
