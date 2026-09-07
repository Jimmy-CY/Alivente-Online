"""apply_issues_table.py - the main Issues list joins the table standard.

    python apply_issues_table.py --check     dry run, writes nothing
    python apply_issues_table.py

Run from the repo root. First of the 26-page table-standard queue written down
in claude/print_leak_round.md.

THIRTY-NINE PAGE RULES, AND THIRTY-TWO OF THEM ARE THINGS BASE ALREADY DOES.

    .status-badge + .status-success/-warning/-danger    4   -> .alv-pill*
    .action-btn + hover + a + hover a                   4   -> .status-btn
    .delete-issue-btn + hover + focus                   3   -> .icon-delete
    #issuesTable ... 21 phone-card rules               21   -> .alv-table
    (of which tr.no-issues-row + td + td::before        3   -> .alv-empty)
    .sortable + .sort-icon family                       7   STAYS - see below

THE ONE THING BASE CANNOT TAKE OVER, AND WHY, BECAUSE THIS ROUND ALMOST GOT
IT WRONG THE OTHER WAY.

`.sortable` looked like a base candidate: four templates carry a sortable
header - this page, passport_management, financial_indicators and
vacancy_management - and four askers is well past the bar that finally
justified .alv-seg. Measured, they are not one thing:

    fsr.html                  .sortable        .sort-asc/.sort-desc
                              icon inline after the label, 7 rules
    passport_management       .sortable-header no icon, no state, 2 rules
    financial_indicators      .sortable-header .sorted-asc/.sorted-desc
                              icon absolutely positioned right, 11 rules
    vacancy_management        .sortable-header same family, 5 rules

Two class names, two state vocabularies, two icon placements. And the
deciding fact: `.sorted-asc` and `.sorted-desc` appear NOWHERE in
financial_indicators or vacancy_management - not in markup, not in script -
so those state rules are dead, and passport_management has a cursor and a
hover but no sort indicator at all.

So the system contains exactly ONE working, stateful sortable header, and it
is this page's. It stays page-local and takes tokens instead of literals. The
other three carry more dead rules for a later sweep. MEASURE THE SHAPE BEFORE
GENERALISING FROM ONE CASE - four askers turned out to be one.

WHAT THE ROW BECOMES, decided from rendered options.

  Status       .status-badge painted Bootstrap's alert colours (#d4edda on
               #155724 and so on). base's pills, on the same map the Comments
               Report round settled: Resolved -> good, Unresolved -> attn,
               anything else -> neutral rather than danger, because "not one
               of the two known statuses" is not a failure.

  Comments     was `<button class="btn btn-light action-btn"><a href=...>` -
               an ANCHOR NESTED INSIDE A BUTTON, which is invalid HTML and
               which browsers resolve however they like. It is one <a> now,
               wearing base's .status-btn, with the word kept: Comments is
               the main way into an issue on this screen, and an icon alone
               would hide the primary action to save a few pixels.

  Delete       a filled #dc3545 Bootstrap square becomes base's quiet
               .icon-action-btn .icon-delete, the same control Properties,
               Tenants and Customers already use.

  The cells    hand-rolled .action-cell / -comments / -delete become the
               house pair: .desktop-action-cell for the table and
               .mobile-action-bar cols-2 for the phone, copied from
               customer_list.html rather than invented.

INLINE COLUMN WIDTHS STAY, and this corrects something said while the round
was being agreed. The proposal said the six `style="width: {% if superuser
%}16%{% else %}18%{% endif %}"` would go "so the table can size itself".
Measured against a page that has already migrated - customer_list.html -
widths on <th> are house-consistent; it carries five of them. They stay, with
the two action columns merged into one.

CLASS NAMES THE SCRIPT NEEDS ARE KEPT while their RULES are deleted - the
same move the Notify round made. The sorter reads `.sortable` and its
`data-sort`, finds rows by `.issue-row` and their data-property / data-date /
data-status, writes `.sort-asc` / `.sort-desc` and repaints `.sort-icon`, and
the delete flow finds `.delete-issue-btn` by `data-issue-id`. Every one of
those survives; losing one leaves a table that renders correctly and does
nothing, which is the failure mode this suite exists to catch.

HOUSE RULES: idempotent, .bak_isstbl backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
IA = os.path.join(T, 'fsr.html')
BASE = os.path.join(T, 'base.html')
for _p in (IA, BASE):
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
                 % (what, n, old[:130]))
    return t.replace(old, new, 1)


def drop_rule(text, selector, what, expect=1):
    pat = re.compile(r'(?m)^[ \t]*' + re.escape(selector) + r'[ \t]*\{')
    hits = list(pat.finditer(text))
    if len(hits) != expect:
        sys.exit('! %s: %r matched %d rule openings, expected %d'
                 % (what, selector, len(hits), expect))
    for m in reversed(hits):
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
        text = text[:i] + text[k:]
    return text


def cut_region(text, first, last, prefix, what, n_expected):
    """Delete a contiguous run of rules, having CHECKED that the run really
       does contain only rules whose selector starts with `prefix`.

       Twenty-one rules is too many to name one at a time, and a blind span
       cut between two anchors is how a round eats a rule it never meant to.
       So the span is measured before it is removed: every rule opening
       inside it must match, and the count must be what the survey found."""
    if text.count(first) != 1 or text.count(last) != 1:
        sys.exit('! %s: region anchors did not match once each' % what)
    a = text.index(first)
    b = text.index(last) + len(last)
    span = text[a:b]
    opens = re.findall(r'(?m)^[ \t]*([^{}\n@/][^{}\n]*)\{', span)
    stray = [s.strip() for s in opens if not s.strip().startswith(prefix)]
    if stray:
        sys.exit('! %s: the region also holds %s' % (what, stray[:4]))
    if len(opens) != n_expected:
        sys.exit('! %s: expected %d rules in the region, found %d'
                 % (what, n_expected, len(opens)))
    while b < len(text) and text[b] in '\r\n':
        b += 1
    return text[:a] + text[b:], len(opens)


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


F_ORIG, F_CRLF, f = load(IA)
_f_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
DONE = ('THE MAIN ISSUES LIST IS BASE' in f
        and 'status-badge' not in _f_nc)
if DONE:
    print('  fsr.html already patched')
else:
    # =======================================================================
    # 1. MARKUP - the table, its head, and the two action columns
    # =======================================================================
    f = sub1(f,
             '<table class="table table-bordered table-striped" id="issuesTable">',
             '<table class="table alv-table" id="issuesTable">',
             'IT: the table class')

    # The head. Comments and Delete merge into one Actions column, so the
    # widths are redistributed rather than dropped - see the docstring.
    f = sub1(f, """                <th class="text-center" style="width: 10%">Comments</th>
                {% if request.user.is_superuser %}
                <th class="text-center" style="width: 8%">Delete</th>
                {% endif %}""",
             """                <th class="desktop-action-cell cell-actions" style="width: {% if request.user.is_superuser %}18%{% else %}10%{% endif %}">Actions</th>""",
             'IT: the two action headers become one')

    # -------------------------------------------------- the status pill
    # The map the Comments Report round settled on 2 Sep. The `else` branch
    # is NEUTRAL, not danger: a status that is neither Resolved nor
    # Unresolved is unrecognised, and an unrecognised status is not a
    # failure. The old rule painted it Bootstrap's alert red.
    f = sub1(f, """                                    <span class="status-badge
                                        {% if isresults.issues_status == 'Resolved' %}status-success
                                        {% elif isresults.issues_status == 'Unresolved' %}status-warning
                                        {% else %}status-danger{% endif %}">
                                        {{ isresults.issues_status }}
                                    </span>""",
             """                                    <span class="alv-pill
                                        {% if isresults.issues_status == 'Resolved' %}alv-pill-good
                                        {% elif isresults.issues_status == 'Unresolved' %}alv-pill-attn
                                        {% else %}alv-pill-neutral{% endif %}">
                                        {{ isresults.issues_status }}
                                    </span>""",
             'IT: the status pill')

    # ------------------------------------------- the two cells become two
    # The desktop cell and the phone bar, copied from customer_list.html.
    _URL = ("{% url 'fsr_details' isresults.issues_id %}?from=fsr"
            "&search={{ request.POST.search|default:'' }}"
            "&propcountry={{ request.POST.propcountry|default:'' }}"
            "&propname={{ request.POST.propname|default:'' }}"
            "&issuestatus={{ request.POST.issuestatus|default:'' }}")
    _DATA = """data-issue-id="{{ isresults.issues_id }}"
                                                data-issue-heading="{{ isresults.issues_heading }}"
                                                data-issue-description="{{ isresults.issues_description }}"
                                                data-property-name="{{ results.prop_name }}"
                                                data-date-logged="{{ isresults.issues_date_logged|date:'d/m/Y' }}"
                                                data-status="{{ isresults.issues_status }}\""""
    _OLD = """                                <td data-label="Comments" class="text-center action-cell action-cell-comments">
                                    <button type="button" class="btn btn-light action-btn">
                                        <a href="%s" class="issue-heading-link">
                                            Comments
                                        </a>
                                    </button>
                                </td>
                                {%% if request.user.is_superuser %%}
                                <td data-label="Delete" class="text-center action-cell action-cell-delete">
                                    <button type="button"
                                            class="btn btn-danger btn-sm delete-issue-btn"
                                            %s
                                            title="Delete Issue">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                                {%% endif %%}""" % (_URL, _DATA.replace('\n                                                ', '\n                                            '))
    _NEW = """                                <td data-label="Actions" class="desktop-action-cell cell-actions">
                                    <div class="row-actions">
                                        <a href="%s" class="status-btn issue-comments-btn">
                                            <i class="fas fa-comments"></i> Comments
                                        </a>
                                        {%% if request.user.is_superuser %%}
                                        <button type="button"
                                                class="icon-action-btn icon-delete delete-issue-btn"
                                                %s
                                                title="Delete Issue">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                        {%% endif %%}
                                    </div>
                                </td>

                                <td class="mobile-action-bar {%% if request.user.is_superuser %%}cols-2{%% else %%}cols-1{%% endif %%}">
                                    <a href="%s" class="mobile-action-btn">
                                        <i class="fas fa-comments mobile-action-icon icon-color-view"></i>
                                        <span class="mobile-action-label">Comments</span>
                                    </a>
                                    {%% if request.user.is_superuser %%}
                                    <button type="button" class="mobile-action-btn delete-issue-btn"
                                            %s
                                            title="Delete Issue">
                                        <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                                        <span class="mobile-action-label">Delete</span>
                                    </button>
                                    {%% endif %%}
                                </td>""" % (_URL, _DATA, _URL,
                                            _DATA.replace(
                                                '\n                                                ',
                                                '\n                                            '))
    f = sub1(f, _OLD, _NEW, 'IT: the action cells')

    # --------------------------------------------------- the empty state
    f = sub1(f, """                <tr class="no-issues-row">
                    <td colspan="{% if request.user.is_superuser %}7{% else %}6{% endif %}" class="text-center">No issues found</td>
                </tr>""",
             """                <tr class="no-issues-row">
                    <td colspan="6">
                        <div class="alv-empty">
                            <i class="fas fa-clipboard-list"></i>
                            <div class="alv-empty-title">No issues found</div>
                            <div class="alv-empty-hint">Nothing matches the
                                current filter. Clear it, or add an issue.</div>
                        </div>
                    </td>
                </tr>""", 'IT: the empty state')

    # =======================================================================
    # 2. CSS - the eleven that base already owns
    # =======================================================================
    for sel, what in (('.status-badge', 'IT: the badge shell'),
                      ('.status-success', 'IT: the green'),
                      ('.status-warning', 'IT: the amber'),
                      ('.status-danger', 'IT: the red'),
                      ('.action-btn', 'IT: the Comments button'),
                      ('.action-btn:hover', 'IT: its hover'),
                      ('.action-btn a', 'IT: the nested anchor'),
                      ('.action-btn:hover a', 'IT: its hover'),
                      ('.delete-issue-btn', 'IT: the red slab'),
                      ('.delete-issue-btn:hover', 'IT: its hover'),
                      ('.delete-issue-btn:focus', 'IT: its focus ring')):
        f = drop_rule(f, sel, what)

    # =======================================================================
    # 3. CSS - the twenty-one phone-card rules, cut as one measured region
    # =======================================================================
    f, _n = cut_region(
        f,
        """    #issuesTable {
        border: none;
    }""",
        """    #issuesTable tr.no-issues-row td::before {
        display: none;
    }""",
        '#issuesTable', 'IT: the hand-rolled card view', 21)

    # =======================================================================
    # 4. CSS - .sortable stays, and stops spelling colours by hand
    # =======================================================================
    for lit, tok in (('#e9ecef', 'var(--alv-neutral-soft)'),
                     ('#adb5bd', 'var(--alv-ink-faint)'),
                     ('#6c757d', 'var(--alv-ink-soft)'),
                     ('#0e7c8b', 'var(--alv-accent)')):
        f = re.sub(r'(\.sortable[^{}]*\{[^}]*?)' + re.escape(lit),
                   lambda m, t=tok: m.group(1) + t, f)

    # =======================================================================
    # 5. the note, LAST - after the sweep, never before it
    # =======================================================================
    f = sub1(f, """.sortable {
    user-select: none;""",
             """/* THE MAIN ISSUES LIST IS BASE'S TABLE NOW - 5 Sep. Thirty-two page
   rules went: four painting a status badge in Bootstrap's alert
       colours, four on a Comments control that nested an <a> INSIDE a
   <button>, three on a filled red Delete, and twenty-one rebuilding
   by hand the phone cards .alv-table already builds.

   THE CLASS NAMES THE SCRIPT NEEDS ARE STILL HERE while their rules
       are not - .issue-row, .delete-issue-btn and .no-issues-row carry no
   appearance any more and exist so the sorter and the delete flow can
   find their elements.

   .sortable IS THE EXCEPTION, and it was nearly deleted for the wrong
   reason. Four templates carry a sortable header, which is past the
   bar that justified .alv-seg - but they are two class names, two
   state vocabularies and two icon placements, and the state rules on
   two of them are dead. One working sortable header in the system,
   and it is this one. It stays here and takes tokens. */
.sortable {
    user-select: none;""", 'IT: say what happened and why .sortable stayed')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
