# -*- coding: utf-8 -*-
"""apply_one_list.py - round CF-2, 23 Oct 2026.

FOUR REQUIREMENTS FILES. ONE OF THEM DEPLOYS. THE OTHER THREE ARE
DECORATION, AND THEY HAVE DRIFTED.

Demetri, 23 October: "I have four requirements files in my
environment. I am not sure which one I use and which are not being
used."

Show-RequirementsAudit.py answers it, and has been able to answer it
all along:

    requirements.txt               utf-16   85 pins   no
    cron-requirements.txt          utf-16   86 pins   no
    mysite/requirements.txt        utf-16   87 pins   no
    mysite/cron-requirements.txt   utf-8    88 pins   YES

railway.json AND the Dockerfile both install mysite/cron-requirements
.txt. Nothing reads the other three. They are not a backup, a staging
copy or a local variant - they are three near-copies of one list that
nothing consults, and the drift is already measurable: seven packages
differ in MEMBERSHIP and six in VERSION.

AND ONE OF THEM CANNOT RESOLVE. requirements.txt pins httpcore==0.9.1
while httpx==0.27.0 requires httpcore==1.*. A fresh
`pip install -r requirements.txt` cannot satisfy both, and
anthropic==0.72.0 sits on that same chain. The file at the repo root -
the one a person types by habit - is the broken one.

SO THEY ARE RETIRED, NOT CONVERTED. CF-1 converted the deployed file
to UTF-8 on 22 October so it could be read; converting these three
would make them easier to read while leaving them exactly as able to
mislead. The cost they impose is not that they are unreadable. It is
that somebody has to ask which one is real.

A BYTE COPY, NOT A TEXT ONE. All three are UTF-16 LE with a BOM. The
backup helper every other round uses reads and writes utf-8, and a
utf-8 "copy" of a utf-16 file is mojibake that revert_all.sh would
cheerfully restore. That exact helper crashed on a UTF-16 file on 22
October and left three files reverted in an applied tree. These are
copied with shutil.copy2 and nothing else.

ONE LIVE READ HAD TO BE REPAIRED. test_translate_api.py section 5
opens requirements.txt off disk rather than through the scope helper -
which is the defect its own sibling, test_translate_honest.py,
describes at length and fixed in itself:

    "a round's suite must judge the tree as that round left it, or
     every round after it is a false failure waiting to happen"

TR-2's suite has the bug TR-1's suite grew out of. Retiring the file
would make it fail on a line TR-2 correctly wrote. as_left_by handles
a file the tree no longer has - RT-1, 18 October, in so many words -
so the read goes through it and the claim survives the retirement.

AND THE AUDIT HAD A BLIND SPOT WORTH CLOSING. It reports
pymupdf-fonts under USED ONLY BY TOOLING, because nothing imports it:
pymupdf resolves `notos` and `notosbo` by NAME at runtime. Acting on
that verdict - moving it to requirements-dev.txt - makes the e-signing
signature page print a row of dots on Live and nowhere else. It joins
whitenoise and mysqlclient in RUNTIME_NAMED.

Idempotent. Every file backed up to .bak_onelist, including the three
that are removed.
"""
import os
import re
import shutil
import sys

SUFFIX = '.bak_onelist'
AUDIT = 'Show-RequirementsAudit.py'
TRAPI = 'test_translate_api.py'
THONEST = 'test_translate_honest.py'
KEEP = os.path.join('mysite', 'cron-requirements.txt')
RAIL = 'railway.json'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'CF-2, 23 Oct 2026'
CHECK = False

CREATES = ()

# THE THREE THAT GO. Repo-relative, and the one that deploys is
# deliberately NOT among them - the gate re-reads railway.json rather
# than trusting this tuple.
RETIRE = (
    'requirements.txt',
    'cron-requirements.txt',
    os.path.join('mysite', 'requirements.txt'),
)

A_WAS = """        'whitenoise': 'middleware, named in settings as a string',"""
A_NOW = """        'whitenoise': 'middleware, named in settings as a string',
        # CF-2, 23 Oct 2026. NOTHING IMPORTS THIS AND IT IS NOT
        # TOOLING. pymupdf resolves 'notos' and 'notosbo' by NAME at
        # runtime, so a static import scan cannot see it and this
        # script reported it under USED ONLY BY TOOLING - a verdict
        # that, acted on, makes the e-signing signature page print a
        # row of dots on Live and nowhere else.
        'pymupdf-fonts': 'font faces resolved by name at runtime - '
                         'ES-2 draws the signature page with notos',"""

T_WAS = """def section_5():
    print('\\n5. requirements.txt')
    raw = open(REQS, 'rb').read()"""

