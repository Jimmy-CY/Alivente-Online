# -*- coding: utf-8 -*-
"""test_contrast.py - Section D, round D10: white text that could not be
read.

    python test_contrast.py

Run from the repo root, after apply_contrast.py.

  1. RENDERED: every repaired rule, before and after, with its contrast
     computed. That IS the round - a number in a commit message is a
     measurement somebody took; this is the measurement taken again.
  2. The whole property side is swept again, so a new one cannot land
     unnoticed.
  3. Nothing was deleted, and .priority-high - which a first pass called
     an orphan - is still painted.
  4. Scope, registered, on the gate.

Run it against the REVERTED tree and it must FAIL, not crash.
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
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
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
    print('     checks below it never ran.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_contrast'
ME = 'test_contrast.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
PERSONAL = ('recipe', 'meal_plan', 'ingredient', 'wcim', 'celebration',
            'pantry', 'unit_conversions', 'measurement_units',
            'household_member', 'map_ingredients', 'import_recipe',
            'preview_imported', 'categories_management', 'my_profile',
            'personal_', 'passport', 'personal.html')

# (file, selector to probe, hover?, the floor it must now clear)
PROBES = [
    ('edit_asset.html', 'btn-photo-star btn-photo-star-active', False),
    ('customer_invoice_form.html', 'btn-approve', False),
    ('customer_invoice_form.html', 'btn-approve', True),
    ('customer_invoice_form.html', 'btn-unapprove', False),
    ('customer_invoice_form.html', 'btn-unapprove', True),
    ('customer_invoice_form.html', 'btn-send', False),
    ('customer_invoice_form.html', 'btn-send', True),
    ('physical_invoice_edit.html', 'btn-approve', False),
    ('physical_invoice_edit.html', 'btn-approve', True),
    ('physical_invoice_edit.html', 'btn-unapprove', False),
    ('physical_invoice_edit.html', 'btn-unapprove', True),
    ('property_detail.html', 'badge badge-success', False),
    ('property_detail.html', 'badge badge-available', False),
    ('finance_revenue_types_add.html', 'quickset-btn', True),
    ('finance_revenue_types_edit.html', 'quickset-btn', True),
    ('projects/project_task_list.html', 'priority-badge priority-high', False),
    ('projects/projects_detail.html', 'priority-badge priority-high', False),
]

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def nocomment(c):
    return re.sub(r'/\*.*?\*/', '', c, flags=re.S)


# --- contrast, computed --------------------------------------------------
# A COLOUR ARRIVES IN THREE SPELLINGS AND THE PARSER MUST KNOW ALL THREE.
# The first draft of this helper read `[\d.]+` out of whatever it was
# given. Handed `#ffffff` it found no digits at all and returned 0 - so
# WHITE was scored as BLACK, and a perfectly good `#0e7c8b` button came
# back at 1.03 instead of 4.91. Handed Chromium's answer for a
# color-mix(), `color(srgb 0.09 0.38 0.24)`, it read those 0-1 numbers as
# 0-255 and scored a dark green as pure black, 20.96.
#
# Neither failure raised anything. A colour parser that returns a NUMBER
# for input it did not understand will score every rule in the codebase
# and be wrong about an unknown share of them. This one refuses instead.
def parse_rgb(s):
    """(r, g, b) in 0-255, or None if the colour is not understood."""
    s = s.strip().lower()
    m = re.match(r'^#([0-9a-f]{3}|[0-9a-f]{6})$', s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    if s == 'white':
        return (255, 255, 255)
    if s == 'black':
        return (0, 0, 0)
    m = re.match(r'^rgba?\(([^)]*)\)$', s)
    if m:
        v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))[:3]]
        return tuple(v) if len(v) == 3 else None
    # Chromium answers a color-mix() in modern syntax, 0-1 per channel.
    m = re.match(r'^color\(srgb ([^)]*)\)$', s)
    if m:
        v = [float(x) for x in re.findall(r'-?[\d.]+', m.group(1))[:3]]
        return tuple(x * 255 for x in v) if len(v) == 3 else None
    return None


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _relL(rgb):
    r, g, b = (_lin(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    """Raises on a colour it cannot read, rather than scoring it."""
    ra, rb = parse_rgb(a), parse_rgb(b)
    if ra is None or rb is None:
        raise ValueError('unreadable colour: %r / %r' % (a, b))
    x, y = _relL(ra) + 0.05, _relL(rb) + 0.05
    return max(x, y) / min(x, y)


def worst_contrast(bg, ink):
    """Against the WORST part of the paint.

    A gradient has no backgroundColor - it reads rgba(0,0,0,0) and scores
    as a perfect pass, which is how D8's first draft gave three broken
    headers 21.00."""
    stops = re.findall(r'rgba?\([^)]*\)|color\(srgb [^)]*\)|#[0-9a-fA-F]{6}',
                       bg)
    if not stops:
        return contrast(bg, ink)
    return min(contrast(s, ink) for s in stops)


# ==========================================================================
head('1. RENDERED - EVERY REPAIRED RULE, BEFORE AND AFTER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'

LOOK = r"""() => {
  const e = document.querySelector('.probe');
  const s = getComputedStyle(e);
  return {bg: s.backgroundImage !== 'none' ? s.backgroundImage
                                           : s.backgroundColor,
          ink: s.color, size: s.fontSize, weight: s.fontWeight};
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 1 and 2', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def look(br, base_css, page_css, cls, hover):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_ct_%04d.html' % n[0])
        # A :hover is measured by copying the hover rule onto the element,
        # because a headless probe cannot hold a pointer still.
        extra = ''
        if hover:
            extra = ('<style>' + '\n'.join(
                re.sub(r'([^{}]*)\.%s:hover' % re.escape(cls.split()[-1]),
                       r'\1.probe', c)
                for c in page_css
                if '.%s:hover' % cls.split()[-1] in c) + '</style>')
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>c</title><style>%s</style><style>%s</style>%s%s'
                '</head><body><span class="probe %s">Text</span></body></html>'
                % (boot, base_css,
                   ''.join('<style>%s</style>' % c for c in page_css),
                   extra, cls))
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        B_NOW, B_WAS = '\n'.join(styles_of(now(BASE))), \
                       '\n'.join(styles_of(was(BASE)))
        print('')
        print('      %-32s %-26s %6s %6s' % ('file', 'rule', 'before', 'after'))
        worse, still_bad, measured = [], [], 0
        for rel, cls, hover in PROBES:
            p = os.path.join(T, rel.replace('/', os.sep))
            if not os.path.isfile(p + SUFFIX):
                skip('%s .%s' % (rel, cls), 'no %s backup' % SUFFIX)
                continue
            a = look(br, B_NOW, styles_of(now(p)), cls, hover)
            b = look(br, B_WAS, styles_of(was(p)), cls, hover)
            ca = worst_contrast(a['bg'], a['ink'])
            cb = worst_contrast(b['bg'], b['ink'])
            measured += 1
            label = cls.split()[-1] + (':hover' if hover else '')
            print('      %-32s %-26s %6.2f %6.2f%s'
                  % (rel[:32], label[:26], cb, ca,
                     '   <- was below 3.0' if cb < 3 else ''))
            if ca < cb - 0.01:
                worse.append('%s .%s %.2f -> %.2f' % (rel, label, cb, ca))
            if ca < 4.5:
                still_bad.append('%s .%s %.2f' % (rel, label, ca))
        print('')
        ok(measured == len(PROBES),
           'every repaired rule rendered and was measured (%d)' % measured,
           (len(PROBES), measured))
        ok(not still_bad,
           'AFTER: every one of them carries its white text at 4.5:1 or '
           'better', '\n'.join(still_bad[:6]))
        ok(not worse, '  and not one of them got darker to get there',
           '\n'.join(worse[:6]))

        # ==============================================================
        head('2. THE WHOLE PROPERTY SIDE, SWEPT AGAIN')
        # ==============================================================
        # The round exists because a sweep found what no list knew about.
        # The sweep is the check, so the next one cannot land unnoticed.
        HEX = re.compile(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b')
        LIGHT = {'white', '#fff', '#ffffff', '#fefefe'}
        found, unreadable = [], []
        for d, dirs, fs in os.walk(T):
            dirs[:] = [x for x in dirs if x != '__pycache__']
            for f in sorted(fs):
                if not f.endswith('.html') or '.bak' in f:
                    continue
                rel = os.path.relpath(os.path.join(d, f), T).replace('\\', '/')
                if any(k in rel for k in PERSONAL) or rel == 'base.html':
                    continue
                css = nocomment('\n'.join(styles_of(now(os.path.join(d, f)))))
                for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
                    body = m.group(2)
                    c = re.search(r'(?:^|;)\s*color:\s*([^;]+)', body)
                    bg = re.search(r'(?:^|;)\s*background(?:-color)?:\s*'
                                   r'([^;]+)', body)
                    if not (c and bg):
                        continue
                    if c.group(1).strip().lower() not in LIGHT:
                        continue
                    stops = HEX.findall(bg.group(1))
                    if not stops:
                        continue
                    try:
                        w = min(contrast(s, '#ffffff') for s in stops)
                    except ValueError as e:
                        unreadable.append('%s %s' % (rel, e))
                        continue
                    if w < 4.5:
                        found.append('%s %s %.2f'
                                     % (rel, ' '.join(m.group(1).split())[:30],
                                        w))
        # THE THREE THAT REMAIN ARE DEAD, AND THAT IS CHECKED, NOT CLAIMED.
        # D10 repairs live rules and deletes nothing - a contrast round that
        # also deleted would have taken .priority-high, which looked orphaned
        # and is built by the template. These three go to the orphan round.
        DEAD = {'comments_report.html .btn-print': 'btn-print',
                'finance_expense_add.html #prorataPreviewModal .modal-he':
                    'prorata',
                'finance_expense_edit.html #prorataPreviewModal .modal-he':
                    'prorata'}
        live = [f for f in found
                if not any(f.startswith(k) for k in DEAD)]
        ok(not live,
           'no LIVE rule on the property side still puts white text on a '
           'colour below 4.5:1', '\n'.join(live[:8]))
        ok(len(found) == 3,
           '  and exactly three remain, every one of them dead (%d)'
           % len(found), '\n'.join(found[:6]))
        # .btn-print: worn by nothing, in markup, in a script, or built by
        # the template - which is the spelling that nearly fooled this round.
        cr = now(os.path.join(T, 'comments_report.html'))
        mk = re.sub(r'<style[^>]*>.*?</style>', '', cr, flags=re.S | re.I)
        ok(not re.search(r'class="[^"]*\bbtn-print\b', mk)
           and 'btn-print' not in '\n'.join(
               re.findall(r'<script[^>]*>(.*?)</script>', cr, re.S))
           and not re.search(r'btn-print-?\{\{', cr),
           '  .btn-print is worn by nothing - no attribute, no script, and '
           'no {{ }} building the name')
        for f in ('finance_expense_add.html', 'finance_expense_edit.html'):
            t = now(os.path.join(T, f))
            ok('class="modal-header alv-modal-head"' in t,
               '  %s: the prorata markup wears .alv-modal-head' % f[:22])
        ok('!important' in re.search(
               r'\.alv-modal-head \{[^}]*\}',
               '\n'.join(styles_of(now(BASE))), re.S).group(0),
           '  and base paints that class with !important, so the page rule '
           'has been overridden since D6')
        ok(not unreadable,
           '  and every colour in that sweep was one the parser understands',
           '\n'.join(unreadable[:5]))
        was_found = 0
        for rel, cls, hover in PROBES:
            p = os.path.join(T, rel.replace('/', os.sep))
            if os.path.isfile(p + SUFFIX):
                was_found += 1
        ok(was_found >= 15,
           'CONTROL: %d rule(s) did before this round, on %d file(s)'
           % (was_found, len(set(r for r, _c, _h in PROBES))))
        br.close()

# ==========================================================================
head('3. NOTHING WAS DELETED')
# ==========================================================================
# A first pass called .priority-high an orphan: it is in no class attribute
# and no script. It is built by the TEMPLATE -
# `class="priority-badge priority-{{ item.priority|lower }}"` - and
# deleting it would have taken the paint off every High badge in Projects.
for rel in ('projects/project_task_list.html', 'projects/projects_detail.html'):
    p = os.path.join(T, rel.replace('/', os.sep))
    src = now(p)
    ok(re.search(r'priority-\{\{\s*\w+[\w.]*\.\w*priority\w*\|lower\s*\}\}',
                 src) is not None,
       '%s builds its priority class from the template' % rel.split('/')[-1])
    ok('.priority-high {' in src,
       '  so .priority-high is LIVE, and it is still here')
    ok('var(--alv-warn)' in src, '  repainted, not removed')
for rel, _c, _h in PROBES:
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.isfile(p + SUFFIX):
        continue
    a, b = now(p), was(p)
    ok(a.count('}') == b.count('}'),
       '%-34s the same number of rules as before' % rel[:34],
       (b.count('}'), a.count('}')))

# ==========================================================================
head('4. SCOPE, THEN REGISTERED AND ON THE GATE')
# ==========================================================================
for rel in sorted(set(r for r, _c, _h in PROBES)):
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.isfile(p + SUFFIX):
        continue
    a, b = now(p), was(p)
    ok(re.sub(r'<style[^>]*>.*?</style>', '', a, flags=re.S | re.I)
       == re.sub(r'<style[^>]*>.*?</style>', '', b, flags=re.S | re.I),
       '%-34s outside <style>, byte-for-byte what it was' % rel[:34])
ok(SUFFIX in ROUNDS and '.bak_avatar' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_avatar'),
   'alv_rounds lists %s after .bak_avatar' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
