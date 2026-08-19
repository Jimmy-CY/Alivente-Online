#!/usr/bin/env python3
"""
apply_payment_days_cutoff.py
============================

Re-syncs an ALREADY-INSTALLED tenant payment-behaviour screen with whatever
apply_tenant_payment_days.py currently says. Run it after any change to that
file; on a fresh install, apply_tenant_payment_days.py alone is enough.

It is deliberately a SYNC, not a one-shot upgrade: "already applied" means the
installed code matches the master, not that the script has been run before. A
sentinel would have made every later tweak need its own throwaway patcher.

What it first delivered
-----------------------
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

# Guards against being pointed at a stale apply_tenant_payment_days.py. Not an
# idempotence marker - that is a straight comparison against the master.
MASTER_MARKER = 'PAYMENT_DATA_STARTS'

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
    if MASTER_MARKER not in view:
        print('! apply_tenant_payment_days.py is the OLD version - it has no %s.'
              % MASTER_MARKER)
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
    new_src = head.rstrip('\n') + '\n\n\n' + view.strip('\n') + '\n'

    with open(TEMPLATE_PATH, encoding='utf-8') as fh:
        current_template = fh.read()

    # Idempotence is "matches the master", not "has been run once". A sentinel
    # would make this a one-shot tool, and every later tweak to the view would
    # then need its own throwaway patcher.
    view_changed = new_src != src
    template_changed = (current_template.replace('\r\n', '\n')
                        != template.replace('\r\n', '\n'))

    if not view_changed and not template_changed:
        print('= already in sync with apply_tenant_payment_days.py - nothing to do')
        return 0

    if CHECK:
        print('= check only, nothing written')
        print('    tenants.py  %s' % ('would be re-spliced' if view_changed else 'in sync'))
        print('    template    %s' % ('would be rewritten' if template_changed else 'in sync'))
        return 0

    if view_changed:
        bak = VIEWS + '.bak_cutoff'
        if not os.path.exists(bak):
            shutil.copy2(VIEWS, bak)
        with open(VIEWS, 'w', encoding=enc, newline='') as fh:
            fh.write(new_src.replace('\n', nl) if nl == '\r\n' else new_src)
        print('+ pages/views/tenants.py - view block re-synced (backup: .bak_cutoff)')
    else:
        print('= pages/views/tenants.py already in sync')

    if template_changed:
        with open(TEMPLATE_PATH, 'w', encoding='utf-8', newline='\r\n') as fh:
            fh.write(template)
        print('+ pages/templates/tenant_payment_days.html rewritten')
    else:
        print('= template already in sync')

    print('')
    print('Verify:  python -m py_compile pages/views/tenants.py')
    print('         python test_tenant_payment_days.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
