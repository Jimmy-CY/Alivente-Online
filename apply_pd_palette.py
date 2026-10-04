# -*- coding: utf-8 -*-
"""PD-1 - property_detail's PALETTE: five dark headers and nine badges

The last big page the standard never reached. 1,992 lines, 227 local CSS
rules, and the only house component on it is the action bar.

This round takes the two things you see on every visit. PD-2 takes the
tables themselves; PD-3 takes what is left.

==========================================================================
FIVE TABLES WEAR A NEAR-BLACK HEADER
==========================================================================
    .issues-table th           background-color: #343a40 !important
    .invoices-table th         #343a40 !important
    .revenue-table th          #343a40 !important
    .expenses-table th         #343a40 !important
    .actual-expenses-table th  #343a40 !important

Every other table in this app draws its header on --alv-surface with
--alv-ink-strong, uppercase. These five are a dark bar with white text,
and the !important means base could not reach them even if the tables
took .alv-table tomorrow - which is PD-2's job and would have failed
silently without this.

FIVE RULES BECOME ONE, and that one mirrors base's .alv-table thead th
declaration for declaration, by TOKEN. It is still a local rule and that
is still not where a table header belongs; PD-2 deletes it outright when
the tables take the class. Written as one grouped selector so that
deletion is one edit rather than five.

==========================================================================
AND A GREEN PILL BESIDE A RED PILL, ON TWO COUNTS
==========================================================================
    Active Warranties:   <span class="badge badge-success">4</span>
    Expired Warranties:  <span class="badge"
                               style="background-color: #dc3545">2</span>

Demetri's call, asked: "Neutral - they are numbers." Two expired
warranties on a forty-asset property is a fact, not a failure, and it
sits directly under Total Assets, which is drawn as plain text. Both take
.alv-pill-neutral and read as the counts they are.

THIS IS THE AGEING DECISION, ONE PAGE ALONG. Green-to-red is a verdict
vocabulary. AG-1 took it off a scale this morning because ageing is a
progression rather than a verdict; a tally is not a verdict either.

A STATUS IS DIFFERENT, and keeps good and bad:

    Status            Active / Inactive        good / neutral
    Available         Yes / No                 good / neutral
    Current Tenant    Yes / No                 good / neutral
    Invoice           Overdue / Current        bad  / good
    from lease        a note on a figure       info

Those are the tones the rest of this app already uses for those exact
words, so a reader moving between Invoices and a property sees one
vocabulary.

==========================================================================
WHAT IT REPLACED
==========================================================================
#343a40 five times, white five times, Bootstrap's badge-success,
badge-secondary, badge-danger and badge-info, the local .badge-available
and .badge-not-available pair, and one #dc3545 written inline on an
element. Nothing is added to the palette: every tone is a token base
already owns.

Backups: .bak_pdpalette. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_pdpalette'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

PAGE = alv_tree.path_of('property_detail.html')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('PD1: %s is not a byte copy' % bak)


def swap(nl, old, new, what, times=1):
    c = nl.count(old)
    if c != times:
        raise SystemExit('PD1: %s appears %d times, not %d' % (what, c, times))
    return nl.replace(old, new)


print('=' * 74)
print('PD-1 - property_detail: the headers and the badges%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

if 'PD-1, 4 Oct 2026' in nl:
    print('  property_detail.html       already on the house palette')
    print('=' * 74)
    print('PD-1 applied')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# 1. THE FIVE HEADERS.
# ==========================================================================
HEADS = [
    ('.issues-table th { background-color: #343a40 !important; color: white;'
     ' font-weight: 600; border: none; padding: 12px 8px; }\n'),
    ('.invoices-table th { background-color: #343a40 !important;'
     ' color: white; font-weight: 600; }\n'),
    ('.revenue-table th { background-color: #343a40 !important;'
     ' color: white; font-weight: 600; border: none; padding: 15px; }\n'),
    ('.expenses-table th { background-color: #343a40 !important;'
     ' color: white; font-weight: 600; border: none; padding: 15px; }\n'),
    ('.actual-expenses-table th { background-color: #343a40 !important;'
     ' color: white; font-weight: 600; border: none; padding: 15px; }\n'),
]

ONE_HEAD = """/* PD-1, 4 Oct 2026 - FIVE RULES, ONE HEADER. These five tables each
   wrote their own `th` as #343a40 !important with white text - a
   near-black bar that no other table in this app has. Every other list
   here draws its header on --alv-surface with --alv-ink-strong,
   uppercase, and that is what these read as now.

   THE !important MATTERED BEYOND THE COLOUR. It meant base could not
   reach these headers even if the tables took .alv-table - which is
   exactly what PD-2 is going to do, and it would have failed silently.

   STILL A LOCAL RULE, AND STILL IN THE WRONG PLACE. A table header
   belongs to base. This mirrors base's .alv-table thead th by token so
   the page reads correctly today, written as ONE grouped selector so
   that PD-2 deletes it in a single edit rather than five. */
