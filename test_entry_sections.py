"""test_entry_sections.py - entry sections, push 1: one component, and base
   owns the phone.

    python test_entry_sections.py

Run from the repo root, after apply_entry_sections_1.py.

WHAT THIS SUITE IS FOR

  * SECTION 1 checks BASE, because the round's premise is that base owns the
    section component and both halves of the phone. It also insists the media
    query says `screen and` - base already carries one bare
    `@media (max-width: 768px)`, A4 portrait is about 718 CSS px of content,
    and that one fires on paper.

  * SECTION 3 compares every heading's text with the .bak_sect1 backup byte
    for byte, and NAMES the single wording change rather than permitting
    movement in general. A suite that allows drift finds none.

  * SECTION 4 is the round's hard promise: push 1 moves no fields, so the
    ordered list of name= attributes is an EQUALITY against the backup, not a
    list of exceptions.

  * SECTION 5 exists because one of these headings is a control. It opens and
    closes a notification card; six CSS rules and a line of JavaScript
    reached for it by tag. A suite that only checked how the heading LOOKS
    would have passed a page whose cards no longer open.

  * SECTION 7 renders, at 375, 390, 768 and 1280, WITH BOOTSTRAP AND BASE
    INLINED. A rendering test that renders without the page's stylesheet
    measures nothing: the btn-sm round reported browser defaults as the
    system's numbers, and the panel-title round did it again five days later.
    1280 is carried as a control, because without one a rule that fires at
    every width passes every phone check.

WHAT IT DELIBERATELY DOES NOT FAIL ON

    Tap targets. Every .form-control renders 41px and every .btn 38px against
    a 44px target, on every entry screen, and did so before this round. It is
    reported at the end. A suite that fails on inherited debt blocks the push
    without telling anybody anything they did not already know.
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

# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import json
import os
import re
import sys

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_sect1'
TAG, CLS = 'h3', 'form-section-title'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_entry_sections.py'
BOOT = 'test_fixture_bootstrap413.css'
EMOJI = '\U0001f525'

# What push 1 claimed it would do, per file. The suite asserts the claim; it
# does not re-derive it from the markup, because a test that asks the code
# what it did agrees with the code by construction.
CLAIM = {
    'notification_settings.html': 13,
    'personal_notification_settings.html': 2,
    'edit_asset.html': 2,
    'property_assets.html': 1,
    'customer_invoice_form.html': 1,
    'create_meal_plan.html': 2,
    'preview_imported_recipe.html': 8,
}
# customer_invoice_form already carried one before this round - stage D put
# it on the Customer panel - so the file's total is claim + this.
ALREADY = {'customer_invoice_form.html': 1}

RETIRED = ('section-title', 'form-section-heading', 'lines-title',
           'pi-section-title')

passed = failed = skipped = 0
notes = []


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


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def markup_only(text):
    """<script> and <style> bodies blanked to spaces, offsets preserved."""
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def css_of(text):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))


def plain(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


def all_rules(css):
    """(selector, body) for every rule, at the top level AND inside every
    @media. A walk that skipped @media has been a bug in four rounds; the
    last shape of it was a COMMENT in front of the @, which made the at-rule
    invisible to a startswith('@') test."""
    out = []

    def bare(s):
        return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).strip()

    def walk(text):
        i, n = 0, len(text)
        while i < n:
            b = text.find('{', i)
            if b < 0:
                return
            sel, depth, j = text[i:b], 1, b + 1
            while j < n and depth:
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                j += 1
            if bare(sel).startswith('@') and '{' in text[b + 1:j]:
                walk(text[b + 1:j - 1])
            else:
                out.append((re.sub(r'\s+', ' ', bare(sel)),
                            re.sub(r'\s+', ' ', text[b + 1:j - 1]).strip()))
            i = j
    walk(css)
    return out


def headings(text):
    return list(re.finditer(r'<%s class="%s">(.*?)</%s>' % (TAG, CLS, TAG),
                            markup_only(text), re.S))


def fields(text):
    """The ordered list of every control's name=. The round's hard promise."""
    out = []
    for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>',
                         markup_only(text), re.I):
        n = re.search(r'\bname\s*=\s*["\']([^"\']+)', m.group(2))
        out.append(n.group(1) if n else '-')
    return out


BASE = read(os.path.join(ROOT, 'base.html'))
BASE_CSS = css_of(BASE)


# ==========================================================================
print('\n' + '=' * 74)
print('1. BASE DECLARES THE COMPONENT, AND BOTH HALVES OF THE PHONE')
print('=' * 74)
print("""
   The round's premise is that base owns this, so base is where it is
   checked. The zoom guard is the half worth stating plainly: iOS Safari
   zooms the page whenever a focused input is under 16px, .form-control was
   14px, and 62 pages had each written their own guard before base did.
