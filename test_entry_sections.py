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

  * SECTIONS 9 TO 12 are push 2 - the half that CREATES panels and MOVES
    fields. Section 10 is the one that changed shape: push 1's field check
    was an EQUALITY because push 1 moved nothing, and push 2 moves seven
    controls, so it takes the named movers OUT of both lists and requires
    what is left to be in exactly the order it was. THE INVARIANT IS
    RELATIVE ORDER, NOT ABSOLUTE POSITION - comparing each field's index
    flagged nineteen fields across four screens that had not moved relative
    to anything, they had simply been stepped over.

    Section 10 also COUNTS THE FORM TAGS. Rebuilding a panel that contains
    the <form> deletes the open tag and its close together, so a balance
    check stays at zero and passes a file with no form in it. The first
    draft of the push-2 tool did exactly that to customer_form and the
    balance check passed it.

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


# Each round's backup IS the state the previous round left behind, so a
# check about round N reads the backup of the EARLIEST round after N that
# touched this file - and the live file only if none did.
LATER_BACKUPS = {1: ('.bak_sect2', '.bak_sect3'),
                 2: ('.bak_sect3',)}


def state_after(p, n):
    """The file as round n left it.

    Sections 2 to 4 are about push 1, and once a later push has run the
    live file is no longer push 1's output - customer_invoice_form gained
    two more titles in push 2, so 'every heading reads as it did' zipped
    'Invoice Lines' against 'Email' and failed a round that had done
    nothing wrong.

    THE NEXT ROUND IS NOT ALWAYS THE NEXT NUMBER. edit_asset and
    property_assets were not in push 2 at all, so their post-push-1 state
    is in .bak_sect3. Looking only at .bak_sect2 read the live file and
    failed on push 3's work, which is the same fault one round further on.
    """
    for suf in LATER_BACKUPS.get(n, ()):
        if os.path.isfile(p + suf):
            return read(p + suf)
    return read(p)


def after_push_one(p):
    return state_after(p, 1)


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
    text = after_push_one(p)
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
    mk = markup_only(after_push_one(p))
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
    now = after_push_one(p)
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
    a, b = fields(read(bak)), fields(after_push_one(p))
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
# PUSH 2 - the half that creates panels and moves fields
# ==========================================================================
SUFFIX2 = '.bak_sect2'

# What push 2 claimed, per file: how many titles it puts on the page, and
# whether it built panels or only placed headings.
CLAIM2 = {
    'properties_add.html':                  (4, True),
    'properties_edit.html':                 (4, True),
    'tenant_add.html':                      (4, True),
    'tenant_edit.html':                     (4, True),
    'customer_form.html':                   (2, False),
    'customer_invoice_form.html':           (2, False),
    'act_expense_add.html':                 (1, False),
    'act_expense_edit.html':                (1, False),
    'finance_revenue_add.html':             (1, False),
    'finance_revenue_edit.html':            (1, False),
    'finance_expense_line_types_add.html':  (1, False),
    'finance_expense_line_types_edit.html': (1, False),
    'finance_revenue_line_types_add.html':  (1, False),
    'finance_revenue_line_types_edit.html': (1, False),
    'finance_valuations_add.html':          (1, False),
    'finance_valuations_edit.html':         (1, False),
}
# Titles already on the page before push 2 ran.
ALREADY2 = {'tenant_add.html': 1, 'tenant_edit.html': 1,
            'customer_invoice_form.html': 2}

MOVES2 = {
    'properties_add.html':  ['prop_floor_area', 'prop_year_built'],
    'properties_edit.html': ['prop_floor_area', 'prop_year_built'],
    'tenant_add.html':  ['tenant_current', 'prop', 'tenant_payment_terms'],
    'tenant_edit.html': ['tenant_current', 'prop', 'tenant_payment_terms'],
}

print('\n' + '=' * 74)
print('9. PUSH 2 - EVERY SCREEN CARRIES ITS SECTIONS')
print('=' * 74)

ran2 = any(os.path.isfile(os.path.join(ROOT, r) + SUFFIX2) for r in CLAIM2)
if not ran2:
    skip('push 2', 'no %s backup - push 2 has not run on this tree'
         % SUFFIX2)
else:
    for rel, (n, panelled) in sorted(CLAIM2.items()):
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            skip(rel, 'not in this checkout')
            continue
        text = read(p)
        hs = headings(text)
        want = n + ALREADY2.get(rel, 0)
        ok(len(hs) == want, '%-38s %2d section title(s)' % (rel, want),
           'found %d' % len(hs))
        bad = [plain(h.group(1))[:34] for h in hs
               if len(re.findall(r'<i\s', re.match(
                   r'\s*(<i\s[^>]*>\s*</i>\s*)*', h.group(1)).group(0))) != 1]
        ok(not bad, '%-38s opens with exactly one icon' % rel, bad)
        if panelled:
            cards = len(re.findall(r'<div class="form-card">',
                                   markup_only(text)))
            ok(cards >= n, '%-38s %d panel(s), one per section'
               % (rel, cards), 'expected at least %d' % n)


