"""
Manually craft a multi-size Windows .ico file from individual PNG images.
This bypasses PIL's limitations with multi-resolution transparent ICOs.
"""
import os
import struct
from PIL import Image

# Sizes to include (electron-builder requires at least 256x256)
SIZES = [16, 24, 32, 48, 64, 128, 256]


def png_to_bytes(img: Image.Image) -> bytes:
    """Convert a PIL image to PNG bytes (in-memory)."""
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_ico(png_paths: dict, out_path: str) -> int:
    """Build a Windows .ico file containing the given sizes."""
    images = []
    for s in SIZES:
        img = Image.open(png_paths[s]).convert("RGBA")
        # Make sure dimensions are right
        if img.size != (s, s):
            img = img.resize((s, s), Image.LANCZOS)
        png_data = png_to_bytes(img)
        # ICO entry: width (0=256), height (0=256), color count, reserved, planes, bitcount, data size, data offset
        w = s if s < 256 else 0
        h = s if s < 256 else 0
        images.append((w, h, png_data))

    # Build the file
    n = len(images)
    header_size = 6 + 16 * n
    data_offset = header_size
    entries = b""
    all_data = b""
    for w, h, png in images:
        size = len(png)
        entries += struct.pack(
            "<BBBBHHII",
            w, h, 0, 0, 1, 32, size, data_offset
        )
        all_data += png
        data_offset += size

    with open(out_path, "wb") as f:
        f.write(struct.pack("<HHH", 0, 1, n))  # reserved, type=1 (icon), count
        f.write(entries)
        f.write(all_data)

    return os.path.getsize(out_path)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    png_paths = {s: os.path.join(here, f"icon-{s}.png") for s in SIZES}
    out = os.path.join(here, "icon.ico")
    size = build_ico(png_paths, out)
    print(f"✅ Created multi-size ICO: {out}  ({size:,} bytes)")
    print(f"   Contains sizes: {SIZES}")