""")

rules = all_rules(BASE_CSS)
title = [b for s, b in rules if s == '.' + CLS]
ok(bool(title), 'base declares .%s' % CLS)
if title:
    body = ' '.join(title)
    for prop, want in (('font-size', '16px'), ('padding-bottom', '9px')):
        ok('%s: %s' % (prop, want) in body,
           'base sets %s: %s on the component' % (prop, want), body[:120])
    ok('border-bottom' in body and 'var(--alv-accent)' in body,
       'the accent rule under the title comes from the accent variable')

ok(any(s == '.%s i' % CLS for s, _b in rules),
   'base declares .%s i, so an icon takes the accent' % CLS)
ok(any(s == '.%s small' % CLS for s, _b in rules),
   'base declares .%s small, so a section title can carry a quiet note' % CLS)

# THE MEDIA QUERY MUST SAY `screen and`. base already carries one bare
# `@media (max-width: 768px)`; A4 portrait is about 718 CSS px of content, so
# that one fires on paper. The print-leak round found it the hard way and a
# second instance is not getting in.
def media_blocks(css, head=r'@media\s+screen\s+and\s*\(max-width:\s*768px\)'):
    """EVERY block with this head, brace-matched.

    The first version of this used one regex with a nested-brace character
    class and matched base's FIRST screen-768 block - which is about tables -
    then reported that the panel padding was missing from it. base has three
    of these blocks. A rule is in base if it is in ANY of them, and only
    counting braces can tell you where one ends."""
    out = []
    for m in re.finditer(head + r'\s*\{', css):
        i, depth = m.end(), 1
        while i < len(css) and depth:
            if css[i] == '{':
                depth += 1
            elif css[i] == '}':
                depth -= 1
            i += 1
        out.append(css[m.end():i - 1])
    return out


blocks = media_blocks(BASE_CSS)
ok(bool(blocks), 'base carries an @media screen and (max-width: 768px) block')
if blocks:
    blk = re.sub(r'\s+', ' ', ' '.join(blocks))
    ok('.form-card' in blk and 'padding: 16px 14px' in blk,
       'the panel takes phone padding (measured: 293px -> 313px of field)',
       blk[:160])
    ok('.form-control' in blk and 'font-size: 16px' in blk,
       'the iOS zoom guard is base\'s, not each page\'s', blk[:160])
    ours = [b for b in blocks if '.form-card' in b and 'padding' in b]
    ok(bool(ours) and 'margin-bottom' not in re.sub(r'\s+', ' ', ours[0]),
       'the panel margin is NOT dropped on the phone - at 16px the gap '
       'between panels equals the 16px gap between fields, which erases '
       'the grouping this round exists to create')

_bare = re.findall(r'@media\s*\(max-width', BASE_CSS)
notes.append('base still carries %d bare `@media (max-width: ...)` block(s) '
             'with no `screen`, which fire on paper. Pre-existing; the '
             'print-leak round owns them.' % len(_bare))


# ==========================================================================
print('\n' + '=' * 74)
print('2. EVERY HEADING THIS ROUND TOUCHED IS THE COMPONENT, WITH ONE ICON')
print('=' * 74)

for rel, n in sorted(CLAIM.items()):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        skip(rel, 'not in this checkout')
        continue
    text = read(p)
    hs = headings(text)
    ok(len(hs) == n + ALREADY.get(rel, 0),
       '%-38s %2d component heading(s)' % (rel, n + ALREADY.get(rel, 0)),
       'found %d' % len(hs))
    # THE SECTION ICON IS THE HEADING'S FIRST CHILD, and counting every <i>
    # inside the heading is not the same question. Four of
    # preview_imported_recipe's headings carry an "AI Extracted" badge behind
    # {% if mode == 'import' %}, and that badge has an icon of its own that
    # belongs to it. What the component requires is that the heading OPENS
    # with exactly one icon; what the badge does inside a <span> is the
    # badge's business.
    bad = []
    for h in hs:
        inner = h.group(1)
        lead = re.match(r'\s*(<i\s[^>]*class="[^"]*\bfa[srlbd]?\b[^"]*"'
                        r'[^>]*>\s*</i>\s*)+', inner)
        n_lead = len(re.findall(r'<i\s', lead.group(0))) if lead else 0
        if n_lead != 1:
            bad.append('%s -> opens with %d icon(s)'
                       % (plain(inner)[:40], n_lead))
    ok(not bad, '%-38s opens with exactly one icon' % rel, '\n'.join(bad))

# The old dialects are gone from the files this round touched - and ONLY
# from those. A page this round never opened is not this round's failure.
for rel in sorted(CLAIM):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        continue
    mk = markup_only(read(p))
    left = [c for c in RETIRED
            if re.search(r'class\s*=\s*"[^"]*(?<![\w-])%s(?![\w-])' % c, mk)]
    ok(not left, '%-38s no retired class left on its markup' % rel, left)


# ==========================================================================
print('\n' + '=' * 74)
print('3. NO HEADING SAYS ANYTHING DIFFERENT THAN IT DID')
print('=' * 74)
print("""
   Compared against the .bak_sect1 backups, byte for byte. ONE exception is
   named rather than movement allowed in general: preview_imported_recipe's
   Cooking Calculator heading loses a fire emoji, because fa-fire now does
   that job. The emoji is in four other places on that page and none of them
   is this round's business.
