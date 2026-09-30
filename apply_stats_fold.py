# -*- coding: utf-8 -*-
"""SECTION T, ROUND T3 - PAYMENT BEHAVIOUR ON A PHONE

Demetri, walking Tenant Payment Behaviour on a phone:

    "Back Button and also move 'Include Past Tenants' up and in line (but
    to the left) of the Back Button. As a default, on Mobile only show
    Average Days to Pay and Flagged Slow. The user can press a chevron
    type expand to see the rest."

Two things, and they are both about the same 390 pixels. The Back is T1.
This round is the other two.

ONE - THE TOGGLE COMES UP INTO THE HEAD.

`Include past tenants` is a view switch, not an action on the data, and
it sat in .pd-toolbar below the summary strip - a full-width button on a
phone, three scrolls away from the thing it switches. It joins Back in
the report head, on BOTH screens, which Demetri chose on 30 Sep: one
markup change, the same structure at every width, and nothing to keep in
step later.

    .alv-report-actions - a flex row for what sits beside Back.

Back stops being a direct child of .alv-report-head, so neither base's
phone stretch rule nor T1's exception to it reaches Back ON THIS PAGE
any more. That is not a loss: inside the row Back is a flex item at its
own width, which is what T1 was arranging for. The other seven report
pages are untouched and keep T1's rule. Both states are measured.

TWO - TWO STATS, AND A CHEVRON FOR THE OTHER TWO.

The strip carries four: payments measured, tenants with data, average
days to pay, flagged slow. On a phone base already drops it to two
columns, so four tiles are a 2x2 block above the table. Demetri wants
the two that answer the question - average days to pay, flagged slow -
and the other two behind a chevron.

The mechanism goes in base, OPT-IN, because four pages use .alv-stats
and only this one asked:

    .alv-stats-collapse   on the group  - this group folds on a phone
    .alv-stat-more        on a tile     - this tile is one of the hidden
    .alv-stats-more       a row         - the chevron, spanning the grid

    financial_indicators  3 stats   not folded
    vacancy_management    3 stats   not folded
    fsr                   5 stats   not folded - the obvious next one
    tenant_payment_days   4 stats   FOLDS

NOTHING IS HIDDEN UNTIL THE SCRIPT SAYS SO. The phone rules hide
.alv-stat-more only under .alv-stats-collapse.js-ready, and base's script
adds js-ready. With JavaScript off the page renders exactly as it does
today - four tiles, no chevron - rather than hiding two numbers behind a
control that cannot be pressed.

THE COUNT IS base's, NOT THE PAGE'S. The chevron's label is written from
the number of .alv-stat-more tiles it finds, so "2 more" is measured
rather than typed, and a page that folds three does not have to remember
to change a word.

EXPANDED STAYS EXPANDED for the session - Demetri's choice, and the same
sessionStorage habit the recipe filters already have. The key is the
path, so two folding pages do not share one answer.

Backups: .bak_statsfold. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_statsfold'
CRLF = {}

BASE = 'base.html'
PAGE = 'tenant_payment_days.html'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('T3: %s is not a byte copy' % bak)


def patch(path, text, pairs, what):
    """Every WAS must appear exactly once, or nothing is written."""
    for i, (was, now) in enumerate(pairs):
        a = eol(path, was)
        if text.count(a) != 1:
            raise SystemExit('T3: %s - anchor %d of %d is there %d time(s), '
                             'not 1:\n%s' % (what, i + 1, len(pairs),
                                             text.count(a), was[:90]))
        text = text.replace(a, eol(path, now), 1)
    return text


# ==========================================================================
# base - THE ROW BESIDE BACK
# ==========================================================================
A_WAS = """.alv-report-brand { display: none; }"""
A_NOW = """.alv-report-brand { display: none; }
/* WHAT SITS BESIDE BACK - 30 Sep 2026. A report head holds titles and,
   on the right, Back. Payment Behaviour also carries a view switch -
   Include past tenants - which is navigation like Back rather than an
   action on the data, and it had been sitting in a toolbar below the
   summary strip, three scrolls from the thing it switches.

   A row, so the head keeps its two children and anything beside Back is
   laid out by one rule rather than by each page. Back inside this row is
   a flex item at its own width, which is what the phone rule below was
   arranging for when Back was a direct child.  [test_stats_fold.py] */