print('\n' + '=' * 74)
print('10. PUSH 2 - NO FIELD MOVED EXCEPT THE ONES THIS ROUND NAMES')
print('=' * 74)
print("""
   Push 1's version of this was an EQUALITY, because push 1 moved nothing.
   Push 2 moves seven controls across four files, so the check takes the
   named movers OUT of both lists and requires what is left to be in exactly
   the order it was. THE INVARIANT IS RELATIVE ORDER, NOT ABSOLUTE POSITION:
   comparing each field's index flagged seven fields on Properties and
   twelve on Tenants that had not moved relative to anything - they had
   simply been stepped over.
""")

if ran2:
    for rel in sorted(CLAIM2):
        p = os.path.join(ROOT, rel)
        bak = p + SUFFIX2
        if not os.path.isfile(bak):
            skip('%-38s field order' % rel, 'no %s backup' % SUFFIX2)
            continue
        a, b = fields(read(bak)), fields(read(p))
        named_ = set(MOVES2.get(rel, []))
        ok(sorted(a) == sorted(b),
           '%-38s %3d control(s), none lost or gained' % (rel, len(b)),
           '%d before, %d after' % (len(a), len(b)))
        ra = [x for x in a if x not in named_]
        rb = [x for x in b if x not in named_]
        where = ''
        if ra != rb:
            i = next((k for k, (x, y) in enumerate(zip(ra, rb)) if x != y),
                     min(len(ra), len(rb)))
            where = 'at %d, %r became %r' % (i, ra[i:i + 1], rb[i:i + 1])
        ok(ra == rb,
           '%-38s the unnamed fields keep their order' % rel, where)
        for x in sorted(named_):
            ok(a.index(x) != b.index(x),
               '%-38s %s moved, and was named' % (rel, x),
               'it is named as moving and did not move')
        # A FORM CANNOT VANISH. Rebuilding a panel that CONTAINS the form
        # deletes the open tag and its close together, so a balance check
        # stays at zero and passes a file with no form in it. That is not a
        # hypothetical: the first draft of the push-2 tool did exactly that
        # to customer_form, and the balance check passed it.
        ok(read(p).count('<form') >= read(bak).count('<form'),
           '%-38s still has every <form> it started with' % rel,
           '%d -> %d' % (read(bak).count('<form'), read(p).count('<form')))


print('\n' + '=' * 74)
print('11. PUSH 2 - THE MODEL SCREEN STACKS ON A PHONE')
print('=' * 74)
print("""
   customer_invoice_form was the only entry screen in the system whose
   fields did not stack below 768px. It used Bootstrap's UNPREFIXED column
   classes, which hold their percentage at every width. Measured at 375 wide
   before the fix: Customer Name and Customer ID rendered 152px side by
   side. col-12 is left alone - full width at every size, never part of it.
""")

MODEL = 'customer_invoice_form.html'
_p = os.path.join(ROOT, MODEL)
if not os.path.isfile(_p) or not ran2:
    skip('the model screen', 'push 2 has not run on this tree')
else:
    mk_ = markup_only(read(_p))
    left = sorted(set(re.findall(
        r'class="[^"]*(?<![-\w])(col-(?:1[01]|[1-9]))(?![-\w])', mk_)))
    ok(not left, '%-38s no unprefixed column left' % MODEL, left)
    ok('col-md-6' in mk_ and 'col-md-4' in mk_,
       '%-38s and it carries the prefixed ones instead' % MODEL)
    # the rest of the corpus, so this cannot regress somewhere else
    others = []
    for dp, _d, ns in os.walk(ROOT):
        for n_ in sorted(ns):
            if not n_.endswith('.html'):
                continue
            rel_ = os.path.relpath(os.path.join(dp, n_),
                                   ROOT).replace(os.sep, '/')
            if rel_ == 'base.html':
                continue
            m_ = markup_only(read(os.path.join(dp, n_)))
            if not re.search(r'<form[^>]*method\s*=\s*["\']post', m_, re.I):
                continue
            hit = sorted(set(re.findall(
                r'class="[^"]*(?<![-\w])(col-(?:1[01]|[1-9]))(?![-\w])', m_)))
            if hit:
                others.append('%s %s' % (rel_, ','.join(hit)))
    if others:
        notes.append('%d other screen(s) that post a form still use an '
                     'unprefixed column: %s. Each was measured; they carry '
                     'only col-12 or sit outside this round.'
                     % (len(others), '; '.join(others[:4])))


