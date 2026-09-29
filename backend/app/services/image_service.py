from pathlib import Path
from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = 40_000_000


def process_image(tool: str, source: Path, target: Path, options: dict) -> None:
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original)
        image.load()
        if tool == "jpg-to-png":
            image.save(target, format="PNG")
        elif tool == "png-to-jpg":
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, "white")
            background.paste(rgba, mask=rgba.getchannel("A"))
            background.save(target, format="JPEG", quality=90, optimize=True)
        elif tool == "image-to-pdf":
            rgb = image.convert("RGB")
            rgb.save(target, format="PDF", resolution=150)
        else:
            raise ValueError("Unsupported image operation.")
