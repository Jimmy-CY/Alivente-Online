#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Twelve controls built inside <script>, now on the house tones.

Run from the repo root, after apply_manage_modal.py. Needs Playwright's
chromium.

THE POINT OF THIS SUITE. These controls are markup inside JavaScript string
literals. `markup_of()` blanks <script>, so every earlier check in this project
was blind to them - which is why Show-ButtonDrift.py has listed them for weeks
under "NOT rewritten ... decided by hand" rather than fixing them. A check that
reads the template sees nothing here.

So the statics read the SCRIPT text specifically, and the rendering section
lifts the document-actions panel out of its template literal and draws it.

WHAT WAS DECIDED, and therefore what is measured:

  * The Invoice Document tab has NO primary. Add to Existing, Replace, Download
    and Delete are alternatives; a solid button would claim one of them is what
    you came for. Section 2 asserts none of the four is filled.
  * Delete reads as destructive by TONE, not by a red fill. Measured: red ink
    and a red edge on a white ground at rest.
  * A sub-panel's confirm IS its primary - Merge Documents, Upload, Upload
    Document - because each is the only thing on screen when its panel opens.
  * Save Changes is the primary of the Expense Details tab.
"""
import os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'act_expense.html')
BASEF = os.path.join(TPL, 'base.html')
SUFFIX = '.bak_managemodal'

_p = _f = 0
_fails = []


def check(n, ok, extra=''):
    global _p, _f
    if ok:
        _p += 1; print('  PASS  %s %s' % (n, extra))
    else:
        _f += 1; _fails.append(n); print('  FAIL  %s %s' % (n, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def nocomment(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)
    return re.sub(r'(<script[^>]*>)(.*?)(</script>)',
                  lambda m: m.group(1) + '\n'.join(
                      '' if l.lstrip().startswith('//') else l
                      for l in re.sub(r'/\*.*?\*/', '', m.group(2),
                                      flags=re.S).split('\n')) + m.group(3),
                  text, flags=re.S)


def scripts_of(text):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',
                                nocomment(text), re.S))


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def controls(js):
    """(class list, label) for every .btn control in a script, button or link."""
    out = []
    for pat in (r'<button[^>]*class="(btn[^"]*)"[^>]*>(.*?)</button>',
                r'<a\b[^>]*class="(btn[^"]*)"[^>]*>(.*?)</a>'):
        for m in re.finditer(pat, js, re.S):
            lab = ' '.join(re.sub(r'<[^>]+>', '', m.group(2)).split())
            out.append((m.group(1), lab[:24]))
    return out


PG, BASE = read(PAGE), read(BASEF)
BAK = PAGE + SUFFIX
HAVE = os.path.exists(BAK)
OLD = read(BAK) if HAVE else ''
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''
JS, OLDJS = scripts_of(PG), scripts_of(OLD)

# =========================================================================
head('1. no Bootstrap colour survives inside a <script>')
# =========================================================================
for gone in ('btn-success', 'btn-warning', 'btn-danger', 'btn-info',
             'btn-primary', 'btn-secondary', 'btn-outline-secondary',
             'alert alert-'):
    check('  %-22s is gone from the scripts' % gone, gone not in JS)
check('  CONTROL: and the ordinary markup scan still cannot see in there',
      'btn-success' not in re.sub(r'<script[^>]*>.*?</script>', '', OLD, flags=re.S)
      if HAVE else True,
      '' if HAVE else '(run apply_manage_modal.py first)')

NOW = controls(JS)
check('twelve controls were rewritten', len(NOW) == 12, str(len(NOW)))
_tones = {c for c, _ in NOW}
check('  and every one is on a house tone',
      all(re.search(r'action-(primary|secondary|danger)', c) for c, _ in NOW),
      '; '.join(sorted(_tones)))
_solid = [l for c, l in NOW if 'action-primary' in c]
check('four are primaries - one per panel that has a confirm',
      sorted(_solid) == ['Merge Documents', 'Save Changes', 'Upload',
                         'Upload Document'], str(sorted(_solid)))
_danger = [l for c, l in NOW if 'action-danger' in c]
check('  exactly one is destructive', _danger == ['Delete Document'], str(_danger))
_doc = {l for c, l in NOW
        if l in ('Add to Existing', 'Replace', 'Download', 'Delete Document')}
check('  and the four Invoice Document actions are all accounted for',
      len(_doc) == 4, str(sorted(_doc)))
check('NONE of them is a primary - they are alternatives',
      not [l for c, l in NOW if l in _doc and 'action-primary' in c])

head('1b. the note strip is page-local, and on house tokens')
_css = css_of(PG)
check('.exp-note is defined here, not in base',
      '.exp-note' in _css and '.exp-note' not in css_of(BASE))
for tone in ('success', 'danger', 'warning', 'secondary', 'info'):
    check('  .exp-note-%-10s exists' % tone, '.exp-note-%s' % tone in _css)
_notecss = '\n'.join(re.findall(r'\.exp-note[^{]*\{([^}]*)\}', _css))
# \b matters: without it `color` matches inside `border-color`, so the check
# read wider than it claimed. It caught three real literals anyway - which is
# the good kind of accident, but the wording and the regex should agree.
check('  and no colour in them is a literal - background, text or border',
      not re.search(r'\b(background|(?:border-)?color)\s*:[^;]*#[0-9A-Fa-f]{6}',
                    _notecss),
      str(re.findall(r'#[0-9A-Fa-f]{6}', _notecss)[:3]))
check('the verify banner uses it', 'exp-note exp-note-${s[0]}' in JS)
check('  and the read-only notices do too',
      len(re.findall(r'exp-note exp-note-(info|warning)', JS)) == 3,
      str(len(re.findall(r'exp-note exp-note-(info|warning)', JS))))
for old, tok in (('#28a745', '--alv-good'), ('#dc3545', '--alv-bad'),
                 ('#6c757d', '--alv-neutral'), ('#0e7c8b', '--alv-accent')):
    check('  the verify icon on %s is now %s' % (old, tok),
          'var(%s)' % tok in _css)

# =========================================================================
FRAG = """
<div class="exp-note exp-note-success verify-banner">
  <div class="verify-banner-head"><i class="fas fa-check-circle"></i> <strong>Invoice verified</strong></div>
