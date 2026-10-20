"""NatTypeTester 图标生成器。

概念：一条双向箭头从虚线墙里凿穿过去 —— UDP 打洞（hole punching）。
左端绿色（内网 / 发起），右端橙色（公网 / 对端），中间虚线是 NAT 边界。

输出：
  app.ico            多尺寸图标（16/24/32/48/64/128/256）
  icon-preview.png   512px 预览
"""
from PIL import Image, ImageDraw, ImageFilter
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_ICO = os.path.join(HERE, "..", "NatTypeTester", "app.ico")
PIC = os.path.join(HERE, "..", "pic")

S = 1024            # 超采样画布
R = 208             # 圆角半径

C_TOP = (0x28, 0x6D, 0xF0)      # 亮蓝
C_BOT = (0x14, 0x2A, 0x66)      # 深蓝
C_LEFT = (0x34, 0xD3, 0x99)     # 内网端 绿
C_RIGHT = (0xFF, 0xB2, 0x24)    # 公网端 橙


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_bg():
    grad = Image.new("RGB", (S, S))
    px = grad.load()
    for y in range(S):
        for x0 in range(0, S, 8):
            t = (x0 * 0.30 + y * 0.70) / S
            c = lerp(C_TOP, C_BOT, min(max(t, 0.0), 1.0))
            for k in range(8):
                px[min(x0 + k, S - 1), y] = c
    return grad.convert("RGBA")


def main():
    base = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], R, fill=255)
    base.paste(make_bg(), (0, 0), mask)

    d = ImageDraw.Draw(base, "RGBA")
    # 内圈细高光，让边缘在浅色桌面上也立得住
    d.rounded_rectangle([10, 10, S - 11, S - 11], R - 8, outline=(255, 255, 255, 55), width=8)

    cy = S // 2

    # ---- 虚线墙：6 段竖条，代表 NAT 边界 ----
    wall_w, seg_h, gap, segs = 48, 62, 40, 8
    total = segs * seg_h + (segs - 1) * gap
    top = cy - total // 2
    for i in range(segs):
        y0 = top + i * (seg_h + gap)
        d.rounded_rectangle(
            [S // 2 - wall_w // 2, y0, S // 2 + wall_w // 2, y0 + seg_h],
            wall_w // 2, fill=(255, 255, 255, 120),
        )

    # ---- 穿透通道：横线 + 两端箭头 ----
    line_w = 52
    x_l, x_r = 168, 856
    d.line([x_l, cy, x_r, cy], fill=(255, 255, 255, 248), width=line_w)

    def head(tip_x, direction, color):
        L, W = 142, 124
        d.polygon(
            [(tip_x, cy), (tip_x - direction * L, cy - W), (tip_x - direction * L, cy + W)],
            fill=color + (255,),
        )

    head(x_l, -1, C_LEFT)      # 左尖朝左
    head(x_r, 1, C_RIGHT)      # 右尖朝右

    # ---- 两端光晕，增加层次 ----
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([x_l - 118, cy - 118, x_l + 118, cy + 118], fill=C_LEFT + (120,))
    gd.ellipse([x_r - 118, cy - 118, x_r + 118, cy + 118], fill=C_RIGHT + (120,))
    base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(46)))

    # 光晕压暗了主干，重画一遍前景保证锐利
    d.line([x_l, cy, x_r, cy], fill=(255, 255, 255, 248), width=line_w)
    head(x_l, -1, C_LEFT)
    head(x_r, 1, C_RIGHT)

    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    imgs = [base.resize(s, Image.LANCZOS) for s in sizes]
    imgs[-1].save(OUT_ICO, format="ICO", sizes=sizes, append_images=imgs[:-1])

    # 仓库里的预览图
    os.makedirs(PIC, exist_ok=True)
    base.resize((512, 512), Image.LANCZOS).save(os.path.join(PIC, "icon.png"))

    # 各尺寸实拍对照（上排原尺寸，下排 4x 最近邻放大，方便看小尺寸糊不糊）
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
