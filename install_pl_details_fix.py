#!/usr/bin/env python
"""
install_pl_details_fix.py  —  Phase 2 follow-up.

The P&L table already resolves budgeted figures per year (Phase 2). But the
drill-down popups (click a figure) are served by separate views that still read
the CURRENT cells, so they showed today's number regardless of the year picked.
This resolves those three views to the selected year too, using the same engine:
  - budget_expense_details_view
  - revenue_details_view
  - total_expense_details_view (budget portion)

SAFE: idempotent; newline-anchored; preserves CRLF/LF; re-parses and aborts on
any syntax error; backup to finance.py.bak_detailsfix; --dry-run. No migration.

Run from the project root:
    python install_pl_details_fix.py --dry-run
    python install_pl_details_fix.py
Then restart the dev server and re-open a P&L drill-down for an earlier year.
"""
import ast, base64, os, sys
DRY = '--dry-run' in sys.argv
REPL = [['ICAgICMgQ3JlYXRlIGEgbGlzdCBvZiBleHBlbnNlIGl0ZW1zIHdpdGggbW9udGhseSBicmVha2Rvd24KICAgIGV4cGVuc2VfaXRlbXMgPSBbXQogICAgdG90YWxfYW1vdW50ID0gMAoKICAgIGZvciBleHAgaW4gZXhwZW5zZXM6', 'ICAgICMgUGhhc2UgMjogcmVzb2x2ZSBidWRnZXRlZCBmaWd1cmVzIHRvIHRoZSBzZWxlY3RlZCB5ZWFyIChzYW1lIGFzIHRoZSBQJkwpLgogICAgdHJ5OgogICAgICAgIF95ZWFyX2ludCA9IGludCh5ZWFyKQogICAgZXhjZXB0IChUeXBlRXJyb3IsIFZhbHVlRXJyb3IpOgogICAgICAgIF95ZWFyX2ludCA9IE5vbmUKICAgIF95ZWFyX21hcCA9IChyZXNvbHZlX3llYXJfbW9udGhzX2J1bGsoCiAgICAgICAgbGlzdChleHBlbnNlcy52YWx1ZXNfbGlzdCgncHJvcF9pZCcsIGZsYXQ9VHJ1ZSkuZGlzdGluY3QoKSksCiAgICAgICAgRmluYW5jaWFsRmlndXJlSGlzdG9yeS5LSU5EX0JVREdFVCwgX3llYXJfaW50KSBpZiBfeWVhcl9pbnQgaXMgbm90IE5vbmUgZWxzZSBOb25lKQoKICAgICMgQ3JlYXRlIGEgbGlzdCBvZiBleHBlbnNlIGl0ZW1zIHdpdGggbW9udGhseSBicmVha2Rvd24KICAgIGV4cGVuc2VfaXRlbXMgPSBbXQogICAgdG90YWxfYW1vdW50ID0gMAoKICAgIGZvciBleHAgaW4gZXhwZW5zZXM6'], ['ICAgICAgICBmb3IgaSwgbW9udGhfZmllbGQgaW4gZW51bWVyYXRlKG1vbnRocywgMSk6CiAgICAgICAgICAgIG1vbnRoX3ZhbHVlID0gZ2V0YXR0cihleHAsIGYnZXhwZW5zZV97bW9udGhfZmllbGR9JywgMCk=', 'ICAgICAgICBmb3IgaSwgbW9udGhfZmllbGQgaW4gZW51bWVyYXRlKG1vbnRocywgMSk6CiAgICAgICAgICAgIGlmIF95ZWFyX21hcCBpcyBub3QgTm9uZSBhbmQgZXhwLmV4cGVuc2VfaWQgaW4gX3llYXJfbWFwOgogICAgICAgICAgICAgICAgbW9udGhfdmFsdWUgPSBfeWVhcl9tYXBbZXhwLmV4cGVuc2VfaWRdW2kgLSAxXQogICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgbW9udGhfdmFsdWUgPSBnZXRhdHRyKGV4cCwgZidleHBlbnNlX3ttb250aF9maWVsZH0nLCAwKQ=='], ['ICAgICMgQ3JlYXRlIGEgbGlzdCBvZiByZXZlbnVlIGl0ZW1zIHdpdGggbW9udGhseSBicmVha2Rvd24KICAgIHJldmVudWVfaXRlbXMgPSBbXQogICAgdG90YWxfYW1vdW50ID0gMAoKICAgIGZvciByZXYgaW4gcmV2ZW51ZXM6', 'ICAgICMgUGhhc2UgMjogcmVzb2x2ZSByZXZlbnVlIGZpZ3VyZXMgdG8gdGhlIHNlbGVjdGVkIHllYXIgKHNhbWUgYXMgdGhlIFAmTCkuCiAgICB0cnk6CiAgICAgICAgX3llYXJfaW50ID0gaW50KHllYXIpCiAgICBleGNlcHQgKFR5cGVFcnJvciwgVmFsdWVFcnJvcik6CiAgICAgICAgX3llYXJfaW50ID0gTm9uZQogICAgX3llYXJfbWFwID0gKHJlc29sdmVfeWVhcl9tb250aHNfYnVsaygKICAgICAgICBsaXN0KHJldmVudWVzLnZhbHVlc19saXN0KCdwcm9wX2lkJywgZmxhdD1UcnVlKS5kaXN0aW5jdCgpKSwKICAgICAgICBGaW5hbmNpYWxGaWd1cmVIaXN0b3J5LktJTkRfUkVWRU5VRSwgX3llYXJfaW50KSBpZiBfeWVhcl9pbnQgaXMgbm90IE5vbmUgZWxzZSBOb25lKQoKICAgICMgQ3JlYXRlIGEgbGlzdCBvZiByZXZlbnVlIGl0ZW1zIHdpdGggbW9udGhseSBicmVha2Rvd24KICAgIHJldmVudWVfaXRlbXMgPSBbXQogICAgdG90YWxfYW1vdW50ID0gMAoKICAgIGZvciByZXYgaW4gcmV2ZW51ZXM6'], ['ICAgICAgICBmb3IgaSwgbW9udGhfbmFtZV9maWVsZCBpbiBlbnVtZXJhdGUobW9udGhzLCAxKToKICAgICAgICAgICAgbW9udGhfdmFsdWUgPSBnZXRhdHRyKHJldiwgZidyZXZlbnVlX3ttb250aF9uYW1lX2ZpZWxkfScsIDAp', 'ICAgICAgICBmb3IgaSwgbW9udGhfbmFtZV9maWVsZCBpbiBlbnVtZXJhdGUobW9udGhzLCAxKToKICAgICAgICAgICAgaWYgX3llYXJfbWFwIGlzIG5vdCBOb25lIGFuZCByZXYucmV2ZW51ZV9pZCBpbiBfeWVhcl9tYXA6CiAgICAgICAgICAgICAgICBtb250aF92YWx1ZSA9IF95ZWFyX21hcFtyZXYucmV2ZW51ZV9pZF1baSAtIDFdCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBtb250aF92YWx1ZSA9IGdldGF0dHIocmV2LCBmJ3JldmVudWVfe21vbnRoX25hbWVfZmllbGR9JywgMCk='], ['ICAgICMgQ3JlYXRlIGJ1ZGdldCBleHBlbnNlIGl0ZW1zIHdpdGggbW9udGhseSBicmVha2Rvd24gKHNpbWlsYXIgdG8gYnVkZ2V0X2V4cGVuc2VfZGV0YWlsc192aWV3KQogICAgYnVkZ2V0X2V4cGVuc2VfaXRlbXMgPSBbXQogICAgZm9yIGV4cCBpbiBidWRnZXRfZXhwZW5zZXM6', 'ICAgICMgUGhhc2UgMjogcmVzb2x2ZSBidWRnZXRlZCBmaWd1cmVzIHRvIHRoZSBzZWxlY3RlZCB5ZWFyLgogICAgdHJ5OgogICAgICAgIF95ZWFyX2ludCA9IGludCh5ZWFyKQogICAgZXhjZXB0IChUeXBlRXJyb3IsIFZhbHVlRXJyb3IpOgogICAgICAgIF95ZWFyX2ludCA9IE5vbmUKICAgIF95ZWFyX21hcCA9IChyZXNvbHZlX3llYXJfbW9udGhzX2J1bGsoCiAgICAgICAgbGlzdChidWRnZXRfZXhwZW5zZXMudmFsdWVzX2xpc3QoJ3Byb3BfaWQnLCBmbGF0PVRydWUpLmRpc3RpbmN0KCkpLAogICAgICAgIEZpbmFuY2lhbEZpZ3VyZUhpc3RvcnkuS0lORF9CVURHRVQsIF95ZWFyX2ludCkgaWYgX3llYXJfaW50IGlzIG5vdCBOb25lIGVsc2UgTm9uZSkKCiAgICAjIENyZWF0ZSBidWRnZXQgZXhwZW5zZSBpdGVtcyB3aXRoIG1vbnRobHkgYnJlYWtkb3duIChzaW1pbGFyIHRvIGJ1ZGdldF9leHBlbnNlX2RldGFpbHNfdmlldykKICAgIGJ1ZGdldF9leHBlbnNlX2l0ZW1zID0gW10KICAgIGZvciBleHAgaW4gYnVkZ2V0X2V4cGVuc2VzOg=='], ['ICAgICAgICBmb3IgaSwgbW9udGhfbmFtZSBpbiBlbnVtZXJhdGUobW9udGhzLCAxKToKICAgICAgICAgICAgbW9udGhfdmFsdWUgPSBnZXRhdHRyKGV4cCwgZidleHBlbnNlX3ttb250aF9uYW1lfScsIDAp', 'ICAgICAgICBmb3IgaSwgbW9udGhfbmFtZSBpbiBlbnVtZXJhdGUobW9udGhzLCAxKToKICAgICAgICAgICAgaWYgX3llYXJfbWFwIGlzIG5vdCBOb25lIGFuZCBleHAuZXhwZW5zZV9pZCBpbiBfeWVhcl9tYXA6CiAgICAgICAgICAgICAgICBtb250aF92YWx1ZSA9IF95ZWFyX21hcFtleHAuZXhwZW5zZV9pZF1baSAtIDFdCiAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICBtb250aF92YWx1ZSA9IGdldGF0dHIoZXhwLCBmJ2V4cGVuc2Vfe21vbnRoX25hbWV9JywgMCk=']]
MARKER = '_year_map = (resolve_year_months_bulk('

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()
def detect_nl(p):
    with open(p,'rb') as f: return '\r\n' if f.read().count(b'\r\n') else '\n'