print('\n' + '=' * 74)
print('12. PUSH 2 - RENDERED, THE REBUILT PANELS ON A PHONE')
print('=' * 74)

if not ran2 or not os.path.isfile(BOOT):
    skip('the rebuilt panels', 'push 2 has not run, or no %s' % BOOT)
else:
    try:
        from playwright.sync_api import sync_playwright as _pw2
    except Exception as _e:
        skip('the rebuilt panels', 'playwright not importable')
        _pw2 = None
    if _pw2:
        # The four-across row this round writes, at the width it was
        # written for. col-md-3 is the ONLY width push 2 sets.
        four = ''.join(
            '<div class="col-md-3"><div class="form-group"><label><strong>'
            '%s</strong></label><select class="form-control"><option>Yes'
            '</option></select></div></div>' % t
            for t in ('Include in Occupancy Calculations', 'Status',
                      'Available For Rent', 'Title Deed Available'))
        html2 = ("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>p2</title><style>%s</style><style>%s</style></head><body>
<div class="container-fluid" style="padding:16px"><form method="post">
<div class="form-card"><h3 class="form-section-title">
<i class="fas fa-clipboard-check"></i> Status &amp; Reporting</h3>
<div class="form-row">%s</div></div></form></div></body></html>"""
                 % (read(BOOT), BASE_CSS, four))
        fx2 = os.path.join(SCRATCH, '_sections_p2.html')
        with open(fx2, 'w', encoding='utf-8') as f:
            f.write(html2)
        JS2 = r"""() => {
          const c = [...document.querySelectorAll('.form-control')];
          const tops = c.map(x => Math.round(
              x.getBoundingClientRect().top));
          return {w: c.map(x => Math.round(
                      x.getBoundingClientRect().width)),
                  lines: new Set(tops).size,
                  scrollW: document.documentElement.scrollWidth,
                  innerW: window.innerWidth};
        }"""
        M2 = {}
        with _pw2() as pw2:
            exe2 = '/opt/pw-browsers/chromium'
            br2 = pw2.chromium.launch(
                **({'executable_path': exe2} if os.path.exists(exe2) else {}))
            for w2, h2 in ((375, 667), (1280, 900)):
                ctx2 = br2.new_context(viewport={'width': w2, 'height': h2})
                pg2 = ctx2.new_page()
                _goto(pg2, fx2)
                pg2.wait_for_timeout(120)
                M2[w2] = pg2.evaluate(JS2)
                ctx2.close()
            br2.close()
        ok(M2[375]['lines'] == 4,
           '375 wide  the four-across row becomes four lines',
           '%d line(s)' % M2[375]['lines'])
        ok(M2[375]['scrollW'] <= M2[375]['innerW'],
           '375 wide  the four-across row causes no horizontal scroll')
        ok(min(M2[375]['w']) > 250,
           '375 wide  each of the four is still a usable width',
           M2[375]['w'])
        ok(M2[1280]['lines'] == 1,
           '1280 control  and on the desktop the four share one line',
           '%d line(s)' % M2[1280]['lines'])
        notes.append('PUSH 2 MEASURED: the col-md-3 row renders %dpx per '
                     'field at 375 wide and %dpx at 1280.'
                     % (min(M2[375]['w']), min(M2[1280]['w'])))

notes.append('CASH RECEIPTS IS NOT IN PUSH 2. cash_receipt_add already '
             'has two titled sections in the house .alv-card - "The '
             'payment" and "Received from", the first with an aside - so it '
             'is an adopt job on a panel component this round has not '
             'touched, and its wording is better than the one proposed. '
             'Push 3, with the .alv-card question.')
notes.append('ASSETS IS NOT IN PUSH 2. purchase_invoice is not a row block - '
             'it is a .form-group inside {% if asset.purchase_invoice %} '
             'after the Warranty row - and a Purchase section needs '
             'brand_manufacturer lifted too, on two screens whose form sits '
             'inside the panel. Two block lifts and a conditional is a '
             'different kind of surgery; it goes in push 3 with its own '
             'anchors.')



# ==========================================================================
# PUSH 3 - Issues, the Personal modals, and the Assets deferral
# ==========================================================================
SUFFIX3 = '.bak_sect3'

CLAIM3 = {
    'fsr_add.html': 1,
    'celebration_management.html': 3,
    'household_member_management.html': 1,
    'passport_management.html': 3,
    'view_meal_plan.html': 1,
    'edit_asset.html': 2,
    'property_assets.html': 3,
}
ALREADY3 = {'edit_asset.html': 2, 'property_assets.html': 1}
MOVES3 = {
    'edit_asset.html': ['brand_manufacturer', 'purchase_invoice'],
    'property_assets.html': ['brand_manufacturer', 'purchase_invoice'],
}
# A modal is already a box with a border, a shadow and a header bar. These
# screens put their form in one and must NOT have gained a panel.
MODALS = ('celebration_management.html', 'household_member_management.html',
          'passport_management.html', 'view_meal_plan.html')

print('\n' + '=' * 74)
print('13. PUSH 3 - TITLES, AND NO PANEL INSIDE A MODAL')
print('=' * 74)

ran3 = any(os.path.isfile(os.path.join(ROOT, r) + SUFFIX3) for r in CLAIM3)
if not ran3:
    skip('push 3', 'no %s backup - push 3 has not run on this tree' % SUFFIX3)
else:
    for rel, n in sorted(CLAIM3.items()):
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            skip(rel, 'not in this checkout')
            continue
        text = read(p)
        want = n + ALREADY3.get(rel, 0)
        hs = headings(text)
        ok(len(hs) == want, '%-34s %2d section title(s)' % (rel, want),
           'found %d' % len(hs))
        bad = [plain(h.group(1))[:30] for h in hs
               if len(re.findall(r'<i\s', re.match(
                   r'\s*(<i\s[^>]*>\s*</i>\s*)*', h.group(1)).group(0))) != 1]
        ok(not bad, '%-34s opens with exactly one icon' % rel, bad)

    for rel in MODALS:
        p = os.path.join(ROOT, rel)
        bak = p + SUFFIX3
        if not os.path.isfile(bak):
            skip('%-34s gained no panel' % rel, 'no %s backup' % SUFFIX3)
            continue
        a = read(bak).count('<div class="form-card">')
        b = read(p).count('<div class="form-card">')
        ok(a == b, '%-34s a modal body is already a panel, so it gained '
           'none' % rel, '%d -> %d' % (a, b))

print('\n' + '=' * 74)
print('14. PUSH 3 - THE ASSETS LIFTS, AND NOTHING ELSE MOVED')
print('=' * 74)
print("""
   Both moves are made by anchor rather than by the block index, because
   purchase_invoice is not a row block - it is a .form-group inside
   {% if asset.purchase_invoice %} with a link to the existing file in the
   conditional. The conditional has to survive the lift.
""")

if not ran3:
    skip('the Assets lifts', 'push 3 has not run on this tree')
else:
    for rel in sorted(MOVES3):
        p = os.path.join(ROOT, rel)
        bak = p + SUFFIX3
        if not os.path.isfile(bak):
            skip('%-34s the lifts' % rel, 'no %s backup' % SUFFIX3)
            continue
        was, now = read(bak), read(p)
        a, b = fields(was), fields(now)
        named_ = set(MOVES3[rel])
        ok(sorted(a) == sorted(b),
           '%-34s %3d control(s), none lost or gained' % (rel, len(b)),
           '%d before, %d after' % (len(a), len(b)))
        ra = [x for x in a if x not in named_]
        rb = [x for x in b if x not in named_]
        ok(ra == rb, '%-34s the unnamed fields keep their order' % rel)
        for x in sorted(named_):
            ok(a.index(x) != b.index(x),
               '%-34s %s moved, and was named' % (rel, x))
        # THE CONDITIONAL SURVIVED THE LIFT. A block cut out of one place
        # and pasted into another can lose the {% if %} that wrapped it,
        # and nothing about the field list would show that.
        for tag in ('{% if', '{% endif %}'):
            ok(now.count(tag) == was.count(tag),
               '%-34s Django %s tags unchanged (%d)'
               % (rel, tag.strip('{% '), was.count(tag)),
               '%d -> %d' % (was.count(tag), now.count(tag)))
        # the order the sections now read in
        titles = [plain(h.group(1)).split('(')[0].strip()
                  for h in headings(now)]
        ok(titles[:3] == ['Asset', 'Purchase', 'Warranty Information'],
           '%-34s the sections read Asset, Purchase, Warranty' % rel, titles)

notes.append('OUT OF THE ROUND, each with a reason measured rather than '
             'assumed: cash_receipt_add (already sectioned in .alv-card, '
             'and its first head carries an aside .form-section-title '
             'cannot); fsr_details (its Edit Issue modal uses .ei-label and '
             '.ei-input, not the field components - the form-components '
             'round owns that first); help_page (selected_modules is a '
             'selection tree, not a form); generate_lease_agreement (its '
             'colour-coded headers stay, by decision).')
notes.append('PROJECTS IS HELD. Five screens wait for the rollup fix: a '
             'parent task has all six get_calculated_* methods and nothing '
             'that calls them, while a Project has update_project_from_'
             'tasks() and a signal that fires it. Sectioning those screens '
             'would rearrange the markup of a behaviour about to change. '
             'See claude/projects_auto_calculated_rollup.md.')


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
