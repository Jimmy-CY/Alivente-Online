#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""lease_renewal_report joins the card standard, and stops contradicting us.

WHY THIS ONE WAS URGENT. Every other item on the outstanding list was
inherited; this one WE caused. The Tenants push moved tenant_report to paint a
declined renewal AMBER - on the reasoning that a tenant declining to renew is
an answer, not a failure - while this page went on painting it RED. Two
screens, one fact, two colours, and our round is what made them disagree.

Decided 27 Aug: the SAME colour on both. Pending and Declined are both
`alv-pill-attn` here exactly as they are on tenant_report. They are then
visually identical and told apart by their label, which was raised as a real
cost on a page built for triaging renewals and accepted deliberately: one fact
having one colour is worth more than a page's scanning convenience.

Structurally this needs NOTHING invented. Each card has exactly three direct
children - a coloured status bar, an h3, and a details block - so the bar and
the h3 merge into `.alv-card-head` and the details block becomes
`.alv-card-body`. No div is created or destroyed.

WHAT CHANGES ON PAPER. The page currently forces its three bar colours to
print with `print-color-adjust: exact` and `!important`. Base governs printing,
and base turns a pill into an OUTLINE on paper rather than a filled block - so
the printed report gains outlined pills instead of solid colour bands. That is
a deliberate consequence of the plan's rule, not an oversight.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
PAGE  = os.path.join(ROOT, 'pages', 'templates', 'lease_renewal_report.html')
CHECK = '--check' in sys.argv


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:100]))


# Bar + heading become one head. The h3 SURVIVES - it is the card's heading and
# dropping it would cost the page its document outline to save a line.
CARDS = [
    ('tenant', 'pending', 'alv-pill-attn', 'fa-clock', 'Renewal pending',
     '{{ tenant.prop_name }}'),
    ('declined', 'declined', 'alv-pill-attn', 'fa-times-circle', 'Renewal declined',
     '{{ declined.prop_name }}'),
    ('vacant', 'vacant', 'alv-pill-neutral', 'fa-home', 'Vacant - needs new tenant',
     '{{ property.prop_name }}'),
]

OLD_HEAD = """<div class="card-status-bar status-bar-%s">
                        <i class="fas %s"></i> %s
                    </div>
                    <h3 class="property-name">%s</h3>"""

NEW_HEAD = """<div class="alv-card-head">
                        <h3 class="property-name">%s</h3>
                        <span class="alv-pill %s"><i class="fas %s"></i> %s</span>
                    </div>"""

LABELS = {'pending': 'RENEWAL PENDING',
          'declined': 'RENEWAL DECLINED',
          'vacant': 'VACANT - NEEDS NEW TENANT'}

# CSS the round removes outright, screen and print. Each of these styles a
# class that no longer exists - and a rule left behind after its class is
# renamed is the tenant_report trap: it goes on looking correct in the file
# while styling nothing at all.
DROP = ('.card-status-bar', '.status-bar-pending', '.status-bar-declined',
        '.status-bar-vacant')

# DECLARATION-level edits, not whole-rule replacements.
#
# `.renewal-card` appears THREE times with three different bodies - screen,
# mobile and print - and only some declarations are wrong in each. Replacing
# the body wherever the selector matched would have written the desktop
# 24px margin over the mobile 16px one and deleted the print page-break rule.
# The unit that is wrong here is the declaration, so that is what this names.
DECL_DROP = {
    # base's .alv-card supplies the border, radius and background now.
    #
    # `overflow` is here for a reason worth writing down. base sets
    # `overflow: clip` on .alv-card and says why in a comment: `hidden` makes
    # the card a scroll container, so a sticky heading inside one has nothing
    # to stick to. This page's `.renewal-card { overflow: hidden }` is the
    # same specificity as `.alv-card` (0,1,0) and its <style> comes AFTER
    # base's, so it WINS - the page would quietly reinstate the exact fault
    # base's comment describes. `background-color` and `box-shadow` are the
    # same story without the trap: base's card is flat with a bordered edge,
    # and a page keeping its own shadow is a card that does not match the
    # other cards in the system.
    '.renewal-card': ('padding', 'border', 'border-radius', 'background',
                      'background-color', 'box-shadow', 'overflow'),
    # the heading sits inside .alv-card-head, which supplies padding and a
    # rule of its own. Its own margin/underline would double them.
    '.property-name': ('margin', 'padding-bottom', 'border-bottom'),
    # base's head and body supply the horizontal padding these three were
    # standing in for.
    '.renewal-card .property-name, .renewal-card .card-message, '
    '.renewal-card .tenant-details': ('padding-left', 'padding-right'),
}

# Value swaps, applied wherever the selector appears.
DECL_SET = {
    # A declined renewal is no longer an error, so its message stops being
    # red. The pill carries the status; the paragraph is just text.
    '.card-message': {'color': 'var(--alv-ink)'},
    '.property-name': {'color': 'var(--alv-ink)'},
}

