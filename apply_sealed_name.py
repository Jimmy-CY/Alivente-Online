# -*- coding: utf-8 -*-
"""apply_sealed_name.py - round ES-2a, 24 Oct 2026.

A RE-SEAL MUST LAND ON THE SAME NAME, AND IT COULD NOT.

Demetri's push gate found this on 24 October. test_esign_pdf failed
in the pool and passed alone, and the runner reported "the pool was
the cause, not the tree" - which is true of the TREE and false of the
CLAIM. The assertion is that re-sealing is deterministic. It is not.

    FAIL re-sealing lands on the SAME name, so the row never points
         at a file one suffix out of date
         lease-1--20261024140644.pdf then lease-1--20261024140645.pdf

TWO SOURCES OF NON-DETERMINISM, AND SD-1 NEEDS NEITHER.

    THE TIMESTAMP. lease_signing_upload_path builds the filename with
    timezone.now().strftime('%Y%m%d%H%M%S'), and seal() calls that
    path function TWICE - once through generate_filename to work out
    what to DELETE, and once inside field.save() to WRITE. On a fast
    idle machine both land in the same second. Under pool contention
    they straddle a second boundary: the delete targets ...644 and
    the write creates ...645. The old file is orphaned and SD-1's
    delete-then-write rule is silently defeated.

    THE TENANT SLUG. The same name embeds slugify(tenant_name). T2-1
    gave a tenancy a second person this morning and T2-4 taught
    sixteen screens to print both - a tenant being RENAMED is an
    ordinary Tuesday. Rename one between two seals and the name moves
    again, for a second reason, on a machine of any speed.

SO THE SEALED PDF GETS A PATH OF ITS OWN THAT DEPENDS ONLY ON THE
PRIMARY KEY, which never changes:

    lease_signing/sealed/lease-<pk>.pdf

Nothing else. No clock, no slug. The delete and the write cannot
disagree because there is nothing left to disagree about.

THE ORIGINAL PDF KEEPS ITS TIMESTAMPED NAME, deliberately. Uploading
a REPLACEMENT lease is a different act from re-sealing the same one:
two different documents genuinely want two different names, and the
row points at whichever was uploaded last. Only the SEALED file is
"one envelope, one output, rebuilt in place", which is what SD-1 is
about.

WITH SLASHES, NOT os.path.join - ES-2's own lesson, 23 October, and
the function it fixed sits forty lines above the one it did not.
os.path.join gives Windows a backslash key and Linux a slash, so a
development file and a Live file are named differently for ever.

EXISTING ROWS ARE NOT MOVED AND DO NOT NEED TO BE. A FileField stores
the name it was given; changing upload_to changes where the NEXT save
goes and nothing else. Any sealed PDF already on Live keeps its name
and keeps resolving. The first re-seal after this lands on the new
path and the old file is then the only orphan this defect ever
produced for that envelope.

AND seal() NOW REFUSES AN UNSAVED ENVELOPE. A path built from
`instance.pk or 'new'` is deterministic only while the pk exists;
two unsaved envelopes would both be 'new'. Nothing calls it that way
- you seal an envelope that exists - and now nothing can.

Idempotent. Every file backed up to .bak_sealedname.
"""
import os
import re
import sys

SUFFIX = '.bak_sealedname'
MODELS = os.path.join('pages', 'models.py')
SEAL = os.path.join('pages', 'services', 'lease_sealing.py')
MIG = os.path.join('pages', 'migrations', '0105_es2a_sealed_name.py')
SENTS = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'ES-2a, 24 Oct 2026'
CHECK = False

CREATES = (MIG,)

# ---------------------------------------------------------------- MODEL

P_WAS = """def lease_signature_upload_path(instance, filename):"""

P_NOW = '''def lease_sealed_upload_path(instance, filename):
    """Where an envelope's SEALED pdf lives. ES-2a, 24 Oct 2026.

    ONE ENVELOPE, ONE OUTPUT, REBUILT IN PLACE - which is what SD-1
    is about, and what the timestamped path above could not deliver.

    THIS NAME DEPENDS ON THE PRIMARY KEY AND NOTHING ELSE. The other
    path in this file embeds a clock AND a tenant slug, and seal()
    calls its path function twice - once to decide what to delete and
    once to write. Either ingredient moving between those two calls
    leaves the delete pointing at a file that is no longer the one
    being replaced:

        the CLOCK moves whenever the two calls straddle a second,
        which on a loaded machine is most of the time - Demetri's
        push gate caught exactly that on 24 October

        the SLUG moves whenever a tenant is renamed, which T2-1 and
        T2-4 made an ordinary thing to do this morning

    A primary key moves never.

    SLASHES, NOT os.path.join - ES-2's lesson of 23 October, learned
    forty lines below this one and not applied here until now.
    os.path.join gives Windows a backslash key and Linux a slash, so
    the same envelope is named differently on a laptop and on Live.
    """
    del filename                      # the extension is always pdf
    return 'lease_signing/sealed/lease-%s.pdf' % instance.pk


def lease_signature_upload_path(instance, filename):'''

