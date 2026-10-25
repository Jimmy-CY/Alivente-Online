# -*- coding: utf-8 -*-
"""lease_sealing.py - ES-2, 23 Oct 2026.

THE TWO THINGS THE E-SIGNING FLOW DOES TO A PDF.

  render_pages   turn the uploaded lease into page images, so the
                 signing page can show the document INSIDE itself
                 rather than sending the tenant away to a viewer
  seal           append one signature page to the original and take
                 the sha256 of the result

THE ORIGINAL IS NEVER TOUCHED. Signatures go on an APPENDED page -
decided 23 October - so the lease everybody signed stays byte for byte
the lease that was sent. That is also why this works on a PDF nobody
here produced: there is nothing to position, no layout to understand,
and no field to find.

AND THE SAME PAGE FOR BOTH PATHS. An uploaded lease and a
system-generated one get the identical appended page. In-place blocks
on one and an appended page on the other would be two code paths
wearing one name, and "this exact same process" - Demetri, 22 October
- would stop being literally true.

THE APPENDED PAGE IS THE EVIDENCE, because there is no certificate.
It prints who signed, when, from which address, with which device, and
how they proved who they were. Nothing in the FILE proves anything;
this page and the stored sha256 are what a dispute is argued from.

IT CANNOT PRINT ITS OWN HASH. The sha256 is taken OF the sealed bytes,
so it does not exist until the page is already in them. The hash lives
in the envelope row, which is the whole point of keeping one.

pymupdf, NOT fitz. `import fitz` still works and warns that it is
deprecated; the package has been `pymupdf` since 1.24 and the warning
is printed on every single import, which would land in every log line
this application writes.
"""
import hashlib
import os

from django.core.files.base import ContentFile
from django.utils import timezone


# WHAT A PHONE ACTUALLY NEEDS. A4 at 120 dpi is 992px wide, which is
# a touch over 2x a 390px screen and a touch under 3x. Going higher
# costs bytes on a phone connection for detail nobody can see; going
# lower makes 9pt lease text mush.
PAGE_DPI = 120
# AND A CEILING, because a PDF can declare any page size it likes and
# a poster-sized one at 120 dpi is an image nobody's browser will
# thank us for.
MAX_PAGE_PX = 1400

# A4 portrait in points, for the appended page when the original has
# no page to copy its size from - which cannot happen today, since an
# envelope always has an original, and is here because a function
# that would divide by zero should say what it does instead.
A4 = (595.0, 842.0)


def _open(raw):
    """Open PDF bytes, raising nothing the caller cannot read."""
    import pymupdf
    return pymupdf.open(stream=raw, filetype='pdf')


def render_pages(signing, dpi=PAGE_DPI):
    """Write one PNG per page of the ORIGINAL and return how many.

    THE RETURN VALUE IS WHAT `LeaseSigning.page_count` HOLDS - the
    ORIGINAL's page count, not the sealed one. page_count exists so the
    signing page knows how many images to ask for, and the signing page
    only ever shows the document as it was SENT. The sealed file has at
    least one page more and is not what anybody signs against.

    The signing page shows these rather than embedding the PDF: a
    phone browser handed an embedded PDF may render it, may offer to
    download it, or may show nothing, and which of those happens is
    not something this application can test on a device it does not
    have.

    IDEMPOTENT. Re-rendering overwrites each page at its own exact
    name, which SD-1 made possible on 22 October - a storage that does
    not overwrite hands back a suffixed name and the next read looks
    for a file that is not there.
    """
    from django.core.files.storage import default_storage

    signing.original_pdf.open('rb')
    try:
        raw = signing.original_pdf.read()
    finally:
        signing.original_pdf.close()

    doc = _open(raw)
    try:
        n = doc.page_count
        for i in range(n):
            page = doc[i]
            zoom = dpi / 72.0
            wide = page.rect.width * zoom
            if wide > MAX_PAGE_PX:
                zoom = zoom * (MAX_PAGE_PX / wide)
            import pymupdf
            pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom))
            name = page_name(signing, i + 1)
            # DELETE THEN WRITE - SD-1's rule. Django storage does not
            # overwrite; it hands back the name you asked for with a
            # random suffix, and then nothing can find the page again.
            if default_storage.exists(name):
                default_storage.delete(name)
            default_storage.save(name, ContentFile(pix.tobytes('png')))
    finally:
        doc.close()
    return n


