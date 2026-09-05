"""test_ia_palette.py - the Issues Analysis modal stops having its own palette.

    python test_ia_palette.py

Run from the repo root, after apply_ia_palette.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 3 RUNS THE MODAL'S OWN TOKEN READER in a browser, against base's
    real stylesheet. `iaTok` is a RUNTIME claim: it says the charts will get
    base's colours off :root. Reading the source proves the code was written,
    not that a custom property resolves - and Chart.js draws an invisible bar
    for an empty string and reports no error, so a token that fails to
    resolve is a chart that silently loses a series. It also checks the
    FALLBACKS are base's real values, both in the JS and in base itself: a
    safety net set to the wrong colour is worse than none, because it looks
    deliberate.
  * SECTION 4 renders base's five .alv-tag-* chips and requires each to look
    EXACTLY as it did before the round. The base change is meant to be
    invisible - the classes name their inks instead of repeating them - so
    "nothing moved" is the claim, and it is measured against .bak_iapal.
  * SECTION 2 walks the ageing ramp arithmetically, band by band, including
    the boundaries. The off-by-one this round fixed was in a LABEL, which no
    amount of running the code would have caught.
  * SECTION 1 hunts all four copies of the palette, and SECTION 5 asserts the
    things this round deliberately left alone are still there.
"""
import os
import re
import sys
import json
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FSR = os.path.join(T, 'fsr.html')
BBAK = BASE + '.bak_iapal'