F_WAS = """    sealed_pdf = models.FileField(upload_to=lease_signing_upload_path,
                                  max_length=255, blank=True, null=True)"""

F_NOW = """    # ES-2a, 24 Oct 2026 - ITS OWN PATH, and the original keeps the
    # timestamped one. Uploading a REPLACEMENT lease is a different
    # act from re-sealing the same one: two documents want two names.
    # Only the sealed file is one envelope, one output, rebuilt in
    # place - and a name with a clock in it cannot be rebuilt in
    # place at all.
    sealed_pdf = models.FileField(upload_to=lease_sealed_upload_path,
                                  max_length=255, blank=True, null=True)"""

# ----------------------------------------------------------- THE SEALER

S_WAS = """    raw, _pages = build_sealed(signing, parties=parties, events=events)
    digest = hashlib.sha256(raw).hexdigest()"""

S_NOW = """    # AN UNSAVED ENVELOPE HAS NO NAME TO LAND ON - ES-2a, 24 Oct
    # 2026. The sealed path is built from the primary key, which is
    # what makes a re-seal land where the last one did; without a pk
    # every unsaved envelope would be called the same thing. Nothing
    # calls it this way, and now nothing can.
    if not signing.pk:
        raise ValueError(
            'seal() needs a saved envelope: the sealed pdf is named '
            'from its primary key, and an unsaved one has none.')

    raw, _pages = build_sealed(signing, parties=parties, events=events)
    digest = hashlib.sha256(raw).hexdigest()"""


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
    raise SystemExit('ES-2a REFUSED: %s' % msg)


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

    pm = os.path.join(root, MODELS)
    m = read(pm)
    if MARK in m:
        print('ES-2a  already applied - a re-seal lands where the last '
              'one did.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if 'def seal(' not in read(os.path.join(root, SEAL)):
        refuse('ES-2 is not applied - %s has no seal() to fix.' % SEAL)

    pg = os.path.join(root, MIG)
    if not os.path.isfile(pg):
        refuse('%s is not on disk. Django generates it from the models, '
               'so it cannot disagree with them.' % MIG)

    out[pm] = swap(swap(m, P_WAS, P_NOW, '%s (the sealed path)' % MODELS),
                   F_WAS, F_NOW, '%s (the field)' % MODELS)

    ps = os.path.join(root, SEAL)
    out[ps] = swap(read(ps), S_WAS, S_NOW, '%s (the pk guard)' % SEAL)

    # ---- THE SENTINEL THIS ROUND REVEALS
    #
    # THE THIRD TIME TODAY, AND IT IS THE SAME STORY EVERY TIME. A
    # round that is the FIRST to back up a file turns every sentinel
    # on that file from untested into tested - and one written by
    # the round that CREATED the file can never have been absent,
    # because the file did not exist before it.
    #
    # ES-2 created lease_sealing.py on 23 October with that heading
    # in it. ES-2a is the first round to touch the file since. The
    # row did not become weak; it became checkable.
    psn = os.path.join(root, SENTS)
    out[psn] = swap(read(psn), """PINNED = {""",
                    """PINNED = {
    # THE TWELFTH, 24 OCT 2026 - REVEALED, NOT BROKEN, and the third
    # of its kind today after T2-4's two and PG-2's one.
    #
    # ES-2 CREATED pages/services/lease_sealing.py on 23 October, and
    # created it WITH this heading - the paragraph explaining why a
    # signature page is APPENDED rather than stamped, which is the
    # whole basis of the round. No version of that file has ever
    # lacked it and none can have. ES-2a is simply the first round
    # since to back the file up, so the verdict is provable rather
    # than untested.
    #
    # The day somebody stamps in place instead, the row fails.
    'THE ORIGINAL IS NEVER TOUCHED':
        'why the signature page is appended and not stamped - ES-2 '
        'created the file WITH it on 23 Oct, and ES-2a is the first '
        'round since to back that file up',""",
                    '%s (the revealed sentinel)' % SENTS)

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_preflight_names.py'
)""", """    'test_preflight_names.py',
    # ES-2a, 24 Oct 2026 - a re-seal lands where the last one did.
    'test_sealed_name.py'
)""", '%s (the suites)' % PS1)
    q = swap(q,
             """    @{ File = 'pages/services/lease_sealing.py'; Text""",
             """    @{ File = 'pages/models.py'; Text = 'def lease_sealed_upload_path'; What = 'ES-2a: the sealed pdf is named from the primary key and NOTHING else - the path it used before embedded a clock and a tenant slug, and seal() calls its path function twice, so either one moving between those two calls left the delete pointing at a file that was no longer the one being replaced' },
    @{ File = 'pages/services/lease_sealing.py'; Text""",
             '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_preflight_names.py',
]""", """    'test_preflight_names.py',
    # ES-2a, 24 Oct 2026 - a re-seal lands where the last one did.
    'test_sealed_name.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_pgnames',
]""", """    '.bak_pgnames',
    # ES-2a, 24 Oct 2026 - a re-seal lands where the last one did.
    '.bak_sealedname',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-2a, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nm = T.python_code_only(out[pm], payloads=True)

    a = nm.find('def lease_sealed_upload_path')
    if a < 0:
        refuse('%s: there is no sealed path function' % MODELS)
    body = nm[a:nm.find('\ndef ', a + 10)]

    # NOTHING THAT MOVES. This is the whole round.
    for moving, why in (
            ('strftime', 'a clock - the two calls straddle a second on '
                         'any loaded machine, which is how this was '
                         'found'),
            ('now()', 'a clock'),
            ('slugify', 'a tenant slug - renaming a tenant is an '
                        'ordinary act, and T2-1 made it a commoner one'),
            ('tenant_name', 'the tenant name, which can be edited')):
        if moving in body:
            refuse('%s: the sealed path still depends on %s (%s). A '
                   're-seal must land on the name the last one did, '
                   'and anything that can change between two calls '
                   'defeats that.' % (MODELS, moving, why))

    if 'os.path.join' in body:
        refuse('%s: the sealed path uses os.path.join, which gives '
               'Windows a backslash key and Linux a slash. ES-2 fixed '
               'exactly this in page_name on 23 October.' % MODELS)
    if 'instance.pk' not in body:
        refuse('%s: the sealed path is not built from the primary key, '
               'which is the only ingredient that never moves.'
               % MODELS)

    # AND THE FIELD REALLY USES IT.
    if 'upload_to=lease_sealed_upload_path' not in nm:
        refuse('%s: sealed_pdf does not use the new path, so nothing '
               'this round wrote is reached.' % MODELS)

    # THE ORIGINAL IS DELIBERATELY LEFT ALONE.
    if 'original_pdf = models.FileField(upload_to=' \
            'lease_signing_upload_path' not in nm.replace('\n', '').replace(
                '                                    ', ''):
        i_o = nm.find('original_pdf = models.FileField')
        if 'lease_signing_upload_path' not in nm[i_o:i_o + 200]:
            refuse('%s: original_pdf no longer uses the timestamped '
                   'path. Uploading a REPLACEMENT lease is a different '
                   'act from re-sealing the same one, and two '
                   'documents want two names.' % MODELS)

    # seal() REFUSES AN UNSAVED ENVELOPE.
    ns = T.python_code_only(out[ps], payloads=True)
    i_s = ns.find('def seal(')
    seg = ns[i_s:ns.find('\ndef ', i_s + 10)] if i_s >= 0 else ''
    if 'signing.pk' not in seg or 'raise' not in seg:
        refuse('%s: seal() does not refuse an unsaved envelope. The '
               'sealed name is built from the primary key; without one '
               'every unsaved envelope is called the same thing.'
               % SEAL)

    # THE MIGRATION IS AN AlterField AND TOUCHES NO DATA.
    g = read(pg)
    if 'AlterField' not in g:
        refuse('%s: expected an AlterField for the changed upload_to'
               % MIG)
    for banned in ('RunPython', 'RunSQL', 'DeleteModel', 'RemoveField'):
        if banned in g:
            refuse('%s names %r. Changing upload_to moves no file and '
                   'touches no row - the names already stored stay '
                   'exactly as they are.' % (MIG, banned))
    names = sorted(n_[:-3] for n_ in
                   os.listdir(os.path.join(root, 'pages', 'migrations'))
                   if n_.endswith('.py') and n_ != '__init__.py'
                   and '.bak_' not in n_)
    mine = [n_ for n_ in names if 'es2a_sealed_name' in n_]
    prior = [n_ for n_ in names if mine and n_ < mine[0]]
    if not prior or ("'%s'" % prior[-1]) not in g.replace('"', "'"):
        refuse('%s: it does not depend on %s, the migration immediately '
               'before it' % (MIG, prior[-1] if prior else '?'))

    if CHECK:
        print('ES-2a  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        plus %s, which this round CREATES' % MIG)
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('ES-2a  applied - the sealed pdf is named from the primary '
          'key, so a re-seal lands where the last one did.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      plus %s, which this round CREATES' % MIG)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