def page_name(signing, number):
    """Where page N of this envelope's lease is rendered.

    DERIVED, NOT STORED. The signing page asks for page 3 by building
    this name, so there is no second list of filenames to keep in
    agreement with the files.

    FORWARD SLASHES, BUILT BY HAND, NOT os.path.join. A storage key is
    not a filesystem path. os.path.join on Windows returns
    `lease_signing_pages\\3\\001.png` and on Linux
    `lease_signing_pages/3/001.png` - two different keys for one page.
    Development happens on Windows and Live runs on Linux, so a name
    written by one and read by the other would simply not be found,
    and the signing page would show a blank where the lease is.
    """
    return 'lease_signing_pages/%s/%03d.png' % (signing.pk, number)


# NOTO SANS, NOT HELVETICA, AND THIS IS NOT A TASTE DECISION.
#
# The first draft of this module drew the signature page in Helvetica.
# Helvetica is one of the PDF Base-14 fonts and has no Greek glyphs,
# so a tenant called Ανδρέας Γεωργίου printed as `······· ········` -
# a row of dots where the name should be. It did not raise. It did
# not warn. It produced a signature page that looked finished and
# named nobody.
#
# This is a Cyprus letting company. A Greek name on a lease is the
# ORDINARY case, not an edge one, and the one thing the appended page
# exists to say is WHO signed.
#
# notos / notosbo are Noto Sans regular and bold, from pymupdf-fonts -
# a pure wheel, pinned beside pymupdf itself, which is why the two
# pins are one claim: a renderer that cannot draw the name of the
# person signing is not a renderer.
FONT = 'notos'
FONT_BOLD = 'notosbo'


def _line(page, x, y, text, size=9, bold=False, colour=(0, 0, 0)):
    page.insert_text((x, y), text, fontsize=size, color=colour,
                     fontname=FONT_BOLD if bold else FONT)