.issues-table th,
.invoices-table th,
.revenue-table th,
.expenses-table th,
.actual-expenses-table th {
    background: var(--alv-surface);
    color: var(--alv-ink-strong);
    font-weight: 600;
    font-size: 13.5px;
    letter-spacing: .01em;
    text-transform: uppercase;
    vertical-align: middle;
    padding: 11px 12px;
    border: none;
    border-bottom: 0;
    box-shadow: inset 0 -1px 0 var(--alv-line);
}
"""

# AND TWO MORE, WHICH THE FIRST PASS OF THIS ROUND MISSED. The census
# found seven tables and five `th` rules naming #343a40, so five is what
# this round took - and the RENDER showed two dark headers still standing
# beside five that had changed, which is worse than seven that match.
#
# categories-table and assets-table colour the ROW, not the cell:
#
#     .categories-table thead tr,
#     .assets-table thead tr { background-color: #2c3e50; color: white; }
#
# a different hex, a different selector, same dark bar. Searching for the
# colour found the first five; looking at the picture found the other two.
TWO_MORE = (
    """.categories-table thead tr,
.assets-table thead tr {
    background-color: #2c3e50;
    color: white;
}
.categories-table th,
.assets-table th {
    padding: 12px;
    text-align: left;
    border: 1px solid #34495e;
}
""",
    """/* PD-1, 4 Oct 2026 - the other two dark headers. These colour the
   ROW rather than the cell, in #2c3e50 rather than #343a40, with a
   #34495e cell border - which is why a search for the first colour
   missed them and the render did not. Same house header as the five
   above; the border goes to the line token. */