PASS = FAIL = 0
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


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def nocomment(text):
    """A CHECK THAT READS TEXT CATCHES PROSE, and this round's comments name
       every literal they removed - including one that says
       style="color:#898781" on purpose, to record what was there."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


for p in (BASE, FSR):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the repo root' % p)
BS, F = read(BASE), read(FSR)
if '--alv-tag-sky-ink' not in BS:
    print('\n! not patched - run apply_ia_palette.py first.')
    sys.exit(1)
BC, FC = nocomment(BS), nocomment(F)

# The tokens this round claims base holds. Everything else is measured
# against these, so they are read from base rather than restated.
TOKENS = {}
for m in re.finditer(r'--(alv-[\w-]+):\s*([^;]+);', BS):
    TOKENS.setdefault(m.group(1), m.group(2).strip())

# ===========================================================================
head('1. four copies of one palette')
# ===========================================================================
check("CONTROL: the round's prose still names #898781", '#898781' in F)
check('CONTROL: .. and it is gone once stripped', '#898781' not in FC)

# copy 1 - the custom properties on .ia-body
for tok in ('--good:', '--warn:', '--serious:', '--crit:', '--sblue:',
            '--sgreen:', '--ink:', '--ink2:', '--muted:', '--grid:',
            '--surf:', '--hair:'):
    check('copy 1: the page-local token %s is gone' % tok.rstrip(':'),
          tok not in FC)

# copies 2, 3 and 4 - the literals, wherever they were written.
#
# SCOPED, and it took a draft to learn why. The accent pair #0e7c8b /
# #0a5e6a also appears 40-odd times elsewhere in fsr.html - the page's other
# modals, its buttons, its header - and this round opens none of those
# blocks. A blanket file scan reported them as failures, which is a check
# wider than its round reporting the rest of the file as a defect. The
# palette scan runs on the MODAL'S region; only colours that were unique to
# the modal are asked for file-wide.
_i = FC.index('#issuesAnalysisModal .ia-body{')
MODAL = FC[_i:FC.index('</script>', _i)]

for lit in ('#0ca30c', '#fab219', '#ec835a', '#d03b3b', '#2a78d6', '#008300',
            '#52514e', '#898781', '#e1e0d9', '#fcfcfb', '#0b0b0b', '#f0efec',
            '#f1f3f4', 'rgba(11,11,11,.10)'):
    check('  and the literal %s is gone from the file' % lit, lit not in FC)
for lit in ('#0a5e6a', '#0e7c8b'):
    check('  the accent literal %s is gone from the MODAL '
          '(it stays elsewhere in this page - not this round)' % lit,
          lit not in MODAL)

check('the inline colour in drillRows became a class',
      'class="ia-desc"' in FC and '.ia-desc{color:var(--alv-ink-faint);}' in FC)
check('the scrim KEEPS its literal - it is a shadow, not a palette colour',
      'rgba(11,11,11,.45)' in FC)

# THE TWO GREENS.
check('"Resolved" appears as a series twice', FC.count("label:'Resolved'") == 2)
check('  and both take the SAME green now',
      len(set(re.findall(r"label:'Resolved',data:res,backgroundColor:(\w+),",
                         FC))) == 1,
      str(set(re.findall(r"label:'Resolved',data:res,backgroundColor:(\w+),",
                         FC))))
check('  which is the good token, not a chart-local green',
      "label:'Resolved',data:res,backgroundColor:GOOD," in FC)
check('Logged takes a CATEGORY tone, not a verdict',
      "label:'Logged',data:logged,backgroundColor:CAT," in FC)

# TOKENS is keyed WITHOUT the leading '--' - the regex captures the name,
# not the dashes. A first draft asked for '--alv-tag-sky-ink' and reported a
# token that was right there.
check('base exposes the five category inks',
      all('alv-tag-%s-ink' % n in TOKENS
          for n in ('sky', 'moss', 'clay', 'slate', 'plum')),
      str(sorted(k for k in TOKENS if k.startswith('alv-tag'))))
check('  and the chip classes name them rather than repeating them',
      all('var(--alv-tag-%s-ink)' % n in BC
          for n in ('sky', 'moss', 'clay', 'slate', 'plum')))

# ===========================================================================
head('2. the ageing ramp, written once')
# ===========================================================================
check('the bands are declared exactly once', FC.count('AGE_BANDS=[') == 1)
check('  and BUCKETS is that same table, not a second one',
      'var BUCKETS=AGE_BANDS;' in FC)
check('  ageChip reads the table instead of restating 0/30/90/180',
      'AGE_BANDS[i].min' in FC and 'if(a>180)' not in FC)

BANDS = re.findall(r"\{label:'([^']+)',min:(\d+),max:([\de]+)", FC)
check('  four bands', len(BANDS) == 4, str([b[0] for b in BANDS]))
if len(BANDS) == 4:
    # THE OFF-BY-ONE. The middle label read '90-180 days' while its own min
    # was 91, so an issue at exactly 90 days sat in the band ABOVE the one
    # the label claimed. Running the code would never have caught it.
    for label, mn, mx in BANDS:
        nums = re.findall(r'\d+', label)
        if nums and not label.endswith('+ days'):
            check('  the label "%s" agrees with its own min' % label,
                  nums[0] == mn, 'label says %s, min is %s' % (nums[0], mn))
    check('  the bands are contiguous - no day falls between two of them',
          all(int(BANDS[i][2]) + 1 == int(BANDS[i + 1][1])
              for i in range(3)),
          ' '.join('%s-%s' % (b[1], b[2]) for b in BANDS))
    check('  and they start at 0, so a brand-new issue has a band',
          BANDS[0][1] == '0')

check('the first band is the GOOD token, per base\'s own scale comment',
      "min:0,max:30,c:GOOD" in FC)
check('  and --alv-age-1 goes unused here - the first band is the ABSENCE '
      'of ageing, not its mildest degree',
      "c:WARN" in FC and 'age-1' not in FC.split('AGE_BANDS')[0][-2000:])

# ===========================================================================
head('3. RUNTIME: does iaTok actually resolve against base?')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

# The fallbacks must be base's REAL values. A safety net set to the wrong
# colour is worse than no net, because it looks deliberate.
FBS = dict(re.findall(r"iaTok\('([\w-]+)',\s*'(#[0-9a-fA-F]{6})'\)", FC))
check('every iaTok call carries a fallback', len(FBS) == 9, str(len(FBS)))
for name, fb in sorted(FBS.items()):
    real = TOKENS.get('alv-' + name, '')
    check('  fallback for --alv-%s matches base' % name,
          real.lower() == fb.lower(), '%s vs base %s' % (fb, real or 'ABSENT'))

if sync_playwright is not None:
    def css_of(src):
        return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))

    # Lift the modal's OWN reader out of the template and run it, so this
    # tests the shipped code rather than a re-implementation of it.
    m = re.search(r'(var IA_CS = getComputedStyle.*?SURF  = iaTok\([^)]*\);)',
                  F, re.S)
    if not m:
        check('the token reader could be lifted out of the template', False)
        READER = ''
    else:
        check('the token reader could be lifted out of the template', True)
        READER = m.group(1)

    FIX = """<!doctype html><meta charset=utf-8>
<style>%s</style>
<div id="issuesAnalysisModal"><div class="ia-body">
  <span class="alv-tag alv-tag-sky" id="tsky">sky</span>
  <span class="alv-tag alv-tag-moss" id="tmoss">moss</span>
  <span class="alv-tag alv-tag-clay" id="tclay">clay</span>
  <span class="alv-tag alv-tag-slate" id="tslate">slate</span>
  <span class="alv-tag alv-tag-plum" id="tplum">plum</span>
</div></div>
<script>
%s
window.__IA = {GOOD:GOOD, WARN:WARN, SERIOUS:SERIOUS, CRIT:CRIT, CAT:CAT,
               INK2:INK2, MUTED:MUTED, GRID:GRID, SURF:SURF};
