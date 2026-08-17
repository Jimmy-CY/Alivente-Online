#!/usr/bin/env python3
"""
apply_skip_paid_email.py
========================

Do not send the routine "invoice ready to pay" email when the expense has
already been marked Paid - the premise of the notice is false, and bulk
re-uploads of historic documents would otherwise flood the inbox (the initial
back-fill of 35 invoices would have sent 35 emails, all for paid expenses).

ONE EXCEPTION, deliberately kept: a MISMATCH on an already-paid expense still
sends, with a distinct subject. Money has already gone out against a figure the
invoice does not support - that is worse news than a mismatch found before
payment, not lesser news, and suppressing it would hide a real problem.

  Paid=No   any verdict   -> send (unchanged)
  Paid=Yes  mismatch      -> send, subject marked ALREADY PAID
  Paid=Yes  anything else -> no email

Idempotent; backs up pages/views/expenses.py to .bak_skippaid.
Run from the project root:

    python apply_skip_paid_email.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, 'pages', 'views', 'expenses.py')
SENTINEL = '_should_email_upload'

# --- 1. gate the send at the end of _run_invoice_verification --------------
SEND_OLD = "    send_invoice_verification_email(expense, verdict)\n"

SEND_NEW = ('    if _should_email_upload(expense, verdict):\n'
            '        send_invoice_verification_email(expense, verdict)\n')

# Helper functions, inserted ahead of _verify_extra rather than spliced into a
# comment banner - dash counts in banners are not a safe anchor.
HELPERS_ANCHOR = 'def _verify_extra(expense):'

HELPERS = '''def _is_paid(expense):
    return (expense.act_expense_paid or '').strip().lower() == 'yes'


def _should_email_upload(expense, verdict):
    """Whether an upload is worth emailing about.

    The routine notice says "ready to pay", so it is pointless once the expense
    IS paid - and re-uploading historic documents would otherwise send a burst
    of them.

    But a MISMATCH on a paid expense still sends: the money is already gone
    against a figure the invoice does not support, which is a bigger problem
    than the same mismatch caught beforehand. Silence there would hide it.
    """
    if not _is_paid(expense):
        return True
    return (verdict or {}).get('status') == iv.STATUS_MISMATCH


'''

# --- 2. distinct subject for the already-paid mismatch ---------------------
SUBJ_OLD = """    if status == iv.STATUS_MISMATCH:
        return ('** INVOICE MISMATCH ** %s - invoice EUR %s vs approved EUR %s'
                % (prop, total if total is not None else '?', amount))"""

SUBJ_NEW = """    if status == iv.STATUS_MISMATCH:
        # An expense already marked Paid deserves louder wording: the money has
        # gone, so this is a recovery question rather than an approval one.
        if _is_paid(expense):
            return ('** MISMATCH ON A PAID EXPENSE ** %s - invoice EUR %s vs paid EUR %s'
                    % (prop, total if total is not None else '?', amount))
        return ('** INVOICE MISMATCH ** %s - invoice EUR %s vs approved EUR %s'
                % (prop, total if total is not None else '?', amount))"""

# --- 3. say so in the body too --------------------------------------------
BODY_OLD = """        if status == iv.STATUS_MISMATCH:
            lines += [
                '',
                'To correct this: un-approve the expense, ask the user to amend the',
                'amount, then re-approve. The check runs again on re-approval and',
                'clears if it then matches.',
            ]"""

BODY_NEW = """        if status == iv.STATUS_MISMATCH and _is_paid(expense):
            lines += [
                '',
                'NOTE: this expense is already marked PAID, so the payment has',
                'already been made against the approved figure above. Check the',
                'invoice and, if the supplier has over-billed, recover or offset',
                'the difference before amending the record.',
            ]
        elif status == iv.STATUS_MISMATCH:
            lines += [
                '',
                'To correct this: un-approve the expense, ask the user to amend the',
                'amount, then re-approve. The check runs again on re-approval and',
                'clears if it then matches.',
            ]"""


def main():
    if not os.path.exists(TARGET):
        print('! pages/views/expenses.py not found - run from the project root')
        return 1
    with open(TARGET, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    src = raw.decode(enc).replace('\r\n', '\n')

    if SENTINEL in src:
        print('= already patched - nothing to do')
        return 0

    for name, old in (('send call', SEND_OLD), ('helpers anchor', HELPERS_ANCHOR),
                      ('subject', SUBJ_OLD), ('body', BODY_OLD)):
        n = src.count(old)
        if n != 1:
            print('! %s anchor matched %d times, expected 1 - aborting, nothing written'
                  % (name, n))
            print('  Run apply_invoice_upload_email.py first.')
            return 1

    src = src.replace(SEND_OLD, SEND_NEW, 1)
    src = src.replace(HELPERS_ANCHOR, HELPERS + HELPERS_ANCHOR, 1)
    src = src.replace(SUBJ_OLD, SUBJ_NEW, 1)
    src = src.replace(BODY_OLD, BODY_NEW, 1)

    if CHECK:
        print('= check only: all four anchors matched, nothing written')
        return 0

    bak = TARGET + '.bak_skippaid'
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak)
    with open(TARGET, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)

    print('+ pages/views/expenses.py patched (backup: .bak_skippaid)')
    print('  - no routine email once an expense is marked Paid')
    print('  - a MISMATCH on a paid expense still sends, marked ALREADY PAID')
    print('\nVerify:  python -m py_compile pages/views/expenses.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