.categories-table thead tr,
.assets-table thead tr {
    background: var(--alv-surface);
    color: var(--alv-ink-strong);
}
.categories-table th,
.assets-table th {
    padding: 11px 12px;
    text-align: left;
    font-weight: 600;
    font-size: 13.5px;
    letter-spacing: .01em;
    text-transform: uppercase;
    border: 1px solid var(--alv-line);
}
""")

for i, h in enumerate(HEADS):
    nl = swap(nl, h, ONE_HEAD if i == 0 else '', 'the %s header rule' % (
        re.match(r'\.([a-z-]+)-table', h).group(1)))

# ==========================================================================
# 2. THE BADGES.
# ==========================================================================
# EACH ONE NAMED, with the reason it takes the tone it takes. A pill is
# either a VERDICT - Active, Overdue, Current - or it is not, and the two
# warranty figures are not: they are counts, sitting under Total Assets,
# which is drawn as plain text.
PILLS = [
    # (what, old, new)
    ('the property status',
     '<span class="badge {% if property.prop_status == \'Active\' %}'
     'badge-success{% else %}badge-secondary{% endif %}">',
     '{# PD-1 - a verdict, so good and neutral, on the house tokens. #}\n'
     '                                            '
     '<span class="alv-pill {% if property.prop_status == \'Active\' %}'
     'alv-pill-good{% else %}alv-pill-neutral{% endif %}">'),

    ('available for rent',
     '<span class="badge {% if property.prop_available_for_rent == \'Yes\' %}'
     'badge-available{% else %}badge-not-available{% endif %}">',
     '{# PD-1 - badge-available and badge-not-available were local      #}\n'
     '                                            '
     '{# classes, one of them a raw #dc3545. A property that is not     #}\n'
     '                                            '
     '{# available is not FAILING, so No reads neutral, not red.        #}\n'
     '                                            '
     '<span class="alv-pill {% if property.prop_available_for_rent == \'Yes\' %}'
     'alv-pill-good{% else %}alv-pill-neutral{% endif %}">'),

    ('active warranties',
     '<span class="badge badge-success">{{ active_warranties }}</span>',
     '{# PD-1 - A COUNT, NOT A VERDICT. Demetri, asked: "Neutral - they #}\n'
     '                                            '
     '{# are numbers." It sits under Total Assets, which is plain text. #}\n'
     '                                            '
     '<span class="alv-pill alv-pill-neutral">{{ active_warranties }}</span>'),

    ('expired warranties',
     '<span class="badge" style="background-color: #dc3545; color: white;">'
     '{{ expired_warranties }}</span>',
     '{# PD-1 - the same, and this one was a hex written ON the element. #}\n'
     '                                            '
     '{# Two expired warranties on a forty-asset property is a fact,     #}\n'
     '                                            '
     '{# not a failure, and a red pill on a tally says otherwise.        #}\n'
     '                                            '
     '<span class="alv-pill alv-pill-neutral">{{ expired_warranties }}</span>'),

    ('the current tenant',
     '<span class="badge {% if active_tenant.tenant_current == \'Yes\' %}'
     'badge-success{% else %}badge-secondary{% endif %}">',
     '{# PD-1 - a verdict: this tenant is the current one, or is not. #}\n'
     '                                                    '
     '<span class="alv-pill {% if active_tenant.tenant_current == \'Yes\' %}'
     'alv-pill-good{% else %}alv-pill-neutral{% endif %}">'),

    ('the from-lease note',
     '<span class="badge badge-info" style="margin-left:6px;">from lease</span>',
     '<span class="alv-pill alv-pill-info" style="margin-left:6px;">'
     'from lease</span>'),

    ('the invoice status',
     '<span class="badge {% if invoice.overdue %}badge-danger{% else %}'
     'badge-success{% endif %} px-3 py-2">',
     '{# PD-1 - the one pill on this page that keeps RED. An overdue   #}\n'
     '                                                        '
     '{# invoice is a verdict and it reads red on the Invoices list,   #}\n'
     '                                                        '
     '{# so it reads red here too - one vocabulary across the app.     #}\n'
     '                                                        '
     '<span class="alv-pill {% if invoice.overdue %}alv-pill-bad{% else %}'
     'alv-pill-good{% endif %}">'),
]

for what, old, new in PILLS:
    nl = swap(nl, old, new, what)

# THE TWO LOCAL BADGE CLASSES GO WITH THEIR LAST CALLER.
nl = swap(nl,
          '.badge-available { background-color: var(--alv-good);'
          ' color: var(--alv-on-accent); }\n'
          '.badge-not-available { background-color: #dc3545; color: white; }\n',
          '/* PD-1, 4 Oct 2026 - .badge-available and .badge-not-available are\n'
          '   gone with their only caller. The second was a raw #dc3545, and\n'
          '   a property that is not available for rent is not failing. */\n',
          'the available/not-available pair')

# ==========================================================================
# 3. AND THE BADGE RULES THEMSELVES, WHICH NOW HAVE NO CALLER.
# ==========================================================================
# A round that removes the last caller of a rule owns the rule. After the
# swaps above, the string `badge` appears nowhere in this page's markup -
# so five declarations are dead CSS.
#
# AND .badge WAS DECLARED TWICE, 138 lines apart, with different values:
# font-size .75em at one, then display/padding/border-radius/.9rem/500 at
# the other. The second wins and the first never rendered. That is the
# same shape as the filter frame FRAME-1 found on four pages, in a page
# nobody had looked at.
DEAD = [
    ('.badge {\n    font-size: 0.75em;\n}\n',
     '/* PD-1, 4 Oct 2026 - .badge, declared HERE and again 138 lines\n'
     '   below with different values, so this one never rendered. Both\n'
     '   are gone: nothing on this page wears the class any more. */\n'),
    ('.badge {\n    display: inline-block;\n    padding: 5px 10px;\n'
     '    border-radius: 12px;\n    font-size: 0.9rem;\n'
     '    font-weight: 500;\n}\n\n', ''),
    ('.badge-secondary { background-color: #6c757d; color: white; }\n', ''),
    ('.badge-light { background-color: #f8f9fa; color: #212529; }\n', ''),
    ('.badge-danger { background-color: #dc3545; color: white; }\n', ''),
]

# PROVED DEAD BEFORE REMOVED, not assumed. The markup is what decides.
#
# ASKED FOR THE CLASS TOKEN, NOT THE SUBSTRING. The first version of this
# gate tested `'badge' in body` and refused to run - correctly, by its own
# lights, because this page also carries .renewal-status-badge and
# .status-badge, two different components whose names merely END in the
# word, plus a comment this round had just written containing it.
#
# So: every class ATTRIBUTE, emptied of Django tags, split on whitespace,
# and compared token by token.
_body = re.sub(r'<style[^>]*>.*?</style>', '', nl, flags=re.S)
_body = re.sub(r'<script[^>]*>.*?</script>', '', _body, flags=re.S)
_body = re.sub(r'\{#.*?#\}', '', _body, flags=re.S)
_worn = set()
for _m in re.finditer(r'class="([^"]*)"', _body):
    _v = re.sub(r'\{%[^%]*%\}', ' ', _m.group(1))
    _v = re.sub(r'\{\{[^}]*\}\}', ' ', _v)
    for _c in _v.split():
        if _c == 'badge' or _c.startswith('badge-'):
            _worn.add(_c)
if _worn:
    raise SystemExit('PD1: the markup still wears %s - the rules are not '
                     'dead' % ', '.join(sorted(_worn)))
for old_d, new_d in DEAD:
    nl = swap(nl, old_d, new_d, 'the dead rule %r' % old_d.split('{')[0].strip())

nl = swap(nl, TWO_MORE[0], TWO_MORE[1], 'the categories/assets header')

out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
if not CHECK:
    back_up(PAGE, raw)
    write(PAGE, out)
print('  property_detail.html       7 headers -> house, 7 badges -> pills, 5 dead rules out')

print('=' * 74)
print('PD-1 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
