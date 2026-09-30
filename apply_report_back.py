# -*- coding: utf-8 -*-
"""SECTION T, ROUND T1 - THE REPORT'S BACK BUTTON STOPS LOOKING LIKE A
PARAGRAPH

Demetri, testing on a phone, on four report screens in a row: "Back
button". Tenant Details, Outstanding Invoices, Lease Renewal, Tenant
Payment Behaviour - the same note each time, and he was right four
times.

THE STRUCTURE WAS NEVER WRONG. All four already sit inside
.alv-report-head with Back on the right, which is exactly what base's
standard 3.10 asks for. So does every one of the other four reports that
have a Back - eight in all.

IT IS ONE RULE IN base, AND IT ONLY BITES ON A PHONE.

    @media screen and (max-width: 768px) {
        .alv-report-head { flex-direction: column; align-items: stretch; }
        .alv-report-head > .btn { width: 100%; justify-content: center; }
    }

MEASURED at 390px, on tenant_report with its own stylesheet loaded:

    Back is 362px wide, centred, with a TRANSPARENT background and a
    TRANSPARENT border.

Back is the one control in this system that is deliberately borderless -
it is quiet on purpose, everywhere. Stretched to the full width of a
phone and centred, a borderless control stops reading as a control at
all: it is a line of centred text with an arrow in front of it, sitting
under the date. That is what the screenshots show, and it is why four
screens in a row drew the same note.

ON A DESKTOP IT IS FINE - 75px wide, on the right, exactly where Back
lives on every other screen. Nothing about the desktop changes here.

WHAT CHANGES. Back stops being stretched. It keeps its own width and
goes to the right of the column, which is where it sits on the desktop,
where it sits in every action bar, and where base's own phone rule for
an action bar puts it. Its 44px target is untouched - it already had
one, and this round measures that it still does.

    .alv-report-head > .btn.back-button,
    .alv-report-head > .btn.action-back { width: auto; align-self: flex-end; }

EIGHT PAGES, NO PAGE EDITS. Every one of the eight already writes the
markup base asks for, so not one template is touched. That is the whole
argument for a component owning its own rules.

Backups: .bak_reportback. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_reportback'
CRLF = {}

BASE = 'base.html'


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
            raise SystemExit('T1: %s is not a byte copy' % bak)


# ==========================================================================
WAS = """    .alv-report-head > .btn {
        width: 100%;
        justify-content: center;
        text-align: center;
        padding: 10px 12px;
    }"""

NOW = """    .alv-report-head > .btn {
        width: 100%;
        justify-content: center;
        text-align: center;
        padding: 10px 12px;
    }
    /* EXCEPT BACK - 30 Sep 2026. Demetri, testing on a phone, wrote
       "Back button" against four report screens in a row.

       The rule above stretches every button in the head to the full
       width and centres it, which is right for a headline figure and
       wrong for Back. Back is the one control in this system that is
       deliberately BORDERLESS - transparent background, transparent
       border, quiet on purpose. Measured at 390px it came out 362px
       wide, centred, and invisible: a line of centred text with an
       arrow in front of it, sitting under the date.

       So Back keeps its own width and goes to the right of the column -
       which is where it sits on a desktop, where it sits in every
       action bar, and where base's own phone rule for an action bar
       puts it. The 44px target is untouched.

       EIGHT REPORT PAGES, AND NOT ONE OF THEM IS EDITED. Every one
       already writes the markup 3.10 asks for.
                                             [test_report_back.py] */
    .alv-report-head > .btn.back-button,
    .alv-report-head > .btn.action-back {
        width: auto;
        align-self: flex-end;
    }"""

# ==========================================================================
print('=' * 74)
print('SECTION T, ROUND T1 - THE REPORT BACK STOPS BEING A PARAGRAPH%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if 'EXCEPT BACK' in t:
    print('     already leaves Back its own width')
else:
    a = eol(p, WAS)
    if t.count(a) != 1:
        raise SystemExit('T1: base - the report head phone rule is there '
                         '%d time(s), not 1' % t.count(a))
    t = t.replace(a, eol(p, NOW), 1)
    print('     Back keeps its width and goes right, on a phone only')

    # GATES.
    css = re.sub(r'/\*.*?\*/', '', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S)), flags=re.S)
    rule = re.search(r'\.alv-report-head > \.btn\.back-button,\s*'
                     r'\.alv-report-head > \.btn\.action-back\s*\{([^}]*)\}',
                     css)
    if not rule:
        raise SystemExit('T1: the new rule is not in base once')
    body = ' '.join(rule.group(1).split())
    for must in ('width: auto', 'align-self: flex-end'):
        if must not in body:
            raise SystemExit('T1: the new rule does not say %s: %s'
                             % (must, body))
    # IT MUST BE INSIDE THE PHONE BLOCK, or it changes the desktop too -
    # where Back is already 75px and on the right, and nothing is wrong.
    block = re.search(r'@media screen and \(max-width: 768px\)\s*\{'
                      r'(?:[^{}]|\{[^{}]*\})*?'
                      r'\.alv-report-head > \.btn\.back-button', css, re.S)
    if not block:
        raise SystemExit('T1: the new rule is not inside the phone block, '
                         'so it would reach the desktop')
    # AND NOTHING ELSE MOVED.
    def inert(s):
        s = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', s,
                   flags=re.S | re.I)
        s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
        return re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    before = inert(raw.decode('utf-8'))
    after = inert(t)
    added = [l for l in after.split('\n') if l.strip()
             and l not in before.split('\n')]
    if len(added) > 8:
        raise SystemExit('T1: %d lines of live code arrived, not the five '
                         'of one rule: %s' % (len(added), added[:4]))
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the eight it reaches, none of them edited --------------------------
eight = []
for q in alv_tree.templates():
    t2 = re.sub(r'<(script|style)\b.*?</\1>', '',
                re.sub(r'<!--.*?-->', '', read(q)[0], flags=re.S), flags=re.S)
    # INSIDE THE HEAD, not anywhere on the page. comments_report and
    # friday_status_report have a Back in their action bar, which this
    # rule does not touch and should not - the first version of this
    # census asked the whole page and found ten.
    i = t2.find('alv-report-head')
    if i < 0:
        continue
    j = t2.find('</div>', t2.find('alv-report-titles', i))
    head_block = t2[i:t2.find('<div', j) if t2.find('<div', j) > 0 else j + 400]
    if re.search(r'class="[^"]*\b(?:back-button|action-back)\b', head_block):
        eight.append(alv_tree.rel(q))
print('  the eight this reaches, and none of them is edited')
for rel in sorted(eight):
    print('     %s' % rel)
if len(eight) != 8:
    raise SystemExit('T1: %d report head(s) carry a Back, not 8: %s'
                     % (len(eight), sorted(eight)))

print('-' * 74)
print('  one rule in base, eight screens, no page edited - and Back goes')
print('  back to looking like a control.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
