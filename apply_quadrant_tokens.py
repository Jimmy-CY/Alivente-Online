# -*- coding: utf-8 -*-
"""apply_quadrant_tokens.py - Section C, round C4: the Expenses vs Rent
analysis takes base's meaning colours.

    python apply_quadrant_tokens.py --check     dry run, nothing written
    python apply_quadrant_tokens.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 22 Sep (claude/section_c_decision_sheet.md item 3, and the three
answers after the C4 survey):

  - THE FOUR QUADRANTS take base's soft tints at full strength, in the
    order the quadrants already mean: Watch is bad, Costs high / rent
    rising is warn, Rent stalled is info, Healthy is good. They were four
    hand-picked pastels painted at 32% opacity - a scale nothing else in
    the system used, and so faint that on a phone the bands barely read.
  - THE CORNER LABELS and the 10% threshold line take the same tokens,
    solid. They were rgba() fades of four more literals.
  - THE WHOLE POP-UP, not only the chart: the watch dot, the Watch and OK
    flags, the red row tint, the red/green change column and the note's
    warning icon. One pop-up, one set of reds and greens.
  - A CANVAS CANNOT READ A CLASS, so the chart reads the tokens off :root
    once - the same way fsr.html's Issues Analysis charts have since
    20 Sep - with base's own values as fallbacks.
  - INLINE COLOURS GO with them: the legend's swatches and words, the
    change column and the note icon are classes now.

Not in this round, and deliberately: PALETTE, the twelve colours that
tell one property's trail from another - a category, not a verdict, like
base's tag inks; the teal (#0e7c8b) the pop-up shares with the rest of the
page, including its title icon; its greys; and the amber YTD badge. All
logged for Section D.
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
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_quad'
SUITE = 'test_quadrant_tokens.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
PAGE = os.path.join(T, 'act_expense.html')

TOKENS = """    /* THE ANALYSIS POP-UP READS BASE'S MEANING TOKENS - 22 Sep 2026.
       A canvas element cannot wear a class, so a chart's colours have to be
       VALUES; they do not have to be LITERALS. Read off :root once, as
       fsr.html's Issues Analysis charts have since 20 Sep, with base's own
       values as fallbacks so a renamed token degrades to the right colour
       rather than to nothing - Chart.js draws nothing at all for an empty
       string, and reports no error.

       The four quadrants ARE the four meanings: Watch is bad, costs high
       with rent rising is warn, rent stalled is info, healthy is good. */
    var AN_CS = getComputedStyle(document.documentElement);
    function anTok(name, fallback){
        var v = AN_CS.getPropertyValue('--alv-' + name);
        return (v && v.trim()) || fallback;
    }
    var Q_BAD       = anTok('bad',       '#b3261e'),
        Q_BAD_SOFT  = anTok('bad-soft',  '#fbeae9'),
        Q_WARN      = anTok('warn',      '#9a6a08'),
        Q_WARN_SOFT = anTok('warn-soft', '#fdf3dd'),
        Q_INFO      = anTok('accent-ink', '#0a5e6a'),
        Q_INFO_SOFT = anTok('accent-soft', '#e4f3f5'),
        Q_GOOD      = anTok('good',      '#1e7d4f'),
        Q_GOOD_SOFT = anTok('good-soft', '#e6f4ec');