_nc = re.sub(r'<!--.*?-->', '', _nc, flags=re.S)
_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', _nc, re.S))
_js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', _nc, re.S))
_mk = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', _nc, flags=re.S)

# CLASS TOKENS, NOT SUBSTRINGS. The first draft asked `'action-btn' not in
# _mk` and failed on a correct file: `icon-action-btn` and
# `mobile-action-btn` both contain it, and `desktop-action-cell` contains
# `action-cell`. A substring test catches every superstring, which is the
# same shape of error as counting characters and calling them bytes. Split
# the class attributes into TOKENS and ask about membership.
_TOKENS = set()
for _a in re.findall(r'class="([^"]*)"', _mk):
    _TOKENS.update(_a.replace('{%', ' ').replace('%}', ' ').split())
for gone in ('status-badge', 'status-success', 'status-warning',
             'status-danger', 'action-btn', 'action-cell',
             'action-cell-comments', 'action-cell-delete', 'btn-light',
             'btn-danger', 'table-bordered', 'table-striped'):
    want(gone not in _TOKENS, 'IT: the class %s survives in the markup' % gone)
# and the CONTROL for that helper - if tokenising silently produced nothing,
# every check above would pass on an empty set.
want('alv-table' in _TOKENS and 'issue-row' in _TOKENS,
     'IT: the class tokeniser found nothing - the checks above are vacuous')