.alv-report-actions {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 10px;
    flex: 0 0 auto;
}"""

B_WAS = """    .alv-report-head > .btn.back-button,
    .alv-report-head > .btn.action-back {
        width: auto;
        align-self: flex-end;
    }
}"""
B_NOW = """    .alv-report-head > .btn.back-button,
    .alv-report-head > .btn.action-back {
        width: auto;
        align-self: flex-end;
    }
    /* The head is a column here, and .alv-report-actions is stretched
       across it like any other child - so the row it draws runs the full
       width of the phone with its first child left and Back right, which
       is what Demetri asked for. 30 Sep 2026. [test_stats_fold.py] */
    .alv-report-actions {
        justify-content: space-between;
        width: 100%;
    }
}"""

# ==========================================================================
# base - A SUMMARY STRIP THAT FOLDS ON A PHONE
# ==========================================================================
C_WAS = """.alv-stat-age .alv-stat-value { color: var(--age, var(--alv-ink-strong)); }"""
C_NOW = """.alv-stat-age .alv-stat-value { color: var(--age, var(--alv-ink-strong)); }
/* A STRIP THAT FOLDS ON A PHONE - 30 Sep 2026, OPT-IN. Demetri, on
   Payment Behaviour: on a phone show average days to pay and flagged
   slow, and put the rest behind a chevron. Four tiles are a 2x2 block on
   a phone, and two of the four answered the question.

   Three names. .alv-stats-collapse says this group folds;
   .alv-stat-more marks a tile that folds away; .alv-stats-more is the
   chevron, a grid item spanning both columns. Opt-in because four pages
   use .alv-stats and one of them asked - fsr, with five, is the obvious
   next one and is NOT folded.

   The chevron is desktop-invisible: above 768px the strip is four
   columns across and there is nothing to fold.
                                              [test_stats_fold.py] */
.alv-stats-more { display: none; }"""

D_WAS = """    .alv-stat-value { font-size: 1.4rem; }"""
D_NOW = """    .alv-stat-value { font-size: 1.4rem; }
    /* THE FOLD, AND WHY IT WAITS FOR THE SCRIPT - 30 Sep 2026. Hiding is
       conditional on .js-ready, which base's script adds. With
       JavaScript off nothing is hidden and no chevron appears: the page
       renders as it does today rather than putting two numbers behind a
       control that cannot be pressed.        [test_stats_fold.py] */
    .alv-stats-collapse.js-ready .alv-stat-more { display: none; }
    .alv-stats-collapse.js-ready.is-open .alv-stat-more { display: block; }
    .alv-stats-collapse.js-ready .alv-stats-more {
        display: flex;
        grid-column: 1 / -1;
        align-items: center;
        justify-content: center;
        gap: 8px;
        min-height: 44px;
        padding: 10px 12px;
        background: var(--alv-surface);
        border: 1px dashed var(--alv-line);
        border-radius: 6px;
        font-family: var(--alv-font-ui);
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        color: var(--alv-ink-soft);
        cursor: pointer;
        user-select: none;
    }
    .alv-stats-collapse.js-ready .alv-stats-more:focus-visible {
        outline: 2px solid var(--alv-accent);
        outline-offset: 2px;
    }
    .alv-stats-more-chev { transition: transform .15s ease; }
    .alv-stats-collapse.is-open .alv-stats-more-chev {
        transform: rotate(180deg);
    }"""

# ==========================================================================
# base - THE CONTROLLER
# ==========================================================================
E_WAS = """})();
</script>

{% block extra_scripts %}{% endblock %}"""
E_NOW = """})();
</script>

  <script>