EXTRA_CSS = """
    /* base's .alv-card-head is `display:flex; gap:10px` - it does not space
       its children apart, because most heads are a title and nothing else.
       This page's head is a title AND a status, so the status is pushed to
       the far end here. Page-specific layout on a shared component: exactly
       what a page-local rule is for. */
    .renewal-card > .alv-card-head { justify-content: space-between; }
    .renewal-card > .alv-card-head .alv-pill { flex: 0 0 auto; }

    /* base greys every icon in a card head - `color: var(--alv-ink-faint)` -
       because an icon in a head is ornament. An icon INSIDE a pill is not
       ornament: it is part of the pill, and the pill's colour is the entire
       point of this round. Without this the clock renders grey inside an
       amber pill - which the browser check below caught and the file
       inspection did not, because nothing in the markup is wrong.
       This wins on SPECIFICITY - (0,4,1) against base's (0,3,1) - not on
       document order, so re-ordering the <style> blocks cannot grey it
       again. */
    .renewal-card > .alv-card-head > .alv-pill i.fas { color: inherit; }
"""


def edit_css(text):
    """Drop DROP outright; edit declarations in DECL_DROP / DECL_SET.

    A rule this leaves EMPTY is removed rather than written back as `sel {}`.
    Two of them would be: `.renewal-card .property-name, .renewal-card
    .card-message, .renewal-card .tenant-details` existed only to set the
    horizontal padding that base's head and body now supply, on screen and
    again on mobile. An empty rule is not harmless - it reads as a hook
    somebody deliberately left, and the next person to need one edits it
    instead of asking where the padding actually comes from. The match starts
    at the end of the PREVIOUS rule, so the comment sitting above it goes with
    it, which is right: `/* Card content (below status bar) */` describes a
    status bar this round deletes.
    """
    dropped = touched = emptied = 0
    missing = list(DROP)
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
        css = text[a:z]
        out, cur = [], 0
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
            if sel in DROP:
                out.append(css[cur:m.start()]); cur = m.end(); dropped += 1
                if sel in missing:
                    missing.remove(sel)
                continue
            if sel not in DECL_DROP and sel not in DECL_SET:
                continue
            body = m.group(2)
            before = body
            for prop in DECL_DROP.get(sel, ()):
                # `padding` must not eat `padding-bottom`, and `border` must
                # not eat `border-radius`: anchor on the colon.
                body = re.sub(r'(?:^|;)\s*%s\s*:[^;}]*;?' % re.escape(prop),
                              ';', body, flags=re.I)
            for prop, val in DECL_SET.get(sel, {}).items():
                body = re.sub(r'(%s\s*:\s*)[^;}]*' % re.escape(prop),
                              r'\g<1>' + val, body, flags=re.I)
            body = re.sub(r';\s*;', ';', body)
            body = re.sub(r'^(\s*);', r'\1', body)
            if body != before:
                out.append(css[cur:m.start()])
                if body.strip().strip(';'):
                    out.append('%s{%s}' % (m.group(1), body))
                    touched += 1
                else:
                    emptied += 1
                cur = m.end()
        if out:
            out.append(css[cur:])
            text = text[:a] + ''.join(out) + text[z:]
    if missing:
        sys.exit('! these rules were expected and not found: %s'
                 % ', '.join(missing))
    # .highlight-red onto the token, as tenant_report did. NOT dropped - base
    # does not own that selector, and a rule nothing replaces must never go.
    # The dates it marks really are overdue, so it stays red.
    text = re.sub(r'(\.highlight-red\s*\{[^}]*?)#dc3545', r'\1var(--alv-bad)', text)
    return text, dropped, touched, emptied


