#!/usr/bin/env python3
"""
apply_payment_days_cutoff.py
============================

Upgrades an ALREADY-INSTALLED tenant payment-behaviour screen to the agreed
scope rules. Run this only if you have already run apply_tenant_payment_days.py;
on a fresh install that script now produces this version directly.

What changes
------------
1. **A hard 1 Aug 2026 cutoff.** Nothing dated earlier is in scope. The paid
   date only began being recorded when the feature went live, so every earlier
   invoice can say exactly one thing - unknown - and a list of unknowns made a
   tenant with a clean record look like a tenant with a problem.

2. **The "Not yet measurable" section is removed.** With the cutoff in place it
   could only ever repeat what "Currently unpaid" already said. Replaced by a
   single count line, so nobody is silently dropped.

3. **Pre-cutoff unpaid invoices are counted, not listed.** This is the one
   thing the cutoff does NOT throw away: an old unpaid invoice is still a debt,
   and hiding it because of an implementation date would be the report quietly
   losing a receivable. It appears as a count and a total beneath the unpaid
   table.

Files touched
-------------
  pages/views/tenants.py                     the view block is replaced
  pages/templates/tenant_payment_days.html   rewritten

No migration, no model change, no URL change.

Where the code comes from
-------------------------
This script does not carry its own copy of the view or the template. It reads
both out of `apply_tenant_payment_days.py`, which must sit beside it - one
source of truth, so the fresh-install path and the upgrade path cannot drift
apart.

Idempotent; backs pages/views/tenants.py up to .bak_cutoff. Run from the
project root:

    python apply_payment_days_cutoff.py [--check]
"""

import importlib.util
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(ROOT, 'apply_tenant_payment_days.py')
VIEWS = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
TEMPLATE_PATH = os.path.join(ROOT, 'pages', 'templates', 'tenant_payment_days.html')

SENTINEL = 'PAYMENT_DATA_STARTS'

# The view block was appended to tenants.py by the original patcher and starts
# with this comment. Everything from here to end-of-file is ours to replace.
BLOCK_START = '# Days past the agreed terms before a tenant is flagged as slow.'


def load_master():
    """Pull VIEW and TEMPLATE out of the original patcher.

    Importing it is safe: everything there is module-level definitions, and the
    entry point is guarded by `if __name__ == '__main__'`.
    """
    if not os.path.exists(MASTER):
        print('! apply_tenant_payment_days.py must sit beside this script')
        return None, None
    spec = importlib.util.spec_from_file_location('_pd_master', MASTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    view, template = getattr(mod, 'VIEW', None), getattr(mod, 'TEMPLATE', None)
    if not view or not template:
        print('! could not read VIEW/TEMPLATE out of apply_tenant_payment_days.py')
        return None, None
    if SENTINEL not in view:
        print('! apply_tenant_payment_days.py is the OLD version - it has no %s.'
              % SENTINEL)
        print('  Replace it with the updated one first; this script only carries')
        print('  the splice logic, not the code.')
        return None, None
    return view, template


def main():
    for path in (VIEWS, TEMPLATE_PATH):
        if not os.path.exists(path):
            print('! %s not found.' % os.path.relpath(path, ROOT))
            print('  Run apply_tenant_payment_days.py first.')
            return 1

    view, template = load_master()
    if view is None:
        return 1

    with open(VIEWS, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    src = raw.decode(enc).replace('\r\n', '\n')

    if SENTINEL in src:
        print('= tenants.py already carries the cutoff')
        already_view = True
    else:
        already_view = False

    if not already_view:
        n = src.count(BLOCK_START)
        if n != 1:
            print('! block-start marker matched %d times, expected 1 - aborting.' % n)
            print('  Expected the view appended by apply_tenant_payment_days.py.')
            return 1

        head, _, tail = src.partition(BLOCK_START)

        # Refuse to swallow anything that was added after our block. The splice
        # runs to end-of-file, so a stray function below would be destroyed.
        strays = [m for m in re.findall(r'^def (\w+)', tail, re.M)
                  if m != 'tenant_payment_days_view']
        if strays:
            print('! found other top-level function(s) after the payment-days block: %s'
                  % ', '.join(strays))
            print('  Refusing to replace to end-of-file - move them above the block,')
            print('  or apply the change by hand.')
            return 1

        # Two blank lines before the block, per PEP 8 - rstrip removes the
        # existing ones, so they have to be put back deliberately.
        src = head.rstrip('\n') + '\n\n\n' + view.strip('\n') + '\n'

    if CHECK:
        print('= check only, nothing written')
        print('    tenants.py  %s' % ('already current' if already_view else 'would be spliced'))
        print('    template    would be rewritten')
        return 0

    if not already_view:
        bak = VIEWS + '.bak_cutoff'
        if not os.path.exists(bak):
            shutil.copy2(VIEWS, bak)
        with open(VIEWS, 'w', encoding=enc, newline='') as fh:
            fh.write(src.replace('\n', nl) if nl == '\r\n' else src)
        print('+ pages/views/tenants.py - view replaced (backup: .bak_cutoff)')

    with open(TEMPLATE_PATH, 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write(template)
    print('+ pages/templates/tenant_payment_days.html rewritten')

    print('')
    print('  - nothing dated before 1 Aug 2026 is in scope')
    print('  - "Not yet measurable" section removed, replaced by a count')
    print('  - pre-cutoff unpaid invoices counted and totalled, not listed')
    print('')
    print('Verify:  python -m py_compile pages/views/tenants.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
