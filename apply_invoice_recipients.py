# -*- coding: utf-8 -*-
"""apply_invoice_recipients.py - round T2-5, 24 Oct 2026.

A JOINT TENANT GETS THE INVOICE.

His decision, 23 October: scheduled mail reaches BOTH tenants,
always. This is the round that does it, and it is the only one of the
five that changes what leaves the building.

IT IS SMALLER THAN IT SOUNDS, AND T2-1 IS WHY. The mailer already
pulls EVERY address out of tenant_email with a regex, because that
field is free text and always has been - the form labels it Email
Address(es) and its placeholder reads "One or more emails, separated
by commas". So a joint tenant crammed into that one box has been
receiving invoices for as long as anyone has typed them that way.

T2-1 PUT THE SAME EXPRESSION ON THE MODEL for exactly this moment,
and its suite asserted the two were character-for-character identical
precisely so this round could delete one of them. That claim is
repaired here rather than left to fail: the point was never that
there should be two copies that agree, it was that there should not
be two answers. One parser is the stronger form of the same claim.

WHAT CHANGES, EXACTLY:

    to_list now comes from tenant.tenant_emails, which reads
    tenant_email AND tenant_2_email with the one expression, in
    order, without repeats - a tenancy that already had both people
    in the first box is UNAFFECTED, because the same addresses come
    out in the same order.

    the SKIP message names both columns, because "no valid email in
    tenant_email" would send somebody to the wrong field.

    the greeting names both people, since both are being billed.

    `import re` goes, because line 244 was its only use and an unused
    import is a thing somebody later has to wonder about.

WHAT DOES NOT CHANGE:

    THE PDF FILENAME keeps the stored first name. It is how a
    document is found on disk and how it sorts beside its siblings -
    an identifier, not a label, and T2-4 drew that line everywhere
    else in the application yesterday.

    check_lease_renewal_and_invoices is NOT TOUCHED. Measured 23
    October: it mails CONFIGURED STAFF RECIPIENTS, not tenants. There
    is no tenant address in it to widen.

    THE CC LIST, which is a recipient card and nothing to do with who
    is on a tenancy.

NOBODY LOSES AN EMAIL. tenant_emails returns tenant_email's addresses
FIRST and in order, so every address that reached somebody yesterday
reaches them today. The suite proves that specifically, because a
round that changes who gets billed has to prove the negative as well
as the positive.

Idempotent. Every file backed up to .bak_invrecip.
"""
import os
import re
import sys

SUFFIX = '.bak_invrecip'
MAIL = os.path.join('pages', 'management', 'commands',
                    'send_physical_invoices.py')
SECOND = 'test_second_tenant.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'T2-5, 24 Oct 2026'
CHECK = False

# ----------------------------------------------------------- THE MAILER

R_WAS = '''            # tenant_email is a free-text field that may hold several addresses
            # (separated by "and", commas, spaces, etc.). Pull out every email so
            # the invoice reaches all recipients recorded on the tenant.
            raw_email = getattr(tenant, "tenant_email", "") or ""
            to_list = re.findall(r"[^\\s,;<>()]+@[^\\s,;<>()]+\\.[^\\s,;<>()]+", raw_email)'''

R_NOW = '''            # EVERY ADDRESS ON THE TENANCY, BOTH PEOPLE - T2-5,
            # 24 Oct 2026, his decision of 23 October.
            #
            # tenant_email is free text and always has been: the form
            # labels it Email Address(es) and its placeholder reads
            # "One or more emails, separated by commas". This used to
            # pull every address out of THAT ONE FIELD with a regex
            # written here - so a joint tenant typed into it has been
            # receiving invoices for as long as anyone typed them
            # that way, while one entered properly in tenant_2_email
            # received nothing.
            #
            # tenant_emails IS THE SAME PARSER, ON THE MODEL. T2-1 put
            # it there with this exact expression and its suite
            # asserted the two were identical character for character,
            # so that this round could delete one of them. Two copies
            # that agree today are still two answers tomorrow.
            #
            # NOBODY LOSES AN EMAIL: it returns tenant_email's
            # addresses first and in order, so a tenancy that already
            # had both people in the one box is unaffected.
            to_list = list(getattr(tenant, "tenant_emails", None) or [])'''

S_WAS = '''                    f"  SKIP {pi.invoice_number} ({tenant}): no valid email in "
                    f"tenant_email; stays approved for retry."'''