""")

WORDING_EXCEPTIONS = {('preview_imported_recipe.html', 'Cooking Calculator')}

for rel in sorted(CLAIM):
    p = os.path.join(ROOT, rel)
    bak = p + SUFFIX
    if not os.path.isfile(bak):
        skip('%-38s wording unchanged' % rel,
             'no %s backup - it has been cleared' % SUFFIX)
        continue
    was = read(bak)
    now = read(p)
    old = [plain(m.group(1)) for m in re.finditer(
        r'<h[1-6][^>]*>(.*?)</h[1-6]>', markup_only(was), re.S)]
    new = [plain(m.group(1)) for m in re.finditer(
        r'<h[1-6][^>]*>(.*?)</h[1-6]>', markup_only(now), re.S)]
    drift = []
    for a, b in zip(old, new):
        if a == b:
            continue
        if a.lstrip(EMOJI + ' ') == b and \
                any(k in b for _f, k in WORDING_EXCEPTIONS
                    if _f == rel):
            continue
        drift.append('%r -> %r' % (a[:52], b[:52]))
    ok(len(old) == len(new) and not drift,
       '%-38s every heading reads as it did' % rel,
       '\n'.join(drift) or 'heading count %d -> %d' % (len(old), len(new)))
    ok(EMOJI not in ' '.join(
        plain(h.group(1)) for h in headings(now)),
       '%-38s no emoji left in a section title' % rel)


# ==========================================================================
print('\n' + '=' * 74)
print('4. NO FIELD MOVED, AND NONE WAS LOST')
print('=' * 74)
print("""
   Push 1 moves no fields at all - that is pushes 2 and 3 - so this is an
   equality and not a list of exceptions. A round that can silently reorder
   a form is a round that can silently drop a field from it.
