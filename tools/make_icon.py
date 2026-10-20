"""NatTypeTester 图标生成器。

复刻 1.1 版窗口上那个图标 —— 即 .NET WinForms 的默认 Form 图标：
一块浅灰面板上排着白/金/红/蓝几个控件块。

原图只有 32x32，直接放大必然糊，所以按 32 网格的原始布局与取色重新矢量绘制，
以 64 倍超采样（2048x2048）画完再 LANCZOS 降采样到各尺寸。

输出：
  ../NatTypeTester/app.ico    多尺寸图标（16/24/32/48/64/128/256）
  ../pic/icon.png             512px 预览
  ../pic/icon-sizes.png       各尺寸渲染对照
"""
from PIL import Image, ImageDraw
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ICO = os.path.join(HERE, "..", "NatTypeTester", "app.ico")
PIC = os.path.join(HERE, "..", "pic")

GRID = 32          # 原始图标网格
SS = 64            # 每格超采样倍数 -> 2048 画布


def r(v):
    return int(round(v * SS))


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgrad(w, h, top, bottom):
    g = Image.new("RGB", (1, h))
    for i in range(h):
        g.putpixel((0, i), lerp(top, bottom, i / max(h - 1, 1)))
    return g.resize((w, h))


def block(base, box, radius, top, bottom, border, bw=0.55, gloss=0.0):
    """在 base(RGBA) 上画一个带描边、纵向渐变、可选顶部高光的圆角块。"""
    x0, y0, x1, y1 = (r(v) for v in box)
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return
    rad = max(int(radius * SS), 1)

    fill = vgrad(w, h, top, bottom)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], rad, fill=255)
    base.paste(fill, (x0, y0), mask)

    d = ImageDraw.Draw(base, "RGBA")
    if gloss > 0:                                   # 顶部高光：越往上越亮，向下淡出
        gh = int(h * 0.55)
        gmask = Image.new("L", (w, gh), 0)
        ImageDraw.Draw(gmask).rounded_rectangle([0, 0, w - 1, gh * 2], rad, fill=255)
        fade = Image.new("L", (1, gh))
        for i in range(gh):
            fade.putpixel((0, i), int(255 * gloss * (1 - i / max(gh - 1, 1)) ** 1.6))
        fade = fade.resize((w, gh))
        glaze = Image.new("RGBA", (w, gh), (255, 255, 255, 255))
        import PIL.ImageChops as chops
        glaze.putalpha(chops.multiply(gmask, fade))
        base.alpha_composite(glaze, (x0, y0))

    if bw > 0:
        d.rounded_rectangle(
            [x0, y0, x1 - 1, y1 - 1], rad,
            outline=border + (255,), width=max(int(bw * SS), 1),
        )


def main():
    S = GRID * SS
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(base, "RGBA")

    # ---- 面板本体：浅灰底 + 淡灰圆角描边 ----
    block(base, (3, 2, 31, 30), 2.0, (0xF7, 0xF7, 0xF7), (0xE9, 0xE9, 0xE9), (0xC9, 0xC9, 0xC9), bw=0.5)

    # ---- 左上：白色输入框 ----
    block(base, (5, 4, 12.6, 9.6), 1.0, (0xFF, 0xFF, 0xFF), (0xF2, 0xF2, 0xF2), (0xBC, 0xBC, 0xBC), bw=0.45)

    # ---- 右上：金色按钮（最大的一块）----
    block(base, (14, 3, 29.4, 17.4), 1.4, (0xFF, 0xE9, 0x9C), (0xD9, 0xA5, 0x14), (0x9C, 0x74, 0x0C), bw=0.6, gloss=0.35)

    # ---- 左中：红色按钮 ----
    block(base, (5, 11, 12.6, 21.4), 1.2, (0xE0, 0x4A, 0x2A), (0x92, 0x1F, 0x0C), (0x74, 0x16, 0x08), bw=0.6, gloss=0.30)

    # ---- 右下：蓝色按钮 ----
    block(base, (14, 19, 25.4, 28.4), 1.4, (0x9C, 0xC4, 0xFF), (0x3F, 0x63, 0xB0), (0x2E, 0x4A, 0x8A), bw=0.6, gloss=0.35)

    # ---- 左下：两个复选框 ----
    block(base, (5, 24, 8.6, 27.6), 0.5, (0xFF, 0xFF, 0xFF), (0xE8, 0xE8, 0xE8), (0xBC, 0xBC, 0xBC), bw=0.4)
    block(base, (9, 24, 12.6, 27.6), 0.5, (0xFF, 0xFF, 0xFF), (0xE8, 0xE8, 0xE8), (0xBC, 0xBC, 0xBC), bw=0.4)

    # ---- 右下角：白色竖条（滚动条）----
    block(base, (27, 20, 29.6, 27.6), 0.5, (0xFF, 0xFF, 0xFF), (0xE8, 0xE8, 0xE8), (0xBC, 0xBC, 0xBC), bw=0.4)

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    imgs = {s: base.resize(s, Image.LANCZOS) for s in sizes}

    # 32 及以下用原图同尺寸重绘的结果，避免细描边在缩小时发糊
    imgs[(256, 256)].save(OUT_ICO, format="ICO", sizes=sizes,
                          append_images=[imgs[s] for s in sizes[:-1]])

    os.makedirs(PIC, exist_ok=True)
    base.resize((512, 512), Image.LANCZOS).save(os.path.join(PIC, "icon.png"))

    checks = [16, 24, 32, 48, 64]
    sheet = Image.new("RGBA", (len(checks) * 140 + 10, 300), (245, 245, 248, 255))
    x = 10
    for s in checks:
        im = base.resize((s, s), Image.LANCZOS)
        sheet.alpha_composite(im, (x, 20))
        sheet.alpha_composite(im.resize((128, 128), Image.NEAREST), (x, 150))
        x += 140
    sheet.save(os.path.join(PIC, "icon-sizes.png"))

    print("ok:", sizes, "->", os.path.normpath(OUT_ICO))


if __name__ == "__main__":
    main()
