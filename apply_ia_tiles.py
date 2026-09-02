"""apply_ia_tiles.py - the Issues Analysis modal joins the components too.

    python apply_ia_tiles.py --check     dry run, writes nothing
    python apply_ia_tiles.py

Run from the repo root. Round C2 of the Issues module, after C1 (the palette).

THE PRIMITIVE WAS BUILT FOR THIS MODAL AND NEVER APPLIED TO IT.

base's .alv-stat comment names the four screens that made it necessary, and
.ia-kpi is one of them by name. --alv-stats-cols is a DEFAULTED custom
property because of "the five in the Issues Analysis strip" - the five tiles
this round is finally migrating. Same for .alv-age-pill, which Outstanding
Invoices already drives from a days-to-class function of exactly the shape
ageChip has always had.

WHAT THIS ROUND DOES
  * .ia-kpis / .ia-kpi / .v / .l  ->  .alv-stats / .alv-stat /
    .alv-stat-value / .alv-stat-label. Two of the three verdict classes go
    onto base's .alv-stat-attn and .alv-stat-good; the third is the one
    below.
  * .ia-badge.open / .res  ->  .alv-pill-attn / .alv-pill-good. A fourth
    spelling of the status pill, after .status-badge (removed 2 Sep), the
    template chain and the JS map.
  * .ia-age  ->  .alv-age-pill, with the step class coming from AGE_BANDS.
    The inline style="color:..." goes with it.
  * A STATIC VERDICT STOPS PRETENDING TO BE ONE. "Oldest open" carried
    .v.crit in the MARKUP - the script only ever wrote textContent - so it
    read 12d in red exactly as loudly as it read 300d. It takes the ageing
    scale now, from the same AGE_BANDS the chart bars and the drill chips
    read. That closes section 1.C on the running list.

base GAINS ONE THING: .alv-stat-age, the application class that puts --age
on a figure, the way .alv-age-pill and .alv-age-dot put it on a chip and a
dot.

IT ALMOST GAINED A SECOND, AND THE BROWSER SAID NO. A draft of this round
shipped .alv-stats-sm, a compact density for the strip, on the argument that
"Median to resolve" at .78rem uppercase does not fit a 180px tile. Measured,
that is false:

    label text widths   93  76  70  137  93 px
    label box widths   142 142 142  142 142 px
    lines per label      1   1   1    1   1

Every label fits at base's full size. The variant's only real effect was 23px
of strip height, 83px against 60px, in a dialogue that has the room - and
rendered side by side the full size reads better, because the compact label
lands at 9.9px. 23px is not a reason to add a class to a shared stylesheet,
which is the same restraint base applied when it withheld the variant in the
first place. The suite asserts base did NOT gain one, so a later round has to
argue for it rather than inherit it.

ON A PHONE, base's rule wins: two tiles across, not five. base says "Four
figures across a phone is four figures nobody can read"; the modal overrode
that to keep five across at 14px figures and 8px labels, which is five
numbers you squint at rather than one glance. The page-local override goes.

NOT THIS ROUND: .ia-tab (a segmented control by another name, which goes
with the Budget/Actuals .btn-group in a round of its own), the .ia-drill
overlay and its table.ia-tbl, and the page-local @media that still prints.

HOUSE RULES: idempotent, .bak_iatile backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
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


def drop_rule(text, selector, what):
    """Delete the CSS rule whose selector is EXACTLY `selector`, matched at a
       line start so `.ia-kpi` never matches inside `.ia-kpis`."""
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*\{')
    hits = list(pat.finditer(text))
    if len(hits) != 1:
        sys.exit('! %s: %r matched %d rule openings, expected 1'
                 % (what, selector, len(hits)))
    m = hits[0]
    i, depth, k = m.start(), 1, m.end()
    while depth and k < len(text):
        if text[k] == '{':
            depth += 1
        elif text[k] == '}':
            depth -= 1
        k += 1
    if depth:
        sys.exit('! %s: unbalanced braces after %r' % (what, selector))
    while k < len(text) and text[k] in '\r\n':
        k += 1
    return text[:i] + text[k:]


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


# ===========================================================================
# 1. base.html - ONE addition, and one that was measured and rejected
# ===========================================================================
B_ORIG, B_CRLF, b = load(BASE)
B_DONE = '.alv-stat-age' in b
if B_DONE:
    print('  base.html already patched')
else:
    b = sub1(b, """      .alv-stat-bad  .alv-stat-value { color: var(--alv-bad); }
