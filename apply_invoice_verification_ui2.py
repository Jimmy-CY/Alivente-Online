#!/usr/bin/env python3
"""
apply_invoice_verification_ui2.py
=================================

Return to the expense after a document action, instead of dropping the user
back to the list.

Uploading an invoice redirected to act_expense_all and closed the modal - the
pre-existing behaviour for every document action. Now that an upload produces a
verdict, that verdict is the thing you actually want to see, so the redirect
carries ?manage=<expense_id> and the page reopens that expense on the Invoice
Document tab.

Touches:
  pages/views/expenses.py           redirect carries the expense id
  pages/templates/act_expense.html  id on the Manage button + auto-open on load

Idempotent; backs up each file. Run from the project root:

    python apply_invoice_verification_ui2.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
report = []


def rw(path, transform, tag, sentinel):
    """Read, transform, write - preserving encoding and line endings."""
    full = os.path.join(ROOT, path)
    if not os.path.exists(full):
        report.append('! %s not found' % path)
        return False
    with open(full, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    src = raw.decode(enc).replace('\r\n', '\n')

    if sentinel in src:
        report.append('= %s already patched' % path)
        return True

    out = transform(src)
    if out is None:
        return False
    if CHECK:
        report.append('+ %s would be patched' % path)
        return True

    bak = full + '.bak_' + tag
    if not os.path.exists(bak):
        shutil.copy2(full, bak)
    with open(full, 'w', encoding=enc, newline='') as fh:
        fh.write(out.replace('\n', nl) if nl == '\r\n' else out)
    report.append('+ %s patched' % path)
    return True


# ---------------------------------------------------------------- views ----
VIEWS_OLD = """        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')

    return redirect('act_expense_all')"""

VIEWS_NEW = """        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')

    # Come back to the expense we were working on rather than the bare list.
    # An upload now produces a verdict, and the verdict is the thing the user
    # wants to see; being bounced to the list hides it behind two more clicks.
    expense_id = request.POST.get('expense_id')
    if expense_id:
        from django.urls import reverse
        return redirect('%s?manage=%s' % (reverse('act_expense_all'), expense_id))
    return redirect('act_expense_all')"""


def patch_views(src):
    if src.count(VIEWS_OLD) != 1:
        report.append('! views anchor matched %d times, expected 1' % src.count(VIEWS_OLD))
        return None
    return src.replace(VIEWS_OLD, VIEWS_NEW, 1)


# ------------------------------------------------------------- template ----
BTN_OLD = """                <button type="button" class="status-btn"
                        onclick="openManageModal({{ expense.act_expense_id }},"""
BTN_NEW = """                <button type="button" class="status-btn"
                        id="manage-btn-{{ expense.act_expense_id }}"
                        onclick="openManageModal({{ expense.act_expense_id }},"""

AUTO_OPEN = """
// ---------------------------------------------------------------------
// Reopen the expense after a document action. act_expense_manage_document
// redirects with ?manage=<id>; land back on the Invoice Document tab so the
// verdict is visible immediately instead of two clicks away.
// ---------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function () {
    var wanted = new URLSearchParams(window.location.search).get('manage');
    if (!wanted) { return; }

    var btn = document.getElementById('manage-btn-' + wanted);
    if (!btn) { return; }          // filtered out of the current view - fine

    btn.click();
    var tab = document.getElementById('invoice-tab');
    if (tab) { tab.click(); }

    // Drop the parameter so a refresh does not reopen the modal again.
    if (window.history && window.history.replaceState) {
        var url = new URL(window.location.href);
        url.searchParams.delete('manage');
        window.history.replaceState({}, '', url.toString());
    }
});

"""

ANCHOR_JS = 'function showAddToExisting() {'


def patch_template(src):
    if src.count(BTN_OLD) != 1:
        report.append('! Manage-button anchor matched %d times, expected 1' % src.count(BTN_OLD))
        return None
    if src.count(ANCHOR_JS) != 1:
        report.append('! JS anchor matched %d times, expected 1' % src.count(ANCHOR_JS))
        return None
    src = src.replace(BTN_OLD, BTN_NEW, 1)
    return src.replace(ANCHOR_JS, AUTO_OPEN + ANCHOR_JS, 1)


def main():
    print('Return-to-expense patch - %s\n' % ('CHECK ONLY' if CHECK else 'APPLYING'))
    ok = rw('pages/views/expenses.py', patch_views, 'returnto', "?manage=%s")
    ok &= rw('pages/templates/act_expense.html', patch_template, 'returnto', 'manage-btn-')
    for line in report:
        print('  ' + line)
    if not ok:
        print('\nNothing was written for the failing file(s).')
        return 1
    if not CHECK:
        print('\nVerify:  python -m py_compile pages/views/expenses.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
