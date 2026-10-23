# -*- coding: utf-8 -*-
"""apply_esign_pdf.py - round ES-2, 23 Oct 2026.

E-SIGNING, RUNG TWO: THE TWO THINGS THE FLOW DOES TO A PDF.

  render_pages   turn the uploaded lease into page images, so the
                 signing page can show the document INSIDE itself
                 rather than sending the tenant away to a viewer
  seal           append one signature page to the original and take
                 the sha256 of the result

No view, no screen, no route, no email. ES-1 was the shape of the
data; this is the machinery. ES-3 upward is what calls it.

THE ORIGINAL IS NEVER TOUCHED. Signatures go on an APPENDED page -
decided 23 October - so the lease everybody signed stays byte for byte
the lease that was sent. That is also why this works on a PDF nobody
here produced: there is nothing to position, no layout to understand,
and no field to find.

AND THE SAME PAGE FOR BOTH PATHS. An uploaded lease and a
system-generated one get the identical appended page. In-place blocks
on one and an appended page on the other would be two code paths
wearing one name.

ONE NEW DEPENDENCY, IN THE FILE RAILWAY ACTUALLY READS.
railway.json's installCommand names mysite/cron-requirements.txt, NOT
requirements.txt - so a pymupdf line in the wrong file is a line that
deploys nothing and fails at the first import on Live. The gate below
re-reads railway.json rather than trusting this comment.

PURE WHEEL, NO SYSTEM PACKAGES. PyMuPDF 2.0 bundles MuPDF 1.28.5, so
nothing has to be apt-installed into the Nixpacks image. That was the
reason to prefer it over pdf2image, which needs poppler on the box.

pymupdf, NOT fitz. `import fitz` still works and warns that it is
deprecated on EVERY import, which would land in every log line this
application writes.

WHAT THIS ROUND DELIBERATELY DOES NOT DO. It does not remove
pyHanko==0.30.0, pyhanko-certvalidator==0.28.0 or oscrypto==1.3.0,
which no Python file in this tree imports and which are the
certificate-based approach we decided against on 23 October. Removing
three packages is a different claim from adding one, and a round that
made both could not say which half broke the build. Named here so it
is not lost: it is its own round.

requirements.txt is NOT touched either - it is UTF-16LE, which these
helpers do not write, and it already has an owner on the flagged list.
Install locally with:  pip install pymupdf==2.0

Idempotent. Every file backed up to .bak_esignpdf.
"""
import os
import re
import sys

# THE NAME CHECK RAISES A QUESTION ABOUT ES-2 AND THE ANSWER IS NO.
# check_gates finds the string twice in test_esign_model.py. Both are
# ES-1's own prose pointing FORWARD - "those are ES-2 upward" - naming
# the rung that had not been built yet, not a round that owns the
# label. ES-2 has no register entry and .bak_esignpdf is free, so the
# name is this round's. Recorded rather than silenced, because the
# next person to run the gate will see the same two hits.
SUFFIX = '.bak_esignpdf'
SEAL = os.path.join('pages', 'services', 'lease_sealing.py')
REQ = os.path.join('mysite', 'cron-requirements.txt')
RAIL = 'railway.json'
PS1 = 'Push-PendingChanges.ps1'
# CF-1's SUITE COUNTS WHAT IS ADDED TO THE FILE THIS ROUND EDITS.
#
# test_config_truth.py asserts that exactly ONE package arrived in
# mysite/cron-requirements.txt since CF-1 - pillow-heif, the round's
# own. This round adds two more, so that census moves with it.
#
# IT WAS MISSED ON THE FIRST DELIVERY. Release 9 push 1 shipped with
# this number unmoved and the sweep refused the push, correctly. The
# sandbox sweep that should have caught it first died at suite 87 of
# 437 and nobody noticed for ninety minutes. Eleven censuses were
# moved by hand for RV-1 the day before; this is the twelfth, and it
# was found by the instrument rather than by reading.
TRUTH = 'test_config_truth.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'ES-2, 23 Oct 2026'
# TWO PINS, ONE CLAIM. pymupdf renders and appends; pymupdf-fonts is
# the glyphs it draws with. The first draft pinned only the first and
# drew the signature page in Helvetica, which is Base-14 and has no
# Greek - so a tenant called Ανδρέας Γεωργίου printed as a row of
# dots, silently. A renderer that cannot draw the name of the person
# signing is not a renderer, so the two ship together or not at all.
#
# AND 1.28.2, NOT 2.0, WHICH IS A BUILD-WEIGHT DECISION.
#
# This round pinned 2.0 first and the claim beside it said Nixpacks
# would install nothing. That was true of SYSTEM packages and
# misleading about everything else: PyMuPDF 2.0 folded the layout and
# LLM extras into the base package, so `pip install pymupdf==2.0`
# pulls networkx, protobuf, flatbuffers, psutil, tabulate,
# pymupdf-layout, pymupdf4llm AND onnxruntime - a machine-learning
# runtime - into every build, for a module that draws text on a page
# and rasterises three sheets of A4.
#
# 1.28.2 is the last release with NO dependencies at all. `pip show`
# reports an empty Requires, it carries the same MuPDF 1.28 engine,
# and every call this module makes - new_page, insert_text,
# insert_image, get_pixmap, tobytes - has been stable since 1.18. The
# suite passes identically on it, which is the only evidence that
# counts.
PINS = ('pymupdf==1.28.2', 'pymupdf-fonts==1.0.5')
CHECK = False