</script>""" % (css_of(BS), READER)

    _f = os.path.join(tempfile.gettempdir(), 'ia_palette_fixture.html')
    with open(_f, 'w', encoding='utf-8') as fh:
        fh.write(FIX)

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1100, 'height': 800})
        pg.goto('file://' + _f)
        R = pg.evaluate("() => window.__IA")
        CHIPS = pg.evaluate("""() => {
            const o = {};
            for (const n of ['sky','moss','clay','slate','plum']) {
                const cs = getComputedStyle(document.querySelector('#t'+n));
                o[n] = [cs.color, cs.backgroundColor, cs.borderColor];
            }
            return o;
        }""")
        b.close()

    def norm(v):
        return (v or '').strip().lower()

    WANT = {'GOOD': 'alv-good', 'WARN': 'alv-age-2', 'SERIOUS': 'alv-age-3',
            'CRIT': 'alv-age-4', 'CAT': 'alv-tag-sky-ink',
            'INK2': 'alv-ink-soft', 'MUTED': 'alv-ink-faint',
            'GRID': 'alv-line', 'SURF': 'alv-paper'}
    for js, tok in sorted(WANT.items()):
        got, want = norm(R.get(js)), norm(TOKENS.get(tok, ''))
        check('RUNTIME %-8s resolves to --%s' % (js, tok),
              got == want and got != '', '%s (base: %s)' % (got or 'EMPTY',
                                                            want))

    # A chart colour that resolves to '' draws an invisible bar and reports
    # NO error, so an empty string is the failure mode to name explicitly.
    check('  and none of the nine came back empty',
          all(norm(v) for v in R.values()),
          '%d of 9 resolved' % sum(1 for v in R.values() if norm(v)))

    # THE CONTROL: a token that does not exist must fall back, or the check
    # above passes on a reader that returns its argument regardless.
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto('file://' + _f)
        FBK = pg.evaluate(
            "() => iaTok('no-such-token-here', '#abcdef')")
        b.close()
    check('CONTROL: an absent token falls back rather than returning empty',
          FBK == '#abcdef', str(FBK))

# ===========================================================================
head('4. the base change is invisible - measured, not asserted')
# ===========================================================================
if sync_playwright is not None and os.path.exists(BBAK):
    OLD = read(BBAK)
    OFIX = """<!doctype html><meta charset=utf-8><style>%s</style>
