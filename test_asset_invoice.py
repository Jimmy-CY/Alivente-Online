# -*- coding: utf-8 -*-
"""test_asset_invoice.py - Section AI round AI-1, 5 Oct 2026.

Demetri: "The add file to the Edit Asset works perfectly. However, I need
to add the functionality to remove an attached file."

He was right that there was none. The field showed the current file and a
Choose file box, and REPLACE was the only verb it had.

SECTION 3 IS THE ONE THAT MATTERS, and it is about form ownership. The
Remove button has to sit beside the file it removes, which is in the
middle of editAssetForm, and HTML does not allow a form inside a form -
so it names a hidden form that lives outside, exactly as the photo
buttons on that page already do. SV-1 spent a whole round on what happens
when a submit button has no form owner: nothing, silently. This checks
the button names a form AND that the form exists.

SECTION 4 IS ABOUT THE BYTES. The view calls .delete(save=False) before
clearing the field, so the file leaves storage. Clearing the field alone
would leave a file nobody can reach still occupying disk - hidden rather
than removed. The check reads the view's source for the call, because
nothing in this sandbox has the storage to prove it any other way, and
says so.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_assetinv'
ME = 'test_asset_invoice.py'
PATCHER = 'apply_asset_invoice.py'
PS1 = 'Push-PendingChanges.ps1'

PAGE = alv_tree.path_of('edit_asset.html')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
VIEWS = os.path.join(ROOT, 'pages', 'views', 'properties.py')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


SRC = alv_tree.code_only(now(PAGE))
OLD = alv_tree.code_only(was(PAGE)) if os.path.exists(PAGE + SUFFIX) else ''

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. replace really was the only verb')

ok(bool(OLD), 'edit_asset.html has a backup')
ok('Upload a new file to replace the existing one' in OLD,
   'the field offered a replacement')
ok('deleteInvoiceForm' not in OLD,
   '  and no way at all to remove what was there',
   'it had one - then this round is solving a solved problem')

# ==========================================================================
head('2. and now there is a Remove')

ok('deleteInvoiceForm' in SRC, 'the page carries a Remove control')
ok('icon-action-btn icon-delete' in SRC.split('deleteInvoiceForm')[0][-400:]
   or 'icon-delete' in SRC,
   '  wearing the house delete name')
ok('title="Remove this file"' in SRC and 'aria-label="Remove this file"'
   in SRC, '  named, so an icon-only control can be read')
ok('confirm(' in SRC.split('deleteInvoiceForm')[-1][:400]
   or "onsubmit=\"return confirm(" in SRC,
   '  and it asks before it acts, because there is no undo')

# ==========================================================================
head('3. the button belongs to a form, and the form exists')

m = re.search(r'<button[^>]*\bform="(\w+)"[^>]*icon-delete|'
              r'<button[^>]*icon-delete[^>]*\bform="(\w+)"', SRC)
name = (m.group(1) or m.group(2)) if m else None
ok(name == 'deleteInvoiceForm',
   'the Remove button names form="deleteInvoiceForm"',
   'it names %r - a submit button with no form owner does NOTHING, '
   'silently, which is the whole of SV-1' % (name,))
ok(('id="deleteInvoiceForm"' in SRC),
   '  and a form with that id is on the page')

# OUTSIDE editAssetForm, which is why the attribute is needed at all.
#
# READ OFF THE RAW FILE, NOT code_only(). The note explaining this is an
# HTML comment, and code_only strips those - the first build looked for
# it in the stripped text and failed on a round that was right. The
# POSITION check has the same problem: the landmark it measured from was
# a comment too.
RAW = now(PAGE)
form_open = RAW.find('id="editAssetForm"')
form_close = RAW.find('</form>', form_open)
hidden = RAW.find('id="deleteInvoiceForm"')
ok(form_open > 0 and hidden > form_close,
   '  which sits outside editAssetForm, as HTML requires',
   'editAssetForm closes at %d and the hidden form is at %d - a form '
   'inside a form is not HTML' % (form_close, hidden))
ok("doesn't allow nested forms" in RAW,
   '  beside the photos, which solved this first')

# ==========================================================================
head('4. the file leaves storage, not just the record')

v = read(VIEWS)
ok('def delete_asset_invoice(' in v, 'the view exists')
body = v[v.index('def delete_asset_invoice('):]
body = body[:body.index('@login_required', 10)] if '@login_required' in body[10:] else body[:2000]
ok('.delete(save=False)' in body,
   '  and deletes the file from storage before clearing the field',
   'clearing the field alone leaves a file nobody can reach on disk')
ok('purchase_invoice = None' in body, '  then clears the field')
ok("update_fields=['purchase_invoice']" in body,
   '  and saves that one column, touching nothing else on the row')
ok('@require_POST' in v[:v.index('def delete_asset_invoice(')][-200:],
   '  POST only, so no link or crawler can remove a document')
ok('permission_required' in v[:v.index('def delete_asset_invoice(')][-250:],
   '  and only somebody who may edit properties')
ok('There is no invoice attached to remove' in body,
   '  it says so rather than failing when there is nothing to remove')

u = read(URLS)
ok("name='delete_asset_invoice'" in u, 'and the route is registered')

# ==========================================================================
head('5. the control - a button with no form')

planted = SRC.replace('form="deleteInvoiceForm"', '', 1)
ok(planted != SRC, 'the control could be planted')
m2 = re.search(r'<button[^>]*icon-delete[^>]*>', planted)
ok(m2 is not None and 'form=' not in m2.group(0),
   '  and the check can see a Remove button with no form owner',
   'it cannot - then section 3 proves nothing')
ok('form="deleteInvoiceForm"' in SRC, '  and the page itself is intact')

# ==========================================================================
head('6. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that the file actually disappears from disk.')
print('  Nothing in this sandbox has the storage the view writes to. What')
print('  is proved is that the view CALLS delete() rather than only')
print('  clearing the field, which is the difference between removed and')
print('  hidden.')