# THE SERVICE MODULE SHIPS WITH THE ROUND.
CREATES = (SEAL,)

# ALPHABETICAL, CASE-INSENSITIVE, which is how this file is kept:
# pymupdf sorts before PyMySQL because 'u' precedes 'y'. A pin dropped
# at the end of a sorted file is a merge conflict waiting to happen.
R_WAS = "pyhanko-certvalidator==0.28.0\nPyMySQL==1.1.1"
R_NOW = ("pyhanko-certvalidator==0.28.0\n"
         "# ES-2, 23 Oct 2026. Renders the lease to page images for the\n"
         "# signing page, and appends the signature page at sealing.\n"
         "# Pure wheels - MuPDF and the fonts are bundled, so Nixpacks\n"
         "# installs no system packages for either.\n"
         "%s\n"
         "# AND THE GLYPHS IT DRAWS WITH. Helvetica is Base-14 and has\n"
         "# no Greek: a tenant called Andreas Georgiou in Greek letters\n"
         "# printed as a row of dots, silently. Noto Sans carries them.\n"
         "%s\n"
         "PyMySQL==1.1.1" % PINS)


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
    raise SystemExit('ES-2 REFUSED: %s' % msg)


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


def body_of(code, name):
    """One function's source, from its `def` to the next top-level one."""
    a = code.find('def %s(' % name)
    if a < 0:
        return ''
    rest = code[a:]
    nxt = re.search(r'\ndef \w+', rest[1:])
    return rest[:nxt.start() + 1] if nxt else rest


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pr = os.path.join(root, REQ)
    r = read(pr)
    if MARK in r:
        print('ES-2  already applied - the PDF machinery is here.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    ps = os.path.join(root, SEAL)
    if not os.path.isfile(ps):
        refuse('%s is not on disk. It is what this round IS - the '
               'patcher wires it in, it does not write it.' % SEAL)

    out[pr] = swap(r, R_WAS, R_NOW, '%s (the pin)' % REQ)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_esign_model.py'
)""", """    'test_esign_model.py',
    # ES-2, 23 Oct 2026 - the lease rendered to page images, and the
    # signature page appended at sealing.
    'test_esign_pdf.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/services/lease_sealing.py'; Text = 'THE ORIGINAL IS NEVER TOUCHED'; What = 'ES-2: signatures go on an APPENDED page, so the lease everybody signed stays byte for byte the lease that was sent - which is also why this works on a PDF nobody here produced' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf'; What = 'ES-2: and the pin lives HERE because railway.json installs from this file, not requirements.txt - the same line in the other file would deploy nothing and fail at the first import on Live' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # ES-1, 23 Oct 2026 - the e-signing envelope and its audit trail.
    'test_esign_model.py',
]""", """    # ES-1, 23 Oct 2026 - the e-signing envelope and its audit trail.
    'test_esign_model.py',
    # ES-2, 23 Oct 2026 - the page images and the appended seal.
    'test_esign_pdf.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_esignmodel',
]""", """    '.bak_esignmodel',
    # ES-2, 23 Oct 2026 - the page images and the appended seal.
    '.bak_esignpdf',
]""", '%s (ROUNDS)' % ROUNDS)

    # ---- THE CENSUS CF-1's SUITE KEEPS
    pc = os.path.join(root, TRUTH)
    c = read(pc)
    out[pc] = swap(c,
                   """ok(sorted(set(PK) - set(OLDPK)) == ['pillow-heif'],""",
                   """# ES-2, 23 Oct 2026 - three now, not one. CF-1 added
# pillow-heif; ES-2 adds the PDF renderer and the font faces it
# draws with. The number moves with the round that moved it
# rather than being loosened to a range.
ok(sorted(set(PK) - set(OLDPK)) == ['pillow-heif', 'pymupdf',
                                    'pymupdf-fonts'],""",
                   '%s (what CF-1 counts as added)' % TRUTH)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-2, 23 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    code = T.python_code_only(read(ps), payloads=True)

    # IT MUST BE THE LIBRARY WE CHOSE, BY THE NAME WE CHOSE.
    if 'pymupdf' not in code:
        refuse('%s never names pymupdf, so whatever it opens a PDF '
               'with is not the thing this round pins.' % SEAL)
    if re.search(r'(^|\n)\s*import fitz\b', code) or 'fitz.' in code:
        refuse('%s imports fitz. It still works and it warns that it '
               'is deprecated on EVERY import, which would land in '
               'every log line this application writes. The package '
               'has been called pymupdf since 1.24.' % SEAL)

    # AND IT MUST BE INSTALLABLE HERE, or the suite that proves this
    # round cannot run and the sweep would go green on a skip.
    try:
        import pymupdf as _mu
    except ImportError:
        refuse('pymupdf is not importable in this interpreter. The '
               'suite drives a real PDF through both functions, and a '
               'round whose proof cannot run is a round that proves '
               'nothing. Install it first:  pip install %s' % PINS[0])
    got = str(getattr(_mu, 'VersionBind',
                      getattr(_mu, '__version__', '?')))
    want = PINS[0].split('==')[1]
    if got != want:
        refuse('pymupdf %s is installed but this round pins %s. A '
               'local version that is not the deployed one makes every '
               'green run here a claim about a different library.'
               % (got, want))
    # AND NOT 2.x, WHICH IS NOT A STYLE PREFERENCE.
    #
    # 2.0 requires onnxruntime, networkx, protobuf, flatbuffers,
    # psutil, tabulate, pymupdf-layout and pymupdf4llm. None of them
    # is used by anything in this tree, and one of them is a
    # machine-learning runtime. The gate names the version rather
    # than trusting the comment above it.
    if got.startswith('2.'):
        refuse('pymupdf %s drags an ML runtime and seven other '
               'packages into every Railway build for a module that '
               'draws text and rasterises A4. 1.28.2 has no '
               'dependencies at all and the same engine.' % got)
    deps = [d for d in getattr(
        __import__('importlib.metadata', fromlist=['x']),
        'requires', lambda n: [])('pymupdf') or []
        if 'extra ==' not in d]
    if deps:
        refuse('pymupdf %s declares dependencies %r. The pin this '
               'round chose has none, and a build that quietly grew '
               'eight packages is a build nobody measured.'
               % (got, deps[:6]))

    # AND THE FONTS, which are not optional decoration.
    try:
        import pymupdf_fonts as _fonts
    except ImportError:
        refuse('pymupdf-fonts is not importable. Without it the only '
               'fonts available are the PDF Base-14 set, none of which '
               'carries Greek, and the signature page prints a Cyprus '
               'tenant name as a row of dots without raising. Install '
               'it:  pip install %s' % PINS[1])
    have = set(getattr(_fonts, 'fontdescriptors', {}))
    for want in ('notos', 'notosbo'):
        if want not in have:
            refuse('pymupdf-fonts does not offer %r, which %s draws '
                   'with. A font name that does not resolve does not '
                   'raise - it draws dots.' % (want, SEAL))

    # A STORAGE KEY IS NOT A FILESYSTEM PATH.
    #
    # page_name built its key with os.path.join in the first draft,
    # which returns backslashes on Windows and forward slashes on
    # Linux. Development is Windows and Live is Linux, so the same
    # page would be WRITTEN under one key and LOOKED FOR under
    # another, and the signing page would show a blank where the
    # lease is - on Live only, and never on the machine it was
    # written on, which is the worst place for a bug to hide.
    pn = body_of(code, 'page_name')
    if not pn:
        refuse('%s has no page_name' % SEAL)
    if 'os.path.join' in pn:
        refuse('%s: page_name builds a storage key with os.path.join, '
               'which gives backslashes on Windows and slashes on '
               'Linux. One page, two keys, and the mismatch only '
               'shows on Live.' % SEAL)
    if "'/" not in pn and '"/' not in pn and '/%' not in pn:
        refuse('%s: page_name does not build a slash-separated key'
               % SEAL)

    # THE ORIGINAL IS NEVER TOUCHED - the whole basis of the design.
    sealed = body_of(code, 'build_sealed')
    if not sealed:
        refuse('%s has no build_sealed' % SEAL)
    if re.search(r'original_pdf\.(save|delete)\b', sealed):
        refuse('%s: build_sealed writes to original_pdf. Signatures go '
               'on an APPENDED page precisely so the lease everybody '
               'signed stays byte for byte the lease that was sent; a '
               'sealer that rewrites the original destroys the one '
               'thing a dispute is argued from.' % SEAL)

    # SD-1's RULE, IN BOTH PLACES THAT STORE A FILE. Django storage
    # does not overwrite - it hands back the name you asked for with a
    # random suffix - so a re-render or a re-seal must DELETE first or
    # the row points at a file nothing can find again.
    for fn in ('render_pages', 'seal'):
        b = body_of(code, fn)
        if not b:
            refuse('%s has no %s' % (SEAL, fn))
        d = b.find('.delete(')
        s = b.find('.save(')
        if d < 0 or s < 0 or d > s:
            refuse('%s: %s saves a file without deleting the old one '
                   'first. Django storage does not overwrite - SD-1, '
                   '22 October - so the second write lands on a '
                   'suffixed name and the next read looks for a file '
                   'that is not there.' % (SEAL, fn))

    # SEALING TAKES THE HASH OF WHAT WAS STORED.
    sl = body_of(code, 'seal')
    if 'sha256' not in sl:
        refuse('%s: seal does not hash anything. With no certificate '
               'the sha256 of the sealed bytes is the whole of the '
               'tamper-evidence.' % SEAL)

    # AND CF-1's CENSUS AGREES WITH THE FILE.
    #
    # The gate re-derives the added set from the two texts rather
    # than trusting that the swap above wrote the right names. That
    # is the whole difference between moving a census and editing a
    # number until a suite stops complaining.
    import re as _re
    def _pins(txt):
        return set(l_.split('==')[0].split('>=')[0].strip().lower()
                   for l_ in txt.splitlines()
                   if l_.strip() and not l_.lstrip().startswith('#'))
    added_now = sorted(_pins(out[pr]) - _pins(read(pr + SUFFIX)
                                              if os.path.exists(pr + SUFFIX)
                                              else r))
    claimed = _re.search(r"== \[('pillow-heif'[^\]]*)\]", out[pc])
    if not claimed:
        refuse('%s: the added-package census is not where this round '
               'expects it' % TRUTH)
    names = sorted(x.strip().strip(chr(39)) for x in
                   claimed.group(1).replace('\n', ' ').split(','))
    if names != sorted(set(names)) or 'pymupdf' not in names:
        refuse('%s: the census does not name what this round adds - '
               'it says %r' % (TRUTH, names))

    # THE PIN LANDED IN THE FILE RAILWAY ACTUALLY INSTALLS FROM.
    rail = read(os.path.join(root, RAIL))
    want = REQ.replace(os.sep, '/')
    if want not in rail:
        refuse('%s does not name %s, so the pin this round just added '
               'would install nowhere and Live would fail at the first '
               'import. Whichever file it DOES name is the one that '
               'needs the line.' % (RAIL, want))
    if 'requirements.txt' in rail.replace(want, ''):
        refuse('%s names a second requirements file as well. This '
               'round pinned one of them; which one deploys is then a '
               'coin toss.' % RAIL)

    # AND NOTHING CERTIFICATE-SHAPED CREPT BACK IN.
    added = [l_ for l_ in out[pr].splitlines()
             if l_ not in r.splitlines()]
    if any('hanko' in l_.lower() for l_ in added):
        refuse('this round added a pyHanko line. There is no '
               'certificate - decided 23 October - and the evidence is '
               'the appended page plus the stored sha256.')
    pins_added = [l_.strip() for l_ in added if l_.strip()
                  and not l_.lstrip().startswith('#')]
    if sorted(pins_added) != sorted(PINS):
        refuse('expected exactly the two pins %r, got %r. They are one '
               'claim - the renderer and the glyphs it draws with - '
               'and a tree with one of them produces a signature page '
               'that names nobody.' % (list(PINS), pins_added))

    # AND NOTHING ON THAT PAGE IS DRAWN IN A BASE-14 FONT.
    #
    # This gate exists because the first draft failed it. Helvetica,
    # Times and Courier are the PDF Base-14 set; none has a Greek
    # glyph, and pymupdf does not raise when asked for one it cannot
    # draw - it emits a dot. The failure is invisible until a lease
    # comes back with a row of dots where the tenant signed.
    for b14 in ('helvetica', 'helv', 'times-roman', 'times', 'courier',
                'zapfdingbats', 'symbol'):
        if re.search(r"fontname\s*=\s*['\"]%s" % re.escape(b14), code):
            refuse('%s draws with %r. That is a PDF Base-14 font and '
                   'it has no Greek glyphs - a tenant called Ανδρέας '
                   'Γεωργίου prints as a row of dots and nothing '
                   'raises. This is a Cyprus letting company; a Greek '
                   'name is the ordinary case.' % (SEAL, b14))
    if "FONT = 'notos'" not in code or "FONT_BOLD = 'notosbo'" not in code:
        refuse('%s does not name the Noto faces it must draw with.'
               % SEAL)

    # THE PIN LANDED IN THE RIGHT PLACE - asked as a DELTA, because
    # the file is NOT sorted and never was.
    #
    # The first spelling of this gate demanded `pins == sorted(pins)`
    # and refused the round over oscrypto/openpyxl and
    # pillow-heif/pillow, two inversions that were already there. A
    # gate that asserts a property the file never had is the same
    # error as a claim that can never fail, pointing the other way:
    # it reports the tree as broken for not matching a standard
    # nobody set. So count the inversions before and after and refuse
    # only if THIS round added one.
    def inversions(text):
        pins = [l_.split('==')[0].split('>=')[0].strip().lower()
                for l_ in text.splitlines()
                if l_.strip() and not l_.lstrip().startswith('#')]
        return [(a, b) for a, b in zip(pins, pins[1:]) if a > b]

    before, after = inversions(r), inversions(out[pr])
    new = [p_ for p_ in after if p_ not in before]
    if new:
        refuse('the pin landed out of order in %s: %r. The file has '
               '%d pre-existing inversion(s), which this round leaves '
               'alone; it may not add a %dth.'
               % (REQ, new, len(before), len(before) + 1))

    if CHECK:
        print('ES-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        plus %s, which this round CREATES' % SEAL)
        print('        the lease rendered to page images, and the '
              'signature page appended at sealing')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('ES-2  applied - the lease renders to page images, and the '
          'signature page appends at sealing.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      plus %s, which this round CREATES' % SEAL)
    print('      %s pinned in %s - the file railway.json installs from.'
          % (' and '.join(PINS), REQ))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