S_NOW = '''                    f"  SKIP {pi.invoice_number} ({tenant}): no valid email in "
                    f"tenant_email or tenant_2_email; stays approved "
                    f"for retry."'''

# THE GREETING NAMES BOTH PEOPLE, because both are being billed.
# The FILENAME below it deliberately does not - see the note there.
G_WAS = '''            subject = f"{period_label} - Rental Invoice"
            tenant_name = getattr(tenant, "tenant_name", "") or ""'''

G_NOW = '''            subject = f"{period_label} - Rental Invoice"
            # BOTH NAMES IN THE GREETING - T2-5, 24 Oct 2026. Both
            # people are being billed, so the letter addresses both.
            # tenant_display_name falls back to the stored name on a
            # tenancy with one person, so nothing moves for them.
            tenant_name = getattr(tenant, "tenant_display_name", "") or ""'''

# AND THE FILENAME KEEPS THE STORED NAME.
F_WAS = '''            filename = (f"{pi.invoice_number} - {tenant_name} - "
                        f"({year:04d}-{month:02d}-01).pdf")'''

F_NOW = '''            # THE FILENAME KEEPS THE STORED FIRST NAME - T2-5.
            # It is how a document is found on disk and how it sorts
            # beside its siblings: an identifier, not a label, which
            # is the line T2-4 drew everywhere else yesterday.
            file_name_who = getattr(tenant, "tenant_name", "") or ""
            filename = (f"{pi.invoice_number} - {file_name_who} - "
                        f"({year:04d}-{month:02d}-01).pdf")'''

I_WAS = '''import re
'''

I_NOW = ''

# ------------------------------------------- T2-1'S TWO EXPIRING CLAIMS

C_WAS = '''        ok(_T.EMAIL_RE in mailer,
           '  CONTROL: and it is the SAME expression the mailer uses, '
           'character for character - two parsers would be two answers '
           'to who is on a tenancy')'''

C_NOW = '''        # ONE PARSER, WHICH IS THE STRONGER FORM OF THE SAME CLAIM -
        # repaired by T2-5, 24 Oct 2026, the round that deleted the
        # second copy.
        #
        # T2-1 asserted the mailer carried this expression CHARACTER
        # FOR CHARACTER, and said in its own note that two parsers
        # would be two answers to who is on a tenancy. It was right,
        # and the remedy was never to keep two copies in agreement -
        # it was to have one. The mailer now calls tenant_emails.
        #
        # NOT read through as_left_by: "there is only one parser" is a
        # LIVE invariant and has to be true today, not merely true on
        # the day T2-1 ran.
        ok(_T.EMAIL_RE not in mailer,
           '  CONTROL: and the mailer no longer carries a SECOND copy '
           'of that expression - T2-5 deleted it, because two parsers '
           'that agree today are still two answers tomorrow')
        ok('tenant_emails' in mailer,
           '  CONTROL: it asks the model instead, so there is exactly '
           'one answer to who is on a tenancy')'''

T_WAS = '''touched = []
for n in mailers:
    full = os.path.join(ROOT, 'pages', 'management', 'commands', n)
    if os.path.isfile(full) and ('tenant_2' in read(full)
                                 or MARK in read(full)):
        touched.append(n)
ok(not touched,
   'and no scheduled mail reaches anybody new - that is T2-5, decided '
   'as BOTH TENANTS but not built here, because it changes behaviour '
   'on a job that runs every five minutes', touched)'''

