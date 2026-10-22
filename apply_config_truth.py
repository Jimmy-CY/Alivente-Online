# -*- coding: utf-8 -*-
"""apply_config_truth.py - round CF-1, 22 Oct 2026.

THE CONFIGURATION SAYS THINGS THAT ARE NOT TRUE.

FIRST: A SETTING DJANGO 5.1 DOES NOT HAVE.

    #STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    STATICFILES_STORAGE = "/staticfiles/"

A path where a dotted class path belongs. Measured on 22 October: the
line has NO EFFECT AT ALL. STATICFILES_STORAGE was deprecated in Django
4.2 and removed in 5.1, and this tree runs 5.1.4 - asked at runtime,
STORAGES comes back as the untouched default and staticfiles resolves
to plain StaticFilesStorage. The setting is not wrong, it is absent,
and the line is a note somebody left about a decision that no longer
has anywhere to land.

E15 IS NOT FIXED BY DELETING IT. The commented-out WhiteNoise Manifest
line is the one that would matter, and it cannot simply be uncommented:
there is no staticfiles.json on the volume and railway.json has no
collectstatic in it, so turning Manifest storage on would 500 the site
on the first static file. Checked on 22 October. The comment that
replaces these two lines says exactly that, so the next person to look
does not have to find it out again.

SECOND: THE FILE RAILWAY INSTALLS IS NOT THE FILE THAT LOOKS CANONICAL.

railway.json installs mysite/cron-requirements.txt. There are three
requirements files in this tree and they disagree:

    requirements.txt               85 packages
    cron-requirements.txt          86   (= mysite + googletrans)
    mysite/cron-requirements.txt   85   <- the one that is installed

    in requirements.txt and NOT installed: httpcore==0.9.1,
                                           pillow-heif==0.18.0
    installed and not in requirements.txt: httpcore==1.0.7,
                                           pyspellchecker==0.8.1

pillow-heif IS THE ONE THAT COSTS SOMETHING. pages/utils.py registers
the HEIF opener inside a try/except and sets HEIC_SUPPORTED = False
when the import fails - on purpose, so a missing package cannot take
the application down. The consequence is that on Live, today, an iPhone
photo uploaded as HEIC fails quietly and nothing anywhere says why.
This round adds the package to the file that is actually installed.

httpcore disagreeing by a MAJOR version between two files is left
alone. Nothing in this tree imports httpx or httpcore directly; it is
somebody's transitive pin, and guessing which of the two is wanted is
not a thing to do from here.

THIRD: FIVE PACKAGES ARE NOT PINNED, IN THE FILE THAT IS INSTALLED.

    beautifulsoup4>=4.12.0   numpy>=1.26.0   openpyxl>=3.1.5
    pandas>=2.0.0            pydantic>=2.0.0

A Railway rebuild can take a new MAJOR of any of them without one
character changing in this repository. That is the shape of a deploy
that breaks on a day nobody touched the code.

AND THEY ARE BOUNDED, NOT PINNED TO A VERSION INVENTED HERE. An exact
pin would be a guess about a machine this round cannot see - and a
wrong guess downgrades Live on the next build, which is worse than the
problem. An upper bound removes the real risk, the surprise major,
without claiming to know what is installed. Turning them into exact
pins is one `pip freeze` on Live away, and that is Demetri's to run.

FOURTH: ALL THREE FILES ARE UTF-16LE.

pip reads them - its auto_decode handles the BOM, measured on 22
October, so this is not what is breaking anything. Everything ELSE
fails to read them: grep finds nothing, git diff shows a wall of
binary, and Show-RequirementsAudit.py is reading a file nobody can
diff. The file Railway installs is converted to UTF-8 here. The other
two are left exactly as they are - converting a file nobody installs is
churn, and the disagreement between them is a decision, not a cleanup.

Idempotent. Every file backed up to .bak_configtruth.
"""
import os
import re
import sys

SUFFIX = '.bak_configtruth'
SET = os.path.join('mysite', 'settings.py')
REQ = os.path.join('mysite', 'cron-requirements.txt')
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_config_truth.py'
PATCHER = 'apply_config_truth.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'CF-1, 22 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# THE SETTING THAT IS NOT A SETTING
# ==========================================================================
SET_WAS = """# Push site online
#STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATICFILES_STORAGE = "/staticfiles/"
# STATIC_ROOT = BASE_DIR / "staticfiles\""""

