# -*- coding: utf-8 -*-
"""SECTION D, ROUND D1 - THE PROPERTY DASHBOARD BUTTON BECOMES BACK

Demetri: "On the Dashboard, can we make all the Property Dashboard
buttons, Back Buttons and ensure that they comply with our standards."

TWO PAGES CARRY ONE, AND NEITHER HAS A BACK AT ALL.

    property_detail.html    <a class="btn action-secondary">
                              <i class="fas fa-home"></i> Property Dashboard
    dashboard_pl.html       the same anchor, the same classes

Both sit in a hand-rolled header row - one a bare <div>, the other
.page-header-actions - and neither page has a .page-action-buttons bar
or a Back anywhere on it. So the control that takes you back off these
two screens has been a secondary action with a house icon, in a wrapper
base has never heard of.

IT IS ALREADY A BACK. The href goes to the property management dashboard,
which is the screen you came from - that is the definition of Back. It
was only ever dressed as something else.

WHAT CHANGES, AND WHY THE WRAPPER HAS TO CHANGE TOO. base styles
.action-back ONLY inside .page-action-buttons - every geometry rule it
has is scoped that way, and the standalone hover is all that reaches
outside. Putting .action-back on the anchor and leaving it in a bare
<div> would give it the colour and none of the shape. So each anchor
gets the house Back, and the div around it becomes the house bar:

    <div class="page-action-buttons page-action-buttons-single">
      <a class="btn action-back"><i class="fas fa-arrow-left"></i>
         <span class="action-back-label"> Back</span></a>

`-single` is the modifier for a bar holding nothing but Back - it is what
pushes a solitary Back to the right, which is where it sits on every
other screen. property_detail keeps .page-header-actions alongside,
because that class carries a flex-shrink its header row depends on.

THE LABEL. It says Back now, not Property Dashboard. That is the point
of the request - every Back in this system says Back, and the label is
hidden below 768px anyway so the button is a 44px square. The
destination has not changed by one character.

Backups: .bak_dashback. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_dashback'
CRLF = {}

PAGES = ('property_detail.html', 'dashboard_pl.html')


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
            raise SystemExit('D1: %s is not a byte copy' % bak)


# ==========================================================================
ANCHOR_WAS = """<a href="{% url 'property_management_dashboard' %}?property={{ property.prop_id }}" class="btn action-secondary">
                        <i class="fas fa-home"></i> Property Dashboard
                    </a>"""
ANCHOR_NOW = """<a href="{% url 'property_management_dashboard' %}?property={{ property.prop_id }}" class="btn action-back" role="button" aria-label="Back to the property dashboard">
                        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
                    </a>"""

# Each page's wrapper, exactly as it stands. property_detail keeps
# .page-header-actions - it carries a flex-shrink its header relies on.
# property_detail ALSO stretches Back across the phone, which is the
# very defect T1 removed from the report heads - and this round is what
# makes it bite, because the wrapper held no Back until now. Equal
# specificity to base's 44px rule and a later stylesheet, so the page
# wins and Back comes out 390px wide. The wrapper holds nothing but
# Back once this round has run, so the rule's whole effect is on Back
# and it is wrong for Back.
STRETCH = {
    'property_detail.html': (
        """    .page-header-actions .btn {
        width: 100%;
        text-align: center;
        padding: 10px 16px;
    }
""",
        """    /* The .page-header-actions .btn rule that was here stretched
       every button in this header to the full width of the phone. The
       header now holds nothing but Back, and a Back the width of a
       phone is what T1 spent a round removing from the report heads -
       base already makes it a 44px square here. 30 Sep 2026.
                                            [test_dash_back.py] */
"""),
}

WRAP = {
    'property_detail.html': (
        '<div class="page-header-actions">',
        '<div class="page-header-actions page-action-buttons '
        'page-action-buttons-single">'),
    'dashboard_pl.html': (
        """<div>
                    <a href="{% url 'property_management_dashboard' %}""",
        """<div class="page-action-buttons page-action-buttons-single">
                    <a href="{% url 'property_management_dashboard' %}"""),
}

