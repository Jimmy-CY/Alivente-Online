# -*- coding: utf-8 -*-
"""apply_ref_link.py - round IR-1, 23 Oct 2026.

G1: TWO REGISTERS FOR ONE KIND OF IDENTIFIER.

Demetri's finding, 16 October: the receipt number is small grey
monospace; the invoice number is a teal link. Two ways of painting the
same kind of thing, in one application.

It sat on the outstanding list for a week behind this note:

    "it is a BASE component, so this reaches every .ref in the
     application - needs Demetri's call before anything is built"

THAT WAS TRUE OF THE RULE AND FALSE OF THE PRACTICE. Measured on 23
October: `.alv-table .ref` is defined once in base.html and used on
EXACTLY ONE PAGE, on one cell - the Receipt # column of
cash_receipts.html. No Python names it, no script names it, and no
suite pins it. The thing that made this feel risky for a week was not
there.

AND IT WAS NOT A LINK AT ALL, which is the other half. The receipt
number was grey monospace text because there was nowhere for it to go.
RV-1 built the destination in this same push; this round points at it.

ONE REGISTER, AND IT IS THE INVOICE'S. Demetri chose it on 23 October:
teal, weight 600, underline on hover. The accepted cost is the
monospace alignment of the number column.

SO THE COMPONENT GOES IN BASE AND BOTH PAGES TAKE IT. The invoice list
carried its own `.pi-number-link` with those exact three declarations.
Leaving it there and adding a second copy for receipts would make "one
register for one kind of identifier" a thing that happens to be true
today rather than a thing the stylesheet says. Two templates, one
rule.

AND THE DEAD RULE GOES. `.alv-table .ref` has no consumer after this
round. A base rule nothing uses is a rule the next person will use by
accident.

NO MIGRATION, no view change, no new route - RV-1 brought those.

Idempotent. Every file backed up to .bak_reflink.
"""
import os
import re
import sys

SUFFIX = '.bak_reflink'
BASE = os.path.join('pages', 'templates', 'base.html')
RECEIPTS = os.path.join('pages', 'templates', 'cash_receipts.html')
INVOICES = os.path.join('pages', 'templates', 'physical_invoice_list.html')
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_ref_link.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'IR-1, 23 Oct 2026'
CHECK = False
CREATES = ()

# ==========================================================================
# ONE REGISTER, IN BASE
# ==========================================================================
B_WAS = '''      .alv-table .ref {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 12.5px;
        color: var(--alv-ink-soft);
      }'''

B_NOW = '''      /* AN IDENTIFIER YOU CAN CLICK - IR-1, 23 Oct 2026. G1.
         Demetri, 16 Oct: the receipt number is small grey monospace,
         the invoice number is a teal link. Two registers for one kind
         of thing. He chose the invoice's on 23 October.

         ONE RULE, NOT TWO. physical_invoice_list carried its own
         .pi-number-link with these exact three declarations. A second
         copy here would make "one register" true by coincidence
         rather than by construction, so both pages take this.

         WHAT WAS HERE: .alv-table .ref, monospace 12.5px in
         --alv-ink-soft, defined in base and used on ONE cell of ONE
         page. It is gone rather than left, because a base rule with
         no consumer is one the next page will pick up by accident. */
      .alv-ref-link {
        color: var(--alv-accent);
        text-decoration: none;
        font-weight: 600;
      }
      .alv-ref-link:hover { text-decoration: underline; }'''

# ==========================================================================
# AND THE RECEIPT NUMBER TAKES IT, AND GOES SOMEWHERE
# ==========================================================================
R_WAS = '''            <td data-label="Receipt #" class="ref">{{ row.number }}{% if row.is_edited %}'''

R_NOW = '''            {# IR-1, 23 Oct 2026 - G1. This was grey monospace text,    #}
            {# not a link, because until RV-1 there was nowhere for it  #}
            {# to go. It now wears the same register as the invoice     #}
            {# number and opens the record behind the receipt.          #}
            <td data-label="Receipt #"><a href="{% url 'cash_receipt_detail' row.pk %}" class="alv-ref-link">{{ row.number }}</a>{% if row.is_edited %}'''

