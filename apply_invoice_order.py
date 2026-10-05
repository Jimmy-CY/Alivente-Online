"""RA-4 - THE ORDER RA-3b MADE READABLE, PUT RIGHT.

   RA-3b wrapped the ten form-shaped buttons on three pages, and the
   drift report - able to read those groups for the first time - said:

       OUT OF ORDER
         physical_invoice_list.html
           approve -> unapprove -> send -> duplicate -> delete -> pdf
         should read
           pdf -> duplicate -> approve -> unapprove -> send -> delete

   IT IS REAL, NOT AN ARTEFACT, and that had to be checked before
   touching anything. Those six controls sit in mutually exclusive
   {% if %} branches and the report reads SOURCE order, so the question
   is which can appear together on one row:

       a DRAFT customer invoice      approve, duplicate, delete, pdf
       an APPROVED customer invoice  unapprove, send, duplicate, pdf

   Four controls at once, both times. In both the PDF is last and Delete
   comes before it. The house order is

       LOOK -> CHANGE -> COPY -> ADVANCE -> DESTROY

   so the PDF, the only LOOK, belongs first, and Delete, the only
   DESTROY, belongs last. The report was right about a thing a user sees.

   FIVE BLOCKS, REORDERED, NOTHING REWRITTEN. The cell holds five
   top-level blocks - the approve/unapprove pair, send, duplicate,
   delete, and the PDF link. Each moves whole: not one character inside
   any of them changes, including the confirm() texts and the hidden
   `next` inputs. The round is a permutation, which is the only kind of
   reordering that can be checked by comparing sorted contents.

   THE PAIR STAYS A PAIR. approve and unapprove are one {% if %} with an
   {% elif %}, and they are the same step of the sequence seen from
   either side of it. Splitting them to put approve and unapprove in
   different places would be reading the house order as a list of
   buttons rather than a list of stages.

   FILES: physical_invoice_list.html.          [test_invoice_order.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_rowactions as RA

SUFFIX = '.bak_invorder'

PAGE = 'physical_invoice_list.html'
CELL = 'pi-actions-cell'

# The icon each block leads with, in the order the house asks for.
WANT = ['icon-pdf', 'icon-duplicate', 'icon-approve', 'icon-send',
        'icon-delete']


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


def page():
    hits = [p for p in T.templates()
            if T.rel(p).replace(os.sep, '/') == PAGE]
    if len(hits) != 1:
        raise SystemExit('RA-4: %s matched %d templates' % (PAGE, len(hits)))
    return hits[0]


IF = re.compile(r'\{%\s*if\b[^%]*%\}')
END = re.compile(r'\{%\s*endif\s*%\}')
LINK = re.compile(r'<a\b[^>]*>[\s\S]*?</a>')


def blocks(inner):
    """The cell's top-level blocks, in the order they are written.

    A top-level {% if %} and everything to its matching {% endif %},
    nesting-aware - the approve/unapprove pair is an {% if %} with an
    {% elif %} inside the outer permission check, and a non-greedy regex
    would close it on the wrong one.

    THE PREFIX IS NOT PART OF THE FIRST BLOCK, and the first build of
    this round got that wrong. RA-3b put a <span class="row-actions">
    immediately inside this cell, so the text before the first {% if %}
    is the wrapper's OPENING TAG. Letting it ride with the block that
    follows meant moving that block moved the wrapper with it - the PDF
    and duplicate ended up outside it, and the drift report went from
    reporting six actions to four plus two unwrapped.

    It passed every gate the round had, because it IS a permutation of
    the characters: same length, same blocks, same sorted contents. The
    length check cannot see a tag that moved. So the prefix is returned
    separately and never moves.
    """
    out = []
    first = IF.search(inner)
    a0 = LINK.search(inner)
    at = min([x.start() for x in (first, a0) if x] or [0])
    prefix = inner[:at]
    i = at
    while True:
        m = IF.search(inner, i)
        a = LINK.search(inner, i)
        if not m and not a:
            break
        if m and (not a or m.start() < a.start()):
            depth = 1
            j = m.end()
            while depth:
                nxt_if = IF.search(inner, j)
                nxt_end = END.search(inner, j)
                if not nxt_end:
                    raise SystemExit('RA-4: an {% if %} in the cell never '
                                     'closes')
                if nxt_if and nxt_if.start() < nxt_end.start():
                    depth += 1
                    j = nxt_if.end()
                else:
                    depth -= 1
                    j = nxt_end.end()
            out.append((i, j))
            i = j
        else:
            out.append((i, a.end()))
            i = a.end()
    return prefix, out


def lead_icon(seg):
    names = [c for c in re.findall(r'\bicon-[\w-]+', seg)
             if c not in ('icon-action-btn', 'icon-disabled')]
    return names[0] if names else None


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    path = page()
    text = read(path)

    i = text.index(CELL)
    start = text.index('>', i) + 1
    end = text.find('</td>', start)
    if end < 0:
        raise SystemExit('RA-4: the action cell never closes')
    inner = text[start:end]

    prefix, spans = blocks(inner)
    segs = [inner[a:b] for a, b in spans]
    tail = inner[spans[-1][1]:] if spans else inner

    got = [lead_icon(s) for s in segs]
    if len(segs) != len(WANT) or sorted(filter(None, got)) != sorted(WANT):
        raise SystemExit(
            'RA-4: the cell holds %d block(s) leading with %s; expected %d '
            'leading with %s. The page has changed since this was measured.'
            % (len(segs), got, len(WANT), WANT))

    if got == WANT:
        print('RA-4  blocks moved : 0')
        print('RA-4  applied' if check else 'RA-4  ok')
        return 0

    order = [got.index(name) for name in WANT]
    new_inner = prefix + ''.join(segs[k] for k in order) + tail

    # A PERMUTATION, AND THE ROUND PROVES IT IS ONE. Same blocks, same
    # bytes, different order - so the sorted contents must be identical.
    if sorted(segs) != sorted(inner[a:b] for a, b in spans):
        raise SystemExit('RA-4: the blocks changed, which this round does '
                         'not do')
    if len(new_inner) != len(inner):
        raise SystemExit('RA-4: the cell changed length - %d to %d - so '
                         'something was lost or gained'
                         % (len(inner), len(new_inner)))
    # AND EVERY BUTTON IS STILL INSIDE THE WRAPPER. The length check
    # cannot see a tag that merely moved, which is exactly how the first
    # build shipped the PDF and duplicate out of the group.
    probe = text[:start] + new_inner + text[end:]
    wraps = RA.wrappers(probe)
    held = max([len(RA.BTN_FULL.findall(w[2])) for w in wraps] or [0])
    if held != len(WANT) + 1:
        raise SystemExit('RA-4: after reordering the wrapper holds %d icon '
                         'control(s), not the %d it held before - a tag has '
                         'moved' % (held, len(WANT) + 1))

    text = text[:start] + new_inner + text[end:]
    if not check:
        backup(path)
        write(path, text)

    print('RA-4  blocks moved : %d' % sum(1 for k, n in enumerate(order)
                                          if k != n))
    if check:
        print('RA-4  NOT APPLIED')
        return 1
    print('RA-4  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
