# -*- coding: utf-8 -*-
"""test_pl_seg.py - Section SG round SG-2, 3 Oct 2026.

The last two hand-rolled segmented controls in the tree.

finance_pl_act's Budget / Actuals had been on the outstanding list longest.
It did not look like a house control and it did not look like a Bootstrap
one either: the SELECTED half was teal, from a local rule overriding
.btn-info, and the UNSELECTED half had no local rule at all, so it was
Bootstrap's raw .btn-outline-info - #17a2b8, a blue-cyan in no palette.
Reading the stylesheet you would think the whole control was house
coloured. Half of it was.

property_assets' Group by was found BY THIS ROUND'S OWN CLOSING GATE and
taken in the same bundle on Demetri's say-so. Every census of btn-info in
this tree had missed it for a month, because the class name is ASSEMBLED
ACROSS A TEMPLATE TAG:

    class="btn btn-{% if group_by == 'category' %}info{% else %}outline-info{% endif %}"

There is no string "btn-info" anywhere in that file. Section 4 keeps the
census that found it, in the form that can find the next one.

SECTION 3 IS THE PART THAT COULD HAVE GONE WRONG QUIETLY. Both controls
are LINKS carrying a whole query string - year, view, single mode and
every selected property on one, the group and a next URL on the other. A
control restyled into dropping a parameter would lose the reader's
selection on every toggle and look perfect doing it.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
import os
import re
import sys
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_plseg'
ME = 'test_pl_seg.py'
PATCHER = 'apply_pl_seg.py'
PS1 = 'Push-PendingChanges.ps1'
PL = 'finance_pl_act.html'
AS = 'property_assets.html'
PAGES = (PL, AS)
SCRATCH = tempfile.mkdtemp(prefix='alv_plseg_')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))




NOW = {p: now(alv_tree.path_of(p)) for p in PAGES}
CODE = {p: code_only(NOW[p]) for p in PAGES}
WAS = {p: code_only(was(alv_tree.path_of(p))) for p in PAGES}
BASE = read(alv_tree.path_of('base.html'))
BCODE = code_only(BASE)

print('=' * 74)
print('%s - SG-2, THE LAST TWO HAND-ROLLED SEGMENTS' % ME)
print('=' * 74)

# ==========================================================================
head('1. BOTH WEAR base\'s CONTROL')
# ==========================================================================
for p in PAGES:
    ok(CODE[p].count('class="alv-seg"') == 1,
       '%s wears exactly one seg' % p.replace('.html', ''),
       CODE[p].count('class="alv-seg"'))
    seg = CODE[p][CODE[p].index('<div class="alv-seg"'):]
    seg = seg[:seg.index('</div>')]
    ok(len(re.findall(r'<a\s', seg)) == 2,
       '  with two halves, both links')
    ok(seg.count('aria-current="page"') == 2,
       '  each marked aria-current when it is the current view')
    ok('class="active"' not in seg and 'btn-info' not in seg,
       '  and nothing marks it with a class as well')
ok('.alv-seg > [aria-current="page"]' in BCODE,
   'base fills a current segment')
ok('--alv-accent' in BCODE[BCODE.index('.alv-seg > [aria-pressed="true"]'):
                           BCODE.index('.alv-seg > [aria-pressed="true"]') + 300],
   'and fills it with the accent, not a literal')

# ==========================================================================
head('2. THE OLD NAMES AND THE ONE LITERAL')
# ==========================================================================
for dead in ('btn-info', 'pl-view-toggle'):
    ok(not re.search(r'\b%s\b' % dead, CODE[PL]),
       '%s is gone from finance_pl_act' % dead)
ok(not re.search(r'\bview-toggle-group\b', CODE[AS]),
   'view-toggle-group is gone from property_assets')
ok("btn-{% if group_by" not in CODE[AS],
   'and so is the class name assembled across a template tag')

if WAS[PL]:
    ok(WAS[PL].count('#0e7c8b') - CODE[PL].count('#0e7c8b') == 2,
       'finance_pl_act dropped two uses of #0e7c8b',
       '%d before, %d after' % (WAS[PL].count('#0e7c8b'),
                                CODE[PL].count('#0e7c8b')))
    # THE PREMISE, BOTH HALVES OF IT.
    ok('.btn-info {' in WAS[PL],
       'CONTROL: the page really did style .btn-info locally - which is '
       'why the selected half was teal')
    ok(not re.search(r'\.btn-outline-info\s*[,{]', WAS[PL]),
       'CONTROL: and it did NOT style .btn-outline-info - which is why '
       'the unselected half was Bootstrap raw')
else:
    skip('the finance_pl_act controls', 'no %s backup' % SUFFIX)

if WAS[AS]:
    ok("btn-{% if group_by" in WAS[AS],
       'CONTROL: property_assets really did assemble its class across a '
       'template tag, which is why no census of btn-info ever found it')
    # AND A CLAIM THIS ROUND IS NOT ENTITLED TO MAKE.
    ok('btn-outline-info' in CODE[AS],
       'btn-outline-info survives on property_assets - it also dresses a '
       'camera-capture label, which this round never touched')
else:
    skip('the property_assets controls', 'no %s backup' % SUFFIX)

# ==========================================================================
head('3. THE LINKS DID NOT CHANGE')
# ==========================================================================
# A control restyled into dropping a query parameter would lose the
# reader's selection on every toggle and look perfect doing it.
if WAS[PL]:
    for part in ('single=1', 'properties={{ prop_id }}', 'forloop.last',
                 'selected_year', 'view=budget', 'view=actuals'):
        ok(CODE[PL].count(part) == WAS[PL].count(part),
           'finance_pl_act still carries %s %d time(s)'
           % (part, CODE[PL].count(part)),
           '%d before, %d after' % (WAS[PL].count(part),
                                    CODE[PL].count(part)))
if WAS[AS]:
    for part in ('?group_by=category', '?group_by=room', 'request.GET.next'):
        ok(CODE[AS].count(part) == WAS[AS].count(part),
           'property_assets still carries %s' % part,
           '%d before, %d after' % (WAS[AS].count(part),
                                    CODE[AS].count(part)))

# ==========================================================================
head('4. THE CENSUS THAT FOUND THE EIGHTH')
# ==========================================================================
# Kept in the form that can find the next one: it sweeps for the
# CONSTRUCT - a class attribute BUILDING a Bootstrap tone out of a
# conditional - not for a string that an {% if %} can split in half.
hand = []
for rel in sorted(alv_tree.templates()):
    src = code_only(read(alv_tree.path_of(rel)))
    if re.search(r'class="[^"]*btn-\{%\s*if', src):
        hand.append(os.path.basename(rel))
ok(not hand,
   'no template assembles a Bootstrap button tone across a template tag',
   '\n'.join(hand))

# AND THE CONTROL FOR THE CENSUS ITSELF. If it cannot find the thing it
# was written to find, its silence means nothing.
probe = 'class="btn btn-{% if x %}info{% else %}outline-info{% endif %}"'
ok(bool(re.search(r'class="[^"]*btn-\{%\s*if', probe)),
   'CONTROL: the census does match the construct it is looking for')

# ==========================================================================
head('5. code_only READS THESE PAGES AT ALL')
# ==========================================================================
# property_assets carries accept="image/*". `/*` is not a comment opener
# in markup, and a code_only that treats it as one blanks 1,385
# characters of real markup down to the next */ in a stylesheet far
# below - which is exactly how this round's first gate came to report a
# class as absent while grep found it on line 355.
ok('accept="image/*"' in NOW[AS],
   'property_assets really does carry accept="image/*"')
ok('btn-outline-info' in CODE[AS],
   'and code_only can still see past it')
naive = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)),
               re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)),
                      NOW[AS], flags=re.S), flags=re.S)
ok('btn-outline-info' not in naive,
   'CONTROL: the naive form really does lose it - five templates in this '
   'tree carry one, and every gate that blanks comments the usual way is '
   'blind to a window on all five')


# ==========================================================================
head('6. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG_ = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rws = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG_.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rws.append(f)
ok(len(rws) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rws))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rws:
    pth = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(pth):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b2 = read(pth)
    if r.get('Code'):
        b2 = _strip(b2)
    if (r['Text'].lower() in b2.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rws),
   '\n'.join(stale[:6]))

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
