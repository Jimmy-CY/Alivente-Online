"""apply_ia_palette.py - the Issues Analysis modal stops having its own palette.

    python apply_ia_palette.py --check     dry run, writes nothing
    python apply_ia_palette.py

Run from the repo root. Round C1 of the Issues module.

THE PALETTE WAS DECLARED FOUR TIMES.

  1. TWELVE custom properties on `#issuesAnalysisModal .ia-body`.
  2. TEN JS literals at the top of the modal's page script, for Chart.js.
  3. AGAIN as raw literals in the .ia-drill and table.ia-tbl rules - because
     that markup is a SIBLING of the modal, not a child, so it never saw the
     custom properties at all. That is not carelessness; it is the direct
     consequence of scoping the tokens to .ia-body instead of :root.
  4. ONCE MORE inline, in the JS that builds the drill-down table:
     style="color:#898781" on the description span. Found by this patcher's
     own literal scan rather than by reading, which is the argument for
     having the scan.

Three of the twelve were never used in CSS at all: --serious, --sblue and
--sgreen existed ONLY so the charts could read them, and the charts never
did. They read copy 2.

WHAT THIS ROUND DOES
  * base gains --alv-tag-sky-ink .. --alv-tag-plum-ink, and the .alv-tag-*
    classes use them. No chip changes appearance; the category family simply
    becomes readable by anything that needs a categorical tone.
  * All four copies are deleted. The CSS uses base's :root tokens; the JS
    READS them off :root at chart-build time, with base's own values as
    fallbacks so a renamed token degrades to the right colour rather than to
    nothing.
  * "Resolved" stops being two different greens.
  * The ageing thresholds stop being written twice.

NOT THIS ROUND: .ia-kpi -> .alv-stat, .ia-badge -> .alv-pill, .ia-tab ->
the segmented control, and the page-local @media that prints. Those are C2
and the segmented-control round. This one is colour only, so the rounds
after it measure against the right palette.

HOUSE RULES: idempotent, .bak_iapal backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, and guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
FSR = os.path.join(T, 'fsr.html')
for _p in (BASE, FSR):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:90]))
    return t.replace(old, new, 1)


PALETTE_NOTE = """/* THE PALETTE WAS DECLARED FOUR TIMES, and this was copy 1 - twelve
     custom properties scoped to .ia-body.

       copy 2  ten JS literals in the page script below, for Chart.js
       copy 3  the same colours AGAIN as raw literals in the .ia-drill and
               table.ia-tbl rules further down - because that markup is a
               SIBLING of the modal, not a child, so it never saw these
               custom properties at all. Copy 3 exists BECAUSE copy 1 was
               scoped to .ia-body instead of :root.
       copy 4  one inline style="color:#898781" written by drillRows(),
               which no token can reach at all.

     Three of the twelve were never used in CSS: --serious, --sblue and
     --sgreen were declared so that the charts could read them, and the
     charts never did - they read copy 2.

     All four are gone. base's :root tokens are the one source, and the
     script below reads those same tokens rather than restating them. */"""

FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


# ===========================================================================
# 1. base.html - the category family becomes readable
# ===========================================================================
B_ORIG, B_CRLF, b = load(BASE)
B_DONE = '--alv-tag-sky-ink' in b
if B_DONE:
    print('  base.html already patched')
else:
    b = sub1(b, """        --alv-neutral:    #6b7780;
        --alv-neutral-soft: #eef1f2;
""", """        --alv-neutral:    #6b7780;
        --alv-neutral-soft: #eef1f2;

        /* THE CATEGORY FAMILY'S INKS, lifted out of the .alv-tag-* rules so
           that something which is not a chip can use one.

           The Issues Analysis modal's "Logged vs resolved" chart asked
           first. Logged is a CATEGORY - how many arrived - not a verdict,
           so it wanted a categorical tone; but the five tag inks were
           literals inside class definitions, and a canvas element cannot
           read a class. It had #2a78d6, a blue nothing else in the system
           used.

           Lifting all five rather than the one that was asked for: a family
           with one member promoted reads as an accident, and the next
           asker wants a different colour of the same set. No chip changes
           appearance - the classes below now name these instead of
           repeating them. */
        --alv-tag-sky-ink:   #2b6a86;
        --alv-tag-moss-ink:  #4a6b3c;
        --alv-tag-clay-ink:  #8a5a34;
        --alv-tag-slate-ink: #55606b;
        --alv-tag-plum-ink:  #6b4a72;
