# -*- coding: utf-8 -*-
"""House marks - his signature and the company stamp. ES-7, 25 Oct 2026.

HIS DECISIONS OF 25 OCTOBER, all of them here:

  STORED SECURELY. The images live in the database (HouseMark.image),
  never in media and never behind a URL. This screen shows them as an
  inline image to the superuser looking at it, and nothing else in the
  application can fetch them.

  MANAGED BY A SUPERUSER ONLY. The owner of a mark is whoever uploads
  it, so there is one account the marks can be applied for. Another
  superuser uploading REPLACES them - visibly, on this screen.

  USED ONLY WHEN HE IS THE SIGNATORY. Not decided here: the signing view
  asks HouseMark.for_signer(request.user, ...) and gets bytes only for
  the owning account, signing by session.

  THE STAMP IS THE COMPANY NAME ONLY - the company number left off. This
  screen stores what it is given; the stamp he supplied is the name.

THE UPLOAD IS NORMALISED. Whatever comes in - a PNG with transparency,
a scan on white paper, a JPEG photo - leaves as a transparent PNG
cropped to the ink, at most MAX_WIDTH wide. A white background would
print as a white box over the signature line.
"""
import base64
import hashlib
import io

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render

from ..models import HouseMark

__all__ = [
    # __init__.py re-exports with `import *`, which obeys __all__ - RV-1's
    # lesson: a view missing from this list does not exist to the URLconf.
    'house_marks',
]

MAX_BYTES = 5 * 1024 * 1024
MAX_WIDTH = 1200
# HOW FAR FROM PAPER A PIXEL MUST BE TO COUNT AS INK, on a flattened
# image. Below this it is paper or scanner noise and becomes transparent.
PAPER = 28
PAD = 12


def _normalise(raw):
    """Any image in, a transparent PNG cropped to the ink out.

    Returns (png_bytes, width, height). Raises ValueError with a sentence
    a person can act on.
    """
    try:
        from PIL import Image, ImageOps
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception:                                   # noqa: BLE001
        raise ValueError('That file is not an image this screen can read. '
                         'Use a PNG or a JPEG.')
    im = ImageOps.exif_transpose(im)
    has_alpha = 'A' in im.getbands() or 'transparency' in im.info
    rgba = im.convert('RGBA')
    if not has_alpha:
        # A FLATTENED IMAGE - a scan or a photo on paper. Alpha from how
        # far each pixel is from white: paper vanishes, ink stays, and
        # the soft edge of a pen stroke stays soft.
        grey = ImageOps.invert(im.convert('L'))
        alpha = grey.point(lambda v: 0 if v < PAPER
                           else min(255, int((v - PAPER) * 2.2)))
        rgba.putalpha(alpha)
    box = rgba.getchannel('A').point(lambda v: 255 if v > 40 else 0) \
        .getbbox()
    if not box:
        raise ValueError('There is nothing on that image - it is blank, or '
                         'all one colour.')
    x0, y0, x1, y1 = box
    rgba = rgba.crop((max(0, x0 - PAD), max(0, y0 - PAD),
                      min(rgba.width, x1 + PAD), min(rgba.height, y1 + PAD)))
    if rgba.width > MAX_WIDTH:
        rgba = rgba.resize((MAX_WIDTH,
                            max(1, round(rgba.height * MAX_WIDTH
                                         / rgba.width))),
                           Image.LANCZOS)
    out = io.BytesIO()
    rgba.save(out, 'PNG', optimize=True)
    return out.getvalue(), rgba.width, rgba.height


def _as_data_uri(row):
    """The stored PNG inline, for this screen only. Never a URL."""
    return 'data:image/png;base64,' + base64.b64encode(
        bytes(row.image)).decode('ascii')


def _who(user):
    return (user.get_full_name() or user.get_username() or 'someone').strip()


@login_required
@user_passes_test(lambda u: u.is_superuser)
def house_marks(request):
    """Upload, replace or remove the saved signature and the stamp."""
    kinds = dict(HouseMark.KIND_CHOICES)

    if request.method == 'POST':
        kind = (request.POST.get('kind') or '').strip()
        if kind not in kinds:
            messages.error(request, 'Choose the signature or the stamp.')
            return redirect('house_marks')
        label = kinds[kind].lower()

        if request.POST.get('action') == 'remove':
            gone, _ = HouseMark.objects.filter(kind=kind).delete()
            if gone:
                messages.success(request, 'The %s has been removed. Leases '
                                 'already signed keep the copy they were '
                                 'signed with.' % label)
            return redirect('house_marks')

        upload = request.FILES.get('image')
        if not upload:
            messages.error(request, 'Choose an image file for the %s.'
                           % label)
            return redirect('house_marks')
        if upload.size > MAX_BYTES:
            messages.error(request, 'That file is over 5MB.')
            return redirect('house_marks')
        try:
            png, width, height = _normalise(upload.read())
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect('house_marks')
        HouseMark.objects.update_or_create(
            kind=kind,
            defaults={'owner': request.user, 'image': png,
                      'sha256': hashlib.sha256(png).hexdigest(),
                      'width': width, 'height': height})
        messages.success(request, 'The %s is saved. It is used only when '
                         'you sign for Alivente yourself.' % label)
        return redirect('house_marks')

    rows = {r.kind: r for r in HouseMark.objects.select_related('owner')}
    cards = []
    for kind, label in HouseMark.KIND_CHOICES:
        row = rows.get(kind)
        cards.append({
            'kind': kind,
            'label': label,
            'row': row,
            'mine': bool(row and row.owner_id == request.user.pk),
            'owner': _who(row.owner) if row else '',
            # THE PREVIEW IS FOR THE OWNER. Another superuser sees that a
            # mark exists and whose it is, not the mark itself.
            'preview': (_as_data_uri(row)
                        if row and row.owner_id == request.user.pk else ''),
        })
    return render(request, 'house_marks.html', {'cards': cards})