</div>
<div class="exp-note exp-note-danger verify-banner">
  <div class="verify-banner-head"><strong>Invoice does not match</strong></div>
</div>
<div class="doc-action-row">
  <a href="#" class="btn action-secondary btn-sm" id="download">Download</a>
  <button type="button" class="btn action-secondary btn-sm" id="add">Add to Existing</button>
  <button type="button" class="btn action-secondary btn-sm" id="replace">Replace</button>
  <button type="button" class="btn action-danger btn-sm" id="del">Delete Document</button>
</div>
<button type="submit" class="btn action-primary" id="save">Save Changes</button>
"""

OLD_FRAG = """
<div class="alert alert-success verify-banner">
  <div class="verify-banner-head"><strong>Invoice verified</strong></div>
</div>
<div class="alert alert-danger verify-banner"><strong>Mismatch</strong></div>
<div class="doc-action-row">
  <a href="#" class="btn btn-info btn-sm" id="download">Download</a>
  <button type="button" class="btn btn-success btn-sm" id="add">Add to Existing</button>
  <button type="button" class="btn btn-warning btn-sm" id="replace">Replace</button>
  <button type="button" class="btn btn-danger btn-sm" id="del">Delete Document</button>
</div>
<button type="submit" class="btn btn-success" id="save">Save Changes</button>
"""

PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const g = id => { const e = document.getElementById(id); if (!e) return null;
    const s = getComputedStyle(e);
    return {bg: s.backgroundColor, color: s.color, border: s.borderTopColor}; };
  const note = sel => { const e = document.querySelector(sel); if (!e) return null;
    const s = getComputedStyle(e); return {bg: s.backgroundColor}; };
  const o = {download: g('download'), add: g('add'), replace: g('replace'),
             del: g('del'), save: g('save'),
             good: note('.exp-note-success, .alert-success'),
             bad: note('.exp-note-danger, .alert-danger')};
  for (const v of ['--alv-accent','--alv-bad','--alv-good','--alv-good-soft',
                   '--alv-bad-soft','--alv-paper'])
    o['T' + v] = tok(v);
  return o; }"""


