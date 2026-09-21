"""test_panel_title.py - one panel title, one size, one tag, one icon.

    python test_panel_title.py

Run from the repo root, after apply_panel_title.py.

WHAT THE ROUND WAS ABOUT

base declared .form-section-title with NO font-size, so the heading TAG
decided how big a panel title was. Section 5's control takes the size back
out and measures the four tags these titles actually used:

    h2 32px    h3 28px    h5 20px    h6 16px

ONE COMPONENT, FOUR SIZES, chosen by whichever heading a page reached for.

THE ROUND'S OWN PROSE SAID SOMETHING STRONGER AND IT WAS WRONG. It listed
13.28px, 14px, 16px, 16.8px and 16px, and said two of them fell at or below
the 14px field labels - "Personal Information" smaller than "First Name"
beneath it. Those numbers were measured WITHOUT Bootstrap, which is not
what ships. With Bootstrap loaded nothing was smaller than its labels. The
spread is real and is enough; the sentence about the labels was not, and
writing this control is what found it.

SECTION 4 IS THE ONE THAT EARNS ITS KEEP, and it exists because this round
nearly shipped the fault it now checks for. The sweeper renamed three
headings from .pi-section-title / .lines-title to .form-section-title and
left their page-local CSS behind, matching nothing. Nobody would have seen
it: the rules were dead, not wrong. So section 4 asks a question no suite
here asked before - does any page style a class its own markup no longer
uses? - and asks it of every template, not of the nineteen this round
touched.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you 16px is the right size, or that an accent rule under a
panel title is handsome. That was settled on 17 Sep from the two rendered
side by side. What it holds is that there is ONE answer rather than five,
and that the answer is bigger than the labels beneath it.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)
SUFFIX = '.bak_ptitle'

TAG, CLS = 'h3', 'form-section-title'
SIZE, PAD, RULE_PX = 16.0, 9.0, 2.0
LABEL_PX = 14.0

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

# Named, with the reason. A heading inside a form-card that is NOT the
# component has to be explained, not skipped.
NOT_SWEPT = {
    'edit_asset.html': 'one form-card holds the whole form; its first '
                       'heading is the record name, not a section title',
}

# SETTLED BY A LATER ROUND - 19 Sep 2026.
#
# This round measured two headings that kept a name of their own and left
# them alone, calling it "a decision rather than a rename":
# customer_invoice_form's .lines-title sat at 8623 with its card spanning
# 2096-7575, genuinely outside it; property_assets' .form-section-heading
# was a second level of structure inside a panel that already had a title.
#
# The entry-sections round made the decision. Push 1 gave Invoice Lines a
# panel of its own, so its title is a panel title like every other, and
# brought property_assets' sub-heading onto the component too.
#
# SO THIS SUITE NOW ASSERTS THE REVERSE, and writing that down is the
# point. A suite is the record of a decision. When a later round reverses
# the decision, the record changes to say so - it does not quietly stop
# looking, and it does not go on failing because it remembers an older
# answer. The names stay here so the check still runs; the direction is
# what flipped.
SETTLED_BY_ENTRY_SECTIONS = {
    'customer_invoice_form.html': ('lines-title', 'Invoice Lines gained a '
                                   'panel, so its title is a panel title'),
    'property_assets.html': ('form-section-heading', 'it adopted the '
                             'component in push 1'),
}

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')



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
    print('     reason  : %s' % str(err).split('\\n')[0][:150])
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


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out,
                  flags=re.S)


def split_rules(css):
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j < 0:
            break
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{':
                depth += 1
            elif css[k] == '}':
                depth -= 1
            k += 1
        out.append((css[i:j], i, j, k))
        i = k
    return out


def all_rules(text):
    """Every rule in every <style> block, RECURSING INTO @media.

    split_rules does not recurse, and forgetting that has produced a wrong
    answer three separate times in this project. A rule inside a phone
    block is still a rule.
    """
    out = []

    def walk(css):
        for sel, _a, b, c in split_rules(css):
            bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).split())
            if bare.startswith('@'):
                walk(css[b + 1:c - 1])
                continue
            out.append((bare, css[b + 1:c - 1]))

    for blk in re.findall(r'<style[^>]*>(.*?)</style>', text, re.S):
        walk(blk)
    return out


def classes_used(text):
    """Every class name the MARKUP wears."""
    out = set()
    for m in re.finditer(r'class="([^"]*)"', inert(text)):
        for c in m.group(1).split():
            if not c.startswith('{'):
                out.add(c)
    return out


def classes_styled(text):
    """Every class name a page-local rule names as the SUBJECT.

    The subject only - `.prorata-panel .form-section-title` is about the
    title but is scoped by the panel, and the panel's name is what has to
    exist. Reading every class in the selector would call that rule
    orphaned the moment either half moved.
    """
    out = {}
    for sel, _body in all_rules(text):
        for part in [p.strip() for p in sel.split(',') if p.strip()]:
            for tok in re.findall(r'\.([A-Za-z][-\w]*)', part):
                out.setdefault(tok, set()).add(part[:60])
    return out


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html') or '.bak' in n:
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if rel == 'base.html' or any(r in rel for r in RECIPE):
                continue
            out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


def cards(scan):
    out = []
    for m in re.finditer(r'<div\b[^>]*class="[^"]*\bform-card\b[^"]*"[^>]*>',
                         scan):
        d, j = 1, m.end()
        for x in re.finditer(r'<(/?)div\b[^>]*>', scan[m.end():]):
            d += -1 if x.group(1) else 1
            if d == 0:
                j = m.end() + x.start()
                break
        out.append((m.end(), j))
    return out


def first_heading(scan, a, b):
    return re.search(r'<(h[1-6])\b([^>]*)>(.*?)</\1>', scan[a:b], re.S)


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

BASE_SRC = read(BASE)
ALL = [(rel, read(p)) for rel, p in templates()]

# ---------------------------------------------------------------------- 1
head('1. base DECLARES THE COMPONENT, ONCE, AND SAYS THE SIZE')

brules = [(s, b) for s, b in all_rules(BASE_SRC)
          if s.endswith('.' + CLS)]
check('base declares .%s exactly once' % CLS, len(brules) == 1,
      '%d rule(s)' % len(brules))
body = brules[0][1] if brules else ''
for prop, want in (('font-size', '16px'), ('padding-bottom', '9px'),
                   ('border-bottom', '2px solid var(--alv-accent)')):
    m = re.search(r'(?<![-\w])%s\s*:\s*([^;]+)' % re.escape(prop), body)
    check('  it says %s' % prop, bool(m) and m.group(1).strip() == want,
          m.group(1).strip() if m else 'absent')
check('  and the tag carries no appearance - base says all of it',
      'font-weight' in body)

# THE ROUND DEPENDS ON THIS RULE AND DID NOT ADD IT. The form-components
# round put it in base on 16 Sep. This round deletes 13 inline styles and
# 6 page rules that were all saying it again - so if it ever goes, those
# icons lose their colour with nothing replacing it.
irules = [(s, b) for s, b in all_rules(BASE_SRC)
          if re.fullmatch(r'\.%s\s+i' % re.escape(CLS), s)]
check('base styles the title icon', len(irules) == 1,
      '%d rule(s)' % len(irules))
if irules:
    check('  in the accent, which is what the deleted rules said',
          'var(--alv-accent)' in irules[0][1], ' '.join(irules[0][1].split()))
acc = re.search(r'--alv-accent:\s*(#[0-9a-fA-F]{3,6})', BASE_SRC)
check('  and --alv-accent is the literal those rules spelled by hand',
      bool(acc) and acc.group(1).lower() == '#0e7c8b',
      acc.group(1) if acc else 'not declared')

# ---------------------------------------------------------------------- 2
head('2. EVERY PANEL TITLE IS THE SAME TAG AND THE SAME CLASS')

wrong, swept, cardless = [], 0, 0
for rel, src in ALL:
    scan = inert(src)
    for a, b in cards(scan):
        h = first_heading(scan, a, b)
        if not h:
            cardless += 1
            continue
        tag, attrs = h.group(1), h.group(2)
        cls = re.search(r'class="([^"]*)"', attrs)
        ok = tag == TAG and cls and CLS in cls.group(1).split()
        if ok:
            swept += 1
        elif rel not in NOT_SWEPT:
            wrong.append('%s: %s.%s' % (rel, tag,
                                        cls.group(1).split()[0] if cls
                                        else 'NOCLASS'))
for w in wrong:
    print('        %s' % w)
check("every panel's first heading is %s.%s" % (TAG, CLS), not wrong,
      '%d are not' % len(wrong))
# No threshold beyond "there is at least one". The real tree has 34; a
# partial checkout has fewer, and a number I cannot verify in both places
# is worse than a claim I can.
check('  CONTROL: and there are panels to have got wrong',
      swept >= 1, '%d title(s) carry it' % swept)
print('        %d form-card(s) carry no heading at all - a panel without a'
      % cardless)
print('        title is not necessarily wrong, and this round did not add one.')
for rel, why in sorted(NOT_SWEPT.items()):
    here = dict(ALL).get(rel)
    if here is None:
        skip('%s is named as not swept' % rel, 'not in this checkout')
        continue
    check('  %s is named, with its reason' % rel, bool(why), why[:58])

# ---------------------------------------------------------------------- 3
head('3. NO PAGE RESTATES WHAT base OWNS')

def subject_is(sel, name):
    for part in [p.strip() for p in sel.split(',') if p.strip()]:
        h = part.split()[0] if part.split() else ''
        if h == '.' + name or h.startswith('.' + name + ':'):
            return True
        if re.fullmatch(r'\.form-card\s+h[1-6]', part):
            return True
    return False

restated, scoped = [], []
for rel, src in ALL:
    for sel, _b in all_rules(src):
        if subject_is(sel, CLS):
            restated.append('%s: %s' % (rel, sel[:44]))
        elif CLS in sel:
            scoped.append((rel, sel[:50]))
for r in restated:
    print('        %s' % r)
check('no page declares the component base owns', not restated,
      '%d do' % len(restated))
print('        %d scoped rule(s) survive - they name one panel, which base'
      % len(scoped))
print('        cannot say and should not:')
for rel, sel in scoped[:4]:
    print('          %-30s %s' % (rel[:30], sel))
# A partial checkout may hold neither of the two pages that scope the
# component. Saying so is not the same as passing.
if scoped:
    check('  CONTROL: and the scoped ones really were kept', True,
          '%d' % len(scoped))
else:
    skip('  CONTROL: the scoped ones were kept',
         'no page here scopes the component - on the real tree the two '
         '.prorata-panel rules do')
check('  CONTROL: the subject test tells the two apart',
      subject_is('.form-section-title', CLS)
      and not subject_is('.prorata-panel .form-section-title', CLS))

# ---------------------------------------------------------------------- 4
head('4. NO PAGE STYLES A CLASS THIS ROUND TOOK OFF ITS MARKUP')

# THE CHECK THIS ROUND NEEDED AND DID NOT HAVE. The sweeper renamed three
# headings out of .pi-section-title / .lines-title and left their rules
# behind, matching nothing. Dead, not wrong - which is why nothing caught
# it.
#
# IT FAILS ON WHAT THIS ROUND COULD HAVE ORPHANED AND REPORTS THE REST.
# The first draft failed on any orphan at all and found nineteen before
# the round had even run - .btn-info left by the button sweep, and a
# fistful of false positives from `class="status-badge status-{{ pi.status
# }}"`, where the name is built at render time and no literal scan can see
# it. Failing on those would make this suite about other people's debt.
RETIRED = ('pi-section-title', 'lines-title')


def interpolated_prefixes(text):
    """Prefixes of class names Django builds at render time.

    `class="status-badge status-{{ pi.status }}"` means .status-approved
    may well be worn - by a value this file never spells. Anything sharing
    that prefix is unprovable, so it is not called an orphan.
    """
    out = []
    for m in re.finditer(r'class="([^"]*)"', text):
        v = m.group(1)
        if '{{' not in v and '{%' not in v:
            continue
        for tok in v.split():
            if '{' in tok:
                pre = tok.split('{')[0]
                if pre:
                    out.append(pre)
    return out


mine, debt = [], []
for rel, src in ALL:
    used = classes_used(src)
    pres = interpolated_prefixes(src)
    scripts = ' '.join(re.findall(r'<script[^>]*>(.*?)</script>', src, re.S))
    for name, sels in sorted(classes_styled(src).items()):
        if name in used or name in classes_used(BASE_SRC):
            continue
        if any(name.startswith(x) for x in pres):
            continue
        if re.search(r'["\'`]%s["\'`]' % re.escape(name), scripts):
            continue
        line = '%s: .%s  (%s)' % (rel, name, sorted(sels)[0])
        (mine if name in RETIRED else debt).append(line)

for o in mine:
    print('        %s' % o)
check('no rule survives for a class this round renamed away', not mine,
      '%d do' % len(mine))
check('  CONTROL: and the scan reads rules inside @media too',
      len(all_rules(BASE_SRC)) > 100,
      '%d rule(s) read from base' % len(all_rules(BASE_SRC)))
check('  CONTROL: an interpolated name is not called an orphan',
      interpolated_prefixes('class="status-badge status-{{ x }}"')
      == ['status-'])
check('  CONTROL: .. and a plain one still is',
      interpolated_prefixes('class="plain"') == [])

print('        %d orphaned rule(s) belong to earlier rounds - reported,'
      % len(debt))
print('        not failed, because this round did not make them:')
for d in debt[:6]:
    print('          %s' % d)
if len(debt) > 6:
    print('          .. and %d more' % (len(debt) - 6))

for rel, (name, why) in sorted(SETTLED_BY_ENTRY_SECTIONS.items()):
    src = dict(ALL).get(rel)
    if src is None:
        skip('%s and .%s' % (rel, name), 'not in this checkout')
        continue
    check('  %s no longer wears .%s' % (rel, name),
          name not in classes_used(src), why[:52])
    check('    and its rules went with it', name not in classes_styled(src))
check('  CONTROL: the scan can still SEE a class that IS worn',
      any(CLS in classes_used(s) for _r, s in ALL))
check('  CONTROL: .. and one that IS styled',
      any(CLS in classes_styled(s) for _r, s in ALL))

# ---------------------------------------------------------------------- 5
head('5. RENDERED - ONE SIZE, WHERE THE TAG USED TO DECIDE')

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except ImportError:
    HAVE_PW = False

BOOT = None
for cand in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
             '/tmp/bootstrap.min.css'):
    if os.path.exists(cand):
        BOOT = read(cand)
        break


def base_css(src):
    out = []
    for blk in re.findall(r'<style[^>]*>(.*?)</style>', src, re.S):
        d = re.sub(r'/\*.*?\*/', '', blk, flags=re.S)
        if '--alv-accent:' in d or '.form-section-title' in d:
            out.append(blk)
    return '\n'.join(out)


TAGS_SEEN = ('h2', 'h3', 'h5', 'h6')

CTRL_JS = ("()=>{const e=document.getElementById('t'),"
           " l=document.getElementById('lab');"
           " return [getComputedStyle(e).fontSize,"
           "         getComputedStyle(l).fontSize];}")

FIXTURE = """<!doctype html><html><head><meta charset="utf-8">
<style>%s</style><style>%s</style>%s</head><body>
<div class="form-card">
  <h3 class="form-section-title" id="t"><i class="fas fa-user" id="ic"></i>
     Personal Information</h3>
  <div class="form-group"><label id="lab"><strong>First Name</strong></label>
    <input class="form-control"></div>
