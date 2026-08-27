"""test_action_standard - the page-header bar has one home, and one rule.

    python test_action_standard.py

STATIC: base.html owns the component; asset_detail.html stopped paying for
its own copy, without losing anything that was really its own.

BROWSER: three things that only rendering can answer.

  1. WEIGHT READS AS WEIGHT. The primary is solid accent, the danger button
     is OUTLINED at rest and only fills red on hover. Both states measured;
     a control that leaves it solid red fails the rest state.

  2. THE MOBILE COLLAPSE. Secondaries hide, the primary flexes, a 44px More
     button appears and Back keeps a 44px target - all inside 375px. This
     is the half worth hoisting and the half nobody looks at.

  3. THE MORE BUTTON HAS AN EDGE. Found by measuring, not reading:
     `.page-action-buttons .btn { border-color: transparent }` and a bare
     `.action-more-btn { border: ... }` are (0,2,0) against (0,1,0), so the
     generic won and the More button rendered as a white box on white. The
     control puts the unscoped selector back and demands the border vanish.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
D = 'asset_detail.html'

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(name):
    p = os.path.join(TPL, name)
    if not os.path.exists(p):
        sys.exit('! pages/templates/%s not found - run from the root' % name)
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


def strip_comments(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


BASE = read('base.html')
SRC = read(D)
CSS = strip_comments(''.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                        SRC, re.S | re.I)))
_i = BASE.find('--alv-table-std')
BLOCK = strip_comments(BASE[_i:BASE.find('</style>', _i)]) if _i >= 0 else ''
# Anchored on a real SELECTOR, not on the marker comment. BLOCK has its
# comments stripped, so `--alv-actions-std` - which exists only inside a
# comment - was never found, find() returned -1, and the search for the
# media query started from the end of the string. Every mobile check then
# ran against an empty string. Prose is not a mechanism; the marker is fine
# for "is the round applied?" on the RAW file and useless here.
_a = BLOCK.find('.page-action-buttons {')
_m = BLOCK.find('@media (max-width: 768px)', _a) if _a >= 0 else -1
MOBILE = BLOCK[_m:] if _m >= 0 else ''


def rule_starts(css, name):
    return set(m.end() for m in re.finditer(
        r'(?<![\w-])%s(?![\w-])[^{}]*\{' % re.escape(name), css))


def rules_naming(css, *names):
    out = set()
    for n in names:
        out |= rule_starts(css, n)
    return len(out)


# ======================================================= base.html owns it
check('base.html carries the action bar', '--alv-actions-std' in BASE)
check('  and only once', BASE.count('--alv-actions-std') == 1)
for want in ('.page-action-buttons', '.action-primary', '.action-secondary',
             '.action-danger', '.action-back', '.action-more-btn',
             '.action-more-menu', '.action-more-item', '.disabled-btn'):
    check('  %-22s is defined' % want, rules_naming(BLOCK, want) >= 1)
check('  the primary is the accent, not a Bootstrap colour',
      re.search(r'\.action-primary\s*\{[^}]*background:\s*var\(--alv-accent\)',
                BLOCK) is not None)
check('  the danger tone is OUTLINED at rest',
      re.search(r'\.action-danger\s*\{[^}]*background:\s*var\(--alv-paper\)',
                BLOCK) is not None)
check('  and fills red only on hover',
      re.search(r'\.action-danger:hover[^{]*\{[^}]*background:\s*'
                r'var\(--alv-danger\)', BLOCK, re.S) is not None)
check('  Back is quiet - no fill, no border',
      re.search(r'\.action-back\s*\{[^}]*background:\s*transparent', BLOCK)
      is not None)
check('  a disabled button is not still a working link',
      re.search(r'\.disabled-btn\s*\{[^}]*pointer-events:\s*none', BLOCK)
      is not None)
# The bug this suite exists to keep fixed.
check('  the More button is SCOPED, or the generic border wins',
      '.page-action-buttons .action-more-btn' in BLOCK)
check('the mobile collapse came with it', bool(MOBILE))
check('  secondaries step aside',
      re.search(r'\.action-secondary\s*\{\s*display:\s*none', MOBILE)
      is not None)
check('  the primary takes the room',
      re.search(r'\.action-primary\s*\{[^}]*flex:\s*1 1 auto', MOBILE)
      is not None)
check('  the More menu appears',
      re.search(r'\.action-more-wrapper\s*\{[^}]*display:\s*block', MOBILE)
      is not None)
check('  and Back keeps a 44px target',
      re.search(r'\.action-back\s*\{[^}]*width:\s*44px', MOBILE) is not None)
check('  losing only its label',
      '.action-back-label { display: none; }' in MOBILE)
check('base.html braces still balance',
      BLOCK.count('{') == BLOCK.count('}'))

# =================================================== asset_detail.html paid
check('%s: no Bootstrap colour survives on a bar button' % D,
      not re.search(r'class="[^"]*btn-(?:warning|success|light|primary)'
                    r'[^"]*action-', SRC)
      and not re.search(r'class="[^"]*action-[^"]*btn-'
                        r'(?:warning|success|light)', SRC))
check('  Edit is the primary, live and disabled (%d)'
      % SRC.count('action-primary'), SRC.count('action-primary') == 2)
check('  Delete carries the danger TONE, both branches (%d)'
      % SRC.count('action-danger'), SRC.count('action-danger') == 2)
check('  and keeps its position class, so mobile still hides it',
      SRC.count('action-secondary action-danger') == 2)
check('  Back and More lost their fill',
      'btn action-back' in SRC and 'btn action-more-btn' in SRC
      and 'btn-info action-back' not in SRC)
for gone in ('.page-action-buttons', '.action-primary', '.action-secondary',
             '.action-back', '.action-more-btn', '.action-more-menu',
             '.action-more-item', '.action-more-wrapper', '.disabled-btn'):
    check('  %-22s has no local rules left' % gone,
          rules_naming(CSS, gone) == 0)
# Presence is not integrity: the deletion must have stopped where it should.
for sel, floor in (('.photo-grid', 1), ('.photo-tile', 4),
                   ('.warranty-grid', 2), ('.asset-header-thumb', 3),
                   ('.detail-row', 2), ('.notes-section', 2),
                   ('.maintenance-total', 1)):
    got = rules_naming(CSS, sel)
    check('  KEPT %-22s %d rules (need %d)' % (sel, got, floor), got >= floor)
check('  the action-back LABEL is still in the markup',
      'action-back-label' in SRC)
check('  every permission conditional survived (%d)'
      % SRC.count('perms.auth.can_edit_properties'),
      SRC.count('perms.auth.can_edit_properties') >= 3)
check('  and both action targets did',
      'confirmDelete()' in SRC and "url 'edit_asset'" in SRC)
check('  no unclosed Django comment',
      not any('{#' in ln and '#}' not in ln for ln in SRC.split('\n')))

# ============================================================== IN A BROWSER
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('')
    for label, ok in results:
        print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad = sum(0 if ok else 1 for _, ok in results)
    print('')
    print('  SKIP  Chromium checks skipped - playwright not installed')
    print('')
    print('%d of %d failed' % (bad, len(results)) if bad
          else 'All %d checks passed. (browser checks skipped)' % len(results))
    sys.exit(1 if bad else 0)

BOOT = None
for cand in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
             '/tmp/bootstrap.min.css'):
    if os.path.exists(cand):
        BOOT = open(cand, encoding='utf-8').read()
        break

if BOOT is None:
    print('')
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
else:
    _c = re.sub(r'<!--.*?-->', '', BASE, flags=re.S)
    STD = '\n'.join(b for b in re.findall(r'<style[^>]*>(.*?)</style>',
                                          _c, re.S | re.I)
                    if '--alv-paper' in strip_comments(b)
                    or '--alv-accent:' in strip_comments(b))
    check('the standard CSS could be lifted from base.html', bool(STD.strip()))

    def extract_div(text, opening):
        """From an opening <div ...> to ITS closing tag, counting nesting.

        Not a non-greedy regex: `<div class="page-action-buttons">.*?</div>`
        stopped at the first inner </div> - which is inside the More menu -
        so the fragment never reached Back, and four checks reported it
        "absent" when the page has it. The bar contains nested divs; only
        a counting walk finds the real end.
        """
        i = text.find(opening)
        if i < 0:
            return ''
        depth, j = 0, i
        for m in re.finditer(r'<div\b|</div>', text[i:]):
            if m.group(0) == '</div>':
                depth -= 1
                if depth == 0:
                    j = i + m.end()
                    break
            else:
                depth += 1
        return text[i:j]

    frag = extract_div(SRC, '<div class="page-action-buttons">')
    check('the action bar markup could be located', bool(frag))
    check('  and it reaches all the way to Back',
          'action-back' in frag and frag.rstrip().endswith('</div>'))

    def resolve(f, branch):
        prev = None
        while prev != f:
            prev = f
            # flags=re.S, NOT a bare re.S - which re.sub takes as `count`
            # (16). Without DOTALL a multi-line {% if %} never collapsed, so
            # BOTH branches rendered, the bar was twice as full as the real
            # page, and nothing flexed. It failed loudly, which is the only
            # reason it was found.
            f = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|endif)).)*?)'
                       r'\{%\s*else\s*%\}((?:(?!\{%\s*(?:if|endif)).)*?)'
                       r'\{%\s*endif\s*%\}',
                       lambda m: m.group(1 if branch == 0 else 2), f,
                       flags=re.S)
            f = re.sub(r'\{%\s*if[^%]*%\}((?:(?!\{%\s*(?:if|endif)).)*?)'
                       r'\{%\s*endif\s*%\}', r'\1', f, flags=re.S)
        return f

    def page(extra='', branch=0):
        f = re.sub(r'\{[{%][^}%]*[%}]\}', '#', resolve(frag, branch))
        return ('<!doctype html><meta charset=utf-8><style>%s</style>'
                '<style>%s</style><style>%s</style>'
                '<body style="margin:0;padding:20px;background:#fff">%s</body>'
                % (BOOT, STD, extra, f))

    def rgb(v):
        m = re.findall(r'\d+', v or '')
        return tuple(int(x) for x in m[:3]) if len(m) >= 3 else None

    tmp = os.path.join(ROOT, '_action_probe.html')
    try:
      try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())

            def probe(width, extra=''):
                pg = br.new_page(viewport={'width': width, 'height': 700})
                open(tmp, 'w', encoding='utf-8').write(page(extra))
                pg.goto('file://' + tmp)
                pg.wait_for_timeout(180)
                d = pg.evaluate(
                    """()=>{const q=s=>{const e=document.querySelector(s);
                       if(!e) return null;
                       const r=e.getBoundingClientRect(), c=getComputedStyle(e);
                       return {w:Math.round(r.width),h:Math.round(r.height),
                               x:Math.round(r.x),bg:c.backgroundColor,
                               bd:c.borderTopColor,col:c.color,disp:c.display};};
                       return {primary:q('.action-primary'),
                               danger:q('.action-danger'),
                               back:q('.action-back'),
                               more:q('.action-more-btn'),
                               bar:q('.page-action-buttons')};}""")
                # Never None. A missing element must be a NAMED failure, not
                # a TypeError three lines later - the guard was on the
                # desktop probe only in the first draft and the mobile one
                # crashed the suite. "A crash is not a report", twice now.
                for k in ('primary', 'danger', 'back', 'more', 'bar'):
                    if d.get(k) is None:
                        d[k] = {'w': 0, 'h': 0, 'x': 0, 'bg': 'absent',
                                'bd': 'absent', 'col': 'absent',
                                'disp': 'none', 'absent': True}
                return pg, d

            # ---- desktop -------------------------------------------------
            pg, d = probe(1240)
            for k in ('primary', 'danger', 'back', 'bar'):
                check('desktop: .%s is in the bar at all' % k,
                      not d[k].get('absent'))
            check('desktop: the primary is solid accent %s' % d['primary']['bg'],
                  rgb(d['primary']['bg']) == (14, 124, 139))
            check('  Delete is OUTLINED, not solid red (%s)' % d['danger']['bg'],
                  rgb(d['danger']['bg']) == (255, 255, 255))
            check('    with red ink and a red edge (%s / %s)'
                  % (d['danger']['col'], d['danger']['bd']),
                  rgb(d['danger']['col']) is not None
                  and rgb(d['danger']['col'])[0] > rgb(d['danger']['col'])[1] + 40
                  and rgb(d['danger']['bd']) != rgb(d['danger']['bg']))
            # Guarded. A control that took .action-danger off the live
            # branch made hover() wait for a locator that does not exist,
            # time out, and kill the suite - so the batch reported ZERO
            # failures and the control read as "did not bite". A crash is
            # not a report, and here it actively hid one.
            if pg.query_selector('.action-danger') is None:
                check('    the danger button is on the page to hover', False)
            else:
                pg.hover('.action-danger')
                pg.wait_for_timeout(150)
                hov = pg.evaluate("()=>{const c=getComputedStyle("
                                  "document.querySelector('.action-danger'));"
                                  "return [c.backgroundColor,c.color];}")
                check('    and it fills red on hover (%s)' % hov[0],
                      rgb(hov[0]) is not None
                      and rgb(hov[0])[0] > rgb(hov[0])[1] + 60)
                check('    CONTROL: at rest it was NOT that colour',
                      rgb(hov[0]) != rgb(d['danger']['bg']))
            check('  Back is quiet - no fill (%s)' % d['back']['bg'],
                  d['back']['bg'] in ('rgba(0, 0, 0, 0)', 'transparent'))
            check('  and sits on the right (x=%d of %d)'
                  % (d['back']['x'], 1240),
                  d['back']['x'] > 1240 * 0.7)
            check('  the More button is hidden on desktop (w=%d)'
                  % d['more']['w'], d['more']['w'] == 0)
            pg.close()

            # ---- mobile --------------------------------------------------
            pg, d = probe(375)
            check('mobile: the primary flexes to fill (w=%d)'
                  % d['primary']['w'], d['primary']['w'] > 150)
            check('  the secondary steps aside (w=%d)'
                  % d['danger']['w'], d['danger']['w'] == 0)
            check('  a 44px More button appears (%dx%d)'
                  % (d['more']['w'], d['more']['h']),
                  d['more']['w'] == 44)
            check('  AND IT HAS AN EDGE (%s)'
                  % d['more']['bd'],
                  rgb(d['more']['bd']) is not None
                  and d['more']['bd'] not in ('rgba(0, 0, 0, 0)',
                                              'transparent'))
            check('  Back keeps a 44px target (w=%d)' % d['back']['w'],
                  d['back']['w'] == 44)
            check('  and the whole bar fits 375px (right edge %d)'
                  % (d['back']['x'] + d['back']['w']),
                  d['back']['x'] + d['back']['w'] <= 375)
            pg.close()

            # ---- the control for the bug this round found ----------------
            pg, d = probe(375, '.action-more-btn { border: 1px solid '
                               'var(--alv-line) !important; } '
                               '.page-action-buttons .action-more-btn { '
                               'border-color: transparent !important; }')
            check('  CONTROL: an unscoped More rule really does lose its '
                  'border (%s)' % d['more']['bd'],
                  d['more']['bd'] in ('rgba(0, 0, 0, 0)', 'transparent'))
            pg.close()
            br.close()
      except Exception as exc:
        # Whatever went wrong, the run still has to REPORT. Anything that
        # escapes to here is a named failure and the summary still prints.
        check('the browser half ran to the end (%s: %s)'
              % (type(exc).__name__, str(exc).split(chr(10))[0][:70]), False)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