SET_NOW = """# STATICFILES_STORAGE IS GONE - CF-1, 22 Oct 2026.
#
# Two lines stood here. One set STATICFILES_STORAGE to "/staticfiles/",
# which is a path where a dotted class path belongs; the other was the
# WhiteNoise Manifest storage, commented out.
#
# MEASURED, NOT ASSUMED. The setting was deprecated in Django 4.2 and
# REMOVED in 5.1, and this tree runs 5.1.4. Asked at runtime on 22
# October, STORAGES came back as the untouched default and staticfiles
# resolved to plain StaticFilesStorage. The line did nothing whatever.
#
# AND TURNING MANIFEST STORAGE ON IS NOT A ONE-LINE FIX - E15. It wants
# a staticfiles.json that is not on the volume, and railway.json runs
# no collectstatic, so the first static file after that change would
# 500 the site. Checked 22 October. Whoever takes E15 on needs the
# collectstatic step and the STORAGES dict together, in one round, with
# a deploy behind it.
# STATIC_ROOT = BASE_DIR / "staticfiles\""""

# ==========================================================================
# THE REQUIREMENTS FILE THAT IS REALLY INSTALLED
# ==========================================================================
# WHAT THIS ROUND MAY DO TO IT, and nothing else: bound five packages
# that are unbounded, and add one that the application imports and the
# file does not carry. Every other line survives byte for byte, and the
# gate below counts them.
BOUNDS = {
    'beautifulsoup4>=4.12.0': 'beautifulsoup4>=4.12.0,<5.0',
    'numpy>=1.26.0': 'numpy>=1.26.0,<3.0',
    'openpyxl>=3.1.5': 'openpyxl>=3.1.5,<4.0',
    'pandas>=2.0.0': 'pandas>=2.0.0,<3.0',
    'pydantic>=2.0.0': 'pydantic>=2.0.0,<3.0',
}
ADD = 'pillow-heif==0.18.0'
HEADER = (
    '# CF-1, 22 Oct 2026. UTF-8, because everything except pip was\n'
    '# unable to read this file - grep found nothing in it and git\n'
    '# diff showed a wall of binary. pip itself was fine with the\n'
    '# UTF-16 BOM; nothing was broken, and nothing could be read.\n'
    '#\n'
    '# THIS IS THE FILE RAILWAY INSTALLS. railway.json names it.\n'
    '# requirements.txt and cron-requirements.txt are NOT installed\n'
    '# and do not agree with this one - see apply_config_truth.py.\n'
    '#\n'
    '# The five bounded lines were open-ended >= until CF-1, which\n'
    '# let a rebuild take a new MAJOR with nothing in the repository\n'
    '# changing. They are BOUNDED rather than pinned: an exact pin\n'
    '# invented here would be a guess about Live, and a wrong guess\n'
    '# downgrades it on the next build. pip freeze on Live turns\n'
    '# these into exact pins whenever that is wanted.\n'
)


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def read_bytes(p):
    with open(p, 'rb') as f:
        return f.read()


def decode_any(data):
    """Whatever this file is, as text, and what it was. CF-1."""
    if data[:2] == b'\xff\xfe':
        return data.decode('utf-16-le').lstrip('﻿'), 'utf-16-le'
    if data[:2] == b'\xfe\xff':
        return data.decode('utf-16-be').lstrip('﻿'), 'utf-16-be'
    if data[:3] == b'\xef\xbb\xbf':
        return data.decode('utf-8-sig'), 'utf-8-sig'
    return data.decode('utf-8'), 'utf-8'


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def write_bytes(p, b):
    with open(p, 'wb') as f:
        f.write(b)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_bytes(b, read_bytes(p))