for gone in ('.status-badge', '.action-btn', '.delete-issue-btn',
             '#issuesTable'):
    want(not re.search(r'(?m)^[ \t]*' + re.escape(gone) + r'[\s,:{]', _css),
         'IT: a %s rule survives in the stylesheet' % gone)

want('class="table alv-table" id="issuesTable"' in _mk,
     'IT: the table is not base\'s')
want(_mk.count('desktop-action-cell') == 2,
     'IT: expected a desktop action th and td, got %d'
     % _mk.count('desktop-action-cell'))
want('mobile-action-bar' in _mk, 'IT: no phone action bar')
want(_mk.count('alv-pill-good') == 1 and _mk.count('alv-pill-attn') == 1
     and _mk.count('alv-pill-neutral') == 1,
     'IT: the status map is not three branches')
want('alv-empty-title' in _mk, 'IT: the empty state did not migrate')

# THE ANCHOR IS NO LONGER INSIDE A BUTTON. This is the defect, not a tidy-up:
# `<button><a href></a></button>` is invalid HTML and browsers resolve it
# however they like.
want(not re.search(r'<button[^>]*>\s*<a\s', _mk),
     'IT: an anchor is still nested inside a button')
want('class="status-btn issue-comments-btn"' in _mk,
     'IT: Comments is not base\'s inline button')