T_NOW = '''# AS T2-1 LEFT THE TREE, NOT AS IT STANDS - repaired by T2-5,
# 24 Oct 2026, which is the round this sentence was waiting for.
#
# "No scheduled mail reaches anybody new - that is T2-5" was true on
# 24 October and false the same day. The claim worth keeping is about
# T2-1: that the round which added three columns did not also change
# who receives mail, because a round that did both would be two
# claims in one - and the second changes behaviour on a job that runs
# every five minutes.
try:
    from alv_rounds import as_left_by as _alb5
except Exception:
    _alb5 = None
touched = []
for n in mailers:
    full = os.path.join(ROOT, 'pages', 'management', 'commands', n)
    if not os.path.isfile(full):
        continue
    text_ = _alb5(full, SUFFIX, read) if _alb5 else read(full)
    if 'tenant_2' in text_ or MARK in text_:
        touched.append(n)
ok(not touched,
   'and no scheduled mail reached anybody new as T2-1 left the tree - '
   'the columns and who receives mail were deliberately two rounds, '
   'because the second changes behaviour on a job that runs every '
   'five minutes', touched)'''


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
    raise SystemExit('T2-5 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pm = os.path.join(root, MAIL)
    m = read(pm)
    if MARK in m:
        print('T2-5  already applied - a joint tenant gets the invoice.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    mods = read(os.path.join(root, 'pages', 'models.py'))
    if 'def tenant_emails' not in mods:
        refuse('T2-1 is not applied - pages/models.py has no '
               'tenant_emails, so there is nothing for the mailer to '
               'ask. getattr would return None and EVERY invoice '
               'would skip for want of an address.')
    if 'def tenant_display_name' not in mods:
        refuse('T2-2 is not applied - no tenant_display_name for the '
               'greeting.')

    m = swap(m, R_WAS, R_NOW, '%s (the recipients)' % MAIL)
    m = swap(m, S_WAS, S_NOW, '%s (the skip message)' % MAIL)
    m = swap(m, G_WAS, G_NOW, '%s (the greeting)' % MAIL)
    m = swap(m, F_WAS, F_NOW, '%s (the filename)' % MAIL)
    out[pm] = swap(m, I_WAS, I_NOW, '%s (the unused import)' % MAIL)

    ps = os.path.join(root, SECOND)
    sc = swap(read(ps), C_WAS, C_NOW, '%s (the two-parsers claim)' % SECOND)
    out[ps] = swap(sc, T_WAS, T_NOW, '%s (the expiry-dated claim)' % SECOND)

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_report_names.py'
)""", """    'test_report_names.py',
    # T2-5, 24 Oct 2026 - a joint tenant gets the invoice.
    'test_invoice_recipients.py'
)""", '%s (the suites)' % PS1)
    q = swap(q,
             """    @{ File = 'pages/models.py'; Text = 'def joint_name';""",
             """    @{ File = 'pages/management/commands/send_physical_invoices.py'; Text = 'tenant_emails'; What = 'T2-5: the invoice mailer asks the MODEL who is on a tenancy rather than carrying its own copy of the address parser - T2-1 put the same expression on the model for exactly this moment, and two parsers that agree today are still two answers tomorrow' },
    @{ File = 'pages/models.py'; Text = 'def joint_name';""",
             '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_report_names.py',
]""", """    'test_report_names.py',
    # T2-5, 24 Oct 2026 - a joint tenant gets the invoice.
    'test_invoice_recipients.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_reportnames',
]""", """    '.bak_reportnames',
    # T2-5, 24 Oct 2026 - a joint tenant gets the invoice.
    '.bak_invrecip',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # T2-5, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nm = T.python_code_only(out[pm], payloads=True)

    # ONE PARSER. The whole point of the round.
    if 'tenant_emails' not in nm:
        refuse('%s: the mailer does not ask tenant_emails' % MAIL)
    if '@[^' in nm or 'findall' in nm:
        refuse('%s: the mailer still carries its own address parser. '
               'Two parsers are two answers to who is on a tenancy, '
               'which is what T2-1 note said when it put the '
               'expression on the model.' % MAIL)
    if '\nimport re\n' in nm:
        refuse('%s: `import re` is still there with nothing using it.'
               % MAIL)

    # AND THE OTHER MAILER IS NOT TOUCHED. Measured 23 October: it
    # mails configured STAFF recipients, not tenants.
    other = os.path.join(root, 'pages', 'management', 'commands',
                         'check_lease_renewal_and_invoices.py')
    if os.path.isfile(other) and MARK in read(other):
        refuse('check_lease_renewal_and_invoices was edited. It mails '
               'configured STAFF recipients, not tenants - there is '
               'no tenant address in it to widen.')

    # THE FILENAME KEEPS THE STORED NAME.
    i_f = nm.find('filename = (f"')
    if i_f < 0 or 'file_name_who' not in nm[max(0, i_f - 400):i_f]:
        refuse('%s: the pdf filename no longer uses the stored first '
               'name. It is how a document is found on disk - an '
               'identifier, not a label.' % MAIL)

    if CHECK:
        print('T2-5  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        one parser, two recipients')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('T2-5  applied - a joint tenant gets the invoice, and the '
          'mailer stopped keeping its own copy of the address parser.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
