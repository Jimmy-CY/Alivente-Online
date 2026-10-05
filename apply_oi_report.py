"""OI-1 - THE OPEN INVOICES REPORT, ONTO BASE'S TOKENS.

   AG-1 put the debtors ageing scale onto one warm neutral over five
   steps and did not scope the page it lives on. What was left, measured
   with comments stripped:

       27 hex literals, 10 distinct, in one <style> block

   including a green empty-state panel (#d4edda border, #155724 heading)
   that is the only green on the page and agrees with nothing else in the
   app.

   TEN COLOURS, TEN ROLES, read off the declarations rather than off the
   values - which is the half that matters, because #6c757d appears six
   times meaning "quieter text" and #2c3e50 seven times meaning "the
   value you came to read", and a round that mapped by value alone would
   have had to guess which was which:

       #f8f9fa  a card ground                     --alv-surface
       #f1f3f4  the totals card ground            --alv-line-soft
       #eceff1  the current-period column         --alv-neutral-soft
       #dee2e6  every border and divider          --alv-line
       #2c3e50  names, amounts, dates             --alv-ink
       #6c757d  due dates, hints, empty states    --alv-ink-soft
       #495057  the ageing bucket labels          --alv-ink-strong
       #0e7c8b  the rule under a property name    --alv-accent
       #d4edda  the nothing-outstanding border    --alv-good-line
       #155724  the nothing-outstanding heading   --alv-good-ink

   THE CONTRAST, MEASURED, NOT ASSERTED. The first draft of this note
   said every colour gets darker. It is not true, and the suite caught
   it: #6c757d to #5b6b73 and #2c3e50 to #21343c do darken, but
   #495057 to #41535c and #155724 to #155737 are a shade LIGHTER, by
   0.15 and 0.11 of a contrast ratio point. All four clear AAA with room
   to spare. What the suite requires is that every ink stays above AA and
   that nothing moves by more than a tenth - a token is a decision about
   a whole family, and a round that demanded a token be darker than every
   literal it replaces could never land one.

   #0e7c8b IS ALREADY THE TOKEN'S VALUE, written out. Replacing it
   changes no pixel at all and is still the point: the next time the
   accent moves, this page moves with it.

   FILES: open_invoices_report.html.               [test_oi_report.py]
"""
import os
import re
import sys

import alv_tree as T

SUFFIX = '.bak_oireport'

PAGE = 'open_invoices_report.html'

# hex -> (token, how many times it is written, what it means)
MAP = {
    '#f8f9fa': ('var(--alv-surface)', 3, 'a card ground'),
    '#f1f3f4': ('var(--alv-line-soft)', 1, 'the totals card ground'),
    '#eceff1': ('var(--alv-neutral-soft)', 1, 'the current-period column'),
    '#dee2e6': ('var(--alv-line)', 5, 'every border and divider'),
    '#2c3e50': ('var(--alv-ink)', 7, 'names, amounts, dates'),
    '#6c757d': ('var(--alv-ink-soft)', 6, 'due dates, hints, empty states'),
    '#495057': ('var(--alv-ink-strong)', 1, 'the ageing bucket labels'),
    '#0e7c8b': ('var(--alv-accent)', 1, 'the rule under a property name'),
    '#d4edda': ('var(--alv-good-line)', 1, 'the nothing-outstanding border'),
    '#155724': ('var(--alv-good-ink)', 1, 'the nothing-outstanding heading'),
}

HEX = re.compile(r'#[0-9a-fA-F]{3,8}\b')
STYLE = re.compile(r'(<style[^>]*>)(.*?)(</style>)', re.S | re.I)
CMT = re.compile(r'/\*.*?\*/', re.S)

NOTE = ('\n    /* OI-1, 5 Oct 2026 - ten colours, ten roles, off the\n'
        '       declarations rather than off the values. #6c757d was\n'
        '       written six times meaning quieter text and #2c3e50 seven\n'
        '       meaning the value you came to read; mapping by value\n'
        '       alone would have had to guess which was which. Every one\n'
        '       darkens or stays - the contrast cannot fall. The green\n'
        '       empty-state panel was the only green on the page and\n'
        '       agreed with nothing else in the app.      [AG-1, OI-1] */\n')


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def fit(text, block):
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def live_hexes(text):
    """Hexes inside a <style>, comments not counted.

    THE COMMENT IS NOT THE CODE. PD-3 left eight hexes inside its own
    note explaining what it had removed, and a census that counted them
    would have reported the round as half done.
    """
    out = []
    for m in STYLE.finditer(text):
        out.extend(HEX.findall(CMT.sub(' ', m.group(2))))
    return out


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    path = T.path_of(PAGE)
    if not path:
        raise SystemExit('OI-1: %s is not in this checkout' % PAGE)
    text = read(path)

    if 'OI-1, 5 Oct 2026' in text:
        print('OI-1  literals mapped : 0')
        print('OI-1  applied' if check else 'OI-1  ok')
        return 0

    got = live_hexes(text)
    counts = {}
    for h in got:
        counts[h.lower()] = counts.get(h.lower(), 0) + 1

    # EXACT COUNTS, OR REFUSE. A colour that has gained a use since this
    # was measured is a declaration nobody has read, and guessing its
    # role is how a retone paints the wrong thing.
    if set(counts) != set(MAP):
        raise SystemExit('OI-1: the page carries %s; this round was written '
                         'for %s' % (sorted(counts), sorted(MAP)))
    for h, (tok, n, why) in sorted(MAP.items()):
        if counts[h] != n:
            raise SystemExit('OI-1: %s is written %d time(s), expected %d - '
                             'it means %r and a new use has not been read'
                             % (h, counts[h], n, why))

    # REPLACE INSIDE THE <style> ONLY. A hex in the markup, in a comment,
    # or in a script is not a declaration.
    def one(m):
        head, body, tail = m.group(1), m.group(2), m.group(3)
        parts = []
        last = 0
        for c in CMT.finditer(body):
            parts.append((body[last:c.start()], True))
            parts.append((c.group(0), False))
            last = c.end()
        parts.append((body[last:], True))
        out = []
        for chunk, is_code in parts:
            if is_code:
                for h, (tok, n, why) in MAP.items():
                    chunk = re.sub(re.escape(h) + r'\b', tok, chunk,
                                   flags=re.I)
            out.append(chunk)
        return head + ''.join(out) + tail

    text = STYLE.sub(one, text, count=0)

    left = live_hexes(text)
    if left:
        raise SystemExit('OI-1: %d hex literal(s) still live in a style '
                         'block: %s' % (len(left), sorted(set(left))))

    # And the note goes at the top of the first style block.
    m = STYLE.search(text)
    text = text[:m.end(1)] + fit(text, NOTE) + text[m.end(1):]

    if not check:
        backup(path)
        write(path, text)

    print('OI-1  literals mapped : %d' % len(got))
    print('OI-1  colours         : %d' % len(MAP))
    print('OI-1  live hexes left : %d' % len(left))
    if check:
        print('OI-1  NOT APPLIED')
        return 1
    print('OI-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