</div></body></html>"""

if not HAVE_PW:
    for n in ('the title is 16px', 'it is bigger than its own labels',
              'it carries the 2px accent rule', 'the icon is the accent'):
        skip(n, 'playwright not installed')
elif BOOT is None:
    for n in ('the title is 16px', 'it is bigger than its own labels',
              'it carries the 2px accent rule', 'the icon is the accent'):
        skip(n, 'test_fixture_bootstrap413.css missing')
else:
    def measure(extra_css='', page=FIXTURE):
        p = os.path.join(SCRATCH, 'ptitle.html')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(page % (BOOT, base_css(BASE_SRC),
                            '<style>%s</style>' % extra_css if extra_css
                            else ''))
        with sync_playwright() as pw:
            exe = '/opt/pw-browsers/chromium'
            br = (pw.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else pw.chromium.launch())
            pg = br.new_page(viewport={'width': 1200, 'height': 800})
            _goto(pg, p)
            got = pg.evaluate("""()=>{
                const g=(id,ps)=>{const e=document.getElementById(id);
                  if(!e)return null;const c=getComputedStyle(e);
                  const o={};for(const q of ps)o[q]=c.getPropertyValue(q);
                  return o;};
                return {t:g('t',['font-size','font-weight','padding-bottom',
                                 'border-bottom-width','border-bottom-color']),
                        l:g('lab',['font-size','font-weight']),
                        i:g('ic',['color','margin-right'])};}""")
            br.close()
        return got

    m = measure()
    tp = float((m['t'] or {}).get('font-size', '0px')[:-2] or 0)
    lp = float((m['l'] or {}).get('font-size', '0px')[:-2] or 0)
    check('the title renders %gpx' % SIZE, abs(tp - SIZE) < 0.51, '%gpx' % tp)
    check('  and it is not smaller than its own field labels',
          tp >= lp, 'title %gpx vs label %gpx' % (tp, lp))
    check('  the labels really are the %gpx they were' % LABEL_PX,
          abs(lp - LABEL_PX) < 0.51, '%gpx' % lp)
    bw = float((m['t'] or {}).get('border-bottom-width', '0px')[:-2] or 0)
    check('  it carries the %gpx rule' % RULE_PX, abs(bw - RULE_PX) < 0.51,
          '%gpx' % bw)
    check('  in the accent',
          (m['t'] or {}).get('border-bottom-color') == 'rgb(14, 124, 139)',
          (m['t'] or {}).get('border-bottom-color'))
    pb = float((m['t'] or {}).get('padding-bottom', '0px')[:-2] or 0)
    check('  with %gpx of air above it' % PAD, abs(pb - PAD) < 0.51,
          '%gpx' % pb)
    check("  and the icon takes base's accent, not a page literal",
          (m['i'] or {}).get('color') == 'rgb(14, 124, 139)',
          (m['i'] or {}).get('color'))
    check("  .. and base's 6px gap, which the deleted rules also said",
          (m['i'] or {}).get('margin-right') == '6px',
          (m['i'] or {}).get('margin-right'))

    # THE CONTROL IS THE WHOLE POINT OF THIS SECTION, and writing it
    # corrected the round's own prose. The patcher's docstring listed five
    # measured sizes - 13.28px, 14px, 16px, 16.8px, 16px - and said two of
    # them fell at or below the 14px labels. Those were measured WITHOUT
    # Bootstrap, which is not what ships. With Bootstrap loaded and base's
    # font-size taken away, the four tags these titles actually used come
    # out 32 / 28 / 20 / 16. Nothing was smaller than its labels; what was
    # true, and is enough, is that ONE component had FOUR sizes depending
    # on which heading tag a page happened to reach for.
    # LATER - test_small_controls.py, 21 Sep. base gained a phone rule
    # setting every text control to 16px !important, and a pattern with no
    # room for !important left it standing in the stripped copy, so this
    # control reported it could not run. The strip allows !important now;
    # the rule it also removes is about inputs, which this fixture has none
    # of, so nothing measured here moves.
    stripped = re.sub(r'(?<![-\w])font-size\s*:\s*16px\s*'
                      r'(?:!important\s*)?;', '',
                      base_css(BASE_SRC))
    if 'font-size: 16px' in stripped:
        check('  CONTROL: the size could be taken back out of base', False)
    else:
        sizes = {}
        with sync_playwright() as pw:
            exe = '/opt/pw-browsers/chromium'
            br = (pw.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else pw.chromium.launch())
            pg = br.new_page(viewport={'width': 1200, 'height': 800})
            for tag in TAGS_SEEN:
                q = os.path.join(SCRATCH, 'before_%s.html' % tag)
                with open(q, 'w', encoding='utf-8') as f:
                    f.write((FIXTURE % (BOOT, stripped, ''))
                            .replace('<h3 class', '<%s class' % tag)
                            .replace('</h3>', '</%s>' % tag))
                _goto(pg, q)
                sizes[tag] = pg.evaluate(CTRL_JS)[0]
            br.close()
        print('        without base\'s size, the tag decides: %s'
              % ', '.join('%s %s' % (t, s) for t, s in sizes.items()))
        check('  CONTROL: without it, one component has several sizes',
              len(set(sizes.values())) > 1,
              '%d different size(s)' % len(set(sizes.values())))
        check('  CONTROL: .. and at least one of them is not %gpx' % SIZE,
              any(abs(float(v[:-2]) - SIZE) > 0.51 for v in sizes.values()),
              ', '.join(sorted(set(sizes.values()))))
        check('  CONTROL: .. so base is what makes them agree',
              len(set(sizes.values())) > 1 and abs(tp - SIZE) < 0.51)

# ---------------------------------------------------------------------- 6
head('6. THE THREE RENAMED SUB-TITLES RENDER AS THEY DID')

# The round deletes .pi-section-title i { color:#0e7c8b; margin-right:6px }
# and base says color: var(--alv-accent); margin-right: 6px, with
# --alv-accent: #0e7c8b. So the claim is that nothing moved. Measured.
MOVED = ('tenant_add.html', 'tenant_edit.html', 'physical_invoice_edit.html')
baks = [r for r in MOVED if os.path.exists(os.path.join(T, r) + SUFFIX)]
if not baks:
    skip('the three renamed icons render unchanged',
         'no %s backup present - a fresh clone, or not applied here'
         % SUFFIX)
elif not HAVE_PW or BOOT is None:
    skip('the three renamed icons render unchanged', 'no browser fixture')
else:
    same = []
    for rel in baks:
        before = read(os.path.join(T, rel) + SUFFIX)
        old = re.search(r'\.(pi-section-title|lines-title)\s+i\s*\{([^}]*)\}',
                        before)
        if not old:
            continue
        decl = dict(re.findall(r'([-\w]+)\s*:\s*([^;]+)', old.group(2)))
        col = (decl.get('color') or '').strip().lower()
        gap = (decl.get('margin-right') or '').strip()
        same.append((rel, col == '#0e7c8b' and gap == '6px', col, gap))
    for rel, ok, col, gap in same:
        check('  %s said %s / %s - the same thing base says'
              % (rel[:26], col, gap), ok)
    check('the deleted icon rules were saying what base already said',
          bool(same) and all(ok for _r, ok, _c, _g in same),
          '%d rule(s) compared' % len(same))

# ---------------------------------------------------------------------- 7
head('7. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    ps1 = read(PS1)
    check('this suite is on the gate', ME in ps1, ME)
    check('  and so is the form-components suite this leans on',
          'test_form_components.py' in ps1)

# ---------------------------------------------------------------------- 8
print('\n' + '=' * 72)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.' % SKIP)
print('')
print('  STILL TO COME in these modules: the two tables on')
print('  user_administration and workspace_management. And a component for')
print('  the sub-titles that keep a name of their own - two screens, and a')
print('  decision rather than a rename.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