""", """      .alv-stat-bad  .alv-stat-value { color: var(--alv-bad); }

      /* AND FROM THE AGEING SCALE, for a figure that is a DURATION rather
         than a verdict. .alv-age-0..4 set --age; this is the application
         class that puts it on a figure, the same way .alv-age-pill and
         .alv-age-dot put it on a chip and a dot.

         The Issues Analysis strip asked. Its "Oldest open" tile carried a
         verdict class in the MARKUP - the script only ever wrote the number
         - so it read 12d in red exactly as loudly as it read 300d. A
         verdict that cannot change is decoration.

         NO COMPACT DENSITY CAME WITH IT, though a draft of that round tried.
         The argument was that a .78rem uppercase label does not fit a 180px
         tile; measured, the longest of the five is 137px in a 142px box and
         all five sit on one line. The variant saved 23px of strip height and
         cost a 9.9px label. The restraint above this block stands. */
      .alv-stat-age .alv-stat-value { color: var(--age, var(--alv-ink-strong)); }
""", 'base: .alv-stat-age')

    _bnc = re.sub(r'/\*.*?\*/', '', b, flags=re.S)
    want('.alv-stat-age .alv-stat-value' in _bnc, 'base: .alv-stat-age missing')
    want('alv-stats-sm' not in _bnc,
         'base: a density variant appeared - it was measured and rejected')

# ===========================================================================
# 2. fsr.html
# ===========================================================================
F_ORIG, F_CRLF, f = load(FSR)
F_DONE = 'class="alv-stats"' in f
if F_DONE:
    print('  fsr.html already patched')
else:
    if 'AGE_BANDS' not in f:
        sys.exit('! fsr.html has no AGE_BANDS - run apply_ia_palette.py first')

    # ------------------------------------------------------- 2a. the markup
    f = sub1(f, """        <div class="ia-kpis">
          <div class="ia-kpi"><div class="v" id="iaKTotal">&ndash;</div><div class="l">Total issues</div></div>
          <div class="ia-kpi"><div class="v open" id="iaKOpen">&ndash;</div><div class="l">Still open</div></div>
          <div class="ia-kpi"><div class="v done" id="iaKRes">&ndash;</div><div class="l">Resolved</div></div>
          <div class="ia-kpi"><div class="v" id="iaKMed">&ndash;</div><div class="l">Median to resolve</div></div>
          <div class="ia-kpi"><div class="v crit" id="iaKOld">&ndash;</div><div class="l">Oldest open</div></div>
        </div>""",
             """        <div class="alv-stats">
          <div class="alv-stat"><div class="alv-stat-value" id="iaKTotal">&ndash;</div><div class="alv-stat-label">Total issues</div></div>
          <div class="alv-stat alv-stat-attn"><div class="alv-stat-value" id="iaKOpen">&ndash;</div><div class="alv-stat-label">Still open</div></div>
          <div class="alv-stat alv-stat-good"><div class="alv-stat-value" id="iaKRes">&ndash;</div><div class="alv-stat-label">Resolved</div></div>
          <div class="alv-stat"><div class="alv-stat-value" id="iaKMed">&ndash;</div><div class="alv-stat-label">Median to resolve</div></div>
          <!-- The one tile whose class the script sets: a duration takes the
               ageing scale, not a fixed red. See setKpis() below. -->
          <div class="alv-stat alv-stat-age" id="iaKOldTile"><div class="alv-stat-value" id="iaKOld">&ndash;</div><div class="alv-stat-label">Oldest open</div></div>
        </div>""", 'fsr: the KPI strip')

    # ---------------------------------------------------------- 2b. the CSS
    S_OPEN = "  #issuesAnalysisModal .ia-body{"
    if f.count(S_OPEN) != 1:
        sys.exit('! could not find the modal style block exactly once')
    i = f.index(S_OPEN)
    j = f.index('</style>', i)
    css = f[i:j]

    # SPLIT AT THE MEDIA QUERY FIRST. .ia-kpis and .ia-kpi are each defined
    # twice - once for the desktop strip and once inside the phone block -
    # so a whole-block drop_rule matches two openings and stops the round on
    # its own guard. Same shape as the print block in the Comments Report
    # patcher; the fix there was ordering, the fix here is scoping.
    _MQ = '  @media (max-width:768px){'
    if css.count(_MQ) != 1:
        sys.exit('! the modal style block has no single phone section')
    _k = css.index(_MQ)
    main, phone = css[:_k], css[_k:]

    for _sel in ('#issuesAnalysisModal .ia-kpis',
                 '#issuesAnalysisModal .ia-kpi',
                 '#issuesAnalysisModal .ia-kpi .v',
                 '#issuesAnalysisModal .ia-kpi .l',
                 '.ia-badge',
                 '.ia-age'):
        main = drop_rule(main, _sel, 'drop %s' % _sel)
    css = main + phone

    # TWO MORE RULES SHARING ONE LINE. drop_rule('.ia-badge') took the base
    # rule and left `.ia-badge.open{...} .ia-badge.res{...}` behind, because
    # that line starts with a different selector. The patcher's own dead-class
    # scan caught it. Named in full, like the verdict trio below.
    css = sub1(css, "  .ia-badge.open{background:#fff3d6;color:#8a6100;}"
                    " .ia-badge.res{background:#d8f5da;color:#0a6b1e;}\n",
               "", 'drop the two badge tints')

    # The verdict line is three rules written on ONE line, so drop_rule's
    # brace walk would take only the first. Named in full instead.
    css = sub1(css, "  #issuesAnalysisModal .ia-kpi .v.open{color:var(--alv-warn);}"
                    " #issuesAnalysisModal .ia-kpi .v.done{color:var(--alv-good);}"
                    " #issuesAnalysisModal .ia-kpi .v.crit{color:var(--alv-bad);}\n",
               "", 'drop the three verdict rules')

    css = sub1(css, "  #issuesAnalysisModal .ia-tabs{",
               """  /* THE STRIP IS base's NOW. Deleted from here: .ia-kpis, .ia-kpi, its
     .v and .l, and the three verdict rules. base's own .alv-stat comment
     names .ia-kpi as one of the four screens that made the primitive
     necessary, and --alv-stats-cols is a DEFAULTED custom property
     because of "the five in the Issues Analysis strip" - this strip. It
     was built for this modal and never applied to it.

     One rule stays, and it is the one base cannot know: how many across. */
  #issuesAnalysisModal .alv-stats { --alv-stats-cols: 5; }

  #issuesAnalysisModal .ia-tabs{""", 'fsr: the column count')

    # The phone block kept five across. base's rule wins - see the header.
    css = sub1(css, "    #issuesAnalysisModal .ia-kpis{grid-template-columns:repeat(5,1fr);gap:5px;}\n"
                    "    #issuesAnalysisModal .ia-kpi{padding:8px 5px;}"
                    " #issuesAnalysisModal .ia-kpi .v{font-size:14px;}"
                    " #issuesAnalysisModal .ia-kpi .l{font-size:8px;}\n",
               "    /* FIVE ACROSS ON A PHONE WAS HERE, at 14px figures and 8px\n"
               "       labels. base drops .alv-stats to two columns and says why:\n"
               "       \"Four figures across a phone is four figures nobody can\n"
               "       read.\" Five at 8px is not one glance, it is five numbers\n"
               "       you squint at. base's rule wins, and its own phone sizes\n"
               "       come with it - two across means there is room for them. */\n",
               'fsr: the phone strip defers to base')

    f = f[:i] + css + f[j:]

    # ----------------------------------------------------------- 2c. the JS
    # ONE LOOKUP, THREE CONSUMERS. The bands already fed the chart and the
    # drill chips; the tile makes three, so the band lookup gets a name.
    f = sub1(f, """  function ageChip(a){
    var c=AGE_BANDS[0].c;
    for(var i=0;i<AGE_BANDS.length;i++){
      if(a>=AGE_BANDS[i].min&&a<=AGE_BANDS[i].max){c=AGE_BANDS[i].c;break;}
    }
    return '<span class="ia-age" style="color:'+c+'">'+a+'d</span>';}""",
             """  // ONE LOOKUP, THREE CONSUMERS: the chart bars, the drill-list chips and
  // the "Oldest open" tile. Each band now carries its severity CLASS as
  // well as its colour, so a chip and the bar beside it cannot part
  // company - the class and the value come out of the same row.
  function ageBand(a){
    for(var i=0;i<AGE_BANDS.length;i++){
      if(a>=AGE_BANDS[i].min&&a<=AGE_BANDS[i].max) return AGE_BANDS[i];
    }
    return AGE_BANDS[0];
  }
  function ageChip(a){
    return '<span class="alv-age-pill '+ageBand(a).cls+'">'+a+'d</span>';}""",
             'fsr: ageBand and the age pill')

    f = sub1(f, """  var AGE_BANDS=[{label:'0–30 days',min:0,max:30,c:GOOD},
    {label:'31–90 days',min:31,max:90,c:WARN},
    {label:'91–180 days',min:91,max:180,c:SERIOUS},
    {label:'180+ days',min:181,max:1e9,c:CRIT}];""",
             """  // `cls` is base's severity step. --alv-age-1 is absent on purpose: this
  // modal's first band is the ABSENCE of ageing, which base's scale spells
  // .alv-age-0 and colours with the good token.
  var AGE_BANDS=[{label:'0–30 days',min:0,max:30,c:GOOD,cls:'alv-age-0'},
    {label:'31–90 days',min:31,max:90,c:WARN,cls:'alv-age-2'},
    {label:'91–180 days',min:91,max:180,c:SERIOUS,cls:'alv-age-3'},
    {label:'180+ days',min:181,max:1e9,c:CRIT,cls:'alv-age-4'}];""",
             'fsr: the bands carry their step class')

    f = sub1(f, """    var ages=openW.filter(function(i){return i.age_days!=null;}).map(function(i){return i.age_days;});
    $('iaKOld').textContent=ages.length?Math.max.apply(null,ages)+'d':'–';""",
             """    var ages=openW.filter(function(i){return i.age_days!=null;}).map(function(i){return i.age_days;});
    var oldest=ages.length?Math.max.apply(null,ages):null;
    $('iaKOld').textContent=oldest!=null?oldest+'d':'–';
    // A DURATION IS NOT A VERDICT. This tile carried a fixed red in the
    // markup and the script only ever wrote the number, so 12d shouted
    // exactly as loudly as 300d. The step comes from the same bands the
    // chart and the drill chips read; with nothing open there is no band
    // and the figure stays plain.
    $('iaKOldTile').className='alv-stat alv-stat-age'+
      (oldest!=null?' '+ageBand(oldest).cls:'');""",
             'fsr: Oldest open takes the ageing scale')

    f = sub1(f, "'<span class=\"ia-badge res\">Resolved</span>'",
             "'<span class=\"alv-pill alv-pill-good\">Resolved</span>'",
             'fsr: the resolved badge')
    f = sub1(f, "'<span class=\"ia-badge open\">'+esc(i.status)+'</span>'",
             "'<span class=\"alv-pill alv-pill-attn\">'+esc(i.status)+'</span>'",
             'fsr: the open badge')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