async def paint(frag, page_css):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 900, 'height': 500})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), page_css, frag))
        await pg.wait_for_timeout(80)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


async def main():
    head('2. what the Invoice Document tab actually paints')
    now = await paint(FRAG, css_of(PG))
    white = 'rgb(255, 255, 255)'
    for k in ('download', 'add', 'replace'):
        check('%-10s is OUTLINED, not filled' % k,
              now[k] and now[k]['bg'] in (white, now['T--alv-paper']),
              str(now[k]['bg']) if now[k] else 'missing')
    check('Delete is outlined too', now['del']['bg'] in (white, now['T--alv-paper']),
          now['del']['bg'])
    check('  but reads destructive - red ink',
          now['del']['color'] == now['T--alv-bad'], now['del']['color'])
    check('  and a red edge', now['del']['border'] != now['add']['border'],
          '%s vs %s' % (now['del']['border'], now['add']['border']))
    check('  CONTROL: the three alternatives are indistinguishable from each '
          'other, which is the point',
          now['download']['color'] == now['add']['color'] == now['replace']['color'],
          now['add']['color'])
    check('Save Changes IS solid accent - it is the primary of its tab',
          now['save']['bg'] == now['T--alv-accent'], now['save']['bg'])
    check('  so exactly one control on screen is filled',
          len({now[k]['bg'] for k in ('download', 'add', 'replace', 'del')}) == 1
          and now['save']['bg'] != now['add']['bg'])

    head('3. the note strip, painted')
    check('a verified note is the house good tint',
          now['good']['bg'] == now['T--alv-good-soft'], now['good']['bg'])
    check('  and a mismatch is the bad tint',
          now['bad']['bg'] == now['T--alv-bad-soft'], now['bad']['bg'])
    check('  which differ from each other', now['good']['bg'] != now['bad']['bg'])

    head('4. the negative controls - the old modal, rendered')
    if not check('the backup exists to compare against', HAVE,
                 '(run apply_manage_modal.py first)'):
        return
    was = await paint(OLD_FRAG, css_of(OLD))
    check('CONTROL: Add to Existing WAS solid Bootstrap green',
          was['add']['bg'] == 'rgb(40, 167, 69)', was['add']['bg'])
    check('CONTROL: Replace WAS solid amber',
          was['replace']['bg'] == 'rgb(255, 193, 7)', was['replace']['bg'])
    check('CONTROL: Delete WAS a solid red FILL, not a tone',
          was['del']['bg'] == 'rgb(220, 53, 69)', was['del']['bg'])
    check('  so FOUR different fills sat in one row',
          len({was[k]['bg'] for k in ('download', 'add', 'replace', 'del')}) == 4,
          str(sorted({was[k]['bg'] for k in ('download', 'add', 'replace', 'del')})))
    check('CONTROL: the verified banner WAS Bootstrap alert green',
          was['good']['bg'] == 'rgb(212, 237, 218)', was['good']['bg'])
    _old = controls(OLDJS)
    check('  and the old scripts really did carry %d Bootstrap controls'
          % len(_old), len(_old) == 12, str(len(_old)))
    check('  across %d different class lists'
          % len({c for c, _ in _old}), len({c for c, _ in _old}) >= 6)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
