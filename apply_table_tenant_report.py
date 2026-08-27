"""apply_table_tenant_report - the Tenant Details report joins the standard.

    python apply_table_tenant_report.py --check
    python apply_table_tenant_report.py

Second-track work: a detail screen, not a list. There is no table on this
page and base.html owns exactly ONE of its 49 rules, so unlike the three
rounds before it this is not a deletion exercise. The line count barely
moves. What changes is that six status colours stop being raw Bootstrap.

WHAT WAS THERE
--------------
    .badge-success      #28a745 on white     Active tenant
    .badge-secondary    #6c757d on white     not Active
    .renewal-pending    #ffc107 on #212529   amber
    .renewal-declined   #dc3545 on white     red
    .renewal-signed     #28a745 on white     green
    .highlight-red      #dc3545              an expired end date

All six SOLID-filled. The house pills are tinted, so this is a visible
change - and the same one Properties and Tenants already made.

THE RENEWAL DECISION
--------------------
Pending was amber and Declined was red. Red is reserved for overdue rent,
expired leases and failed sends; a tenant declining to renew is an answer,
not a failure. Agreed: PENDING AND DECLINED ARE BOTH AMBER. Pending waits on
the tenant, Declined waits on you to find another one - neither is finished
business, and neither is a fault. Signed is the only settled outcome, and it
is a good one.

THE CARD
--------
`.property-card` is already a quiet #f8f9fa panel with no coloured bar, so
none of the Asset Details archaeology applies. It becomes `.alv-card
.alv-card-lead` - which needs a head and a body wrapper, so this round adds
two divs rather than only swapping classes.

THE PRINT BLOCK, WHICH IS THE INTERESTING PART
----------------------------------------------
This page carries its own `@media print`, and the migration plan says only
TWO templates do. It is a third, and its print block re-colours the renewal
badges BY NAME:

    @media print { .renewal-declined { background-color: #dc3545 !important } }

Rename those classes and that block goes dead silently - the badges would
print grey while the screen showed amber, and nothing would raise. So the
print rules move in the SAME pass, not afterwards.

The `.property-card` print rule is DELETED rather than renamed. It wanted the
card invisible on paper (no border, no background); base.html's print block
wants a grey border and `break-inside: avoid`. Those are a conflict, not a
complement, and the plan says base governs printing. Consequence, stated
rather than discovered: the card now prints with a hairline border.

Idempotent. Backs up to .bak_tablereport.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant_report.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

for p in (PAGE, BASE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

_base = open(BASE, encoding='utf-8-sig').read()
for need, why in (('.alv-card-lead', 'the lead card variant'),
                  ('.alv-card-body', 'the card body wrapper'),
                  ('.alv-pill-attn', 'the amber pill'),
                  ('.alv-pill-neutral', 'the grey pill')):
    if need not in _base:
        sys.exit('! base.html has no %s (%s).\n'
                 '  Apply the card standard before running this.' % (need, why))

raw = open(PAGE, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

# Selectors this round REPLACES with a base.html component. Note the wording:
# base does not "own" these names - it owns .alv-card and .alv-pill, which
# take over their job. Deleting a rule because something replaces it is a
# different claim from deleting one because base already defines it, and
# conflating the two is how a rule nothing replaces gets dropped.
REPLACED = {
    '.property-card', '.property-name',
    '.badge', '.badge-success', '.badge-secondary',
    '.renewal-status-badge',
    '.renewal-pending', '.renewal-declined', '.renewal-signed',
}

# ---------------------------------------------------------------------------
# The exact markup, lifted from the page rather than retyped
# ---------------------------------------------------------------------------
CARD_OPEN_OLD = '''            <div class="property-card">
                <h3 class="property-name">{{ tenant.tenant_name }}</h3>

                <div class="detail-groups">'''

CARD_OPEN_NEW = '''            <div class="alv-card alv-card-lead">
                <div class="alv-card-head">
                    <h3 class="alv-card-title">{{ tenant.tenant_name }}</h3>
                </div>
                <div class="alv-card-body">

                <div class="detail-groups">'''

# The card gains a body wrapper, so its close gains a </div>. Anchored on the
# Active-tenant row above it, which is the last thing in the card - a bare
# run of closing divs occurs several times in this file and would have
# matched the wrong one.
CARD_CLOSE_OLD = '''                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>'''

CARD_CLOSE_NEW = '''                        </div>
                    </div>
                </div>
                </div>
            </div>
        </div>
    </div>
</div>'''

PILL_OLD = '''<span class="badge {% if tenant.tenant_current == 'Yes' %}badge-success{% else %}badge-secondary{% endif %}">'''
PILL_NEW = '''<span class="alv-pill {% if tenant.tenant_current == 'Yes' %}alv-pill-good{% else %}alv-pill-neutral{% endif %}">'''

# Pending and Declined are BOTH amber, agreed. Pending is waiting on the
# tenant; Declined is waiting on you to find another one. Neither is finished
# business, and neither is a fault - which is why Declined comes off red, the
# same argument that took Inactive off it two pages ago. Signed is the only
# settled outcome, and it is a good one.
RENEWAL_OLD = '''<span class="renewal-status-badge
                                {% if tenant.tenant_renewal_status == 'pending' or not tenant.tenant_renewal_status %}renewal-pending
                                {% elif tenant.tenant_renewal_status == 'declined' %}renewal-declined
                                {% elif tenant.tenant_renewal_status == 'new_lease_signed' %}renewal-signed
                                {% endif %}">'''

RENEWAL_NEW = '''<span class="alv-pill
                                {% if tenant.tenant_renewal_status == 'pending' or not tenant.tenant_renewal_status %}alv-pill-attn
                                {% elif tenant.tenant_renewal_status == 'declined' %}alv-pill-attn
                                {% elif tenant.tenant_renewal_status == 'new_lease_signed' %}alv-pill-good
                                {% endif %}">'''


def strip_comments(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).strip()


def rules(block, offset=0):
    i, n, sel_start = 0, len(block), 0
    while i < n:
        if block[i] == '{':
            selector = block[sel_start:i]
            depth, j = 1, i + 1
            while j < n and depth:
                if block[j] == '{':
                    depth += 1
                elif block[j] == '}':
                    depth -= 1
                j += 1
            yield ('at' if strip_comments(selector).startswith('@') else 'rule',
                   selector, sel_start + offset, j + offset, i + offset,
                   j - 1 + offset)
            i = j
            sel_start = i
        else:
            i += 1


def decide(selector):
    sels = [s.strip() for s in strip_comments(selector).split(',') if s.strip()]
    if not sels:
        return 'keep'
    flags = [s in REPLACED for s in sels]
    return 'drop' if all(flags) else ('mixed' if any(flags) else 'keep')


m = re.search(r'(<style[^>]*>)(.*?)(</style>)', text, re.S | re.I)
if not m:
    sys.exit('! no <style> block found in tenant_report.html')
css = m.group(2)

cuts, dropped, mixed_fixed = [], [], []


def scan(block, offset):
    for kind, selector, s0, s1, b0, b1 in rules(block, offset):
        clean = ' '.join(selector.split())
        if kind == 'at':
            scan(css[b0 + 1:b1], b0 + 1)
            continue
        d = decide(selector)
        if d == 'drop':
            start = s0
            mm = re.search(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/\s*$', css[:start])
            if mm and not css[mm.end():start].strip():
                start = mm.start()
            cuts.append((start, s1, ''))
            dropped.append(clean[:70])
        elif d == 'mixed':
            # A selector list mixing replaced names with surviving ones is
            # NOT left alone. `.badge, .renewal-status-badge, .date-box`
            # would keep styling .date-box correctly while carrying two dead
            # names for ever - and a dead name in a live selector is how the
            # next person concludes the class still exists.
            keep = [s.strip() for s in strip_comments(selector).split(',')
                    if s.strip() and s.strip() not in REPLACED]
            # b0, NOT s1. s1 is the end of the whole RULE; b0 is the opening
            # brace. Replacing up to s1 swapped the declarations away too and
            # left a bare `.date-box` dangling with no block - which closed
            # the enclosing @media early and took the mobile sizing with it.
            # The style tags still balanced and the divs still balanced, so
            # every self-check I had written passed. Only counting CSS braces
            # catches this, which is why that check now exists below.
            cuts.append((s0, b0, '\n    ' + ',\n    '.join(keep) + ' '))
            mixed_fixed.append('%s  ->  %s' % (clean[:44], ', '.join(keep)))


scan(css, 0)

if not cuts and 'alv-card-lead' in text:
    print('')
    print('  ALREADY  tenant_report.html is on the standard.')
    sys.exit(0)

new_css = css
for a, b, rep in sorted(cuts, key=lambda x: -x[0]):
    new_css = new_css[:a] + rep + new_css[b:]
new_css = re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', new_css)
text = text[:m.start(2)] + new_css + text[m.end(2):]

# The expired end date, onto the token - rewritten, not deleted. base.html
# does not own .highlight-red.
_red = re.compile(r'(\.highlight-red\s*\{[^}]*color:\s*)#dc3545')
if _red.search(text):
    text = _red.sub(r'\1var(--alv-bad)', text, count=1)
    print('  OK      the expired end date moves onto --alv-bad')
elif re.search(r'\.highlight-red\s*\{[^}]*var\(--alv-bad\)', text):
    print('  ALREADY the expired end date is on --alv-bad')
else:
    sys.exit('! .highlight-red does not carry #dc3545 - stopping.')


def sub(label, old, new, marker):
    global text
    if marker not in new or marker in old:
        sys.exit('! %s: bad marker.' % label)
    if marker in text:
        print('  ALREADY %s' % label)
        return
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times (expected 1).' % (label, n))
    text = text.replace(old, new, 1)
    print('  OK      %s' % label)


print('')
sub('the card becomes the house card, with a head and a body',
    CARD_OPEN_OLD, CARD_OPEN_NEW, 'alv-card alv-card-lead')
sub('.. and its close gains the body wrapper',
    CARD_CLOSE_OLD, CARD_CLOSE_NEW, CARD_CLOSE_NEW)
sub('Active stops being a solid Bootstrap badge', PILL_OLD, PILL_NEW,
    'alv-pill-neutral{% endif %}')
sub('renewal status: pending and declined both amber, signed green',
    RENEWAL_OLD, RENEWAL_NEW, 'alv-pill-good\n')

# ------------------------------------------------------- verify before write
problems = []
if text.count('alv-card-head') != 1 or text.count('alv-card-body') != 1:
    problems.append('the card needs exactly one head and one body')
if text.count('<div') != text.count('</div>'):
    problems.append('div tags no longer balance: %d open, %d close'
                    % (text.count('<div'), text.count('</div>')))
for gone in ('property-card', 'property-name', 'renewal-status-badge',
             'renewal-pending', 'renewal-declined', 'renewal-signed',
             'badge-success', 'badge-secondary'):
    if gone in text:
        problems.append('%s survives somewhere - markup or CSS' % gone)
# THE ONE THIS PAGE EXISTS TO CATCH. Its own @media print re-coloured the
# renewal badges by name. If those rules had been left behind they would have
# styled nothing, silently, and the badges would print grey while the screen
# showed amber.
_print = text[text.find('@media print'):] if '@media print' in text else ''
for dead in ('.renewal-', '.property-card'):
    if dead in _print:
        problems.append('the print block still names %s, which no longer '
                        'exists in the markup' % dead)
if '#dc3545' in text.split('</style>')[0]:
    problems.append('a raw Bootstrap red survived in the style block')
for i, line in enumerate(text.split('\n'), 1):
    if '{#' in line and '#}' not in line:
        problems.append('unclosed {# comment at line %d' % i)
if text.count('<style') != text.count('</style>'):
    problems.append('style tags no longer balance')
# CSS braces, counted. A rewritten selector that lost its block leaves the
# tags balanced and the markup balanced and the stylesheet broken.
if new_css.count('{') != new_css.count('}'):
    problems.append('CSS braces no longer balance: %d open, %d close - a rule '
                    'has lost its block' % (new_css.count('{'),
                                            new_css.count('}')))
# ..and every surviving selector must actually have one.
for _m in re.finditer(r'([^{}]+)\{', new_css):
    pass
_dangling = re.findall(r'\}\s*([^{}@/\s][^{}]*?)\s*\}', new_css)
if _dangling:
    problems.append('a selector survives with no block: %r'
                    % _dangling[0][:50])
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

before, after = len(css.split('\n')), len(new_css.split('\n'))
print('')
print('  CSS rules removed: %d' % len(dropped))
for d in dropped:
    print('       %s' % d)
if mixed_fixed:
    print('')
    print('  REWRITTEN - a selector list that mixed replaced names with')
    print('  surviving ones. Left alone it would carry dead names for ever.')
    for w in mixed_fixed:
        print('       %s' % w)
print('')
print('  style block: %d lines -> %d  (%d removed, %.0f%%)'
      % (before, after, before - after,
         100.0 * (before - after) / max(before, 1)))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = PAGE + '.bak_tablereport'
if not os.path.exists(bak):
    shutil.copy2(PAGE, bak)
with io.open(PAGE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/tenant_report.html  (backup: .bak_tablereport)')
print('')
print('Now run:  python test_table_tenant_report.py')
