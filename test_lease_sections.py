# -*- coding: utf-8 -*-
"""test_lease_sections.py - Section C, round C5: the lease generator takes
the house sections.

    python test_lease_sections.py

Run from the repo root, after apply_lease_sections.py.

  1. Thirteen house section titles, in the order the page had them, each
     with exactly one icon; the wizard's three keep a panel and the
     pop-up's ten do not; no card header, and none of the four colours.
  2. NOT ONE FIELD MOVED. Every control is still in the same section as
     before - measured in the browser, by walking the rendered document
     and asking each control which heading it sits under. A rewrite of
     this size can lose a field into the wrong block and still balance.
  3. The three titles that carry a control are flex CONTAINERS, so base's
     rule still spans the section; their control sits at the right.
  4. A section title here computes exactly what a section title computes
     on an entry screen that never changed.
  5. The page is still desktop-only below 768px.
  6. Scope: the round's own edits and nothing else, and the five Furniture
     sub-headings keep their words and their teal from a class.
  7. Registered in alv_rounds, and on the gate.
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

SUFFIX = '.bak_lease'
ME = 'test_lease_sections.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
PAGE = os.path.join(T, 'generate_lease_agreement.html')
PEER = os.path.join(T, 'passport_management.html')   # titles this round
PANEL_PEER = os.path.join(T, 'properties_add.html')  # and panels: two
#                        screens this round never touched, for comparison
TITLES = ['Step 1: Select Country and Language',
          'Step 2: Property and Tenant Information',
          'Step 3: Generate Document',
          'Property Information', 'Tenant Information',
          'Additional Information Required for Tenant',
          'New Tenant Information', 'Second Tenant Information',
          'Lease Terms', 'Landlord Information', 'Amenities',
          'Furniture and Appliances', 'Keys Provided']
SUBHEADS = ['Kitchen', 'Lounge / Dining', 'Bedroom', 'General', 'Balcony']

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
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def markup(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


def controls(t):
    return re.findall(r'<(?:input|select|textarea)\b[^>]*?'
                      r'(?:name|id)="([^"]+)"', t)


P_NOW, P_WAS = now(PAGE), was(PAGE)
B_NOW = read(BASE)
MK = markup(P_NOW)

# ==========================================================================
head('1. THIRTEEN HOUSE SECTIONS, THREE OF THEM PANELS')
# ==========================================================================
found = re.findall(r'<h3 class="form-section-title[^"]*">(.*?)</h3>', MK, re.S)
ok(len(found) == 13, 'thirteen section titles', len(found))
words = [' '.join(re.sub(r'<[^>]+>', ' ', f).split()) for f in found]
ok(all(any(w.startswith(t) for t in TITLES) for w in words)
   and len(set(words)) == 13,
   'each says what its coloured bar said, and no two are the same',
   '\n'.join(words))
ok([TITLES.index(next(t for t in TITLES if w.startswith(t))) for w in words]
   == sorted([TITLES.index(next(t for t in TITLES if w.startswith(t)))
              for w in words]),
   '  and they are in the order the page had them', words)
for f in found:
    first = re.match(r'\s*<span>(.*?)</span>', f, re.S)
    ok((first.group(1) if first else f).count('<i class="fas') == 1,
       '  one icon on %-42s'
       % ' '.join(re.sub(r'<[^>]+>', ' ', f).split())[:42])
ok(MK.count('class="form-card mb-4"') == 3,
   'the wizard keeps three panels')
ok('card-header' not in P_NOW and 'card-body' not in P_NOW,
   'no card header or card body is left')
for colour in ('bg-info', 'bg-warning', 'bg-success', 'bg-light'):
    ok(colour not in MK, 'no %s bar is left' % colour)
ok(re.search(r'<div class="modal-body">(?:(?!</div>).)*?card', MK, re.S)
   is None, 'and the pop-up carries titles, not panels')
if os.path.isfile(PAGE + SUFFIX):
    ok(was(PAGE).count('card-header') == 13,
       'CONTROL: there were thirteen coloured bars before',
       was(PAGE).count('card-header'))

for s in SUBHEADS:
    ok(re.search(r'<h6 class="[^"]*lease-subhead">%s</h6>' % re.escape(s), MK)
       is not None, 'the %s sub-heading wears a class' % s)
ok('style="color: #0e7c8b' not in MK and '#0e7c8b' not in MK,
   'no inline teal is left in the markup')
CSS = '\n'.join(styles_of(P_NOW))
for sel, want in (('.lease-title-row', 'display: flex'),
                  ('.lease-subhead', 'var(--alv-accent)'),
                  ('.lease-title-note', 'var(--alv-ink-soft)')):
    m = re.search(re.escape(sel) + r'\s*\{([^}]*)\}', CSS)
    ok(m is not None and want in m.group(1),
       '%-18s is the page\'s, and takes %s' % (sel, want),
       m.group(1) if m else 'no rule')
ok('#0e7c8b' not in CSS.split('.lease-subhead')[-1][:200],
   '  and the sub-heading rule says the token, not the literal')

# ==========================================================================
head('2. NOT ONE FIELD MOVED - WALKED IN THE BROWSER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
OPEN = ('<style>.modal{display:block!important;position:static!important;'
        'opacity:1!important}[style*="display: none"]{display:block!important}'
        '</style>')


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


def fixture(page_src, extra='', width_guard=True):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width, initial-scale=1">'
            '<title>l</title><style>%s</style><style>%s</style>%s%s</head>'
            '<body class="has-sidebar"><div class="main-content with-sidebar">'
            '%s</div></body></html>'
            % (read(BOOT), '\n'.join(styles_of(B_NOW)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_src)),
               extra, body_markup(page_src)))


# Each control, and the heading it sits under - whatever tag that heading
# is. On the backup the heading is the card header's h5/h6; now it is the
# section title. The WORDS are the same, so the grouping can be compared.
GROUPS_JS = r"""() => {
  const heads = [...document.querySelectorAll(
      'h3.form-section-title, .card-header h5, .card-header h6')];
  // The heading's WORDS. Three titles now carry a control inside them -
  // Add Second Tenant, Remove, and the Fully Furnished note - and before
  // the round those sat beside the heading, not in it. Compare what the
  // heading SAYS, which is the same either way.
  const txt = h => { const c = h.cloneNode(true);
    c.querySelectorAll('button, input, label, .lease-title-note')
        .forEach(x => x.remove());
    return (c.textContent || '').replace(/\s+/g, ' ').trim(); };
  const out = [];
  for (const el of document.querySelectorAll('input, select, textarea')) {
    const id = el.id || el.name || el.type;
    let best = null;
    for (const h of heads) {
      const p = h.compareDocumentPosition(el);
      if (p & Node.DOCUMENT_POSITION_FOLLOWING) best = h;
    }
    const modal = !!el.closest('.modal');
    out.push([id, best ? txt(best) : '(no heading)', modal]);
  }
  return out;
}"""
ROW_JS = r"""() => [...document.querySelectorAll('.lease-title-row')].map(h => {
  const s = getComputedStyle(h), r = h.getBoundingClientRect();
  const ps = getComputedStyle(h.parentElement);
  const inner = h.parentElement.clientWidth
      - parseFloat(ps.paddingLeft) - parseFloat(ps.paddingRight);
  const kid = h.lastElementChild.getBoundingClientRect();
  const words = h.firstElementChild.getBoundingClientRect();
  return {display: s.display, border: s.borderBottomWidth,
          full: Math.round(r.width) >= Math.round(inner) - 1,
          rightmost: Math.round(kid.right) <= Math.round(r.right) + 1
                     && kid.left > words.right};
})"""
LOOK_JS = r"""(sel) => {
  const h = document.querySelector(sel);
  if (!h) return null;
  const s = getComputedStyle(h);
  return [s.fontSize, s.fontWeight, s.borderBottomWidth, s.borderBottomStyle,
          s.borderBottomColor, s.paddingBottom, s.color].join(' ');
}"""
CARD_JS = r"""() => {
  const c = document.querySelector('.form-card');
  if (!c) return null;
  const s = getComputedStyle(c);
  return [s.backgroundColor, s.borderTopWidth, s.borderTopColor,
          s.borderRadius, s.padding].join(' ');
}"""
PHONE_JS = r"""() => ({
  wizard: getComputedStyle(
      document.querySelector('.desktop-wizard-container')).display,
  message: getComputedStyle(
      document.querySelector('.desktop-only-message')).display
})"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('2-5', 'playwright or %s missing' % BOOT)
else:
    k = [0]

    def render(pg, html, js, arg=None):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_lease_%04d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        _goto(pg, fx)
        return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()

        g_now = render(pg, fixture(P_NOW, OPEN), GROUPS_JS)
        g_was = render(pg, fixture(P_WAS, OPEN), GROUPS_JS)
        ok(len(g_now) == len(g_was) and len(g_now) > 60,
           '%d control(s) rendered, the same number as before' % len(g_now),
           '%d vs %d' % (len(g_now), len(g_was)))
        ok([x[0] for x in g_now] == [x[0] for x in g_was],
           '  the same controls, in the same order')
        moved = [(a, b) for a, b in zip(g_now, g_was) if a[1] != b[1]]
        ok(not moved, '  and every one sits under the same heading it did',
           '\n'.join('%s: %r -> %r' % (a[0], b[1], a[1])
                     for a, b in moved[:6]))
        ok([x[2] for x in g_now] == [x[2] for x in g_was],
           '  and the ones inside the pop-up are still inside it')
        ok(sum(1 for x in g_now if x[2]) > 40,
           '  CONTROL: most of them ARE in the pop-up, so that means '
           'something', sum(1 for x in g_now if x[2]))

        # ==================================================================
        head('3. A TITLE THAT CARRIES A CONTROL IS STILL A FULL-WIDTH TITLE')
        # ==================================================================
        rows = render(pg, fixture(P_NOW, OPEN), ROW_JS)
        ok(len(rows) == 3, 'three titles carry a control', len(rows))
        ok(all(r['display'] == 'flex' for r in rows),
           '  each is a flex CONTAINER', [r['display'] for r in rows])
        ok(all(r['full'] for r in rows),
           '  each still spans its section, so base\'s rule runs the whole '
           'width', rows)
        ok(all(r['border'] == '2px' for r in rows),
           '  and still carries base\'s 2px rule', [r['border'] for r in rows])
        ok(all(r['rightmost'] for r in rows),
           '  with the control at the right, beside the words', rows)

        # ==================================================================
        head('4. IT LOOKS LIKE EVERY OTHER SECTION TITLE IN THE SYSTEM')
        # ==================================================================
        mine = render(pg, fixture(P_NOW, OPEN), LOOK_JS,
                      'h3.form-section-title')
        peer = render(pg, fixture(read(PEER), OPEN), LOOK_JS,
                      'h3.form-section-title')
        ok(mine is not None and mine == peer,
           'the same size, weight, rule and colour as passport_management\'s',
           '%s\n vs %s' % (mine, peer))
        card = render(pg, fixture(P_NOW, OPEN), CARD_JS)
        peer_card = render(pg, fixture(read(PANEL_PEER), OPEN), CARD_JS)
        ok(card is not None and card == peer_card,
           'and the wizard\'s panel is base\'s .form-card, to the pixel',
           '%s\n vs %s' % (card, peer_card))
        old = render(pg, fixture(P_WAS, OPEN), LOOK_JS, '.card-header h5')
        ok(old is not None and old != mine,
           'CONTROL: the coloured bar did not look like this', old)
        ctx.close()

        # ==================================================================
        head('5. THE PAGE IS STILL DESKTOP-ONLY BELOW 768PX')
        # ==================================================================
        ctx = br.new_context(viewport={'width': 375, 'height': 800})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        ph = render(pg, fixture(P_NOW), PHONE_JS)
        ok(ph['wizard'] == 'none' and ph['message'] == 'flex',
           'at 375 the wizard is hidden and the message shows', ph)
        ph0 = render(pg, fixture(P_WAS), PHONE_JS)
        ok(ph0 == ph, '  exactly as it did before the round', (ph0, ph))
        ctx.close()
        br.close()

