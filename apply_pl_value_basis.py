"""apply_pl_value_basis - the second denominator must not be silent either.

    python apply_pl_value_basis.py --check
    python apply_pl_value_basis.py

Run apply_pl_indicators.py first; this anchors on what that leaves behind.

WHY
---
Round twelve gated the indicator denominators on contribution and put a line
under the chips naming what was left out. But % Value Increase has a SECOND
gate that the note never mentioned: a property with no valuation dated the
selected year or earlier drops out of both sides of that ratio, so the chip can
cover fewer properties than the other four while the note still says "based on
8 of 10".

That is the same failure the note exists to prevent - a denominator you cannot
see - so it gets the same treatment. `ind_value_count` records how many
properties Value Increase actually covers, and the note gains a sentence
whenever that is fewer than the number contributing.

It matters most on old years. `property_value_as_of` looks for the latest
valuation effective on or before 31 Dec of the year in question; a property
whose valuation history begins in 2021 has none for 2019, so 2019's Value
Increase legitimately covers fewer properties. Without the count, that reads as
a portfolio-wide figure when it is not.

Idempotent, backs up to .bak_pl_value_basis, compiles before writing.
"""

import io
import os
import py_compile
import shutil
import sys
import tempfile

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html')

for p in (FINANCE, TPL):
    if not os.path.exists(p):
        sys.exit('! %s not found - run this from the project root'
                 % os.path.relpath(p, ROOT))


def sniff(path):
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        return raw[3:].decode('utf-8'), 'utf-8-sig', (
            '\r\n' if b'\r\n' in raw else '\n')
    return raw.decode('utf-8'), 'utf-8', ('\r\n' if b'\r\n' in raw else '\n')


CHANGES = []


def sub(label, text, old, new, path, marker):
    """`marker` is unique to the replacement - see apply_pl_indicators.py for
    why testing on `new` alone is not enough when an edit inserts into its own
    anchor."""
    if marker not in new or marker in old:
        sys.exit('! %s: bad marker.' % label)
    if marker in text:
        CHANGES.append(('skip', label))
        return text
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times in %s (expected 1).\n'
                 '  Run apply_pl_indicators.py first.'
                 % (label, n, os.path.relpath(path, ROOT)))
    CHANGES.append(('apply', label))
    return text.replace(old, new, 1)


fin, fin_enc, fin_nl = sniff(FINANCE)
fin = fin.replace('\r\n', '\n')
tpl, tpl_enc, tpl_nl = sniff(TPL)
tpl = tpl.replace('\r\n', '\n')

if 'ind_value_purchase' not in fin:
    sys.exit('! the indicator gate is not in finance.py - run '
             'apply_pl_indicators.py first.')

COUNT_OLD = """    ind_value_total = 0
    ind_value_purchase = 0
    for prop in ind_props:"""

COUNT_NEW = """    ind_value_total = 0
    ind_value_purchase = 0
    # Counted, because this is a SECOND denominator and it must not be silent
    # either. A property with no valuation dated this year or earlier leaves
    # BOTH sides of Value Increase, so that one chip can cover fewer properties
    # than the other four - and the note under the chips has to say so. Older
    # years are where this bites: valuation history has to start somewhere.
    ind_value_count = 0
    for prop in ind_props:"""

fin = sub('finance.py: count what Value Increase covers', fin,
          COUNT_OLD, COUNT_NEW, FINANCE, 'ind_value_count = 0')

INC_OLD = """            ind_value_total += _as_of
            ind_value_purchase += _purchase
"""
INC_NEW = """            ind_value_total += _as_of
            ind_value_purchase += _purchase
            ind_value_count += 1
"""
fin = sub('finance.py: increment it', fin, INC_OLD, INC_NEW, FINANCE,
          'ind_value_count += 1')

CTX_OLD = """        'ind_value_purchase': ind_value_purchase,
"""
CTX_NEW = """        'ind_value_purchase': ind_value_purchase,
        'ind_value_count': ind_value_count,
"""
fin = sub('finance.py: pass the count to the template', fin,
          CTX_OLD, CTX_NEW, FINANCE, "'ind_value_count': ind_value_count,")

NOTE_OLD = """        {% if ind_skipped %}
        {# One line, deliberately: a Django comment cannot span lines - it renders as text. #}
        <div class="roi-basis" id="roiBasis">
            Based on <strong>{{ ind_count }} of {{ ind_total_count }}</strong> selected properties.
            Left out of {{ selected_year }} because nothing was earned or spent on
            {% if ind_skipped|length == 1 %}it{% else %}them{% endif %}:
            <span class="roi-basis-names">{% for name in ind_skipped %}{{ name }}{% if not forloop.last %}, {% endif %}{% endfor %}</span>.
            Expenses to Revenue is unaffected - it divides this year&rsquo;s money by this year&rsquo;s money.
        </div>
        {% endif %}"""

NOTE_NEW = """        {% if ind_skipped or ind_value_count < ind_count %}
        {# One line, deliberately: a Django comment cannot span lines - it renders as text. #}
        <div class="roi-basis" id="roiBasis">
            {% if ind_skipped %}Based on <strong>{{ ind_count }} of {{ ind_total_count }}</strong> selected properties.
            Left out of {{ selected_year }} because nothing was earned or spent on
            {% if ind_skipped|length == 1 %}it{% else %}them{% endif %}:
            <span class="roi-basis-names">{% for name in ind_skipped %}{{ name }}{% if not forloop.last %}, {% endif %}{% endfor %}</span>.
            Expenses to Revenue is unaffected - it divides this year&rsquo;s money by this year&rsquo;s money.{% endif %}
            {% if ind_value_count < ind_count %}<span class="roi-basis-val">% Value Increase covers <strong>{{ ind_value_count }} of {{ ind_count }}</strong>: the rest have no valuation dated {{ selected_year }} or earlier, so they leave both sides of that ratio rather than half of it.</span>{% endif %}
        </div>
        {% endif %}"""

tpl = sub('finance_pl_act.html: the note reports the valuation gate too', tpl,
          NOTE_OLD, NOTE_NEW, TPL, 'roi-basis-val')

CSS_OLD = ".roi-basis-names { color: #17677a; font-weight: 600; }"
CSS_NEW = """.roi-basis-names { color: #17677a; font-weight: 600; }
.roi-basis-val { display: block; margin-top: 4px; color: #6b5b12; }"""
tpl = sub('finance_pl_act.html: style the second sentence', tpl,
          CSS_OLD, CSS_NEW, TPL, '.roi-basis-val {')

problems = []
if fin.count('ind_value_count') < 3:
    problems.append('the counter is not wired through the view')
if 'ind_value_count < ind_count' not in tpl:
    problems.append('the note does not test the valuation gate')
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

tmp = os.path.join(tempfile.gettempdir(), '_pl_value_basis_check.py')
with io.open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(fin)
try:
    py_compile.compile(tmp, cfile=tmp + 'c', doraise=True)
except py_compile.PyCompileError as exc:
    sys.exit('! finance.py would not compile:\n%s' % exc)
finally:
    for f in (tmp, tmp + 'c'):
        if os.path.exists(f):
            os.remove(f)

print('')
for kind, label in CHANGES:
    print('  %-6s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

for path, text, enc, nl in ((FINANCE, fin, fin_enc, fin_nl),
                            (TPL, tpl, tpl_enc, tpl_nl)):
    bak = path + '.bak_pl_value_basis'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with io.open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl != '\n' else text)
    print('  wrote %s' % os.path.relpath(path, ROOT))

print('')
print('Done. Backups: *.bak_pl_value_basis')
print('Now run:  python test_pl_indicators.py')