/* ===== alv-stats-fold v1 ===== 30 Sep 2026 =========================
   A summary strip that folds on a phone. Opt in by putting
   .alv-stats-collapse on the .alv-stats group and .alv-stat-more on
   each tile that folds away; this script finds them, writes the chevron
   row, and remembers the state for the session.

   IT WRITES THE CHEVRON, so no page types one - and it writes the COUNT
   from the tiles it found, so "2 more" cannot fall out of step with the
   markup. It adds .js-ready, and the CSS hides nothing until that class
   is on: with this script blocked the strip renders in full, which is
   what it did before the fold existed.

   The key is the path, so two folding pages do not share one answer.
   sessionStorage is wrapped, because a browser refusing it must not
   take the toggle down with it. See test_stats_fold.py. */
(function () {
    "use strict";
    function key(el, i) {
        return 'alvStatsFold:' + location.pathname + ':' + (el.id || i);
    }
    function get(k) {
        try { return sessionStorage.getItem(k); } catch (e) { return null; }
    }
    function set(k, v) {
        try { sessionStorage.setItem(k, v); } catch (e) {}
    }
    function label(row, n, open) {
        row.innerHTML = '<span class="alv-stats-more-text">'
            + (open ? 'Show less' : (n + ' more'))
            + '</span><i class="fas fa-chevron-down alv-stats-more-chev"'
            + ' aria-hidden="true"></i>';
    }
    function fold(group, i) {
        var more = group.querySelectorAll('.alv-stat-more');
        if (!more.length) { return; }
        var row = group.querySelector('.alv-stats-more');
        if (!row) {
            row = document.createElement('div');
            row.className = 'alv-stats-more';
            group.appendChild(row);
        }
        row.setAttribute('role', 'button');
        row.setAttribute('tabindex', '0');
        var k = key(group, i);
        var open = get(k) === 'open';
        function apply() {
            group.classList.toggle('is-open', open);
            row.setAttribute('aria-expanded', open ? 'true' : 'false');
            label(row, more.length, open);
        }
        function flip() {
            open = !open;
            set(k, open ? 'open' : 'shut');
            apply();
        }
        row.addEventListener('click', flip);
        row.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar') {
                e.preventDefault();
                flip();
            }
        });
        group.classList.add('js-ready');
        apply();
    }
    function init() {
        Array.prototype.forEach.call(
            document.querySelectorAll('.alv-stats-collapse'), fold);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
</script>

{% block extra_scripts %}{% endblock %}"""

BASE_PAIRS = [(A_WAS, A_NOW), (B_WAS, B_NOW), (C_WAS, C_NOW),
              (D_WAS, D_NOW), (E_WAS, E_NOW)]

# ==========================================================================
# tenant_payment_days.html
# ==========================================================================
P1_WAS = """      <a href="{% url 'tenant' %}" class="btn back-button" role="button">
        <i class="fas fa-arrow-left"></i> Back
      </a>
    </div>"""
P1_NOW = """      <div class="alv-report-actions">
        {% if show_all %}
          <a href="{% url 'tenant_payment_days' %}" class="btn action-secondary">
            <i class="fas fa-user-check"></i> Current tenants only
          </a>
        {% else %}
          <a href="{% url 'tenant_payment_days' %}?all=1" class="btn action-secondary">
            <i class="fas fa-users"></i> Include past tenants
          </a>
        {% endif %}
        <a href="{% url 'tenant' %}" class="btn back-button" role="button">
          <i class="fas fa-arrow-left"></i> Back
        </a>
      </div>
    </div>"""

P2_WAS = """    <div class="pd-toolbar">
      {% if show_all %}
        <a href="{% url 'tenant_payment_days' %}" class="btn action-secondary">
          <i class="fas fa-user-check"></i> Current tenants only
        </a>
      {% else %}
        <a href="{% url 'tenant_payment_days' %}?all=1" class="btn action-secondary">
          <i class="fas fa-users"></i> Include past tenants
        </a>
      {% endif %}
"""
P2_NOW = """    {% if summary.no_measurement_yet or summary.missing_terms %}
    <div class="pd-toolbar">
"""

P3_WAS = """    <div class="alv-stats">
      <div class="alv-stat">
        <div class="alv-stat-value">{{ summary.payments_measured }}</div>
        <div class="alv-stat-label">payments measured</div>
      </div>
      <div class="alv-stat">
        <div class="alv-stat-value">{{ summary.tenants_measured }}</div>
        <div class="alv-stat-label">tenants with data</div>
      </div>"""
P3_NOW = """    <div class="alv-stats alv-stats-collapse">
      <div class="alv-stat alv-stat-more">
        <div class="alv-stat-value">{{ summary.payments_measured }}</div>
        <div class="alv-stat-label">payments measured</div>
      </div>
      <div class="alv-stat alv-stat-more">
        <div class="alv-stat-value">{{ summary.tenants_measured }}</div>
        <div class="alv-stat-label">tenants with data</div>
      </div>"""

# P2 opened an {% if %} around the toolbar; P4 closes it. Kept as a
# separate pair so the two halves are visible together rather than one
# being a detail of the other - the tag-balance gate below found this
# missing the first time the round was run.
P4_WAS = """      {% endif %}
    </div>

    {% if rows %}"""
P4_NOW = """      {% endif %}
    </div>
    {% endif %}

    {% if rows %}"""

PAGE_PAIRS = [(P1_WAS, P1_NOW), (P2_WAS, P2_NOW), (P3_WAS, P3_NOW),
              (P4_WAS, P4_NOW)]

# ==========================================================================
print('=' * 74)
print('SECTION T, ROUND T3 - PAYMENT BEHAVIOUR ON A PHONE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ---- base ---------------------------------------------------------------
p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if 'alv-stats-fold v1' in t:
    print('     already carries the row beside Back and the folding strip')
else:
    t = patch(p, t, BASE_PAIRS, 'base.html')
    print('     .alv-report-actions - a row for what sits beside Back')
    print('     .alv-stats-collapse - a summary strip that folds, opt-in')
    print('     alv-stats-fold v1   - the controller, and it writes the '
          'chevron')

    css = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S)), flags=re.S)
    js = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', t, re.S))
    # ONE RULE EACH, counted by the EXACT selector. A substring match
    # counts `.alv-stats-collapse.js-ready .alv-stats-more` as a hit for
    # `.alv-stats-more`, which is how the first version of this gate
    # found two of a rule there is one of.
    sels = {}
    for m in re.finditer(r'([^{}]+)\{([^}]*)\}', css):
        sels[' '.join(m.group(1).split())] = \
            sels.get(' '.join(m.group(1).split()), 0) + 1
    for sel, n in (
            ('.alv-report-actions', 2),
            ('.alv-stats-more', 1),
            ('.alv-stats-collapse.js-ready .alv-stat-more', 1),
            ('.alv-stats-collapse.js-ready.is-open .alv-stat-more', 1),
            ('.alv-stats-collapse.js-ready .alv-stats-more', 1)):
        got = sels.get(sel, 0)
        if got != n:
            raise SystemExit('T3: base declares %s %d time(s), not %d'
                             % (sel, got, n))
    phone = re.search(r'@media screen and \(max-width: 768px\)\s*\{'
                      r'((?:[^{}]|\{[^{}]*\})*?)\.alv-stats-collapse'
                      r'\.js-ready \.alv-stat-more', css, re.S)
    if not phone:
        raise SystemExit('T3: the fold is not inside the phone block')
    # THE HIDING IS CONDITIONAL ON THE SCRIPT. A rule that hid a tile
    # without .js-ready would hide data on a page with JavaScript off.
    for m in re.finditer(r'([^{}]*\.alv-stat-more[^{}]*)\{([^}]*)\}', css):
        if 'display: none' in m.group(2) and 'js-ready' not in m.group(1):
            raise SystemExit('T3: a tile is hidden without .js-ready: %s'
                             % ' '.join(m.group(1).split()))
    for must in ('alvStatsFold:', 'js-ready', "' more'", 'Show less',
                 'aria-expanded', 'sessionStorage'):
        if must not in js:
            raise SystemExit('T3: the controller does not mention %r' % must)
    # THE COUNT IS MEASURED, NOT TYPED.
    if not re.search(r'label\(row, more\.length,', js):
        raise SystemExit('T3: the chevron label is not written from the '
                         'number of tiles found')
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the page -----------------------------------------------------------
q = alv_tree.path_of(PAGE)
t2, raw2 = read(q)
print('  %s' % PAGE)
if 'alv-stats-collapse' in t2:
    print('     already folds, and the toggle is already beside Back')
else:
    t2 = patch(q, t2, PAGE_PAIRS, PAGE)
    print('     Include past tenants moves up beside Back, on both screens')
    print('     payments measured and tenants with data fold away on a phone')

    body = re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t2, flags=re.S), flags=re.S)
    # THE TOGGLE EXISTS ONCE. A move that left a copy behind would put
    # two of the same control on one page, and the second would be the
    # one nobody noticed.
    for label, n in (('Include past tenants', 1),
                     ('Current tenants only', 1),
                     ('class="btn back-button"', 1),
                     ('alv-report-actions', 1),
                     ('alv-stats-collapse', 1),
                     ('alv-stat-more', 2)):
        got = body.count(label)
        if got != n:
            raise SystemExit('T3: %s appears %d time(s) on the page, not %d'
                             % (label, got, n))
    # BACK IS INSIDE THE ROW, and the row is inside the head.
    if not re.search(r'<div class="alv-report-actions">(?:(?!</div>).)*?'
                     r'class="btn back-button"', body, re.S):
        raise SystemExit('T3: Back is not inside .alv-report-actions')
    i = body.find('alv-report-head')
    if not (0 <= i < body.find('alv-report-actions')):
        raise SystemExit('T3: the row is not inside the report head')
    # THE TOOLBAR IS GUARDED. With the toggle gone it can be empty, and
    # an empty div is a band of nothing above the table.
    if not re.search(r'\{% if summary\.no_measurement_yet or '
                     r'summary\.missing_terms %\}\s*<div class="pd-toolbar">',
                     t2):
        raise SystemExit('T3: .pd-toolbar is not guarded - it can now be '
                         'empty')
    # AND THE TAGS STILL BALANCE. Three edits in one template, two of
    # them moving a {% if %} - a stray endif is a 500, not a layout bug.
    for tag, close in (('if', 'endif'), ('for', 'endfor'),
                       ('block', 'endblock')):
        a = len(re.findall(r'\{%\s*' + tag + r'\b', t2))
        b = len(re.findall(r'\{%\s*' + close + r'\b', t2))
        if a != b:
            raise SystemExit('T3: %d {%% %s %%} against %d {%% %s %%}'
                             % (a, tag, b, close))
    if not CHECK:
        back_up(q, raw2)
        write(q, t2)

# ---- who does NOT fold --------------------------------------------------
print('  the other three .alv-stats pages, and none of them folds')
for rel in ('finance/financial_indicators.html',
            'finance/vacancy_management.html', 'fsr.html'):
    w = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(w):
        raise SystemExit('T3: %s is not where alv_tree says' % rel)
    txt = read(w)[0]
    # \balv-stat\b also matches alv-stat-value and alv-stat-label,
    # because \b sits happily before a hyphen - so three per tile. Ask
    # for the token and nothing hyphenated after it.
    n = len(re.findall(r'class="[^"]*\balv-stat(?![\w-])', txt))
    if 'alv-stats-collapse' in txt:
        raise SystemExit('T3: %s folds, and it was not asked to' % rel)
    print('     %-40s %d stats, not folded' % (rel, n))

print('-' * 74)
print('  the toggle is beside Back on both screens; on a phone the strip')
print('  shows average days to pay and flagged slow, with a chevron that')
print('  base writes for the other two.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