""", 'base: the five tag inks')

    b = sub1(b, """      .alv-tag-sky   { color: #2b6a86; background: #e8f1f5; border-color: #d3e4ec; }
      .alv-tag-moss  { color: #4a6b3c; background: #eef4e9; border-color: #dde8d6; }
      .alv-tag-clay  { color: #8a5a34; background: #f7efe7; border-color: #ecdfd2; }
      .alv-tag-slate { color: #55606b; background: #eef1f3; border-color: #e0e5e9; }
      .alv-tag-plum  { color: #6b4a72; background: #f3edf5; border-color: #e5dae8; }""",
                """      .alv-tag-sky   { color: var(--alv-tag-sky-ink);   background: #e8f1f5; border-color: #d3e4ec; }
      .alv-tag-moss  { color: var(--alv-tag-moss-ink);  background: #eef4e9; border-color: #dde8d6; }
      .alv-tag-clay  { color: var(--alv-tag-clay-ink);  background: #f7efe7; border-color: #ecdfd2; }
      .alv-tag-slate { color: var(--alv-tag-slate-ink); background: #eef1f3; border-color: #e0e5e9; }
      .alv-tag-plum  { color: var(--alv-tag-plum-ink);  background: #f3edf5; border-color: #e5dae8; }""",
                'base: the tag classes name their inks')

    for _n in ('sky', 'moss', 'clay', 'slate', 'plum'):
        want('--alv-tag-%s-ink:' % _n in b, 'base: --alv-tag-%s-ink missing' % _n)
        want('var(--alv-tag-%s-ink)' % _n in b,
             'base: .alv-tag-%s does not use its token' % _n)

# ===========================================================================
# 2. fsr.html - all four copies of the modal's palette
# ===========================================================================
F_ORIG, F_CRLF, f = load(FSR)
F_DONE = 'var(--alv-ink-faint)' in f and 'AGE_BANDS' in f
if F_DONE:
    print('  fsr.html already patched')
else:
    # ------------------------------------------------ 2a. the style block
    # Scoped surgery: this file has other <style> blocks and other #fff.
    S_OPEN = "  #issuesAnalysisModal .ia-body{--good:#0ca30c;"
    if f.count(S_OPEN) != 1:
        sys.exit('! could not find the modal style block exactly once')
    i = f.index(S_OPEN)
    j = f.index('</style>', i)
    css = f[i:j]

    # ORDER MATTERS HERE, and it cost a draft. The comment below NAMES the
    # literals it is explaining, so if it goes in before the literal sweep
    # the sweep rewrites the explanation into a description of the fix -
    # "one inline style=\'color:var(--alv-ink-faint)\'", which is exactly
    # backwards. Declaration first, sweep second, prose last.
    css = sub1(css, """  #issuesAnalysisModal .ia-body{--good:#0ca30c;--warn:#fab219;--serious:#ec835a;--crit:#d03b3b;--sblue:#2a78d6;--sgreen:#008300;
      --ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--surf:#fcfcfb;--hair:rgba(11,11,11,.10);
      max-height:80vh;overflow-y:auto;background:var(--surf);}""",
                """  @@PALETTE_NOTE@@
  #issuesAnalysisModal .ia-body{max-height:80vh;overflow-y:auto;background:var(--alv-paper);}""",
                'modal: the token block')

    # The page-local names, then the literals that said the same thing.
    VARS = (('--ink2', '--alv-ink-soft'), ('--ink', '--alv-ink'),
            ('--muted', '--alv-ink-faint'), ('--grid', '--alv-line'),
            ('--surf', '--alv-paper'), ('--hair', '--alv-line'),
            ('--good', '--alv-good'), ('--warn', '--alv-warn'),
            ('--crit', '--alv-bad'))
    for old, new in VARS:
        css = css.replace('var(%s)' % old, 'var(%s)' % new)

    LITS = (('#fcfcfb', 'var(--alv-paper)'), ('#0b0b0b', 'var(--alv-ink)'),
            ('#898781', 'var(--alv-ink-faint)'), ('#e1e0d9', 'var(--alv-line)'),
            ('#f0efec', 'var(--alv-line-soft)'), ('#52514e', 'var(--alv-ink-soft)'),
            ('#f1f3f4', 'var(--alv-line-soft)'), ('#0a5e6a', 'var(--alv-accent-ink)'),
            ('#0e7c8b', 'var(--alv-accent)'),
            ('rgba(11,11,11,.10)', 'var(--alv-line)'),
            ('background:#fff;', 'background:var(--alv-paper);'))
    for old, new in LITS:
        css = css.replace(old, new)

    # COPY 4, found by this patcher's own literal scan: drillRows() writes
    # an inline colour on the description span. An inline style cannot read
    # a token, so it gets a class - and .ia-empty-row was already the same
    # colour with a name.
    css = sub1(css, '  .ia-empty-row{padding:20px 16px;color:var(--alv-ink-faint);font-size:12.5px;}',
               '  .ia-empty-row{padding:20px 16px;color:var(--alv-ink-faint);font-size:12.5px;}\n'
               '  /* drillRows() wrote this colour inline, which no token can reach. */\n'
               '  .ia-desc{color:var(--alv-ink-faint);}',
               'modal: the description span gets a class')

    # The scrim stays a literal and says so - it is a shadow over the page,
    # not one of the palette's colours.
    css = sub1(css, '.ia-drill-overlay{position:fixed;inset:0;background:rgba(11,11,11,.45);',
               '/* The scrim stays a literal: it is a shadow cast over the page, not\n'
               '   one of the palette\'s colours, and no token means "45% black". */\n'
               '  .ia-drill-overlay{position:fixed;inset:0;background:rgba(11,11,11,.45);',
               'modal: the scrim keeps its literal')

    # PROSE LAST, so the sweep above cannot rewrite it.
    css = sub1(css, '  @@PALETTE_NOTE@@', PALETTE_NOTE, 'modal: the palette note')

    f = f[:i] + css + f[j:]

    # ------------------------------------------------------- 2b. the script
    f = sub1(f, """  var GOOD='#0ca30c',WARN='#fab219',SERIOUS='#ec835a',CRIT='#d03b3b',BLUE='#2a78d6',GREEN='#008300';
  var INK2='#52514e',MUTED='#898781',GRID='#e1e0d9',SURF='#fcfcfb';
  var BUCKETS=[{label:'0\u201330 days',min:0,max:30,c:GOOD},{label:'31\u201390 days',min:31,max:90,c:WARN},
    {label:'90\u2013180 days',min:91,max:180,c:SERIOUS},{label:'180+ days',min:181,max:1e9,c:CRIT}];""",
             """  // COPY 2 OF THE PALETTE, and the only one the charts ever read. A canvas
  // element cannot take a class, so these have to be values - but they do not have to
  // be LITERALS. Read base's tokens off :root once, when the modal's script
  // runs, and the charts follow the system the way every other surface does.
  //
  // The fallbacks are base's own values, so a renamed token degrades to the
  // right colour rather than to nothing - Chart.js draws an invisible bar for
  // an empty string and reports no error.
  var IA_CS = getComputedStyle(document.documentElement);
  function iaTok(name, fallback){
    var v = IA_CS.getPropertyValue('--alv-' + name);
    return (v && v.trim()) || fallback;
  }
  var GOOD    = iaTok('good',         '#1e7d4f'),
      WARN    = iaTok('age-2',        '#9a6a08'),
      SERIOUS = iaTok('age-3',        '#a8481a'),
      CRIT    = iaTok('age-4',        '#b3261e'),
      CAT     = iaTok('tag-sky-ink',  '#2b6a86');
  var INK2  = iaTok('ink-soft',  '#5b6b73'),
      MUTED = iaTok('ink-faint', '#8a979d'),
      GRID  = iaTok('line',      '#e3e8ea'),
      SURF  = iaTok('paper',     '#ffffff');

  // THE AGEING RAMP, ONCE. This table and ageChip() at the foot of the file
  // each carried their own copy of 0 / 30 / 90 / 180 - two spellings of one
  // decision, which is how the third label came to read '90-180 days' while
  // its own min was 91. An issue at exactly 90 days sits in the band above
  // the one that label claimed. The label is corrected here and ageChip now
  // reads this table rather than restating it.
  //
  // base's scale supplies the tones, and its comment settles the first band:
  // "There is deliberately no step for NOT YET DUE. That is the absence of
  // ageing, not the first degree of it, and it takes the good token." So
  // --alv-age-1 goes unused in this modal - not an oversight, the point.
  var AGE_BANDS=[{label:'0\u201330 days',min:0,max:30,c:GOOD},
    {label:'31\u201390 days',min:31,max:90,c:WARN},
    {label:'91\u2013180 days',min:91,max:180,c:SERIOUS},
    {label:'180+ days',min:181,max:1e9,c:CRIT}];
  var BUCKETS=AGE_BANDS;""", 'script: tokens and the one ramp')

    f = sub1(f, """  function ageChip(a){var c=GOOD; if(a>180)c=CRIT; else if(a>90)c=SERIOUS; else if(a>30)c=WARN; return '<span class="ia-age" style="color:'+c+'">'+a+'d</span>';}""",
             """  function ageChip(a){
    var c=AGE_BANDS[0].c;
    for(var i=0;i<AGE_BANDS.length;i++){
      if(a>=AGE_BANDS[i].min&&a<=AGE_BANDS[i].max){c=AGE_BANDS[i].c;break;}
    }
    return '<span class="ia-age" style="color:'+c+'">'+a+'d</span>';}""",
             'script: ageChip reads the ramp')

    # THE TWO GREENS. 'Resolved' was #0ca30c on one tab and #008300 on
    # another - same word, same concept, same modal.
    f = sub1(f, "{label:'Resolved',data:res,backgroundColor:GREEN,",
             "{label:'Resolved',data:res,backgroundColor:GOOD,",
             'script: Resolved is ONE green')
    f = sub1(f, "{label:'Logged',data:logged,backgroundColor:BLUE,",
             "{label:'Logged',data:logged,backgroundColor:CAT,",
             'script: Logged takes a category tone')
    f = sub1(f, "showDrill(title,list,el.datasetIndex===0?BLUE:GREEN);",
             "showDrill(title,list,el.datasetIndex===0?CAT:GOOD);",
             'script: the drill tag follows the bars')

    f = sub1(f, '\'<br><span style="color:#898781">\'',
             '\'<br><span class="ia-desc">\'',
             'script: the inline description colour becomes a class')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
_nc = '\n'.join('' if l.lstrip().startswith('//') else l
                for l in _nc.split('\n'))

for dead in ('#0ca30c', '#fab219', '#ec835a', '#d03b3b', '#2a78d6', '#008300',
             '#52514e', '#898781', '#e1e0d9', '#fcfcfb', '#0b0b0b', '#f0efec',
             '#f1f3f4'):
    want(dead not in _nc, 'fsr: the literal %s survives' % dead)
for dead in ('--good:', '--warn:', '--serious:', '--crit:', '--sblue:',
             '--sgreen:', '--ink:', '--ink2:', '--muted:', '--grid:',
             '--surf:', '--hair:'):
    want(dead not in _nc, 'fsr: the page-local token %s survives' % dead)
want('var(--sblue)' not in f and 'BLUE' not in _nc.replace('CAT', ''),
     'fsr: a BLUE reference survives')

want(_nc.count("label:'Resolved'") == 2, 'fsr: expected two Resolved series')
want('backgroundColor:GREEN' not in _nc, 'fsr: Resolved is still two greens')
want(_nc.count('AGE_BANDS=[') == 1 and 'var BUCKETS=AGE_BANDS;' in _nc,
     'fsr: the ageing ramp is not written once')
want("'91\u2013180 days'" in _nc, 'fsr: the off-by-one label was not corrected')
want('iaTok(' in _nc and 'getComputedStyle(document.documentElement)' in _nc,
     'fsr: the charts do not read base tokens')
# The fallbacks must be base's REAL values, or the safety net lies.
for _tok, _fb in (('good', '#1e7d4f'), ('age-2', '#9a6a08'),
                  ('age-3', '#a8481a'), ('age-4', '#b3261e'),
                  ('ink-soft', '#5b6b73'), ('ink-faint', '#8a979d'),
                  ('line', '#e3e8ea'), ('tag-sky-ink', '#2b6a86')):
    want(re.search(r"--alv-%s:\s*%s" % (re.escape(_tok), _fb), b) is not None,
         'the %s fallback %s is not what base actually holds' % (_tok, _fb))
    want(re.search(r"iaTok\('%s',\s*'%s'\)" % (re.escape(_tok), _fb), _nc)
         is not None, 'fsr: iaTok fallback for %s is wrong' % _tok)

# Out of scope for C1, and must be untouched.
want('.ia-badge.open{background:#fff3d6' in f,
     'fsr: .ia-badge was touched - it becomes .alv-pill in C2, not here')
want('.ia-kpi{background:' in f, 'fsr: .ia-kpi was touched - that is C2')
want('@media (max-width:768px){' in f,
     'fsr: the page-local media block was touched - that is its own round')

for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
    want(blk.count('{') == blk.count('}'), 'fsr: unbalanced braces in a style block')

# PROSE THAT CONTAINS MARKUP *IS* MARKUP, and this round learned it the
# expensive way. A first draft's CSS comment read "ten JS literals in the
# <script> below" - inside a <style> block, so every browser was perfectly
# happy, because style content is raw text until the closing tag. But any
# scanner that slices script blocks with <script...>(.*?)</script> then
# opened a block INSIDE the comment, and test_filter_toggle.py's parse
# check reported fsr.html block 2 as no longer parsing. It was right to.
#
# So: no comment this round writes may spell an HTML tag. Checked on both
# files, because base.html's new comment made the same mistake.
for _name, _text in (('fsr.html', f), ('base.html', b)):
    for _m in re.finditer(r'/\*.*?\*/', _text, re.S):
        want(not re.search(r'</?(?:script|style)\b', _m.group(0)),
             '%s: a CSS comment spells a script or style tag - '
             'a block scanner will slice the file there' % _name)
    for _line in _text.split('\n'):
        _l = _line.lstrip()
        if _l.startswith('//'):
            want('</script' not in _l,
                 '%s: a JS comment spells a closing script tag - '
                 'that one ends the block for the BROWSER too' % _name)

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


# ===========================================================================
# 3. test_sticky_sweep.py - SECTION 4b, the scope guard, FOURTH occurrence
# ===========================================================================
# Section 5 asserts the sticky sweep changed no MARKUP, by comparing each of
# its six pages with its .bak_sticky snapshot. True, and with an expiry date
# built in: it holds only until a later round legitimately edits one of those
# pages. This round edits fsr.html - the JS that builds the drill-down table
# gains class="ia-desc", and that helper strips <style> and HTML comments but
# not scripts, so it counts.
#
# The mechanism for this already exists. The comment-tint round hit the same
# wall on comments_report.html and moved the comparison to TWO SNAPSHOTS -
# .bak_cmttint vs .bak_sticky - which is true for good rather than decaying.
# It left a LATER map for exactly this. So this is one entry, not a redesign:
#
#     LATER = {'comments_report.html': '.bak_cmttint',
#              'fsr.html': '.bak_iapal'}
#
# .bak_iapal is fsr.html as THIS round found it, and the check passed against
# the live file immediately before, so the two snapshots agree today and will
# go on agreeing.
SW = os.path.join(ROOT, 'test_sticky_sweep.py')
S_ORIG = S_CRLF = sw = None
S_DONE = True
if not os.path.exists(SW):
    print('  test_sticky_sweep.py not found - skipping its 4b')
else:
    S_ORIG, S_CRLF, sw = load(SW)
    S_DONE = "'fsr.html': '.bak_iapal'" in sw
    if S_DONE:
        print('  test_sticky_sweep.py already patched')
    elif "LATER = {'comments_report.html': '.bak_cmttint'}" not in sw:
        want(False, 'test_sticky_sweep.py has no LATER map to extend - '
                    'the comment-tint round should have left one')
    else:
        sw = sub1(sw, "    LATER = {'comments_report.html': '.bak_cmttint'}",
                  "    # FOURTH page-owner entry, 2 Sep. The Issues Analysis\n"
                  "    # palette round edits fsr.html's drill-down script, so\n"
                  "    # its historical claim moves to two snapshots too.\n"
                  "    LATER = {'comments_report.html': '.bak_cmttint',\n"
                  "             'fsr.html': '.bak_iapal'}",
                  'sticky sweep: fsr.html joins the LATER map')
        want("'fsr.html': '.bak_iapal'" in sw,
             'the LATER map did not gain fsr.html')


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-14s %d -> %d bytes' % (os.path.basename(p), len(orig), len(out)))
    if CHECK:
        return
    bak = p + '.bak_iapal'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(BASE, B_ORIG, B_CRLF, b, B_DONE)
save(FSR, F_ORIG, F_CRLF, f, F_DONE)
if sw is not None:
    save(SW, S_ORIG, S_CRLF, sw, S_DONE)
if CHECK:
    print('\n  --check: nothing written.')
else:
    print('\n  done.')