def write(p,s,nl):
    with open(p,'w',encoding='utf-8',newline=nl) as f: f.write(s)
def find_py(root, needle):
    for dp,_,files in os.walk(root):
        if '__pycache__' in dp: continue
        for fn in sorted(files):
            if fn.endswith('.py'):
                p=os.path.join(dp,fn)
                try:
                    if needle in read(p): return p
                except Exception: pass
    return None

def main():
    root=os.getcwd()
    if not os.path.exists(os.path.join(root,'manage.py')):
        print('!! Run from the project root (folder with manage.py).'); sys.exit(1)
    finance_py=find_py(os.path.join(root,'pages'),'def budget_expense_details_view(')
    if not finance_py:
        print('!! Could not find the finance views file. Nothing changed.'); sys.exit(1)
    print('finance.py: ' + finance_py + ('   (dry run)' if DRY else ''))
    text=read(finance_py)
    if MARKER in text:
        print('[skip] drill-down views already year-resolved.'); return
    if 'def resolve_year_months_bulk(' not in read(find_py(os.path.join(root,'pages'),'class FinancialFigureHistory(') or finance_py) \
       and 'resolve_year_months_bulk' not in text:
        print('!! Phase 2 not detected (resolve_year_months_bulk missing). Run install_pl_phase2.py first. Nothing changed.'); sys.exit(1)
    work=text; miss=[]
    for ob,nb in REPL:
        old=base64.b64decode(ob).decode(); new=base64.b64decode(nb).decode()
        key='\n'+old
        if work.count(key)!=1: miss.append('(%d x) %s'%(work.count(key), old.splitlines()[0][:60]))
        else: work=work.replace(key,'\n'+new,1)
    if miss:
        print('!! did not match cleanly:'); [print('    '+m) for m in miss]
        print('   Nothing changed.'); sys.exit(1)
    try: ast.parse(work)
    except SyntaxError as e:
        print('!! result would not parse: %s. Nothing changed.'%e); sys.exit(1)
    if DRY:
        print('[dry-run] would resolve 3 drill-down views to the selected year (%d edits).'%len(REPL)); return
    nl=detect_nl(finance_py)
    bak=finance_py+'.bak_detailsfix'
    if not os.path.exists(bak): write(bak, text, nl)
    write(finance_py, work, nl)
    print('[OK] finance.py updated (backup: finance.py.bak_detailsfix). Restart the dev server.')

if __name__=='__main__': main()