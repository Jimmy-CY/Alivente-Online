# -*- coding: utf-8 -*-
"""apply_blue_ink.py - round ES-6b, 25 Oct 2026.

EVERY DRAWN SIGNATURE IS BLUE.

His instruction of 25 October, in his words: "All signatures that have
been drawn, need to display in Blue."

WHAT THE ROUND DOES

    THE SIGNING PAD DRAWS IN BLUE, so the signer sees blue ink while
    signing. It used to draw in the house dark grey, #21343c, which on a
    printed page reads as print rather than as a hand.

    THE SIGNATURE PAGE PRINTS EVERY DRAWN MARK IN BLUE - re-inked when
    the envelope is sealed, not when the mark is captured. The stored
    image stays exactly what the signer's device sent, because that is
    the evidence; the page shows it in blue. So marks captured before
    this round, in dark grey, come out blue too.

    ONE INK, NAMED ONCE - lease_sealing.SIGNATURE_INK - which the page
    prints with and the view hands to the pad as a hex.

    TYPED SIGNATURES ARE UNCHANGED. He said drawn.

Stands on ES-6 (it registers after it). Idempotent. Three files edited,
each backed up to .bak_blueink; nothing ships new except this patcher
and its suite.
"""
import os
import re
import sys

SUFFIX = '.bak_blueink'
MARK = 'ES-6b, 25 Oct 2026'
CHECK = False