# THE SCRIPT HOOKS. Losing one leaves a table that renders and does nothing.
for hook in ('issuesTableBody', 'issue-row', 'sortable', 'sort-icon',
             'sort-asc', 'sort-desc', 'delete-issue-btn'):
    want(hook in _js, 'IT: the script lost %s' % hook)
    want(hook in _mk or hook in _css,
         'IT: %s is in the script but nothing carries it' % hook)
for attr in ('data-sort=', 'data-property=', 'data-date=', 'data-status=',
             'data-issue-id='):
    want(attr in _mk, 'IT: the markup lost %s' % attr)

# .sortable STAYS, and stops spelling colours.
want('.sortable {' in _css, 'IT: .sortable was deleted')
_sort = '\n'.join(m.group(0) for m in
                  re.finditer(r'\.sortable[^{}]*\{[^}]*\}', _css))
want(not re.search(r'#[0-9a-fA-F]{3,8}\b', _sort),
     'IT: .sortable still spells a colour by hand: %s'
     % re.findall(r'#[0-9a-fA-F]{3,8}\b', _sort))
want('var(--alv-accent)' in _sort, 'IT: the sorted indicator lost its accent')

# base must define what the round leans on.
_b = load(BASE)[2]
_bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', _b, re.S))
for need in ('.alv-pill-good', '.alv-pill-attn', '.alv-pill-neutral',
             '.icon-action-btn', '.icon-delete', '.status-btn',
             '.desktop-action-cell', '.mobile-action-bar', '.alv-empty',
             '.mobile-action-btn', '.mobile-action-icon',
             '.mobile-action-label'):
    want(need in _bcss, 'base does not define %s' % need)