def patch(text):
    n = 0
    # -- the three cards
    for key, state, pill, icon, label, name in CARDS:
        old = OLD_HEAD % (state, icon, LABELS[state], name)
        if old not in text:
            if 'alv-card-head' in text:
                continue
            sys.exit('! the %s card head was not found as expected' % state)
        one(text, old, 'the %s card head' % state)
        text = text.replace(old, NEW_HEAD % (name, pill, icon, label), 1)
        n += 1

    # -- the card wrapper joins base's. ADD the name, never swap it: every
    #    page rule keyed to .renewal-card has to keep working.
    for cls in ('renewal-card tenant-card', 'renewal-card declined-renewal-card',
                'renewal-card vacant-property-card'):
        old = '<div class="%s">' % cls
        if old not in text:
            continue
        one(text, old, cls)
        text = text.replace(old, '<div class="alv-card %s">' % cls, 1)
        n += 1

    # -- THE DECLINED CARD HAS FOUR CHILDREN, not three: a <p class=
    #    "card-message"> sits between the heading and the details. Left where
    #    it is, it ends up between the head and the body - belonging to
    #    neither - and loses the horizontal padding those two now supply. So
    #    it moves INSIDE the body. Nothing is created or destroyed; the <p>
    #    changes parent.
    old = ('<p class="card-message">{{ declined.message }}</p>\n'
           '                    <div class="tenant-details">')
    if old in text:
        one(text, old, 'the declined card message')
        text = text.replace(
            old,
            '<div class="alv-card-body tenant-details">\n'
            '                        <p class="card-message">'
            '{{ declined.message }}</p>', 1)
        n += 1

    # -- the remaining details block IS the body. Naming it beside its own
    #    class means no div is created, so nothing can be left unclosed.
    old = '<div class="tenant-details">'
    c = text.count(old)
    if c:
        text = text.replace(old, '<div class="alv-card-body tenant-details">')
        n += c

    text, dropped, renamed, emptied = edit_css(text)

    i = text.rfind('</style>')
    if i < 0:
        sys.exit('! no </style> to append the head-layout rule to')
    text = text[:i] + EXTRA_CSS + text[i:]
    return text, n, dropped, renamed, emptied


def counts(t):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))
    return dict(divs=len(re.findall(r'<div\b', t)),
                closes=len(re.findall(r'</div\s*>', t)),
                h3=len(re.findall(r'<h3\b', t)),
                ifs=len(re.findall(r'\{%\s*if\b', t)),
                endifs=len(re.findall(r'\{%\s*endif\s*%\}', t)),
                fors=len(re.findall(r'\{%\s*for\b', t)),
                endfors=len(re.findall(r'\{%\s*endfor\s*%\}', t)),
                urls=len(re.findall(r'\{%\s*url ', t)),
                co=css.count('{'), cc=css.count('}'))


def main():
    src = read(PAGE)
    if 'alv-card-head' in src:
        print('  lease_renewal_report.html   already migrated')
        print('\n  0 file(s) changed')
        return
    out, n, dropped, renamed, emptied = patch(src)

    b, a = counts(src), counts(out)
    bad = []
    # NOTHING is created or destroyed: the bar div becomes the head div, the
    # details div gains a name. If these move, the merge went wrong.
    for k in ('divs', 'closes', 'h3', 'ifs', 'endifs', 'fors', 'endfors', 'urls'):
        if b[k] != a[k]:
            bad.append('%s changed %d -> %d' % (k, b[k], a[k]))
    if a['ifs'] != a['endifs'] or a['fors'] != a['endfors']:
        bad.append('template tags do not balance')
    if a['co'] != a['cc']:
        bad.append('CSS braces do not balance (%d/%d)' % (a['co'], a['cc']))
    for dead in ('card-status-bar', 'status-bar-pending', 'status-bar-declined',
                 'status-bar-vacant'):
        if dead in out:
            bad.append('%s survived somewhere' % dead)
    # THE POINT OF THE ROUND. Declined must wear the same pill as pending, or
    # the two pages disagree again and nothing was fixed.
    _pills = re.findall(r'<span class="alv-pill (alv-pill-\w+)">', out)
    if _pills[:2] != ['alv-pill-attn', 'alv-pill-attn']:
        bad.append('pending and declined do not wear the same pill: %s' % _pills)
    if len(_pills) != 3 or _pills[2] != 'alv-pill-neutral':
        bad.append('expected three pills ending in neutral, got %s' % _pills)
    if '#dc3545' in out:
        bad.append('a Bootstrap red survived: %s'
                   % [l.strip()[:60] for l in out.splitlines() if '#dc3545' in l][:2])
    # the declined message must sit INSIDE the body, not between head and body
    _b = out.find('<div class="alv-card-body tenant-details">')
    _m = out.find('<p class="card-message">')
    if _m > 0 and not (0 < _b < _m):
        bad.append('the declined message is not inside a card body')
    # and every card must have a head
    # count the ELEMENT, not the string - the head is named in this page's
    # own CSS too, and the first version of this check counted those.
    _heads = len(re.findall(r'<div class="alv-card-head">', out))
    if _heads != 3:
        bad.append('expected three card heads in the markup, found %d' % _heads)
    if bad:
        sys.exit('! lease_renewal_report.html self-check FAILED, nothing '
                 'written:\n   - %s' % '\n   - '.join(bad))

    print('  lease_renewal_report.html   markup:%d  rules dropped:%d  '
          'rewritten:%d  emptied and removed:%d' % (n, dropped, renamed, emptied))
    print('     pending and declined now wear the SAME pill, as tenant_report does')
    if not CHECK:
        bak = PAGE + '.bak_leaserenewal'
        if not os.path.exists(bak):
            shutil.copy2(PAGE, bak)
        with open(PAGE, 'w', encoding='utf-8') as f:
            f.write(out)
    print('\n  1 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
