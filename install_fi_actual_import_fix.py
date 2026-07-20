#!/usr/bin/env python
"""
install_fi_actual_import_fix.py  --  fix for Phase A (install_indicators_year_basis.py).

Phase A's view calls property_annual_actual_expenses() (Actuals basis) but the
helper was appended to models.py without being added to finance.py's
`from pages.models import (...)` block, so the Actuals view raised
"name 'property_annual_actual_expenses' is not defined". This adds the import.
Budget basis was unaffected (it never calls the helper).

Edits one file (backup finance.py.bak_fiimportfix):
  * pages/views/finance.py : add property_annual_actual_expenses to the models import.

SAFE: idempotent; newline-anchored; preserves CRLF/LF; re-parses; --dry-run. No migration.

    python install_fi_actual_import_fix.py --dry-run
    python install_fi_actual_import_fix.py
Then restart the dev server.
"""
import ast, base64, os, sys
DRY = '--dry-run' in sys.argv
OLD = "ICAgIHByb3BlcnR5X2FubnVhbF9sZWFzZV9yZXZlbnVlLCBwcm9wZXJ0eV9hbm51YWxfYnVkZ2V0ZWRfZXhwZW5zZXMsCik="
NEW = "ICAgIHByb3BlcnR5X2FubnVhbF9sZWFzZV9yZXZlbnVlLCBwcm9wZXJ0eV9hbm51YWxfYnVkZ2V0ZWRfZXhwZW5zZXMsCiAgICBwcm9wZXJ0eV9hbm51YWxfYWN0dWFsX2V4cGVuc2VzLAop"
MARK = 'property_annual_actual_expenses,'

def read(p):
    with open(p, encoding='utf-8') as fh: return fh.read()
def detect_nl(p):
    with open(p,'rb') as fh: return '\r\n' if fh.read().count(b'\r\n') else '\n'
def write(p,s,nl):
    with open(p,'w',encoding='utf-8',newline=nl) as fh: fh.write(s)
def find_py(root,needle):
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
        print('!! Run from the project root.'); sys.exit(1)
    fp=find_py(os.path.join(root,'pages'),'def financial_indicators_view(')
    if not fp: print('!! finance.py not found.'); sys.exit(1)
    print('finance.py:', fp + ('   (dry run)' if DRY else '')); print('')
    t=read(fp)
    if MARK in t and 'property_annual_actual_expenses(' in t and t.count('property_annual_actual_expenses')>=2:
        # import line present (marker) in addition to the call site
        if ('    property_annual_actual_expenses,\n' in t):
            print('[skip] import already present.'); print(''); return
    old=base64.b64decode(OLD).decode(); new=base64.b64decode(NEW).decode()
    if ('\n'+t).count('\n'+old)!=1:
        print('!! import anchor not matched (found %d). Nothing changed.' % ('\n'+t).count('\n'+old)); sys.exit(1)
    w=t.replace('\n'+old,'\n'+new,1)
    try: ast.parse(w)
    except SyntaxError as e:
        print('!! finance.py would not parse: %s'%e); sys.exit(1)
    if DRY: print('[dry-run] would add property_annual_actual_expenses to the import.')
    else:
        nl=detect_nl(fp); b=fp+'.bak_fiimportfix'
        if not os.path.exists(b): write(b,t,nl)
        write(fp,w,nl); print('[OK] finance.py updated (.bak_fiimportfix).')
    print(''); print(('Dry run only.' if DRY else 'Import fix installed.'),'Restart the dev server; Actuals basis now works.')

if __name__=='__main__': main()