want('.mobile-action-bar.cols-2' in _bcss, 'base has no cols-2')

# THE DELTA, measured against the BACKUP when there is one.
_before = F_ORIG.replace('\r\n', '\n')
_bak = IA + '.bak_isstbl'
if os.path.exists(_bak):
    _before = load(_bak)[2]
_b_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                              re.sub(r'/\*.*?\*/', '', _before, flags=re.S),
                              re.S))
_was = len(re.findall(r'(?m)^[ \t]*#issuesTable[^{\n]*\{', _b_css))
want(_was == 21, 'IT: expected 21 card rules before, saw %d' % _was)

for _m in re.finditer(r'/\*.*?\*/', f, re.S):
    want(not re.search(r'</?(?:script|style)\b', _m.group(0)),
         'IT: a CSS comment spells a script or style tag')
for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
    want(blk.count('{') == blk.count('}'), 'IT: unbalanced braces')
# A CHECK THAT COULD NOT FAIL, AND IT LET A 500 THROUGH. This line ended in
# `or True` - so it asserted nothing, and the round shipped with one extra
# {% endif %}: the ORIGINAL `{% if superuser %}` that wrapped the Delete <td>
# closed AFTER the cell, outside the anchor, and the replacement supplied its
# own pairs while the old closer stayed behind. Django raised
# TemplateSyntaxError and /fsr/ returned 500.
#
# "A control that cannot fail is worse than no control" is this project's own
# lesson, written down six times. Here it was written INTO the guard.
_open = len(re.findall(r'\{%\s*if\b', f))
_close = len(re.findall(r'\{%\s*endif\s*%\}', f))
want(_open == _close,
     'IT: %d {%% if %%} against %d {%% endif %%} - the template will not parse'
     % (_open, _close))
# COUNTS ARE NOT STRUCTURE. Balanced totals still pass on a file where an
# endif closes a for-loop it does not belong to - which is precisely what the
# orphan did. Walk the tags in order.
_OPEN = {'if': 'endif', 'for': 'endfor', 'block': 'endblock',
         'with': 'endwith', 'comment': 'endcomment',
         'spaceless': 'endspaceless', 'autoescape': 'endautoescape'}
_CLOSE = {v: k for k, v in _OPEN.items()}
_stack, _fault = [], None
for _m in re.finditer(r'\{%\s*(\w+)', f):
    _t = _m.group(1)
    _ln = f.count('\n', 0, _m.start()) + 1
    if _t in _OPEN:
        _stack.append((_t, _ln))
    elif _t in _CLOSE:
        if not _stack:
            _fault = 'line %d: %s with nothing open' % (_ln, _t); break
        _top, _at = _stack.pop()
        if _OPEN[_top] != _t:
            _fault = ('line %d: %s closes a {%% %s %%} opened on line %d'
                      % (_ln, _t, _top, _at)); break
if not _fault and _stack:
    _fault = 'unclosed {%% %s %%} from line %d' % _stack[-1]
want(_fault is None, 'IT: the template will not parse - %s' % _fault)

_fo = len(re.findall(r'\{%\s*for\b', f))
_fc = len(re.findall(r'\{%\s*endfor\s*%\}', f))
want(_fo == _fc, 'IT: %d {%% for %%} against %d {%% endfor %%}' % (_fo, _fc))
# And the same measured as a DELTA, because a file that was already unbalanced
# would pass the two above while this round made it worse.
_before_t = _before if os.path.exists(_bak) else F_ORIG.replace('\r\n', '\n')
want(_open - _close
     == len(re.findall(r'\{%\s*if\b', _before_t))
     - len(re.findall(r'\{%\s*endif\s*%\}', _before_t)),
     'IT: this round changed the if/endif balance')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-24s %d -> %d bytes'
          % (os.path.basename(p), len(orig.encode('utf-8')),
             len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_isstbl'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(IA, F_ORIG, F_CRLF, f, DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