def build_sealed(signing, parties=None, events=None):
    """The original, plus ONE appended page, as bytes.

    Returns (bytes, page_count_of_the_result). Takes the parties and
    events as arguments rather than reading them back, so a caller
    inside a transaction seals what it is holding.
    """
    import pymupdf

    signing.original_pdf.open('rb')
    try:
        raw = signing.original_pdf.read()
    finally:
        signing.original_pdf.close()

    parties = list(parties if parties is not None
                   else signing.parties.all().order_by('order', 'pk'))
    events = list(events if events is not None
                  else signing.events.all().order_by('at', 'event_id'))

    doc = _open(raw)
    try:
        if doc.page_count:
            w = doc[0].rect.width
            h = doc[0].rect.height
        else:
            w, h = A4
        page = doc.new_page(width=w, height=h)

        y = 64
        _line(page, 56, y, 'Signatures', size=16, bold=True)
        y += 10
        page.draw_line(pymupdf.Point(56, y), pymupdf.Point(w - 56, y),
                       color=(0.8, 0.84, 0.86), width=0.8)
        y += 26

        _line(page, 56, y,
              'This page was added when the agreement was signed. '
              'The pages above it are unchanged.', size=8.5,
              colour=(0.35, 0.4, 0.43))
        y += 26

        for p in parties:
            if not p.signed_at:
                continue
            # THE MARK ITSELF, drawn or typed.
            box_top = y
            if p.signature_image:
                try:
                    p.signature_image.open('rb')
                    img = p.signature_image.read()
                    p.signature_image.close()
                    rect = pymupdf.Rect(56, y, 56 + 190, y + 52)
                    page.insert_image(rect, stream=img, keep_proportion=True)
                except Exception:
                    # A MISSING MARK IS NOT A MISSING SIGNATURE. The
                    # row says they signed and when; the picture is
                    # the decoration, and losing it must not lose the
                    # record of the act.
                    _line(page, 56, y + 34, p.typed_name or p.name,
                          size=13)
            else:
                _line(page, 56, y + 34, p.typed_name or p.name, size=13)
            page.draw_line(pymupdf.Point(56, box_top + 56),
                           pymupdf.Point(56 + 220, box_top + 56),
                           color=(0.6, 0.66, 0.69), width=0.7)
            y = box_top + 70

            _line(page, 56, y, p.name, size=10, bold=True)
            y += 13
            _line(page, 56, y, p.get_role_display(), size=8.5,
                  colour=(0.35, 0.4, 0.43))
            y += 12
            if p.email:
                _line(page, 56, y, p.email, size=8.5,
                      colour=(0.35, 0.4, 0.43))
                y += 12
            _line(page, 56, y,
                  'Signed %s' % p.signed_at.strftime('%d %B %Y at %H:%M'),
                  size=8.5, colour=(0.35, 0.4, 0.43))
            y += 12
            how = {'session': 'signed in to Alivente',
                   'token': 'by emailed link'}.get(p.signed_auth, '')
            tail = ', '.join(x for x in (how, p.signed_ip) if x)
            if tail:
                _line(page, 56, y, tail, size=8.5,
                      colour=(0.35, 0.4, 0.43))
                y += 12
            y += 14

        # THE TRAIL, PRINTED. With no certificate this is the evidence
        # and it travels WITH the document, so a copy handed to a
        # third party carries its own provenance.
        y += 6
        _line(page, 56, y, 'What happened', size=10, bold=True)
        y += 8
        page.draw_line(pymupdf.Point(56, y), pymupdf.Point(w - 56, y),
                       color=(0.88, 0.91, 0.92), width=0.6)
        y += 16
        for e in events:
            if y > h - 70:
                page = doc.new_page(width=w, height=h)
                y = 64
            who = e.party.name if e.party_id and e.party else 'Alivente'
            _line(page, 56, y,
                  '%s   %s   %s%s'
                  % (e.at.strftime('%d %b %Y %H:%M'),
                     e.get_kind_display().ljust(22)[:22], who,
                     ('   ' + e.ip) if e.ip else ''),
                  size=8, colour=(0.25, 0.3, 0.33))
            y += 11

        y += 16
        _line(page, 56, y,
              'Envelope %s   sealed %s'
              % (signing.pk,
                 timezone.now().strftime('%d %B %Y at %H:%M')),
              size=8, colour=(0.45, 0.5, 0.53))

        out = doc.tobytes()
        return out, doc.page_count
    finally:
        doc.close()


def seal(signing, parties=None, events=None):
    """Build the sealed PDF, store it, and take its hash.

    THE HASH IS OF THE BYTES THAT WERE STORED, taken after the build
    and before anything else can touch them. It is the whole of the
    tamper-evidence, because there is no certificate: a year from now
    the question is "what did the tenant actually sign", and this is
    the only thing that answers it.

    Returns the hex digest. Does NOT save the model - the caller owns
    the transaction and what else goes in it.
    """
    # AN UNSAVED ENVELOPE HAS NO NAME TO LAND ON - ES-2a, 24 Oct
    # 2026. The sealed path is built from the primary key, which is
    # what makes a re-seal land where the last one did; without a pk
    # every unsaved envelope would be called the same thing. Nothing
    # calls it this way, and now nothing can.
    if not signing.pk:
        raise ValueError(
            'seal() needs a saved envelope: the sealed pdf is named '
            'from its primary key, and an unsaved one has none.')

    raw, _pages = build_sealed(signing, parties=parties, events=events)
    digest = hashlib.sha256(raw).hexdigest()

    want = 'sealed-%s.pdf' % signing.pk
    field = signing.sealed_pdf
    target = field.field.generate_filename(signing, want)
    if field.storage.exists(target):
        # SD-1's RULE AGAIN. A re-seal must land on its own name, or
        # the row points at a file that is one suffix out of date.
        field.storage.delete(target)
    field.save(want, ContentFile(raw), save=False)

    signing.pdf_sha256 = digest
    return digest