"""

EDITS = [
    # The tokens, once, straight above the plugin that needs them first.
    ('    var quadrantPlugin = {\n', TOKENS + '    var quadrantPlugin = {\n'),
    # The bands: base's soft tints, at full strength.
    ("            ctx.save(); ctx.globalAlpha=0.32;\n"
     "            ctx.fillStyle='#ffd7d7'; ctx.fillRect(a.left,a.top,x0-a.left,y10-a.top);\n"
     "            ctx.fillStyle='#ffe8cc'; ctx.fillRect(x0,a.top,a.right-x0,y10-a.top);\n"
     "            ctx.fillStyle='#e7f5ff'; ctx.fillRect(a.left,y10,x0-a.left,a.bottom-y10);\n"
     "            ctx.fillStyle='#d3f9d8'; ctx.fillRect(x0,y10,a.right-x0,a.bottom-y10);\n"
     "            ctx.globalAlpha=1;\n",
     "            ctx.save();\n"
     "            ctx.fillStyle=Q_BAD_SOFT;  ctx.fillRect(a.left,a.top,x0-a.left,y10-a.top);\n"
     "            ctx.fillStyle=Q_WARN_SOFT; ctx.fillRect(x0,a.top,a.right-x0,y10-a.top);\n"
     "            ctx.fillStyle=Q_INFO_SOFT; ctx.fillRect(a.left,y10,x0-a.left,a.bottom-y10);\n"
     "            ctx.fillStyle=Q_GOOD_SOFT; ctx.fillRect(x0,y10,a.right-x0,a.bottom-y10);\n"),
    # The 10% line.
    ("            ctx.strokeStyle='#dc3545';\n",
     "            ctx.strokeStyle=Q_BAD;\n"),
    # The corner labels, solid.
    ("            ctx.fillStyle='rgba(201,42,42,.78)'; ctx.textAlign='left'; ctx.fillText('WATCH', a.left+6, a.top+5);\n"
     "            ctx.fillStyle='rgba(232,89,12,.8)'; ctx.textAlign='right'; ctx.fillText('COSTS HIGH · RENT RISING', a.right-6, a.top+5);\n",
     "            ctx.fillStyle=Q_BAD;  ctx.textAlign='left'; ctx.fillText('WATCH', a.left+6, a.top+5);\n"
     "            ctx.fillStyle=Q_WARN; ctx.textAlign='right'; ctx.fillText('COSTS HIGH · RENT RISING', a.right-6, a.top+5);\n"),
    ("            ctx.fillStyle='rgba(25,113,194,.8)'; ctx.textAlign='left'; ctx.fillText('RENT STALLED', a.left+6, a.bottom-5);\n"
     "            ctx.fillStyle='rgba(47,158,68,.85)'; ctx.textAlign='right'; ctx.fillText('HEALTHY', a.right-6, a.bottom-5);\n",
     "            ctx.fillStyle=Q_INFO; ctx.textAlign='left'; ctx.fillText('RENT STALLED', a.left+6, a.bottom-5);\n"
     "            ctx.fillStyle=Q_GOOD; ctx.textAlign='right'; ctx.fillText('HEALTHY', a.right-6, a.bottom-5);\n"),
    # The dot for a property in the watch zone.
    ("                pointBackgroundColor: last.danger ? '#dc3545' : col,\n",
     "                pointBackgroundColor: last.danger ? Q_BAD : col,\n"),
    # The change column: a class, not an inline colour.
    ("            var chg = (r.x==null) ? '<span class=\"an-src\">—</span>'\n"
     "                : '<span style=\"color:'+(r.x<0?'#dc3545':'#1f7a37')+';\">'+pctTxt(r.x)+'</span>';\n",
     "            var chg = (r.x==null) ? '<span class=\"an-src\">—</span>'\n"
     "                : '<span class=\"an-chg ' + (r.x<0?'is-bad':'is-good') + '\">'\n"
     "                  + pctTxt(r.x) + '</span>';\n"),
    # The note's warning icon.
    ("            ? ('<i class=\"fas fa-exclamation-triangle\" style=\"color:#dc3545;\"></i> '+flagged+' propert'+(flagged>1?'ies':'y')+' in the watch zone.')\n",
     "            ? ('<i class=\"fas fa-exclamation-triangle an-warn-icon\"></i> '+flagged+' propert'+(flagged>1?'ies':'y')+' in the watch zone.')\n"),
    # The table's reds and greens.
    (".an-table tr.danger td { background:#fdecec; }\n",
     ".an-table tr.danger td { background:var(--alv-bad-soft); }\n"),
    (".an-flag.warn { background:#fdecec; color:#c0322f; }\n"
     ".an-flag.ok { background:#e8f6ec; color:#1f7a37; }\n",
     ".an-flag.warn { background:var(--alv-bad-soft); color:var(--alv-bad); }\n"
     ".an-flag.ok { background:var(--alv-good-soft); color:var(--alv-good); }\n"
     ".an-chg.is-bad { color:var(--alv-bad); }\n"
     ".an-chg.is-good { color:var(--alv-good); }\n"
     ".an-warn-icon { color:var(--alv-bad); }\n"),
    # The legend: the same four meanings, as classes.
    (".an-dot { width:12px; height:12px; border-radius:3px; margin-top:2px; flex-shrink:0; }\n",
     ".an-dot { width:12px; height:12px; border-radius:3px; margin-top:2px; flex-shrink:0; }\n"
     "/* The key says what the bands say, so it takes the same four tokens. */\n"
     ".an-dot.is-bad  { background:var(--alv-bad-soft); }\n"
     ".an-dot.is-warn { background:var(--alv-warn-soft); }\n"
     ".an-dot.is-info { background:var(--alv-accent-soft); }\n"
     ".an-dot.is-good { background:var(--alv-good-soft); }\n"
     ".an-quad-key b.is-bad  { color:var(--alv-bad); }\n"
     ".an-quad-key b.is-warn { color:var(--alv-warn); }\n"
     ".an-quad-key b.is-info { color:var(--alv-accent-ink); }\n"
     ".an-quad-key b.is-good { color:var(--alv-good); }\n"),
    ('            <div><span class="an-dot" style="background:#ffd7d7"></span><b style="color:#c92a2a">Watch</b>',
     '            <div><span class="an-dot is-bad"></span><b class="is-bad">Watch</b>'),
    ('            <div><span class="an-dot" style="background:#ffe8cc"></span><b style="color:#e8590c">Costs high, rent rising</b>',
     '            <div><span class="an-dot is-warn"></span><b class="is-warn">Costs high, rent rising</b>'),
    ('            <div><span class="an-dot" style="background:#e7f5ff"></span><b style="color:#1971c2">Rent stalled</b>',
     '            <div><span class="an-dot is-info"></span><b class="is-info">Rent stalled</b>'),
    ('            <div><span class="an-dot" style="background:#d3f9d8"></span><b style="color:#2f9e44">Healthy</b>',
     '            <div><span class="an-dot is-good"></span><b class="is-good">Healthy</b>'),
]

GONE = ['#ffd7d7', '#ffe8cc', '#e7f5ff', '#d3f9d8', '#c92a2a', '#e8590c',
        '#1971c2', '#2f9e44', '#fdecec', '#c0322f', '#e8f6ec', '#1f7a37',
        'rgba(201,42,42,.78)', 'rgba(232,89,12,.8)', 'rgba(25,113,194,.8)',
        'rgba(47,158,68,.85)']

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


if not os.path.isfile(PAGE):
    problems.append('%s not found' % PAGE)
else:
    src = read(PAGE)
    cur, n = src, 0
    for old, new in EDITS:
        if new in cur:
            continue
        if cur.count(old) != 1:
            problems.append('act_expense.html: anchor found %d time(s): %r'
                            % (cur.count(old), old.strip()[:60]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        planned[PAGE] = (src, cur)
        report.append('%-44s %d edit(s)' % ('act_expense.html', n))
    else:
        report.append('%-44s already done' % 'act_expense.html')

    if PAGE in planned:
        t = planned[PAGE][1]
        # The analysis pop-up - its style block and its markup - keeps none
        # of the literals this round replaced.
        lo = t.find('.analysis-dialog {')
        hi = t.find('</script>', t.find('function updateChrome'))
        zone = t[lo:hi] if lo > 0 and hi > lo else t
        # Two lines in that stretch are NOT this round's, and saying so
        # here is cheaper than a checker that quietly ignores them:
        #   - PALETTE is a CATEGORICAL set, one colour per property, the
        #     same kind of thing as base's tag inks. A property is not a
        #     verdict, so it takes no meaning token.
        #   - the pop-up's title icon is the page's teal, which this round
        #     is not about. Both are logged for Section D.
        zone = '\n'.join(l for l in zone.split('\n')
                         if 'var PALETTE = [' not in l
                         and 'fa-chart-line' not in l)
        for lit in GONE:
            if lit in zone:
                problems.append('act_expense.html: %s survives in the '
                                'analysis pop-up' % lit)
        if '#dc3545' in zone:
            problems.append('act_expense.html: #dc3545 survives in the '
                            'analysis pop-up')
        if zone.count('style="color:') or zone.count('style="background:'):
            problems.append('act_expense.html: an inline colour survives in '
                            'the analysis pop-up')
        if t.count('var AN_CS = getComputedStyle') != 1:
            problems.append('act_expense.html: the token reader is not there '
                            'exactly once')
        # The page still parses as balanced Django, and its CSS balances.
        css = re.sub(r'/\*.*?\*/', '', '\n'.join(
            re.findall(r'<style[^>]*>(.*?)</style>', t, re.S)), flags=re.S)
        if css.count('{') != css.count('}'):
            problems.append('act_expense.html: the CSS braces do not balance')
        if t.count('{%') != src.count('{%'):
            problems.append('act_expense.html: a Django tag moved')

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-44s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_chip',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_chip) - '
                        'apply_filter_chip.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_chip',\n]", "    '.bak_chip',\n    '%s',\n]" % SUFFIX,
            1))
        report.append('%-44s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section C round C4: the Expenses vs Rent analysis takes base's
    # meaning tokens - the quadrants, the labels, the table and the key,
    'test_quadrant_tokens.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-44s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-44s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

print('\n' + '=' * 78)
print('SECTION C, ROUND C4 - THE ANALYSIS COLOURS - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
