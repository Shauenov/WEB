# utils_media.py
from typing import BinaryIO

IMAGE_MAGIC = {
    b"\xFF\xD8\xFF": "jpg",           # JPEG
    b"\x89PNG\r\n\x1a\n": "png",      # PNG
    b"RIFF": "webp",                  # WEBP starts with RIFF, доп. проверка ниже
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}

def is_image_stream(f: BinaryIO, content_type: str | None) -> bool:
    pos = f.tell()
    head = f.read(16)
    f.seek(pos)

    # content-type
    ct_ok = (content_type or "").startswith("image/")

    # magic bytes
    is_webp = head.startswith(b"RIFF") and b"WEBP" in head[:16]
    magic_ok = any(head.startswith(sig) for sig in IMAGE_MAGIC) or is_webp

    return ct_ok and magic_ok