_nc = re.sub(r'<!--.*?-->', '', _nc, flags=re.S)
_nc = '\n'.join('' if l.lstrip().startswith('//') else l
                for l in _nc.split('\n'))

for dead in ('ia-kpis', 'ia-kpi', 'ia-badge', 'ia-age'):
    want(not re.search(r'(?<![\w-])%s(?![\w-])' % dead, _nc),
         'fsr: %s survives outside a comment' % dead)
for lit in ('#fff3d6', '#8a6100', '#d8f5da', '#0a6b1e'):
    want(lit not in _nc, 'fsr: the badge literal %s survives' % lit)

want('class="alv-stats"' in _nc, 'fsr: the strip did not migrate')
want('alv-stats-sm' not in _nc,
     'fsr: the rejected density variant is being used')
want(_nc.count('class="alv-stat-value"') == 5
     and _nc.count('class="alv-stat-label"') == 5,
     'fsr: expected five tiles with a value and a label')
want('--alv-stats-cols: 5' in f, 'fsr: the column count was lost')
want('alv-stat alv-stat-attn' in _nc and 'alv-stat alv-stat-good' in _nc,
     'fsr: the two static verdicts did not migrate')
want('alv-stat-bad' not in _nc,
     'fsr: Oldest open kept a fixed red instead of the ageing scale')
