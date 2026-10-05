# -*- coding: utf-8 -*-
"""test_row_exempt.py - Section RA round RA-5, 5 Oct 2026.

The slot was called RA-3c and said: wrap the last four loose icon
buttons. Reading the markup says they should not be wrapped. Each is a
single Remove button beside the thing it removes, and a .row-actions
around one control tells the report there is an action column with one
action in it.

So the report learns to say NAMED instead, with the reason, out of a
register that lives beside the order itself.

SECTION 3 IS THE CLAIM THE REGISTER CANNOT MAKE FOR ITSELF. A register
is a judgement; it would be worth nothing if nobody checked the
judgement. Section 3 finds each registered button's enclosing element
and requires it to hold exactly one icon control - which is what "not an
action column" means, stated so a machine can refuse it.

SECTION 4 IS THE OTHER HALF: a register must not be able to hide
anything. A fifth loose button planted on a registered page makes the
count stop matching, and the report calls it a problem by name and exits
non-zero under --strict.
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
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree
import alv_rowactions as RA

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_rowexempt'
ME = 'test_row_exempt.py'
PATCHER = 'apply_row_exempt.py'
REPORT = 'Show-RowActionDrift.py'
PS1 = 'Push-PendingChanges.ps1'

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


BLOCKS = ('div', 'td', 'li', 'tr', 'section', 'form')
OPEN = re.compile(r'<(' + '|'.join(BLOCKS) + r')\b[^>]*>', re.I)
CLOSE = re.compile(r'</(' + '|'.join(BLOCKS) + r')\s*>', re.I)


SCRIPT = re.compile(r'<script\b[^>]*>.*?</script>', re.S | re.I)


def enclosing(src, pos):
    """The innermost block element that is still open at `pos`.

    OR, INSIDE A <script>, THE TEMPLATE LITERAL THE MARKUP IS WRITTEN IN.
    create_meal_plan builds its rows with
    `document.createElement('div')` and an innerHTML template literal, so
    the element the button sits in DOES NOT EXIST in the file - there is
    no enclosing tag to find, and the backward scan walks out of the
    script and returns some ancestor holding all three. The literal is
    the element, as written; that is the unit to count in.

    Scanned backwards, counting each tag name's own closes, because
    <div><span></span><div></div> and a regex that counted any close
    against any open would walk straight past the element it wanted.
    Returns (start, end) or None when nothing encloses it.
    """
    insc = next((m for m in SCRIPT.finditer(src)
                 if m.start() <= pos < m.end()), None)
    if insc:
        body, base = insc.group(0), insc.start()
        ticks = [i for i, ch in enumerate(body) if ch == '`'
                 and (i == 0 or body[i - 1] != chr(92))]
        for a, b in zip(ticks[0::2], ticks[1::2]):
            if base + a <= pos < base + b:
                return (base + a, base + b)
        return None

    best = None
    for m in reversed(list(OPEN.finditer(src, 0, pos))):
        name = m.group(1).lower()
        closes = len(CLOSE.findall(src, m.end(), pos))
        opens = len([x for x in OPEN.finditer(src, m.end(), pos)
                     if x.group(1).lower() == name])
        mine = len([c for c in CLOSE.finditer(src, m.end(), pos)
                    if c.group(1).lower() == name])
        if mine <= opens:
            best = m
            break
    if best is None:
        return None
    # forward to its matching close
    d, i = 1, best.end()
    name = best.group(1).lower()
    while d:
        o = re.compile(r'<%s\b[^>]*>' % name, re.I).search(src, i)
        c = re.compile(r'</%s\s*>' % name, re.I).search(src, i)
        if not c:
            return (best.start(), len(src))
        if o and o.start() < c.start():
            d += 1
            i = o.end()
        else:
            d -= 1
            i = c.end()
    return (best.start(), i)


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the register')

ok(hasattr(RA, 'NAMED') and isinstance(RA.NAMED, dict),
   'alv_rowactions carries a NAMED register')
ok(hasattr(RA, 'named'), '  and a named() that reads it')
total = sum(e['count'] for e in RA.NAMED.values())
ok(total == 4, 'it names %d control(s) on %d page(s)'
   % (total, len(RA.NAMED)), total)
for pg, e in sorted(RA.NAMED.items()):
    ok(e['why'] and len(e['why']) > 40,
       '  %-28s %d  %s' % (pg, e['count'], e['classes'][0]),
       'the entry has no reason worth reading')
    print('        %s' % e['why'][:72])

# A REGISTER OF PAGES THAT DO NOT EXIST WOULD PASS EVERY OTHER CHECK.
for pg in RA.NAMED:
    ok(alv_tree.path_of(pg) is not None,
       '  %s is a page in this checkout' % pg)

# ==========================================================================
head('2. and the report reads it')

out = subprocess.run([sys.executable, REPORT], capture_output=True,
                     text=True, cwd=ROOT).stdout
ok('NAMED, NOT IN A WRAPPER - 4 button(s) on 2 page(s)' in out,
   'the report names all four', out[-500:])
for pg, e in sorted(RA.NAMED.items()):
    ok(pg in out, '  %s appears in it' % pg)
    ok(e['why'].split(' - ')[0][:28] in out,
       '  with its reason printed beside it')
m = re.search(r'NOT IN A \.row-actions WRAPPER - (\d+) button', out)
ok(m is None,
   'and nothing is left unexamined - the section is gone',
   'it still reports %s' % (m.group(1) if m else '?'))
ok('Nothing drifting' in out, '  the report is still clean')

# ==========================================================================
head('3. each one really is alone where it sits')

for pg, e in sorted(RA.NAMED.items()):
    src = alv_tree.code_only(now(alv_tree.path_of(pg)))
    hits = [m for m in RA.BTN_FULL.finditer(src)
            if not any(s <= m.start() < en
                       for s, en, _ in RA.wrappers(src))]
    ok(len(hits) == e['count'],
       '%-28s %d loose control(s), as the register says'
       % (pg, len(hits)), '%d, register says %d' % (len(hits), e['count']))
    alone = 0
    for m in hits:
        span = enclosing(src, m.start())
        if span is None:
            continue
        inner = src[span[0]:span[1]]
        if len(RA.BTN_FULL.findall(inner)) == 1:
            alone += 1
    ok(alone == len(hits),
       '  and %d of %d is the only icon control in its element - which is '
       'what "not an action column" means' % (alone, len(hits)),
       '%d of %d' % (alone, len(hits)))

# THE CONTROL FOR SECTION 3: a page that really does have an action
# column must NOT pass this test, or it proves nothing.
col = alv_tree.path_of('physical_invoice_list.html')
csrc = alv_tree.code_only(now(col))
grouped = 0
for s, en, inner in RA.wrappers(csrc):
    if len(RA.BTN_FULL.findall(inner)) > 1:
        grouped += 1
ok(grouped >= 1,
   'CONTROL: physical_invoice_list has %d wrapper(s) holding more than one '
   'control, and would fail section 3 if it were registered' % grouped,
   grouped)

# ==========================================================================
head('4. the register cannot hide anything')

# Plant a fifth loose button on a registered page and require the report
# to refuse it rather than absorb it.
victim = alv_tree.path_of('edit_asset.html')
src = read(victim)
# APPENDED, NOT INJECTED AT </body>. edit_asset extends base and has no
# </body> of its own, so the first build of this control planted nothing
# and then reported that the register had absorbed it - a control that
# passed by doing nothing at all.
extra = ('\n<button type="button" class="icon-action-btn icon-edit" '
         'title="planted"><i class="fas fa-pen"></i></button>\n')
planted = src + extra
ok(planted != src and '</body>' not in src,
   'the control could be planted - and this page has no </body> to use')

bak = victim + '.ra5probe'
try:
    with open(bak, 'wb') as fh:
        fh.write(read(victim).encode('utf-8'))
    with open(victim, 'w', encoding='utf-8', newline='') as fh:
        fh.write(planted)
    r = subprocess.run([sys.executable, REPORT, '--strict'],
                       capture_output=True, text=True, cwd=ROOT)
finally:
    with open(bak, 'rb') as fh:
        data = fh.read()
    with open(victim, 'w', encoding='utf-8', newline='') as fh:
        fh.write(data.decode('utf-8'))
    os.remove(bak)

ok('REGISTERED COUNT HAS MOVED' in r.stdout,
   'a fifth loose button makes the count stop matching',
   r.stdout[-600:])
ok('edit_asset.html' in r.stdout, '  and the page is named')
ok(r.returncode != 0,
   '  and --strict exits non-zero on it', r.returncode)
ok(read(victim) == src, '  and the page was put back exactly as it was')

# ==========================================================================
head('5. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(os.path.exists(os.path.join(ROOT, REPORT + SUFFIX)),
   '%s has a %s backup - this round changed TWO files' % (REPORT, SUFFIX))

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that these four are the RIGHT judgement. The')
print('  register records a decision Demetri made about one of them and')
print('  this round extended to the other three on the ground that they')
print('  are the same control. Section 3 proves each is alone where it')
print('  sits; whether a lone Remove button should be in a column at all')
print('  is a question for a person.')
