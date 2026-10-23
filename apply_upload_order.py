# -*- coding: utf-8 -*-
"""apply_lease_upload.py - round UO-1, 23 Oct 2026.

TWO DOCUMENT UPLOADS STILL DESTROY THE OLD FILE BEFORE THE NEW ONE IS
SAFE. SI-1 fixed this on 22 October and swept recipes. Nobody swept
the rest of the tree, and these two were left standing:

  pages/views/tenants.py          the tenant LEASE AGREEMENT
  pages/views/administration.py   the property TITLE DEED

Both do the same thing, and it is the thing SI-1's own docstring
describes:

    field.delete(save=False)        <- the bytes are gone NOW
    instance.field = uploaded_file  <- not committed
    instance.save()                 <- can raise

A save that fails after that line leaves the file destroyed and the
row still naming it. That is not a theory: it is how 71 Cottage Pie
and 336 Beans, Edamame lost their photographs, demonstrated on 22
October by a POST that omitted difficulty_level - the except fired,
the redirect looked like success, and the picture was already gone.

A LEASE AGREEMENT IS WORSE THAN A PHOTOGRAPH. A recipe photo can be
taken again. A signed lease is the only copy of an agreement, and the
upload screen it is lost from is the one Demetri uses most.

THE FIX IS SI-1's, NOT A NEW ONE. let_go_of_file releases the
reference and returns the name, deleting nothing; delete_unheld
removes the bytes AFTER the save has committed, and only for a name
no other row still holds. Writing a second version of that here would
be two code paths for one job - and the counting half matters, because
duplicate_tenant copies a tenant and two rows can name one file.

WHAT THIS ROUND IS NOT. It is not a sweep of every
`.delete(save=False)` in the tree. There are nine call sites and
seven of them are correct: they delete a document deliberately and
assign None, or they delete nothing that is being replaced. The gate
below carries the detector that tells the two apart, so the next one
written in the wrong order is refused rather than discovered.

THE NAME IS UO-1 AND NOT LU-1, which is what this round was called
for about ten minutes. check_gates refused it: LU-1 already belongs to
apply_login_url.py, which owns .bak_loginurl and is registered in four
files. Two rounds with one name make the register ambiguous, and
renaming afterwards rewrites the older round's comments - history
edited to make room, which is what happened on 18 October and cost a
careful undo. Recorded here because the next person to reach for a
two-letter name should run the gate before, not after.

Idempotent. Every file backed up to .bak_uploadorder.
"""
import os
import re
import sys

SUFFIX = '.bak_uploadorder'
TEN = os.path.join('pages', 'views', 'tenants.py')
ADM = os.path.join('pages', 'views', 'administration.py')
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'UO-1, 23 Oct 2026'
CHECK = False

CREATES = ()

T_IMP_WAS = ("from ..models import PhysicalInvoiceProfile, invoices, "
             "props, tenant")
T_IMP_NOW = ("from ..models import (PhysicalInvoiceProfile, invoices, "
             "props, tenant,\n                      delete_unheld, "
             "let_go_of_file)")

T_WAS = """                        # Delete old file if exists
                        if tenant_obj.tenant_lease_agreement:
                            tenant_obj.tenant_lease_agreement.delete(save=False)

                        # Save new file
                        tenant_obj.tenant_lease_agreement = uploaded_file
                        tenant_obj.tenant_lease_agreement_status = "Lease Agreement Uploaded"
                        tenant_obj.save()"""

T_NOW = """                        # UO-1, 23 Oct 2026. THE OLD LEASE IS RELEASED
                        # BEFORE THE SAVE AND DELETED AFTER IT, which is
                        # SI-1's rule applied to the file that matters
                        # most. This used to call delete(save=False) and
                        # then save(), so anything that raised in between
                        # left the lease destroyed and the row still
                        # naming it. A recipe photo can be taken again; a
                        # signed lease agreement cannot.
                        released = [let_go_of_file(
                            tenant_obj, 'tenant_lease_agreement')]

                        tenant_obj.tenant_lease_agreement = uploaded_file
                        tenant_obj.tenant_lease_agreement_status = "Lease Agreement Uploaded"
                        tenant_obj.save()

                        # AND IT COUNTS FIRST. duplicate_tenant copies a
                        # tenant, so two rows can name one file; the last
                        # row out turns off the light.
                        delete_unheld(tenant, released,
                                      ('tenant_lease_agreement',))"""

A_IMP_WAS = "from ..models import UserProfile, props, tenant"
A_IMP_NOW = ("from ..models import (UserProfile, props, tenant,\n"
             "                      delete_unheld, let_go_of_file)")

A_WAS = """                        # Delete old file if exists (so the FileField swap is clean)
                        if property_obj.prop_title_deed:
                            property_obj.prop_title_deed.delete(save=False)

                        # Save new file via the FileField (uses title_deed_upload_path)
                        property_obj.prop_title_deed = uploaded_file
                        property_obj.prop_title_deed_status = "Available"
                        property_obj.save()"""

