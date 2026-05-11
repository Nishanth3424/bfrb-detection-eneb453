"""Generate the PWA icons (192 + 512) using PIL.  Run once."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def render_icon(size: int, path: str) -> None:
    img = Image.new("RGBA", (size, size), (15, 17, 23, 255))   # --bg
    d = ImageDraw.Draw(img)

    # Outer rounded square
    pad = int(size * 0.07)
    radius = int(size * 0.22)
    d.rounded_rectangle((pad, pad, size - pad, size - pad),
                        radius=radius, fill=(26, 29, 39, 255),
                        outline=(99, 102, 241, 255), width=max(2, size // 64))

    # Concentric pulse rings (the "alert" motif of the app)
    cx, cy = size / 2, size / 2 + size * 0.06
    r0 = size * 0.30
    for i, alpha in enumerate([180, 100, 60]):
        r = r0 + i * size * 0.05
        d.ellipse((cx - r, cy - r, cx + r, cy + r),
                  outline=(239, 68, 68, alpha), width=max(2, size // 96))

    # Hand silhouette (simplified) leading to a target
    hand_color = (99, 102, 241, 255)
    sx = size * 0.52
    sy = size * 0.78
    fingers = [
        (sx,            sy,            sx,            sy - size * 0.15),
        (sx - size*.06, sy + size*.02, sx - size*.06, sy - size*.18),
        (sx - size*.12, sy + size*.04, sx - size*.12, sy - size*.16),
        (sx - size*.18, sy + size*.07, sx - size*.18, sy - size*.10),
    ]
    for x0, y0, x1, y1 in fingers:
        d.line((x0, y0, x1, y1), fill=hand_color, width=max(2, size // 36))
        d.ellipse((x1 - size*.022, y1 - size*.022, x1 + size*.022, y1 + size*.022),
                  fill=hand_color)

    # Center bullseye
    bs = size * 0.06
    d.ellipse((cx - bs, cy - bs, cx + bs, cy + bs),
              fill=(239, 68, 68, 255))

    # Letter mark
    try:
        font = ImageFont.truetype("arialbd.ttf", int(size * 0.18))
    except Exception:
        font = ImageFont.load_default()
    text = "BFRB"
    bbox = d.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) / 2, size * 0.12), text,
           fill=(228, 230, 237, 255), font=font)

    img.save(path, "PNG")
    print(f"  wrote  {path}  ({size}x{size})")


if __name__ == "__main__":
    print("Generating PWA icons ...")
    render_icon(192, os.path.join(OUT_DIR, "icon-192.png"))
    render_icon(512, os.path.join(OUT_DIR, "icon-512.png"))
    print("done.")
