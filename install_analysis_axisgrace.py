#!/usr/bin/env python
"""
install_analysis_axisgrace.py  --  stop the "Expenses vs Rent - Analysis" scatter
chart from clipping dots that sit at 0% surprise-cost.

Problem: the Analysis scatter (the modal with the four quadrants, DANGER line and
"Surprise (ad-hoc) costs as % of rent" y-axis) hardcodes its y-scale to start at
zero (`y:{ min:0 }`). Any property with 0% surprise costs plots exactly on the
bottom axis, so its dot is sliced in half by the chart edge.

Fix: drop the y-axis floor to one tick-step below zero. `axisBounds()` already
computes `ystep`; we return `ymin:-ystep` and feed it into the y-scale as
`min:b.ymin`. Zero stays on a gridline (min is a whole multiple of the step), the
quadrant background plugin fills from `chartArea` so the coloured zones simply
extend down to the new floor with no blank strip, and 0%-cost dots now sit a full
step above the edge, fully visible.

This is the Analysis SCATTER chart only. It does NOT touch:
  * the indexAxis:'y' report bar chart (beginAtZero) higher up in the file, or
  * the Financial Indicators trend line chart (that one got grace:'10%' already).

Edits one file (backup act_expense.html.bak_analysisaxis):
  * pages/templates/act_expense.html
      - axisBounds() return  : add  ymin:-ystep
      - scatter y-scale      : min:0  ->  min:b.ymin

SAFE: idempotent; exact-anchor (each anchor verified unique); preserves CRLF/LF;
JS brace-balance sanity check; --dry-run. No migration. Template only.

    python install_analysis_axisgrace.py --dry-run
    python install_analysis_axisgrace.py
Then restart the dev server (or redeploy), open the Analysis modal, and the
0%-cost dots sit clear of the bottom axis.
"""
import base64, os, sys

DRY = '--dry-run' in sys.argv

OLD_RET = "cmV0dXJuIHsgeG1pbjp4bWluLCB4bWF4OnhtYXgsIHltYXg6eW1heCwgeHN0ZXA6eHN0ZXAsIHlzdGVwOnlzdGVwIH07"
NEW_RET = "cmV0dXJuIHsgeG1pbjp4bWluLCB4bWF4OnhtYXgsIHltYXg6eW1heCwgeW1pbjoteXN0ZXAsIHhzdGVwOnhzdGVwLCB5c3RlcDp5c3RlcCB9Ow=="
OLD_Y   = "eTp7IG1pbjowLCBtYXg6Yi55bWF4LCB0aXRsZTp7ZGlzcGxheTp0cnVlLCB0ZXh0OidTdXJwcmlzZSAoYWQtaG9jKSBjb3N0cyBhcyAlIG9mIHJlbnQnfSwgdGlja3M6eyBzdGVwU2l6ZTpiLnlzdGVwLCBjYWxsYmFjazpmdW5jdGlvbih2KXsgcmV0dXJuIHYrJyUnOyB9IH0sIGdyaWQ6e2Rpc3BsYXk6ZmFsc2V9IH0="
NEW_Y   = "eTp7IG1pbjpiLnltaW4sIG1heDpiLnltYXgsIHRpdGxlOntkaXNwbGF5OnRydWUsIHRleHQ6J1N1cnByaXNlIChhZC1ob2MpIGNvc3RzIGFzICUgb2YgcmVudCd9LCB0aWNrczp7IHN0ZXBTaXplOmIueXN0ZXAsIGNhbGxiYWNrOmZ1bmN0aW9uKHYpeyByZXR1cm4gdisnJSc7IH0gfSwgZ3JpZDp7ZGlzcGxheTpmYWxzZX0gfQ=="

MARKER = 'ymin:-ystep'


def read(p):
    with open(p, encoding='utf-8') as f: return f.read()
def detect_nl(p):
    with open(p, 'rb') as f: return '\r\n' if f.read().count(b'\r\n') else '\n'
def write(p, s, nl):
    with open(p, 'w', encoding='utf-8', newline=nl) as f: f.write(s)
def b64(s): return base64.b64decode(s).decode()


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print('!! Run from the project root (where manage.py lives).'); sys.exit(1)
    tpl = os.path.join(root, 'pages', 'templates', 'act_expense.html')
    if not os.path.exists(tpl):
        print('!! Could not find pages/templates/act_expense.html.'); sys.exit(1)
    print('template:', tpl + ('   (dry run)' if DRY else ''))
    print('')

    txt = read(tpl)
    if MARKER in txt:
        print('[skip] Analysis y-axis grace already applied.'); print(''); return

    old_ret, new_ret = b64(OLD_RET), b64(NEW_RET)
    old_y,   new_y   = b64(OLD_Y),   b64(NEW_Y)

    for label, anchor in (('axisBounds() return', old_ret), ('scatter y-scale', old_y)):
        c = txt.count(anchor)
        if c != 1:
            print('!! %s anchor not matched (found %d). Nothing changed.' % (label, c))
            print('   Expected exactly one occurrence of:')
            print('     ' + anchor); sys.exit(1)

    work = txt.replace(old_ret, new_ret, 1).replace(old_y, new_y, 1)

    if work.count('{') != work.count('}'):
        print('!! brace balance changed after edit (%d { vs %d }). Nothing changed.'
              % (work.count('{'), work.count('}'))); sys.exit(1)

    if DRY:
        print('[dry-run] would:')
        print('   - axisBounds() : add ymin:-ystep to the return object')
        print('   - y-scale      : min:0  ->  min:b.ymin')
        print(''); return

    nl = detect_nl(tpl); bak = tpl + '.bak_analysisaxis'
    if not os.path.exists(bak): write(bak, txt, nl)
    write(tpl, work, nl)
    print('[OK] act_expense.html updated (.bak_analysisaxis).')
    print('')
    print('Analysis scatter y-axis now floors one tick below zero. Restart the dev'
          ' server / redeploy, open the "Expenses vs Rent - Analysis" modal, and the'
          ' 0%-cost dots sit clear of the bottom edge.')


if __name__ == '__main__':
    main()