A_NOW = """                        # UO-1, 23 Oct 2026. RELEASED BEFORE THE SAVE,
                        # DELETED AFTER IT - SI-1's rule. The old order
                        # destroyed the title deed first and then saved,
                        # so a save that raised left the deed gone and
                        # the row still pointing at it.
                        released = [let_go_of_file(
                            property_obj, 'prop_title_deed')]

                        # Save new file via the FileField (uses title_deed_upload_path)
                        property_obj.prop_title_deed = uploaded_file
                        property_obj.prop_title_deed_status = "Available"
                        property_obj.save()

                        delete_unheld(props, released,
                                      ('prop_title_deed',))"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('UO-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


# THE DETECTOR, WHICH IS ALSO THE GATE.
#
# The dangerous shape is `field.delete(save=False)` followed by the
# SAME field being assigned A NEW FILE. Assigning None is a deliberate
# removal and is correct; so is a delete with no reassignment at all.
# The first spelling of this detector did not make that distinction
# and reported four sites, two of which were innocent - a census that
# over-reports is as useless as one that under-reports.
def losers(text):
    out = []
    lines = text.replace('\r\n', '\n').split('\n')
    for i, ln in enumerate(lines):
        m = re.search(r'(\w+)\.(\w+)\.delete\(save=False\)', ln)
        if not m:
            continue
        obj, fld = m.group(1), m.group(2)
        win = '\n'.join(lines[i + 1:i + 12])
        a = re.search(r'\b%s\.%s\s*=\s*(\S+)' % (obj, fld), win)
        if a and a.group(1).rstrip(',)').strip() != 'None':
            out.append('%s.%s line %d' % (obj, fld, i + 1))
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, TEN)
    pa = os.path.join(root, ADM)
    t, a = read(pt), read(pa)

    if MARK in t:
        print('UO-1  already applied - the lease and the deed are '
              'released before the save and deleted after it.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # SI-1 MUST HAVE APPLIED, because this round calls its helpers.
    m = read(os.path.join(root, 'pages', 'models.py'))
    for want in ('def let_go_of_file', 'def delete_unheld',
                 'def file_holders'):
        if want not in m:
            refuse('pages/models.py has no %s. This round uses SI-1\'s '
                   'helpers rather than writing a second copy of them, '
                   'so SI-1 must apply first.' % want)

    # AND THE TWO SITES MUST STILL BE BROKEN. A round that repairs
    # something already repaired has nothing to say.
    before = losers(t) + losers(a)
    if len(before) != 2:
        refuse('expected exactly the two known delete-before-assign '
               'sites, found %d: %r. If the tree has changed, this '
               'round must be re-measured rather than applied.'
               % (len(before), before))

    out[pt] = swap(swap(t, T_IMP_WAS, T_IMP_NOW, '%s (the import)' % TEN),
                   T_WAS, T_NOW, '%s (the lease upload)' % TEN)
    out[pa] = swap(swap(a, A_IMP_WAS, A_IMP_NOW, '%s (the import)' % ADM),
                   A_WAS, A_NOW, '%s (the title deed upload)' % ADM)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_esign_pdf.py'
)""", """    'test_esign_pdf.py',
    # UO-1, 23 Oct 2026 - the lease and the deed survive a failed save.
    'test_upload_order.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/views/tenants.py'; Text = 'let_go_of_file'; What = 'UO-1: the old lease is RELEASED before the save and its bytes deleted after it, because delete-then-save destroys the file whenever the save raises - which is how two recipe photos were lost on 22 October, and a signed lease cannot be taken again' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # ES-2, 23 Oct 2026 - the page images and the appended seal.
    'test_esign_pdf.py',
]""", """    # ES-2, 23 Oct 2026 - the page images and the appended seal.
    'test_esign_pdf.py',
    # UO-1, 23 Oct 2026 - SI-1's rule reaches the lease and the deed.
    'test_upload_order.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_esignpdf',
]""", """    '.bak_esignpdf',
    # UO-1, 23 Oct 2026 - SI-1's rule reaches the lease and the deed.
    '.bak_uploadorder',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # UO-1, 23 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    after = losers(out[pt]) + losers(out[pa])
    if after:
        refuse('a delete-before-assign site survives this round: %r'
               % after)

    for path, code, model, field in (
            (TEN, out[pt], 'tenant', 'tenant_lease_agreement'),
            (ADM, out[pa], 'props', 'prop_title_deed')):
        c = T.python_code_only(code, payloads=True)
        if 'let_go_of_file' not in c or 'delete_unheld' not in c:
            refuse('%s does not use SI-1\'s helpers' % path)
        # THE ORDER IS THE WHOLE ROUND.
        rel = c.find("let_go_of_file(")
        sv = c.find('.save()', rel)
        dele = c.find('delete_unheld(', rel)
        if not (0 <= rel < sv < dele):
            refuse('%s: the order is wrong. Release, THEN save, THEN '
                   'delete. Any other order is the bug this round '
                   'exists to remove. (release %d, save %d, delete %d)'
                   % (path, rel, sv, dele))
        if ("'%s'" % field) not in c:
            refuse('%s does not name %s' % (path, field))

    # AND THE SEVEN INNOCENT SITES ARE UNTOUCHED.
    for p_ in ('pages/views/expenses.py', 'pages/views/receipts.py',
               'pages/views/physical_invoices.py',
               'pages/views/properties.py'):
        full = os.path.join(root, p_.replace('/', os.sep))
        if os.path.isfile(full) and MARK in read(full):
            refuse('%s was edited. It deletes a document deliberately '
                   'and assigns None, which is correct; widening this '
                   'round to it would remove a feature.' % p_)

    if CHECK:
        print('UO-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        the two sites repaired: %s' % ', '.join(before))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('UO-1  applied - the lease agreement and the title deed are '
          'released before the save and deleted after it.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      repaired: %s' % ', '.join(before))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