want("$('iaKOldTile').className" in _nc and 'ageBand(oldest).cls' in _nc,
     'fsr: the Oldest open tile is not driven from the bands')
want(_nc.count('alv-age-pill') == 1, 'fsr: the age chip did not migrate')
want('style="color:' not in _nc,
     'fsr: an inline colour survives in the modal script')
want(all(("cls:'%s'" % c) in _nc
         for c in ('alv-age-0', 'alv-age-2', 'alv-age-3', 'alv-age-4')),
     'fsr: the bands do not all carry a step class')
want("cls:'alv-age-1'" not in _nc,
     'fsr: alv-age-1 appeared - this modal has four bands, not five')
want('alv-pill alv-pill-good' in _nc and 'alv-pill alv-pill-attn' in _nc,
     'fsr: the drill badges did not migrate')

# Out of scope, and must be untouched.
want('.ia-tab{border:none;background:transparent' in f,
     'fsr: .ia-tab was touched - the segmented control is its own round')
want('table.ia-tbl{' in f, 'fsr: table.ia-tbl was touched - that is C3')
want('@media (max-width:768px){' in f,
     'fsr: the page-local media block was requalified - not this round')

# The C1 round's work must survive.
want('iaTok(' in _nc and 'AGE_BANDS' in _nc, 'fsr: C1 was undone')

