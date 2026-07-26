#!/usr/bin/env python
"""
install_pl_col_fit.py  --  stop the P&L month columns from clipping large figures.

Problem: on finance_pl_act.html the table uses `table-layout: fixed` with each
month column pinned to 5.5% width, and every cell has `overflow: hidden;
text-overflow: ellipsis` with `padding: 4px 8px` at `font-size: 0.8rem`. Five-
character figures fit, but a 6-7 character one — June's TOTAL EXPENSES "15,564",
NET PROFIT "-2,4.." and August's "10,4.." — overflows the fixed column and gets
sliced with an ellipsis.

Fix (CSS only, no layout change): for the numeric columns (every column except
the first label column) tighten the horizontal padding to 3px and drop the font
to 0.75rem, so the widest figures fit inside the same 5.5% columns. The fixed
layout, percentages and the phone-landscape sizing (handled inline by
applyTableSizing()) are all untouched.

Edits one file (backup finance_pl_act.html.bak_colfit):
  * pages/templates/finance_pl_act.html — adds a `.pl-act-table
    td/th:not(:first-child)` rule right after the general cell rule.

SAFE: idempotent (marker guard); exact-anchor (verified unique); preserves
CRLF/LF; --dry-run. No migration. CSS only.

    python install_pl_col_fit.py --dry-run
    python install_pl_col_fit.py
Then restart the dev server (or redeploy) and reload the P&L — the June/August
figures show in full.
"""
import base64, os, sys

DRY = '--dry-run' in sys.argv

OLD = "LnBsLWFjdC10YWJsZSB0ZCwgLnBsLWFjdC10YWJsZSB0aCB7CiAgICB3aGl0ZS1zcGFjZTogbm93cmFwOwogICAgb3ZlcmZsb3c6IGhpZGRlbjsKICAgIHRleHQtb3ZlcmZsb3c6IGVsbGlwc2lzOwogICAgcGFkZGluZzogNHB4IDhweDsKICAgIGZvbnQtc2l6ZTogMC44cmVtOwp9"
NEW = "LnBsLWFjdC10YWJsZSB0ZCwgLnBsLWFjdC10YWJsZSB0aCB7CiAgICB3aGl0ZS1zcGFjZTogbm93cmFwOwogICAgb3ZlcmZsb3c6IGhpZGRlbjsKICAgIHRleHQtb3ZlcmZsb3c6IGVsbGlwc2lzOwogICAgcGFkZGluZzogNHB4IDhweDsKICAgIGZvbnQtc2l6ZTogMC44cmVtOwp9CgovKiBOdW1lcmljIG1vbnRoICsgdG90YWwvYXZnIGNvbHVtbnM6IHRpZ2h0ZXIgaG9yaXpvbnRhbCBwYWRkaW5nIGFuZCBhIHNsaWdodGx5CiAgIHNtYWxsZXIgZm9udCBzbyA2LTcgY2hhcmFjdGVyIGZpZ3VyZXMgKGUuZy4gMTUsNTY0IG9yIC0yLDQ5OSkgZml0IGluc2lkZSB0aGUKICAgZml4ZWQgNS41JSBjb2x1bW5zIGluc3RlYWQgb2YgYmVpbmcgY2xpcHBlZCB3aXRoIGFuIGVsbGlwc2lzLiBEZXNrdG9wL3RhYmxldAogICBvbmx5OyBwaG9uZS1sYW5kc2NhcGUgc2l6aW5nIGlzIGhhbmRsZWQgaW5saW5lIGJ5IGFwcGx5VGFibGVTaXppbmcoKS4gKi8KLnBsLWFjdC10YWJsZSB0ZDpub3QoOmZpcnN0LWNoaWxkKSwKLnBsLWFjdC10YWJsZSB0aDpub3QoOmZpcnN0LWNoaWxkKSB7CiAgICBwYWRkaW5nLWxlZnQ6IDNweDsKICAgIHBhZGRpbmctcmlnaHQ6IDNweDsKICAgIGZvbnQtc2l6ZTogMC43NXJlbTsKfQ=="

MARKER = "Numeric month + total/avg columns: tighter horizontal padding"


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
    tpl = os.path.join(root, 'pages', 'templates', 'finance_pl_act.html')
    if not os.path.exists(tpl):
        print('!! Could not find pages/templates/finance_pl_act.html.'); sys.exit(1)
    print('template:', tpl + ('   (dry run)' if DRY else ''))
    print('')

    txt = read(tpl)
    if MARKER in txt:
        print('[skip] column-fit rule already applied.'); print(''); return

    old, new = b64(OLD), b64(NEW)
    c = txt.count(old)
    if c != 1:
        print('!! cell-rule anchor not matched (found %d). Nothing changed.' % c)
        print('   Expected exactly one occurrence of the general'
              ' `.pl-act-table td, .pl-act-table th { ... }` block.'); sys.exit(1)

    work = txt.replace(old, new, 1)
    if work.count('{') != work.count('}'):
        print('!! brace balance changed (%d { vs %d }). Nothing changed.'
              % (work.count('{'), work.count('}'))); sys.exit(1)

    if DRY:
        print('[dry-run] would add a numeric-column rule:')
        print('   - padding-left/right: 3px (from 8px)')
        print('   - font-size: 0.75rem (from 0.8rem)')
        print('   applied to every column except the first (label) column.')
        print(''); return

    nl = detect_nl(tpl); bak = tpl + '.bak_colfit'
    if not os.path.exists(bak): write(bak, txt, nl)
    write(tpl, work, nl)
    print('[OK] finance_pl_act.html updated (.bak_colfit).')
    print('')
    print('Column-fit installed. Restart the dev server / redeploy and reload the'
          ' P&L — the June/August figures now show in full.')


if __name__ == '__main__':
    main()