""")

for rel in sorted(CLAIM):
    p = os.path.join(ROOT, rel)
    bak = p + SUFFIX
    if not os.path.isfile(bak):
        skip('%-38s field order' % rel, 'no %s backup' % SUFFIX)
        continue
    a, b = fields(read(bak)), fields(read(p))
    diff = ''
    if a != b:
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                diff = 'first difference at %d: %r -> %r' % (i, x, y)
                break
        diff = diff or 'length %d -> %d' % (len(a), len(b))
    ok(a == b, '%-38s %3d field(s), same order' % (rel, len(b)), diff)


# ==========================================================================
print('\n' + '=' * 74)
print('5. THE COLLAPSE STILL WORKS')
print('=' * 74)
print("""
   notification_settings' section title is not a label, it is the control
   that opens the card. Six CSS rules selected `.notification-card > h5` and
   one line of JavaScript did card.querySelector('h5'). Both now name the
   component, which is the correct selector either way: what makes that
   element the trigger is that it is the card's title, not its tag.
""")

for rel in ('notification_settings.html', 'personal_notification_settings.html'):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        skip(rel, 'not in this checkout')
        continue
    text = read(p)
    stale = [s for s, _b in all_rules(css_of(text))
             if re.search(r'\.notification-card[^,{]*\bh5\b', s)]
    ok(not stale, '%-38s no rule still selects the old tag' % rel, stale)
    js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', text, re.S))
    hooks = re.findall(r'querySelector\w*\(\s*[\'"]([^\'"]+)', js)
    ok(not any(h.strip() in ('h5', 'h4', 'h2') for h in hooks),
       '%-38s no script reaches for a bare heading tag' % rel, hooks)
    if 'card-body-wrap' in text:
        ok("querySelector('.%s')" % CLS in js,
           '%-38s the collapse hook names the component' % rel)
    # the panel wears base's panel now, and still carries its own state
    mk = markup_only(text)
    n_card = len(re.findall(r'class="[^"]*notification-card[^"]*"', mk))
    n_both = len(re.findall(
        r'class="[^"]*notification-card form-card[^"]*"', mk))
    ok(n_card == n_both and n_card == CLAIM[rel],
       '%-38s all %d card(s) keep their name AND take base\'s panel'
       % (rel, CLAIM[rel]), '%d cards, %d with form-card' % (n_card, n_both))


# ==========================================================================
print('\n' + '=' * 74)
print('6. NO PAGE RESTATES WHAT BASE OWNS, AND NOTHING STYLES A DEAD CLASS')
print('=' * 74)
print("""
   Section 4 of the panel-title suite reports 282 rules across the system
   that name a class no markup wears. This one FAILS only on what THIS round
   could have orphaned, and reports the rest - a suite that fails on
   inherited debt blocks the push without telling anyone anything new.
""")

scoped = []
for rel in sorted(CLAIM):
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        continue
    text = read(p)
    mk = markup_only(text)
    orphan, restated = [], []
    for sel, body in all_rules(css_of(text)):
        names = set(re.findall(r'\.([A-Za-z][\w-]*)', sel))
        for c in names & set(RETIRED):
            if not re.search(r'class\s*=\s*"[^"]*(?<![\w-])%s(?![\w-])' % c,
                             mk):
                orphan.append('%s { %s }' % (sel, body[:60]))
        if re.fullmatch(r'\.%s' % CLS, sel):
            restated.append('%s { %s }' % (sel, body[:60]))
        elif CLS in names and len(names) > 1:
            scoped.append('%-38s %s' % (rel, sel))
    ok(not orphan, '%-38s no rule names a class this round retired' % rel,
       '\n'.join(orphan))
    ok(not restated,
       '%-38s does not restate the component base declares' % rel,
       '\n'.join(restated))

if scoped:
    notes.append('%d scoped rule(s) survive on purpose - they say something '
                 'about ONE place that base cannot say for everywhere:\n     '
                 % len(scoped) + '\n     '.join(scoped))


# ==========================================================================
print('\n' + '=' * 74)
print('7. RENDERED ON A PHONE, WITH THE STYLESHEET THE PAGE ACTUALLY HAS')
print('=' * 74)
print("""
   A rendering test that renders without the page's stylesheet measures
   nothing. Two rounds this month reported browser defaults as the system's
   numbers because the CDN is unreachable from here - the btn-sm round and
   then the panel-title round, five days apart. So Bootstrap 4.1.3 is
   inlined from %s and base's own <style> after it, in
   the order the page loads them, and 1280 is carried as a control so a rule
   that only works on a phone cannot pass.