def refuse(msg):
    raise SystemExit('CF-1 REFUSED: %s' % msg)


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
    raw = {}

    ps = os.path.join(root, SET)
    s = read(ps)
    if MARK in s:
        print('CF-1  already applied - the configuration says what it is.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    out[ps] = swap(s, SET_WAS, SET_NOW, '%s (the dead setting)' % SET)

    # ---- THE REQUIREMENTS FILE
    pr = os.path.join(root, REQ)
    text, was_enc = decode_any(read_bytes(pr))
    lines = text.replace('\r\n', '\n').split('\n')
    before = [ln.strip() for ln in lines if ln.strip()
              and not ln.strip().startswith('#')]

    done = []
    new_lines = []
    for ln in lines:
        key = ln.strip()
        if key in BOUNDS:
            new_lines.append(BOUNDS[key])
            done.append(key)
        elif key:
            new_lines.append(key)
    for key in sorted(BOUNDS):
        if key not in done:
            refuse('%s: %r is not in the file, so this round is bounding '
                   'something that is not there - or somebody already '
                   'changed it' % (REQ, key))

    # pillow-heif GOES IN ALPHABETICAL ORDER, where the rest of the file
    # already is, so a human diff of this against requirements.txt
    # still lines up.
    if any(ln.lower().startswith('pillow-heif') for ln in new_lines):
        refuse('%s: pillow-heif is already here' % REQ)
    at = None
    for i, ln in enumerate(new_lines):
        if ln.lower() > ADD.lower():
            at = i
            break
    new_lines.insert(len(new_lines) if at is None else at, ADD)

    body = HEADER + '\n'.join(new_lines) + '\n'
    raw[pr] = body.encode('utf-8')

    after = [ln.strip() for ln in body.split('\n') if ln.strip()
             and not ln.strip().startswith('#')]

    # ---- THE GATE ON THE FILE RAILWAY INSTALLS.
    #
    # This is the one file in the tree whose contents decide what is on
    # the production machine. Nothing may quietly fall out of it.
    lost = sorted(set(n.split('>')[0].split('=')[0].lower()
                      for n in before)
                  - set(n.split('>')[0].split('=')[0].lower()
                        for n in after))
    if lost:
        refuse('%s: %d package(s) would DISAPPEAR from the file Railway '
               'installs: %r' % (REQ, len(lost), lost))
    gained = sorted(set(n.split('>')[0].split('=')[0].lower()
                        for n in after)
                    - set(n.split('>')[0].split('=')[0].lower()
                          for n in before))
    if gained != ['pillow-heif']:
        refuse('%s: this round may add pillow-heif and nothing else - it '
               'would add %r' % (REQ, gained))
    if len(after) != len(before) + 1:
        refuse('%s: %d line(s) in, %d out, and exactly one was added'
               % (REQ, len(before), len(after)))
    unbounded = [n for n in after
                 if '>=' in n and ',<' not in n]
    if unbounded:
        refuse('%s: %d package(s) are still open-ended: %r'
               % (REQ, len(unbounded), unbounded))
    if was_enc == 'utf-8':
        refuse('%s: already UTF-8, so this round has nothing to convert '
               '- it has been applied or somebody did it by hand' % REQ)
    try:
        body.encode('ascii')
    except UnicodeEncodeError:
        refuse('%s: a requirements file with a non-ASCII character in '
               'it is a requirements file nobody can read twice' % REQ)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_photo_rebuild.py'
)""", """    'test_photo_rebuild.py',
    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    'test_config_truth.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'pages/models.py'; Text = 'def store_display_jpeg';""",
             """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pillow-heif'; What = 'CF-1: railway.json installs THIS file, and it did not carry pillow-heif - so HEIC uploads from an iPhone failed quietly on Live, because pages/utils.py guards that import on purpose. Also UTF-8 now, and five open-ended packages bounded' },
    @{ File = 'pages/models.py'; Text = 'def store_display_jpeg';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # SD-1, 22 Oct 2026 - a rebuild replaces rather than accumulates.
    'test_photo_rebuild.py',
]""", """    # SD-1, 22 Oct 2026 - a rebuild replaces rather than accumulates.
    'test_photo_rebuild.py',
    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    'test_config_truth.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # SD-1, 22 Oct 2026 - a rebuild replaces the file it rebuilds.
    '.bak_photorebuild',
]""", """    # SD-1, 22 Oct 2026 - a rebuild replaces the file it rebuilds.
    '.bak_photorebuild',
    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    '.bak_configtruth',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # CF-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATE ON SETTINGS
    ns = out[ps]
    # check_gates flags this: the round writes the word
    # STATICFILES_STORAGE and the gate refuses it. Benign, and the
    # distinction is the point - the word is written into a COMMENT
    # explaining that Django 5.1 does not have the setting, while the
    # gate is asked of python_code_only, which has no comments in it.
    # A gate that could not tell those apart would make it impossible
    # to write down why a setting was removed.
    code = T.python_code_only(ns, payloads=True)
    if 'STATICFILES_STORAGE' in code:
        refuse('%s: STATICFILES_STORAGE is still set, and Django 5.1 '
               'does not have it' % SET)
    if 'E15' not in ns:
        refuse('%s: the comment that replaces it does not say why '
               'Manifest storage cannot simply be switched on' % SET)
    if 'STATIC_ROOT' not in code:
        refuse('%s: STATIC_ROOT went with it, and collectstatic needs '
               'one' % SET)

    if CHECK:
        print('CF-1  --check: %d file(s) would change, none written.'
              % (len(out) + len(raw)))
        for k in sorted(list(out) + list(raw)):
            print('        %s' % os.path.relpath(k, root))
        print('        %s -> utf-8, %d bounded, pillow-heif added'
              % (was_enc, len(BOUNDS)))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k, val in sorted(raw.items()):
        backup(k)
        write_bytes(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    for k in sorted(raw):
        if read_bytes(k) != raw[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('CF-1  applied - the configuration says what it really is.')
    print('      %d file(s) written, backed up to %s'
          % (len(out) + len(raw), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
