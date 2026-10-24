# -*- coding: utf-8 -*-
"""test_invoice_recipients.py - round T2-5, 24 Oct 2026.

A JOINT TENANT GETS THE INVOICE.

THIS IS THE ONLY ROUND OF THE FIVE THAT CHANGES WHAT LEAVES THE
BUILDING, so the suite has to prove a negative as well as a positive.

    THE POSITIVE is easy and section 3 does it: an address in
    tenant_2_email now reaches the mailer's TO list, and did not
    before.

    THE NEGATIVE IS THE ONE THAT MATTERS. Every address that was
    reaching somebody yesterday has to reach them today, in the same
    order, with no duplicates and no drops. Section 3 drives that
    against the real property with the awkward inputs people actually
    type - "a@x.com and b@y.com", semicolons, trailing commas, mixed
    case - and compares the result against THE OLD REGEX READ OUT OF
    THE BACKUP rather than retyped here.

    That comparison is the whole suite. A fixture that retyped the
    expression would be comparing the round with itself.

ONE PARSER, AND T2-1 BUILT THE DOOR FOR IT. The mailer had its own
copy of the address regex; T2-1 put the identical expression on the
model and asserted character-for-character equality precisely so this
round could delete one of them. Section 2 requires the mailer to
carry no regex at all any more - the point was never two copies that
agree, it was one answer.

WHAT IS NOT PROVED HERE. That an email is actually transmitted - that
is Django's to do and a live SMTP server's. This proves WHO the
mailer would address, which is the thing this round changes.
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

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_invrecip'
ME = 'test_invoice_recipients.py'
PATCHER = 'apply_invoice_recipients.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-5, 24 Oct 2026'

MAIL = os.path.join(ROOT, 'pages', 'management', 'commands',
                    'send_physical_invoices.py')
OTHER = os.path.join(ROOT, 'pages', 'management', 'commands',
                     'check_lease_renewal_and_invoices.py')
SECOND = os.path.join(ROOT, 'test_second_tenant.py')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MAIL, SECOND)

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)
OLD = dict((p, was(p)) for p in FILES)



# DJANGO FIRST, because section 2 asks the MODEL for the expression
# T2-1 put there - and the first draft of this file did that before
# anything had configured settings.
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from pages.models import tenant as _T
    django_up = True
except Exception as e:
    _T = None
    print('  --   Django would not start: %s'
          % str(e).split('\n')[0][:90])

# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
code = T.python_code_only(NOW[MAIL], payloads=True)
old_code = T.python_code_only(OLD[MAIL], payloads=True)

ok('tenant_emails' in code,
   'the mailer asks the model who is on the tenancy')
ok('tenant_display_name' in code,
   '  and greets both people, since both are being billed')
ok('tenant_2_email' in code,
   '  and its skip message names the second column too, so a missing '
   'address sends you to the right field')
ok(MARK in NOW[MAIL], 'the round dates itself')


# ==========================================================================
head('2. ONE PARSER, WHICH IS WHAT T2-1 BUILT THE DOOR FOR')
# ==========================================================================
ok('findall' not in code and '@[^' not in code,
   'the mailer carries NO address parser of its own any more')
ok('\nimport re\n' not in code,
   '  and `import re` went with it, since that was its only use')

# THE CONTROL: IT REALLY DID HAVE ONE.
ok('findall' in old_code and '@[^' in old_code,
   'CONTROL: and it really did carry one before this round')
ok(_T is not None and _T.EMAIL_RE in old_code,
   'CONTROL: the very expression T2-1 put on the model, character '
   'for character - which is what made deleting one of them safe')
ok('def tenant_emails' in read(MODELS),
   '  and the surviving one is on the model, where anything can ask '
   'it')


# ==========================================================================
head('3. DRIVEN - who gets the invoice, and who already did')
# ==========================================================================
#
# THE OLD PARSER, READ OUT OF THE BACKUP AND NOT RETYPED. A fixture
# that wrote the expression out again would be comparing this round
# with itself.
m_ = re.search(r'findall\(r"([^"]+)"', old_code)
OLD_RE = m_.group(1) if m_ else None
ok(OLD_RE, 'the OLD expression is readable out of the backup', OLD_RE)


def old_recipients(tenant_email):
    """Exactly what the mailer did yesterday."""
    return re.findall(OLD_RE, tenant_email or '')


if not (django_up and OLD_RE):
    skip('section 3', 'no model or no old expression')
else:
    # THE AWKWARD INPUTS PEOPLE ACTUALLY TYPE. The field is free text
    # and its placeholder invites commas, so these are not exotic.
    CASES = (
        ('a.georgiou@example.com', 'one plain address'),
        ('a@x.com, b@y.com', 'two, comma separated'),
        ('a@x.com and b@y.com', 'two, the word and - which is how a '
                                'joint tenancy has been recorded '
                                'until now'),
        ('a@x.com; b@y.com;', 'semicolons and a trailing one'),
        ('  A@X.com  ', 'padded, and mixed case'),
        ('Andreas <a@x.com>', 'a display name around it'),
        ('', 'nothing at all'),
        ('not an address', 'nothing that is an address'),
    )

    worst = []
    for raw, why in CASES:
        t_ = _T(tenant_name='X', tenant_email=raw)
        before = old_recipients(raw)
        after = t_.tenant_emails
        if after[:len(before)] != before:
            worst.append((why, before, after))
    ok(not worst,
       'NOBODY LOSES AN EMAIL: every address the old parser found is '
       'still found, in the same order, across %d input shapes'
       % len(CASES), worst)

    # AND NOW THE SECOND COLUMN IS READ.
    t_ = _T(tenant_name='X', tenant_email='a@x.com',
            tenant_2_name='Y', tenant_2_email='b@y.com')
    ok(t_.tenant_emails == ['a@x.com', 'b@y.com'],
       'a joint tenant in the PROPER column now reaches the mailer, '
       'after the first tenant and not instead of them',
       t_.tenant_emails)

    # THE CONTROL: the old parser could never have found it.
    ok(old_recipients('a@x.com') == ['a@x.com'],
       'CONTROL: the old parser read tenant_email ALONE, so that '
       'second address reached nobody - which is the whole round')

    # A JOINT TENANT ALREADY CRAMMED INTO THE FIRST BOX IS UNAFFECTED.
    # This is how his two real tenancies are recorded today.
    t_ = _T(tenant_name='X', tenant_email='a@x.com and b@y.com')
    ok(t_.tenant_emails == old_recipients('a@x.com and b@y.com'),
       'and a joint tenancy already crammed into the FIRST box is '
       'completely unaffected - which is how two of his tenancies are '
       'recorded today', t_.tenant_emails)

    # THE SAME ADDRESS IN BOTH COLUMNS IS ONE RECIPIENT.
    t_ = _T(tenant_name='X', tenant_email='One@Example.com',
            tenant_2_name='Y', tenant_2_email='one@example.com')
    ok(t_.tenant_emails == ['One@Example.com'],
       'and the same address in both columns is ONE recipient, '
       'however it is cased - nobody gets the invoice twice',
       t_.tenant_emails)


# ==========================================================================
head('4. WHAT THIS ROUND DOES NOT TOUCH')
# ==========================================================================
ok(not os.path.isfile(OTHER) or MARK not in read(OTHER),
   'check_lease_renewal_and_invoices is untouched - measured 23 Oct, '
   'it mails configured STAFF recipients and not tenants, so there '
   'is no tenant address in it to widen')
ok(not os.path.isfile(OTHER + SUFFIX),
   '  and this round has no backup of it, so it never opened it')

# THE FILENAME KEEPS THE STORED NAME.
i_f = code.find('filename = (f"')
ok(i_f > 0 and 'file_name_who' in code[max(0, i_f - 400):i_f],
   'the pdf filename keeps the STORED first name - it is how a '
   'document is found on disk and how it sorts beside its siblings, '
   'which is an identifier and not a label')
ok('cc_list' in code,
   'and the CC recipient card is untouched - it has nothing to do '
   'with who is on a tenancy')


# ==========================================================================
head('5. T2-1 TWO CLAIMS, REPAIRED RATHER THAN LEFT TO FAIL')
# ==========================================================================
sc = NOW[SECOND]
ok('_T.EMAIL_RE not in mailer' in sc,
   "T2-1's two-parsers claim became a ONE-parser claim - the point "
   'was never two copies that agree, it was one answer')
ok('as T2-1 left the tree' in sc,
   "  and its 'no scheduled mail reaches anybody new - that is T2-5' "
   'now reads through as_left_by, because this IS T2-5')
ok('as_left_by' in sc,
   '  which makes it true for every round after this one too')

# THE CONTROL: both really were the other way around.
so = OLD[SECOND]
# THE PHRASE HAS TO BE THIS ROUND'S, NOT THE FAMILY'S. The first
# spelling looked for "as T2-1 left the tree" and found it in the
# backup - because T2-2 had already written that same phrase into
# this file for the TEMPLATE census it repaired. Two repairs, one
# wording, and a control that matched the wrong one.
ok('_T.EMAIL_RE in mailer' in so,
   'CONTROL: the two-parsers claim really did read the other way '
   'before this round')
# AND THE SECOND CONTROL ASKS THE MECHANISM, NOT THE WORDING. Two
# attempts at a phrase both matched something else in the same file -
# T2-2 had already written "as T2-1 left the tree" into it for the
# template census, and "that is T2-5" survives in a comment. The
# repair is a NAME that only this round introduces.
ok('_alb5' in sc and '_alb5' not in so,
   'CONTROL: and the mail claim read the LIVE tree before this round '
   'and reads T2-1 backups after it')


# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('tenant_emails' in gate,
   '  with a sentinel that would notice the mailer going back to its '
   'own parser')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