# ==========================================================================
# AND THE INVOICE NUMBER STOPS CARRYING ITS OWN COPY
# ==========================================================================
I_WAS = '''.pi-number-link { color: var(--alv-accent); text-decoration: none; font-weight: 600; }
.pi-number-link:hover { text-decoration: underline; }'''

I_NOW = '''/* .pi-number-link IS GONE - IR-1, 23 Oct 2026. Its three declarations
   are now .alv-ref-link in base, which the receipt number also takes.
   G1 was "two registers for one kind of identifier"; one rule in one
   place is the only version of the fix that stays fixed. */'''

I2_WAS = '''class="pi-number-link">{{ row.number }}</a>
              {% else %}
                <a href="{% url 'physical_invoice_edit' row.pk %}" class="pi-number-link">{{ row.number }}</a>'''

I2_NOW = '''class="alv-ref-link">{{ row.number }}</a>
              {% else %}
                <a href="{% url 'physical_invoice_edit' row.pk %}" class="alv-ref-link">{{ row.number }}</a>'''


# DOES ANY class ATTRIBUTE CARRY THE TOKEN `ref` EXACTLY?
#
# NOT a \bref\b search. A hyphen is a word boundary, so that pattern
# matches inside `alv-ref-link` - this round's OWN new class - and the
# gate below refused the round for the thing it had just added.
# Splitting the attribute into tokens is the only version that asks
# the question that was meant.
def wears_ref(src):
    for m in re.finditer(r'class="([^"]*)"', src):
        if 'ref' in m.group(1).split():
            return True
    return False


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
    raise SystemExit('IR-1 REFUSED: %s' % msg)


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

    pb = os.path.join(root, BASE)
    b = read(pb)
    if MARK in b:
        print('IR-1  already applied - one register for one kind of '
              'identifier.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # RV-1 GOES FIRST IN THIS PUSH. This round points the receipt
    # number at a screen, and a link to a route that does not exist is
    # a NoReverseMatch on the receipts list - every receipt, every
    # time.
    pr = os.path.join(root, RECEIPTS)
    if 'cash_receipt_detail' not in read(os.path.join(root, 'pages',
                                                      'urls.py')):
        refuse('pages/urls.py: RV-1 is not applied, and this round '
               'links to the route it brings. Without it the receipts '
               'list raises NoReverseMatch on every row')

    # AND .ref REALLY DOES HAVE ONE CONSUMER - measured, not assumed.
    # The note that blocked this round for a week said it reached
    # every table in the application.
    users = []
    for folder, dirs, names in os.walk(os.path.join(root, 'pages')):
        dirs[:] = [d for d in dirs if d not in ('__pycache__',)]
        for n in names:
            if '.bak_' in n or not n.endswith(('.html', '.py', '.js')):
                continue
            p = os.path.join(folder, n)
            if wears_ref(read(p)):
                users.append(os.path.relpath(p, root))
    if sorted(users) != [RECEIPTS]:
        refuse('%s: class="ref" is worn by %s. This round deletes the '
               'rule and expected exactly one wearer'
               % (BASE, ', '.join(sorted(users)) or '(nothing)'))

    out[pb] = swap(b, B_WAS, B_NOW, '%s (the register)' % BASE)
    out[pr] = swap(read(pr), R_WAS, R_NOW,
                   '%s (the receipt number)' % RECEIPTS)

    pi = os.path.join(root, INVOICES)
    i = read(pi)
    i = swap(i, I_WAS, I_NOW, '%s (the old local rule)' % INVOICES)
    i = swap(i, I2_WAS, I2_NOW, '%s (both invoice links)' % INVOICES)
    out[pi] = i

    # ---- REGISTRATION
    pg = os.path.join(root, PS1)
    g = read(pg)
    g = swap(g, """    'test_receipt_view.py'
)""", """    'test_receipt_view.py',
    # IR-1, 23 Oct 2026 - one register for one kind of identifier, and
    # the receipt number finally goes somewhere. G1.
    'test_ref_link.py'
)""", '%s (the suites)' % PS1)
    g = swap(g,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/templates/base.html'; Text = 'alv-ref-link'; What = 'IR-1: the receipt number was grey monospace and the invoice number a teal link - two registers for one kind of identifier, Demetri 16 Oct. One rule in base now, which BOTH pages take; a second copy would make one register true by coincidence' },
    @{ File = 'pages/templates/base.html'; Text = '.alv-table .ref'; Absent = $true; Code = $true; What = 'IR-1: and the rule it replaced is gone rather than left. It had one consumer and no suite; a base rule nothing uses is one the next page picks up by accident' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pg] = g

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # RV-1, 23 Oct 2026 - the receipt has a screen for its record.
    'test_receipt_view.py',
]""", """    # RV-1, 23 Oct 2026 - the receipt has a screen for its record.
    'test_receipt_view.py',
    # IR-1, 23 Oct 2026 - one register for one kind of identifier.
    'test_ref_link.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_receiptview',
]""", """    '.bak_receiptview',
    # IR-1, 23 Oct 2026 - one register for one kind of identifier.
    '.bak_reflink',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # IR-1, 23 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    #
    # check_gates says IR-1 is already in use, named in
    # apply_receipt_view.py and test_receipt_view.py. It is, once in
    # each, and on purpose: RV-1 builds a screen with no route to it
    # and says in its docstring that IR-1 points the receipt number at
    # it in this same push. That is a forward reference from the round
    # that builds a thing to the round that reaches it - the same
    # shape as DP-1 naming SD-1 on 22 October - and not a second round
    # wearing this name. The MP-2 case the check warns about was a
    # round that owned no suffix at all; this one owns .bak_reflink.
    nb = T.code_only(out[pb])

    # THE OLD RULE IS GONE, NOT SHADOWED.
    if '.alv-table .ref' in nb:
        refuse('%s: the old rule is still here. A register that is '
               'replaced and left behind is two registers again' % BASE)
    if '.alv-ref-link' not in nb:
        refuse('%s: the new component is not in base' % BASE)

    # AND IT IS DEFINED ONCE IN THE WHOLE TREE.
    #
    # READ FROM `out` FOR THE FILES THIS ROUND IS ABOUT TO WRITE, and
    # from disk for everything else. The first version read only disk
    # and so, under --check, could not see the rule it was adding - it
    # refused the round for defining the component nowhere.
    defs = []
    for folder, dirs, names in os.walk(os.path.join(root, 'pages')):
        for n_ in names:
            if '.bak_' in n_ or not n_.endswith('.html'):
                continue
            p = os.path.join(folder, n_)
            src = out.get(p, None)
            if src is None:
                src = read(p)
            if re.search(r'\.alv-ref-link\s*\{', src):
                defs.append(os.path.relpath(p, root))
    if defs != [BASE]:
        refuse('%s: .alv-ref-link is defined in %s. One register means '
               'one definition' % (BASE, ', '.join(defs)))

    # AND NOTHING STILL WEARS THE OLD NAMES.
    nr = T.code_only(out[pr])
    ni = T.code_only(out[pi])
    if wears_ref(nr):
        refuse('%s: the receipt cell still wears class="ref", whose '
               'rule this round deleted' % RECEIPTS)
    if 'pi-number-link' in ni:
        refuse('%s: pi-number-link survives, so the invoice number and '
               'the receipt number are painted by two rules again'
               % INVOICES)
    if ni.count('alv-ref-link') != 2:
        refuse('%s: %d invoice link(s) take the shared register, and '
               'there are two' % (INVOICES, ni.count('alv-ref-link')))

    # AND THE RECEIPT NUMBER REALLY GOES SOMEWHERE.
    if "{% url 'cash_receipt_detail' row.pk %}" not in nr:
        refuse('%s: the receipt number is painted as a link and points '
               'at nothing' % RECEIPTS)

    # THE TEMPLATES MUST STILL BALANCE - SB-2's lesson, 22 Oct 2026.
    for name, src in ((BASE, out[pb]), (RECEIPTS, out[pr]),
                      (INVOICES, out[pi])):
        body = T.code_only(src)
        for a, bb in (('if', 'endif'), ('for', 'endfor'),
                      ('block', 'endblock')):
            o = len(re.findall(r'{%%\s*%s\b' % a, body))
            c = len(re.findall(r'{%%\s*%s\b' % bb, body))
            if o != c:
                refuse('%s: %d {%% %s %%} against %d {%% %s %%}'
                       % (name, o, a, c, bb))

    if CHECK:
        print('IR-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        one register for one kind of identifier')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('IR-1  applied - one register for one kind of identifier, and '
          'the receipt number goes somewhere.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