""" % BOOT)

if not os.path.isfile(BOOT):
    skip('the phone', '%s not on disk' % BOOT)
else:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        skip('the phone', 'playwright not importable: %s' % str(e)[:60])
        sync_playwright = None

    if 'sync_playwright' in dir() and sync_playwright:
        boot = read(BOOT)
        page_html = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>phone</title><style>%s</style><style>%s</style></head><body>
<div class="container-fluid" style="padding:16px">
<form method="post">
 <div class="form-card"><h3 class="form-section-title">
   <i class="fas fa-home"></i> Property</h3>
   <div class="form-row">
     <div class="col-md-4"><div class="form-group"><label><strong>Property
       Name</strong></label><input type="text" class="form-control"></div></div>
     <div class="col-md-4"><div class="form-group"><label><strong>Floor
       Area</strong></label><input type="text" class="form-control"></div></div>
   </div></div>
 <div class="form-card"><h3 class="form-section-title">
   <i class="fas fa-camera"></i> Photos
   <small class="text-muted">(up to 5 per asset)</small></h3>
   <div class="form-row">
     <div class="col-md-4"><div class="form-group"><label><strong>Status
       </strong></label><select class="form-control"><option>-</option>
       </select></div></div>
   </div></div>
</form></div></body></html>""" % (boot, BASE_CSS)

        fx = os.path.join(SCRATCH, '_sections_phone.html')
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(page_html)

        JS = r"""() => {
          const px = s => parseFloat(s) || 0;
          const cards = [...document.querySelectorAll('.form-card')];
          const titles = [...document.querySelectorAll('.form-section-title')];
          const cols = [...document.querySelectorAll('[class*="col-md-"]')];
          const lines = {};
          cols.forEach(c => { const t = Math.round(
              c.getBoundingClientRect().top); lines[t] = (lines[t]||0)+1; });
          const g = cards[0].querySelectorAll('.form-group');
          const cs = getComputedStyle(cards[0]);
          const ts = getComputedStyle(titles[0]);
          const sm = document.querySelector('.form-section-title small');
          return {
            scrollW: document.documentElement.scrollWidth,
            innerW: window.innerWidth,
            shared: Object.values(lines).filter(n => n > 1).length,
            titleFont: px(ts.fontSize),
            titleClipped: titles.some(t => t.scrollWidth > t.clientWidth + 1),
            labelFont: px(getComputedStyle(
                document.querySelector('.form-group label')).fontSize),
            ctrlFont: px(getComputedStyle(
                document.querySelector('.form-control')).fontSize),
            cardPadL: px(cs.paddingLeft),
            cardInnerW: Math.round(cards[0].clientWidth
                        - px(cs.paddingLeft) - px(cs.paddingRight)),
            cardGap: Math.round(cards[1].getBoundingClientRect().top
                     - cards[0].getBoundingClientRect().bottom),
            fieldGap: g.length > 1 ? Math.round(
                g[1].getBoundingClientRect().top
                - g[0].getBoundingClientRect().bottom) : null,
            smallWeight: sm ? getComputedStyle(sm).fontWeight : null,
            smallDisplay: sm ? getComputedStyle(sm).display : null,
            ctrlH: Math.round(document.querySelector('.form-control')
                   .getBoundingClientRect().height),
          };
        }"""

        M = {}
        with sync_playwright() as pw:
            exe = '/opt/pw-browsers/chromium'
            br = pw.chromium.launch(
                **({'executable_path': exe} if os.path.exists(exe) else {}))
            for w, h in ((375, 667), (390, 844), (768, 1024), (1280, 900)):
                ctx = br.new_context(viewport={'width': w, 'height': h})
                pg = ctx.new_page()
                _goto(pg, fx)
                pg.wait_for_timeout(120)
                M[w] = pg.evaluate(JS)
                ctx.close()
            br.close()

        for w in (375, 390):
            m = M[w]
            ok(m['scrollW'] <= m['innerW'],
               '%d wide  no horizontal scroll' % w,
               '%d > %d' % (m['scrollW'], m['innerW']))
            ok(not m['titleClipped'], '%d wide  no section title clipped' % w)
            ok(m['shared'] == 0, '%d wide  every field on its own line' % w,
               '%d line(s) shared' % m['shared'])
            ok(m['titleFont'] >= m['labelFont'],
               '%d wide  title %gpx is not smaller than labels %gpx'
               % (w, m['titleFont'], m['labelFont']))
            ok(m['cardGap'] > m['fieldGap'],
               '%d wide  panels are further apart (%dpx) than the fields '
               'inside them (%dpx)' % (w, m['cardGap'], m['fieldGap']))
            ok(m['ctrlFont'] >= 16,
               '%d wide  controls are %gpx, so iOS does not zoom on focus'
               % (w, m['ctrlFont']))
            ok(m['cardPadL'] == 14,
               '%d wide  the panel takes phone padding' % w,
               'padding-left %g' % m['cardPadL'])
            ok(m['smallWeight'] in ('400', 400),
               '%d wide  a title\'s quiet note keeps its own weight' % w,
               m['smallWeight'])

        # THE CONTROL. Without it a rule that fires at every width passes the
        # eight checks above and nobody notices.
        d = M[1280]
        ok(d['cardPadL'] == 24,
           '1280 control  the desktop panel keeps 24px padding, so the '
           'phone rule is a phone rule', 'padding-left %g' % d['cardPadL'])
        ok(d['ctrlFont'] == 14,
           '1280 control  desktop controls stay 14px', d['ctrlFont'])
        ok(M[768]['ctrlFont'] >= 16,
           '768 (the breakpoint itself) is on the phone side')

        # THE GUARD FIXED SOMETHING IT WAS NOT AIMED AT, and the honest
        # thing is to say which half. A control sized to stop iOS zooming is
        # also a control big enough to hit: 16px text inside .form-control's
        # 9px padding and 2px border comes out at 46px, over the 44px target
        # it was failing at 41px before. On the DESKTOP nothing changed -
        # 14px still gives 40px - so the tap-target round is still owed, it
        # is just no longer owed on a phone.
        notes.append(
            'TAP TARGETS, reported and not asserted: %dpx at 375 wide '
            '(was 41px before the zoom guard, against a 44px target) and '
            '%dpx at 1280. The phone half of that debt is paid as a side '
            'effect of the guard; the desktop half is still owed and is '
            'still its own round.' % (M[375]['ctrlH'], M[1280]['ctrlH']))
        notes.append(
            'MEASURED: %dpx of usable field width at 375 wide, %dpx at 390.'
            % (M[375]['cardInnerW'], M[390]['cardInnerW']))


# ==========================================================================
print('\n' + '=' * 74)
print('8. THIS SUITE IS ON THE GATE')
print('=' * 74)

if not os.path.isfile(PS1):
    skip('on the gate', '%s not on disk' % PS1)
else:
    ps = read(PS1)
    ok("'%s'" % ME in ps, '%s runs %s' % (PS1, ME))


# ==========================================================================
print('\n' + '=' * 74)
if notes:
    print('NOTED, NOT FAILED')
    print('=' * 74)
    for n in notes:
        print('  *  %s' % n)
    print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