<span class="alv-tag alv-tag-sky" id="tsky">sky</span>
<span class="alv-tag alv-tag-moss" id="tmoss">moss</span>
<span class="alv-tag alv-tag-clay" id="tclay">clay</span>
<span class="alv-tag alv-tag-slate" id="tslate">slate</span>
<span class="alv-tag alv-tag-plum" id="tplum">plum</span>""" % css_of(OLD)
    _o = os.path.join(tempfile.gettempdir(), 'ia_palette_before.html')
    with open(_o, 'w', encoding='utf-8') as fh:
        fh.write(OFIX)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1100, 'height': 800})
        pg.goto('file://' + _o)
        WAS = pg.evaluate("""() => {
            const o = {};
            for (const n of ['sky','moss','clay','slate','plum']) {
                const cs = getComputedStyle(document.querySelector('#t'+n));
                o[n] = [cs.color, cs.backgroundColor, cs.borderColor];
            }
            return o;
        }""")
        b.close()
    for n in ('sky', 'moss', 'clay', 'slate', 'plum'):
        check('.alv-tag-%s renders identically to before the round' % n,
              CHIPS[n] == WAS[n],
              '%s vs %s' % (CHIPS[n][0], WAS[n][0]))
    # CONTROL: the two fixtures must not be the same file, or "identical"
    # is a comparison of a thing with itself.
    check('CONTROL: the two stylesheets really do differ',
          css_of(OLD) != css_of(BS))
elif sync_playwright is not None:
    print('  !! base.html.bak_iapal missing - the before/after skipped')

# ===========================================================================
head('5. scope: what this round deliberately left alone')
# ===========================================================================
# MOVED 2 Sep by C2, and it is the SCOPE GUARD kind of 4b - the fourth
# variant, and the fifth time this project has moved one.
#
# These two said "C1 did not touch the tiles or the badges, they are C2's".
# True when written. C2 then migrated both, and a claim about what C1 left
# alone cannot be measured on a file a later round owns.
#
# So it is measured on the SNAPSHOT: fsr.html.bak_iatile is this page as C1
# left it, because C2 was the first round to touch these components since.
# Two fixed points, true for good, rather than a claim with an expiry date.
_C1 = os.path.join(T, 'fsr.html.bak_iatile')
AS_C1_LEFT_IT = nocomment(read(_C1)) if os.path.exists(_C1) else None
if AS_C1_LEFT_IT is None:
    check('C1 left a snapshot to measure its own scope against', False,
          'fsr.html.bak_iatile')
else:
    check('C1 did not touch the tiles - measured on fsr.html.bak_iatile, '
          'the page as C1 left it',
          '.ia-kpi{background:' in AS_C1_LEFT_IT
          and '.ia-kpi .v{font-size:18px' in AS_C1_LEFT_IT)
    check('  nor the badges',
          '.ia-badge.open{background:#fff3d6' in AS_C1_LEFT_IT
          and '.ia-badge.res{background:#d8f5da' in AS_C1_LEFT_IT)
    # AND THE FORWARD HALF. A guard that only ever loosens ends up
    # asserting nothing, so the live file has to show the work landed.
    check('  and C2 has since migrated both onto base',
          'class="alv-stats"' in FC and 'alv-pill alv-pill-good' in FC
          and '.ia-kpi{background:' not in FC)
check('.ia-tab is still a hand-rolled tab - the segmented control is its '
      'own round, with the Budget/Actuals .btn-group',
      '.ia-tab{border:none;background:transparent' in FC)
# MOVED by the print-leak round - the SCOPE GUARD kind of 4b, and the sixth
# time this project has moved one. This said "the page-local @media is still
# unqualified, that round owns it". True when written; that round has landed.
#
# Measured on the SNAPSHOT now: fsr.html.bak_leak is the page as the
# print-leak round found it, so the historical claim is true for good rather
# than expiring the moment the work it was waiting for arrives.
_PL = os.path.join(T, 'fsr.html.bak_leak')
if not os.path.exists(_PL):
    check('the print-leak round left a snapshot to measure against', False,
          'fsr.html.bak_leak')
else:
    check('the page-local @media WAS still unqualified when this round ran '
          '- measured on fsr.html.bak_leak',
          '@media (max-width:768px){' in read(_PL))
    check('  and the print-leak round has since guarded it',
          '@media screen and (max-width:768px){' in F
          and '@media (max-width:768px){' not in F)

for blk in re.findall(r'<style[^>]*>(.*?)</style>', F, re.S):
    check('braces balance in a style block',
          blk.count('{') == blk.count('}'))

# ===========================================================================
head('6. prose that contains markup IS markup')
# ===========================================================================
# THE PUSH GATE FOUND THIS ONE, in test_filter_toggle.py, which reported
# fsr.html block 2 as "no longer parsing". It was right.
#
# A first draft of this round's CSS comment read "ten JS literals in the
# <script> below". It sits inside a <style> block, so every browser is
# perfectly happy - style content is raw text until the closing tag. But a
# scanner slicing script blocks with <script...>(.*?)</script> then opened a
# block INSIDE the comment, took the rest of the comment as JavaScript, and
# the parse failed on the first real keyword after it.
#
# The check lives HERE now, so the round that writes the prose is the round
# that catches it, rather than three suites downstream.
for _name, _txt in (('fsr.html', F), ('base.html', BS)):
    _bad = [m.group(0)[:70] for m in re.finditer(r'/\*.*?\*/', _txt, re.S)
            if re.search(r'</?(?:script|style)\b', m.group(0))]
    check('%s: no CSS comment spells a script or style tag' % _name,
          not _bad, _bad[0] if _bad else '')
    _badjs = [l.strip()[:70] for l in _txt.split('\n')
              if l.lstrip().startswith('//') and '</script' in l]
    check('  and no JS comment spells a CLOSING script tag '
          '(that one ends the block for the browser too)',
          not _badjs, _badjs[0] if _badjs else '')

# And the thing the gate actually measured: the blocks still parse.
if sync_playwright is not None:
    def _flatten(t):
        t = re.sub(r'\{%[^%]*%\}', '', t)
        return re.sub(r'\{\{[^}]*\}\}', 'x', t)

    _blocks = [_flatten(x) for x in re.findall(
        r'<script(?![^>]*src=)[^>]*>(.*?)</script>', F, re.S)]
    with sync_playwright() as pw:
        _b = pw.chromium.launch()
        _pg = _b.new_page()
        _pg.goto('about:blank')
        _errs = [_pg.evaluate(
            "s => { try { new Function(s); return '' } catch (e) "
            "{ return e instanceof SyntaxError ? String(e.message) : '' } }", x)
            for x in _blocks]
        _b.close()
    check('every script block in fsr.html parses',
          not any(_errs), '; '.join(e for e in _errs if e) or
          '%d blocks' % len(_blocks))
    # CONTROL: the parser must actually be able to reject something.
    with sync_playwright() as pw:
        _b = pw.chromium.launch()
        _pg = _b.new_page()
        _pg.goto('about:blank')
        _neg = _pg.evaluate(
            "s => { try { new Function(s); return '' } catch (e) "
            "{ return e instanceof SyntaxError ? 'rejected' : '' } }",
            'if ( { for (;;) {}')
        _b.close()
    check('  CONTROL: the parser rejects deliberately broken JS',
          _neg == 'rejected', _neg or 'ACCEPTED IT')

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