# ==========================================================================
head('6. SCOPE')
# ==========================================================================
if not os.path.isfile(PAGE + SUFFIX):
    skip('scope', 'no %s backup' % SUFFIX)
else:
    ok(controls(P_NOW) == controls(P_WAS),
       'every control is still there, in order', len(controls(P_NOW)))
    ok(sorted(re.findall(r'\bid="([^"]+)"', P_NOW))
       == sorted(re.findall(r'\bid="([^"]+)"', P_WAS)),
       'every id is still there')
    ok(P_NOW.count('{%') == P_WAS.count('{%')
       and P_NOW.count('{{') == P_WAS.count('{{'),
       'every Django tag is still there')
    _s_now = re.findall(r'<script\b.*?</script>', P_NOW, re.S)
    _s_was = re.findall(r'<script\b.*?</script>', P_WAS, re.S)
    ok(_s_now == _s_was, 'not one line of the page\'s script changed')
    for txt in ('Desktop or Tablet Required', 'Generate Lease Agreement',
                'Fully Furnished'):
        ok(txt in P_NOW, 'the page still says %r' % txt)

# ==========================================================================
head('7. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_quad' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_quad'),
   'alv_rounds lists %s after .bak_quad' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)
_d = read('Show-ButtonDrift.py') if os.path.isfile('Show-ButtonDrift.py') else ''
ok("'lease-title-row'" in _d and 'h[1-6]' in _d,
   'the button classifier reads a heading as a wrapper, and knows a '
   'section title\'s control is a secondary')

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