SEAL = os.path.join('pages', 'services', 'lease_sealing.py')
SIGN = os.path.join('pages', 'views', 'lease_signing_sign.py')
PAD = os.path.join('pages', 'templates', 'lease_sign.html')
CREATES = ()

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# ------------------------------------------------------------- THE SWAPS
# One entry per file. Each WAS is the smallest block of the file as ES-6
# left it that occurs exactly once.
SWAPS = [
    (SEAL, [
        (r'''"""
import hashlib
import os

''',
         r'''"""
import hashlib
import io
import os

'''),
        (r'''

def build_sealed(signing, parties=None, events=None):
    """The original, plus ONE appended page, as bytes.
''',
         r'''

# EVERY DRAWN SIGNATURE IS BLUE - ES-6b, 25 Oct 2026. His instruction:
# "All signatures that have been drawn, need to display in Blue." Blue
# is how a signature on paper says it was signed by hand and is not a
# photocopy, and a dark-grey stroke on a printed page reads as print.
#
# ONE INK, NAMED HERE, used twice: the signing pad draws with the hex
# (so the signer sees blue while signing) and the signature page prints
# every drawn mark in the same colour. A second spelling in the template
# would be a second answer.
SIGNATURE_INK = (26, 61, 158)
SIGNATURE_INK_HEX = '#%02x%02x%02x' % SIGNATURE_INK


def _in_blue(raw):
    """A drawn signature, re-inked in SIGNATURE_INK, as PNG bytes.

    AT SEALING, NOT AT CAPTURE. The stored image stays exactly what the
    signer's device sent - that is the evidence - and the page prints it
    in blue. Which is also why marks captured before ES-6b, drawn in
    dark grey, come out blue too.

    THE SHAPE IS THE ALPHA. The pad's PNG is transparent with the stroke
    painted on it, so the stroke keeps its alpha (and its smoothed edges)
    and only its colour changes. An image with no alpha - a flattened
    one - takes its alpha from how dark each pixel is: white paper
    vanishes, ink stays.

    IF ANYTHING GOES WRONG, THE ORIGINAL. A mark in the wrong colour is
    a cosmetic fault; a mark missing from a signature page is not.
    """
    try:
        from PIL import Image, ImageOps
        im = Image.open(io.BytesIO(raw))
        im.load()
        if 'A' in im.getbands() or 'transparency' in im.info:
            alpha = im.convert('RGBA').getchannel('A')
        else:
            alpha = ImageOps.invert(im.convert('L'))
        inked = Image.new('RGBA', im.size, SIGNATURE_INK + (0,))
        inked.putalpha(alpha)
        out = io.BytesIO()
        inked.save(out, 'PNG')
        return out.getvalue()
    except Exception:                                   # noqa: BLE001
        return raw


def build_sealed(signing, parties=None, events=None):
    """The original, plus ONE appended page, as bytes.
'''),
        (r'''                    p.signature_image.close()
                    rect = pymupdf.Rect(56, y, 56 + 190, y + 52)
                    page.insert_image(rect, stream=img, keep_proportion=True)
                except Exception:
                    # A MISSING MARK IS NOT A MISSING SIGNATURE. The
''',
         r'''                    p.signature_image.close()
                    rect = pymupdf.Rect(56, y, 56 + 190, y + 52)
                    page.insert_image(rect, stream=_in_blue(img),
                                      keep_proportion=True)
                except Exception:
                    # A MISSING MARK IS NOT A MISSING SIGNATURE. The
'''),
    ]),
    (SIGN, [
        (r'''        'pages': _page_urls(request, env, party, how),
        'already': bool(party.signed_at),
    }

''',
         r'''        'pages': _page_urls(request, env, party, how),
        'already': bool(party.signed_at),
        # ES-6b, 25 Oct 2026 - the pad draws in the ink the signature
        # page prints in, named once in lease_sealing.
        'ink': lease_sealing.SIGNATURE_INK_HEX,
    }

'''),
    ]),
    (PAD, [
        (r'''    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#21343c';
    if (keep) {
      var img = new Image();
''',
         r'''    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    // ES-6b, 25 Oct 2026 - BLUE, the ink the signature page prints
    // every drawn mark in; the view passes it from lease_sealing.
    ctx.strokeStyle = '{{ ink|escapejs }}';
    if (keep) {
      var img = new Image();
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('ES-6b REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    ps = os.path.join(root, SEAL)
    if MARK in read(ps):
        print('ES-6b already applied - drawn signatures are blue.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- WHAT THIS ROUND STANDS ON
    if "'test_lease_approval.py'" not in read(os.path.join(root, PS1)):
        refuse('ES-6 is not applied - this round registers after it.')

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_lease_approval.py'
)""", """    'test_lease_approval.py',
    # ES-6b, 25 Oct 2026 - every drawn signature is blue.
    'test_blue_ink.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/services/lease_sealing.py'; Text = 'stream=_in_blue(img)'; What = 'ES-6b: every drawn signature prints in blue on the signature page - re-inked at sealing, so the stored mark stays exactly what the signer sent' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_lease_approval.py',
]""", """    'test_lease_approval.py',
    # ES-6b, 25 Oct 2026 - every drawn signature is blue.
    'test_blue_ink.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_leaseapprove',
]""", """    '.bak_leaseapprove',
    # ES-6b, 25 Oct 2026 - every drawn signature is blue.
    '.bak_blueink',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-6b, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    seal = T.python_code_only(out[ps])
    pad = T.code_only_js(out[os.path.join(root, PAD)])

    # ---- 1. ONE INK.
    if seal.count('SIGNATURE_INK = (') != 1:
        refuse('SIGNATURE_INK must be defined exactly once, in lease_sealing.')
    if "ctx.strokeStyle = '{{ ink|escapejs }}'" not in pad \
            or re.search(r"strokeStyle\s*=\s*'#", pad):
        refuse('the pad must draw with the ink the view passes, not a hex '
               'of its own - a second spelling is a second answer.')

    # ---- 2. EVERY DRAWN MARK GOES THROUGH IT.
    if seal.count('page.insert_image(') != seal.count('stream=_in_blue('):
        refuse('a drawn mark reaches the signature page without being '
               're-inked.')

    # ---- 3. THE STORED MARK IS NOT TOUCHED.
    sign = T.python_code_only(out[os.path.join(root, SIGN)])
    if '_in_blue' in sign:
        refuse('the capture path must store what the device sent; blue is '
               'applied when the page is printed.')

    if CHECK:
        print('ES-6b --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('ES-6b applied - every drawn signature is blue, on the pad and on '
          'the signature page.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
