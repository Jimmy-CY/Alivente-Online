# -*- coding: utf-8 -*-
"""wellness/photos.py - WL-19, 12 Nov 2026. Progress photos, kept locked.

Demetri, 12 Nov: "I want to include progress photos."

WHERE THEY LIVE. Not in MEDIA_ROOT: everything there is served to anyone
with the address (/media/ is open, and Cloudflare caches it). Photos go in
a folder BESIDE it - on Railway /data/wellness_private, on the same volume
as /data/media, so they survive a deploy - and are only ever sent by a
view that checks the photo belongs to whoever is asking.

HOW. Each upload is turned the right way up, shrunk to 1600 px on its long
side (and a 480 px copy for the grid), saved as JPEG, and encrypted with
the journal key (wellness/crypto.py). A copy of the disk shows nothing.

A photo from a Samsung in HEIC is read too (pillow-heif, as recipes do).
"""
import io
import os
import secrets

from django.conf import settings

from . import crypto

FULL = 1600
THUMB = 480
MAX_BYTES = 25 * 1024 * 1024
SIZES = ('full', 'thumb')

try:                                        # HEIC from a phone camera
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:                           # noqa: BLE001 - optional
    pass


def root():
    """The private folder. WELLNESS_PRIVATE_ROOT wins (the suites use a
    temporary one); otherwise beside MEDIA_ROOT."""
    r = getattr(settings, 'WELLNESS_PRIVATE_ROOT', None)
    if not r:
        media = os.path.normpath(str(settings.MEDIA_ROOT))
        r = os.path.join(os.path.dirname(media), 'wellness_private')
    return os.path.join(r, 'photos')


def _path(stem, size):
    if size not in SIZES or not stem.isalnum():
        raise ValueError('bad photo name')
    return os.path.join(root(), '%s-%s.bin' % (stem, size))


def _jpeg(img, longest):
    from PIL import Image
    im = img.copy()
    im.thumbnail((longest, longest), Image.LANCZOS)
    if im.mode not in ('RGB', 'L'):
        im = im.convert('RGB')
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=85, optimize=True, progressive=True)
    return buf.getvalue(), im.size


class NotAPhoto(ValueError):
    pass


def store(upload):
    """An uploaded file -> (stem, width, height). Raises NotAPhoto with a
    sentence for the person when it cannot be read."""
    from PIL import Image, ImageOps, UnidentifiedImageError
    if upload is None:
        raise NotAPhoto('Choose a photo first.')
    if getattr(upload, 'size', 0) > MAX_BYTES:
        raise NotAPhoto('That photo is over 25 MB - try a smaller one.')
    try:
        img = Image.open(upload)
        img = ImageOps.exif_transpose(img)
        img.load()
    except (UnidentifiedImageError, OSError, ValueError):
        raise NotAPhoto('That file is not a photo Wellness can read - '
                        'a JPEG, PNG, WebP or HEIC works.')
    os.makedirs(root(), exist_ok=True)
    stem = secrets.token_hex(16)
    full, size = _jpeg(img, FULL)
    thumb, _ = _jpeg(img, THUMB)
    for name, data in (('full', full), ('thumb', thumb)):
        with open(_path(stem, name), 'wb') as f:
            f.write(crypto.seal_bytes(data))
    return stem, size[0], size[1]


def read(stem, size='full'):
    """The JPEG bytes, or None if the file is gone or the key is wrong."""
    try:
        with open(_path(stem, size), 'rb') as f:
            return crypto.open_bytes(f.read())
    except (OSError, ValueError):
        return None


def remove(stem):
    for size in SIZES:
        try:
            os.remove(_path(stem, size))
        except (OSError, ValueError):
            pass