# PROSE THAT CONTAINS MARKUP IS MARKUP - the lesson from C1, kept.
for _name, _text in (('fsr.html', f), ('base.html', b)):
    for _m in re.finditer(r'/\*.*?\*/', _text, re.S):
        want(not re.search(r'</?(?:script|style)\b', _m.group(0)),
             '%s: a CSS comment spells a script or style tag' % _name)
    for _line in _text.split('\n'):
        if _line.lstrip().startswith('//'):
            want('</script' not in _line,
                 '%s: a JS comment spells a closing script tag' % _name)

for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
    want(blk.count('{') == blk.count('}'), 'fsr: unbalanced braces')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


# ===========================================================================
# 3. test_ia_palette.py - SECTION 4b, the SCOPE GUARD, fifth occurrence
# ===========================================================================
# C1's section 5 asserted "what this round deliberately left alone", naming
# .ia-kpi and .ia-badge and saying in the message that they were C2's. C2 is
# now here, so both fail - which is the guard doing precisely its job rather
# than a defect.
#
# The fix is the sticky sweep's, because it is the same shape. C1's claim is
# HISTORICAL: it says what C1 did not touch. The right thing to measure it
# against is fsr.html AS C1 LEFT IT - which is .bak_iatile, this round's own
# backup - not the live file, which C2 owns now. Measured on the snapshot the
# claim is true for good instead of expiring the moment the next round lands.
#
# The forward half is added too: the components must now be on base's classes.
# A scope guard that only ever loosens would eventually assert nothing.
TP = os.path.join(ROOT, 'test_ia_palette.py')
P_ORIG = P_CRLF = tp = None
P_DONE = True
if not os.path.exists(TP):
    print('  test_ia_palette.py not found - skipping its 4b')
else:
    P_ORIG, P_CRLF, tp = load(TP)
    P_DONE = 'AS_C1_LEFT_IT' in tp
    if P_DONE:
        print('  test_ia_palette.py already patched')
    else:
        tp = sub1(tp, """check('.ia-kpi is untouched - the tiles are C2',
      '.ia-kpi{background:' in FC and '.ia-kpi .v{font-size:18px' in FC)
check('.ia-badge keeps its own tints - it becomes .alv-pill in C2',
      '.ia-badge.open{background:#fff3d6' in FC
      and '.ia-badge.res{background:#d8f5da' in FC)""",
                  """# MOVED 2 Sep by C2, and it is the SCOPE GUARD kind of 4b - the fourth
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
          and '.ia-kpi{background:' not in FC)""",
                  'C1 scope guard moves to the snapshot')
        want('AS_C1_LEFT_IT' in tp, 'the C1 scope guard did not move')


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-14s %d -> %d bytes' % (os.path.basename(p), len(orig), len(out)))
    if CHECK:
        return
    bak = p + '.bak_iatile'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(BASE, B_ORIG, B_CRLF, b, B_DONE)
save(FSR, F_ORIG, F_CRLF, f, F_DONE)
if tp is not None:
    save(TP, P_ORIG, P_CRLF, tp, P_DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