T_NOW = """def section_5():
    print('\\n5. requirements.txt')
    # THROUGH THE SCOPE HELPER, not off disk - repaired by CF-2,
    # 23 Oct 2026, which retired this file.
    #
    # This read was the one defect test_translate_honest.py had
    # already found in ITSELF and written up: "a round's suite must
    # judge the tree as that round left it, or every round after it
    # is a false failure waiting to happen". TR-2's suite kept the
    # bug its sibling grew out of, and it only showed when a later
    # round removed the file.
    #
    # as_left_by answers for a file the tree no longer has - RT-1,
    # 18 October - so the claims below are still about requirements
    # .txt as TR-2 left it, which is what they were always for.
    import alv_rounds
    raw = alv_rounds.as_left_by(REQS, SUFFIX,
                                lambda p: open(p, 'rb').read())"""


H_WAS = """    # And say out loud that the line is gone again, so nobody reads this
    # section as a claim about the tree today.
    live = open(REQS, 'rb').read().decode('utf-16')
    if 'deep-translator' not in live:"""

H_NOW = """    # And say out loud that the line is gone again, so nobody reads this
    # section as a claim about the tree today.
    #
    # GUARDED BY CF-2, 23 Oct 2026, which RETIRED requirements.txt.
    # This read is only a note - it decides what to print, not what to
    # assert - but an unguarded open() crashes just as hard as a false
    # claim, and a crash blocks a push exactly as hard as a failure
    # while saying far less about why.
    live = (open(REQS, 'rb').read().decode('utf-16')
            if os.path.isfile(REQS) else '')
    if not os.path.isfile(REQS):
        print('        (CF-2 has since retired requirements.txt itself -')
        print('         one list now, mysite/cron-requirements.txt.)')
    elif 'deep-translator' not in live:"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    """Text files only. The retired three go through copy_backup."""
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def copy_backup(p):
    """A BYTE COPY. These three are UTF-16 LE with a BOM and the text
    helper above would write mojibake that a revert would restore."""
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        shutil.copy2(p, b)


def refuse(msg):
    raise SystemExit('CF-2 REFUSED: %s' % msg)


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


def installed_file(rail):
    """Which requirements file the deploy really installs, read out of
    railway.json rather than assumed."""
    m = re.search(r'pip install -r ([^\s"\\]+)', rail)
    return m.group(1) if m else None


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pa = os.path.join(root, AUDIT)
    a = read(pa)
    if MARK in a:
        print('CF-2  already applied - one requirements file, and it is '
              'the one that deploys.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE FILE THAT DEPLOYS IS READ, NOT ASSUMED.
    rail = read(os.path.join(root, RAIL))
    deploys = installed_file(rail)
    if not deploys:
        refuse('%s has no pip install line, so this round cannot tell '
               'which file is the real one and must not guess.' % RAIL)
    if deploys.replace('/', os.sep) != KEEP:
        refuse('%s installs %r, not %r. The three files this round '
               'retires were chosen on the strength of that line; if it '
               'has moved, the round must be re-measured.'
               % (RAIL, deploys, KEEP.replace(os.sep, '/')))
    if any(r == deploys.replace('/', os.sep) for r in RETIRE):
        refuse('the deployed file is in the retire list. That would '
               'take the application off the air.')

    gone = []
    for rel in RETIRE:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            refuse('%s is not on disk, so there is nothing to retire '
                   'and the measurement behind this round no longer '
                   'describes the tree.' % rel)
        gone.append(full)

    # AND ALL THREE REALLY ARE UTF-16, which is why they get a byte
    # copy. If one has been converted since, the claim in the
    # docstring is stale and the round should be re-read.
    for full in gone:
        head = open(full, 'rb').read(2)
        if head not in (b'\xff\xfe', b'\xfe\xff'):
            refuse('%s no longer starts with a UTF-16 BOM. This round '
                   'says all three are UTF-16 and copies them as bytes '
                   'for that reason.' % os.path.relpath(full, root))

    out[pa] = swap(a, A_WAS, A_NOW, '%s (RUNTIME_NAMED)' % AUDIT)

    pt = os.path.join(root, TRAPI)
    out[pt] = swap(read(pt), T_WAS, T_NOW,
                   '%s (section 5 reads through the helper)' % TRAPI)

    ph = os.path.join(root, THONEST)
    out[ph] = swap(read(ph), H_WAS, H_NOW,
                   '%s (the note that opened the file)' % THONEST)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_upload_order.py'
)""", """    'test_upload_order.py',
    # CF-2, 23 Oct 2026 - one requirements file, and it is the one
    # railway.json installs.
    'test_one_list.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'Show-RequirementsAudit.py'; Text = 'font faces resolved by name at runtime'; What = 'CF-2: pymupdf-fonts is named by pymupdf at runtime and imported by nothing, so the audit called it tooling-only - a verdict that, acted on, prints a row of dots where the tenant signed, on Live and nowhere else' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    t = read(ptr)
    t = swap(t, """    # UO-1, 23 Oct 2026 - SI-1's rule reaches the lease and the deed.
    'test_upload_order.py',
]""", """    # UO-1, 23 Oct 2026 - SI-1's rule reaches the lease and the deed.
    'test_upload_order.py',
    # CF-2, 23 Oct 2026 - one requirements file, not four.
    'test_one_list.py',
]""", '%s (CONVERTED)' % TREE)
    # NOT alv_tree.RETIRED. THE FIRST SPELLING OF THIS ROUND PUT
    # THE THREE IN THERE AND IT WAS WRONG.
    #
    # RETIRED is a register of retired PAGES: alv_tree resolves a
    # label under pages/templates and crs/templates, and the register
    # exists so last_path() can find a retired page's last text
    # "beside the hole it left". A requirements file is not a page and
    # does not live under a template root, so last_path could never
    # resolve one - it searched pages/templates/cron-requirements.txt
    # .bak_onelist, did not find it, and raised.
    #
    # AND THE KEY IS A BASENAME. RETIRED is looked up by basename as
    # well as by path, and `cron-requirements.txt` is the basename of
    # BOTH the root file this round retires AND the file in mysite/
    # that must never be thought retired. test_recipe_tones died on
    # exactly that collision - the MP-2 shape, found by a suite rather
    # than by reading.
    #
    # The retirement is already fully registered without it: the
    # .bak_onelist files record the text, and .bak_onelist in
    # alv_rounds.ROUNDS is what tells stage_round this is a deliberate
    # retirement rather than a half-applied tree.
    out[ptr] = t

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_uploadorder',
]""", """    '.bak_uploadorder',
    # CF-2, 23 Oct 2026 - one requirements file, not four.
    '.bak_onelist',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # CF-2, 23 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    au = T.python_code_only(out[pa], payloads=True)
    if "'pymupdf-fonts'" not in au:
        refuse('%s does not name pymupdf-fonts as runtime-named' % AUDIT)
    if 'RUNTIME_NAMED' not in au:
        refuse('%s has no RUNTIME_NAMED table to add it to' % AUDIT)

    tr = T.python_code_only(out[pt], payloads=True)
    if re.search(r'raw\s*=\s*open\(REQS', tr):
        refuse('%s still opens the retired file off disk' % TRAPI)
    if 'as_left_by' not in tr:
        refuse('%s does not read through the scope helper' % TRAPI)

    # NOTHING ELSE MAY READ A RETIRED FILE LIVE.
    #
    # Measured rather than assumed: five suites name a requirements
    # file. Two read a backup, one reads only the deployed file, one
    # names them in prose. The fifth was TRAPI and is repaired above.
    live_readers = []
    for n_ in sorted(os.listdir(root)):
        if not (n_.startswith('test_') and n_.endswith('.py')):
            continue
        if n_ == 'test_one_list.py':
            continue
        # THE VERSION THIS ROUND WILL WRITE, not the one on disk.
        # A gate that judges the tree as it stands cannot see the
        # repair the round is making in the same breath, and refuses
        # its own fix.
        full_ = os.path.join(root, n_)
        body = T.python_code_only(out.get(full_, read(full_)),
                                  payloads=True)
        # PER CALL, NOT PER FILE.
        #
        # The first spelling of this asked whether the word `bak_`
        # appeared ANYWHERE in the suite, and excused the whole file
        # if it did. test_translate_honest.py mentions a backup in
        # one function and opens the live file in another, so it
        # sailed through and then died with FileNotFoundError. A gate
        # that judges a file by a word somewhere else in it is not
        # reading the call it is supposed to be judging.
        # A STATEMENT, NOT A LINE. The guard on a wrapped read sits
        # on the continuation line - `... if os.path.isfile(REQS)
        # else ''` - and a line-at-a-time gate cannot see it, so it
        # refused the very repair this round was making.
        lines_ = body.split('\n')
        for i_, line in enumerate(lines_):
            if 'open(' not in line or 'bak' in line.lower():
                continue
            if not re.search(r'open\(\s*(REQS|[^)]*requirements)', line):
                continue
            stmt = ' '.join(lines_[i_:i_ + 3])
            if re.search(r'\+\s*SUFFIX|as_left_by|as_of|isfile|exists',
                         stmt):
                continue
            live_readers.append('%s -> %s' % (n_, line.strip()[:60]))
    if live_readers:
        refuse('these suites would read a file this round removes, '
               'off disk, and would fail on a line their own round '
               'correctly wrote: %r' % live_readers)

    if CHECK:
        print('CF-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        and %d file(s) RETIRED (backed up, then removed):'
              % len(gone))
        for g in gone:
            print('          %s' % os.path.relpath(g, root))
        print('        the one that stays: %s' % KEEP.replace(os.sep, '/'))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)

    # THE RETIREMENTS. Backed up as BYTES, then removed.
    for g in gone:
        copy_backup(g)
        os.remove(g)

    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    for g in gone:
        if os.path.exists(g):
            refuse('%s was not removed' % os.path.relpath(g, root))
        if not os.path.exists(g + SUFFIX):
            refuse('%s has no backup beside the hole it left'
                   % os.path.relpath(g, root))

    print('CF-2  applied - one requirements file, and it is the one '
          'railway.json installs.')
    print('      %d file(s) edited, %d retired, backed up to %s'
          % (len(out), len(gone), SUFFIX))
    for g in gone:
        print('        retired  %s' % os.path.relpath(g, root))
    print('      kept     %s' % KEEP.replace(os.sep, '/'))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