# ==========================================================================
print('=' * 74)
print('SECTION D, ROUND D1 - THE PROPERTY DASHBOARD BUTTON BECOMES BACK%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

EDITED = {}

for rel in PAGES:
    p = alv_tree.path_of(rel)
    t, raw = read(p)
    print('  %s' % rel)
    if 'action-back' in t:
        print('     already carries the house Back')
        continue

    # ---- the wrapper --------------------------------------------------
    w_was, w_now = WRAP[rel]
    a = eol(p, w_was)
    if t.count(a) != 1:
        raise SystemExit('D1: %s - the wrapper is there %d time(s), not 1'
                         % (rel, t.count(a)))
    t = t.replace(a, eol(p, w_now), 1)

    # ---- the anchor ---------------------------------------------------
    b = eol(p, ANCHOR_WAS)
    if t.count(b) != 1:
        raise SystemExit('D1: %s - the Property Dashboard anchor is there '
                         '%d time(s), not 1' % (rel, t.count(b)))
    t = t.replace(b, eol(p, ANCHOR_NOW), 1)
    print('     the house Back, inside the house bar')

    if rel in STRETCH:
        s_was, s_now = STRETCH[rel]
        c = eol(p, s_was)
        if t.count(c) != 1:
            raise SystemExit('D1: %s - the stretch rule is there %d time(s), '
                             'not 1' % (rel, t.count(c)))
        t = t.replace(c, eol(p, s_now), 1)
        print('     and the rule that stretched it across the phone goes')

    # ---- GATES ---------------------------------------------------------
    mk = re.sub(r'<(script|style)\b.*?</\1>', '',
                re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)
    # COUNTED AS TOKENS, NOT SUBSTRINGS. page-action-buttons-single
    # contains page-action-buttons, so a plain count found two of a
    # class there is one of - the same trap D3 and T4 each hit once.
    def tokens(name, hay):
        return len(re.findall(re.escape(name) + r'(?![\w-])', hay))
    # THE BAR ONLY. property_detail has four other .action-secondary
    # buttons, all legitimate and none of them this round's business -
    # the first version of this gate asked the whole page and failed on
    # buttons it had never touched.
    bm = re.search(r'<div class="[^"]*page-action-buttons[^"]*">'
                   r'(?:(?!</div>).)*?</a>', mk, re.S)
    if not bm:
        raise SystemExit('D1: %s - the bar could not be located' % rel)
    bar = bm.group(0)
    for name, n in (('action-back', 1), ('action-back-label', 1),
                    ('fa-arrow-left', 1), ('page-action-buttons', 1),
                    ('page-action-buttons-single', 1),
                    ('action-secondary', 0), ('fa-home', 0)):
        got = tokens(name, bar)
        if got != n:
            raise SystemExit('D1: %s - %s appears %d time(s) in the bar, '
                             'not %d' % (rel, name, got, n))
    # AND THE OLD LABEL IS GONE FROM THE PAGE ENTIRELY.
    if 'Property Dashboard' in mk:
        raise SystemExit('D1: %s still says Property Dashboard' % rel)
    # THE BACK IS INSIDE THE BAR. base scopes every geometry rule it has
    # to .page-action-buttons; outside it the button gets the colour and
    # none of the shape.
    if not re.search(r'<div class="[^"]*page-action-buttons[^"]*">'
                     r'(?:(?!</div>).)*?class="btn action-back"', mk, re.S):
        raise SystemExit('D1: %s - Back is not inside the bar' % rel)
    # THE DESTINATION IS UNTOUCHED.
    was_href = re.search(r"href=\"(\{% url 'property_management_dashboard'"
                         r"[^\"]*)\"", raw.decode('utf-8'))
    now_href = re.search(r"href=\"(\{% url 'property_management_dashboard'"
                         r"[^\"]*)\"", t)
    if not (was_href and now_href
            and was_href.group(1) == now_href.group(1)):
        raise SystemExit('D1: %s - the destination changed' % rel)
    # AND THE PAGE WRITES NO RULE base OWNS.
    css = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S)), flags=re.S)
    own = re.findall(r'(?m)^[ \t]*[^{}\n]*\.(?:page-action-buttons|'
                     r'action-back)[a-zA-Z-]*[^{}\n]*\{', css)
    if own:
        raise SystemExit('D1: %s writes %d rule(s) base owns: %s'
                         % (rel, len(own), [x.strip() for x in own[:2]]))
    # AND NOTHING ON THE PAGE MAY SET A WIDTH ON A BUTTON IN THAT BAR.
    for m2 in re.finditer(r'([^{}]*page-header-actions[^{}]*)\{([^}]*)\}',
                          css):
        if '.btn' in m2.group(1) and re.search(r'\bwidth\s*:', m2.group(2)):
            raise SystemExit('D1: %s still sets a width on a button in the '
                             'header bar: %s'
                             % (rel, ' '.join(m2.group(1).split())))
    # DJANGO STILL BALANCES.
    for tag, close in (('if', 'endif'), ('for', 'endfor'),
                       ('block', 'endblock')):
        x = len(re.findall(r'\{%\s*' + tag + r'\b', t))
        y = len(re.findall(r'\{%\s*' + close + r'\b', t))
        if x != y:
            raise SystemExit('D1: %s - %d {%% %s %%} against %d {%% %s %%}'
                             % (rel, x, tag, y, close))
    EDITED[alv_tree.rel(p)] = t
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- nobody else calls a navigation control Property Dashboard ----------
print('  and nowhere else in the tree still labels one that way')
left = []
for q in alv_tree.templates():
    # THE EDITED TEXT, NOT THE FILE. With --check nothing has been
    # written, so reading from disk finds the button this round has
    # just removed and reports a failure that is only the check mode.
    src = EDITED.get(alv_tree.rel(q)) or read(q)[0]
    txt = re.sub(r'<(script|style)\b.*?</\1>', '',
                 re.sub(r'<!--.*?-->', '', src, flags=re.S), flags=re.S)
    if re.search(r'<a[^>]*>(?:(?!</a>).)*?Property Dashboard'
                 r'(?:(?!</a>).)*?</a>', txt, re.S):
        left.append(alv_tree.rel(q))
if left:
    raise SystemExit('D1: %d page(s) still carry the old button: %s'
                     % (len(left), left))
print('     none')

print('-' * 74)
print('  two screens that had no Back now have the same Back as every')
print('  other screen, going to exactly where they went before.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
