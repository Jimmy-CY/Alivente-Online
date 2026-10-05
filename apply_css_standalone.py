"""CS-2 - TWELVE TEMPLATES THAT CANNOT DRIFT FROM BASE.

   Found while measuring DR-2a. CS-1's drift census had been reporting
   six declarations on manual_pdf.html as a page beating base's
   stylesheets with a different value:

       .badge-info     color  base var(--alv-on-accent)  page #495057
       .badge-warning  color  base var(--alv-on-accent)  page #856404
       .badge-success  color  base var(--alv-on-accent)  page #155724
       ... and three more

   MANUAL_PDF NEVER SEES BASE. help.py renders it with render_to_string
   and hands the result to xhtml2pdf:

       html = render_to_string('manual_pdf.html', ctx)
       status = pisa.CreatePDF(src=html, dest=buf, encoding='utf-8')

   It has no {% extends %}, so base's four stylesheets are not in the
   document at all. It is not overriding base; it is a standalone
   document with no choice but to style itself. A census that compares
   it against a stylesheet which is not there is comparing against
   nothing, and calling the answer drift.

   TWELVE TEMPLATES ARE LIKE THAT, and none of them is an accident:

       manual_pdf, recipe_pdf, receipts/cash_receipt,
       invoices/physical_invoice           rendered to PDF
       fsr_email                           an email body
       help_modal_shell,
       components/pdf_viewer,
       wcim_recipe_quick_view              injected into a page that
                                           already has base
       budget_expense_details,
       revenue_details,
       total_expense_details               detail fragments, the same
       error_pages/connectivity_error      has to render when the
                                           database is down, so cannot
                                           afford a parent that queries it

   THE TEST IS THE TAG, NOT A LIST. A hard-coded list needs editing every
   time a page is added, and what makes a page standalone is exactly that
   it has no {% extends %}. alv_tree.standalone() reads it off the
   markup with the comments stripped, because a page explaining in a
   comment that it does not extend base is still not extending base.

   WHAT THIS CHANGES TODAY: nothing that was failing starts passing.
   Section 5 of test_css_order - the gate - is green either way, because
   no standalone page happens to collide with the block CS-1 moved. What
   changes is 5b's number and, more to the point, that the next drift
   round does not begin by rediscovering this.

   FILES: alv_tree.py, test_css_order.py.      [test_css_standalone.py]
"""
import os
import sys

SUFFIX = '.bak_standalone'

TREE = 'alv_tree.py'
CSS = 'test_css_order.py'

TREE_ANCHOR = 'def rel(path, base=None):'

TREE_BLOCK = '''def standalone(base=None):
    """Templates that do NOT extend base.html, so base cannot reach them.

    CS-2, 5 Oct 2026. Found while measuring DR-2a: CS-1's drift census
    reported six declarations on manual_pdf.html as a page beating base's
    stylesheets with a different value. It is not. manual_pdf is rendered
    by render_to_string and handed straight to xhtml2pdf - it never sees
    a browser and it never sees base. It has no choice but to style
    itself, and a census that compares it against a stylesheet which is
    not in the document is comparing against nothing.

    TWELVE OF THEM, and they are not an accident. PDF bodies, an email
    body, a modal shell, detail fragments injected into a page that
    already has base, and the connectivity error page, which has to
    render when the database is down and so cannot afford a parent
    template that queries it.

    THE TEST IS THE TAG, NOT A LIST. A list would need editing every time
    a page is added, and the thing that makes a page standalone is
    exactly that it has no {% extends %}. Read off the markup with the
    comments stripped, because a page explaining in a comment that it
    does not extend base is still not extending base.

    base.html itself is not standalone - it is the thing not extended -
    and is excluded.
    """
    out = []
    for p in templates(base):
        if os.path.basename(p) == 'base.html':
            continue
        with open(p, encoding='utf-8', errors='replace') as fh:
            s = code_only(fh.read())
        if not re.search(r'\\{%\\s*extends\\b', s):
            out.append(rel(p, base))
    return sorted(out)


def inherits_base(path, base=None):
    """Does this one template get base's stylesheets at all?"""
    return rel(path, base) not in standalone(base)


'''

# --- test_css_order.py: section 5 and 5b both learn about it -------------
C5_OLD = """    out = []
    for q in alv_tree.templates():
        name = alv_tree.rel(q)
        if name == BASE:
            continue
        text = now(q)
        spans = rules_of(text)"""

C5_NEW = """    out = []
    skip = set(alv_tree.standalone())
    for q in alv_tree.templates():
        name = alv_tree.rel(q)
        if name == BASE:
            continue
        # CS-2, 5 Oct 2026 - A PAGE THAT DOES NOT EXTEND BASE CANNOT
        # OVERRIDE IT. manual_pdf is rendered to a PDF by xhtml2pdf and
        # never sees base's stylesheets at all; twelve templates are
        # standalone like that. Comparing one against a block that is
        # not in the document is comparing against nothing.
        if name.replace(os.sep, '/') in skip:
            continue
        text = now(q)
        spans = rules_of(text)"""

B5_OLD = """    older = []
    for q in alv_tree.templates():
        name = alv_tree.rel(q)
        if name == BASE:
            continue
        for sel, props in decls_of(now(q)).items():"""

B5_NEW = """    older = []
    skip = set(alv_tree.standalone())
    for q in alv_tree.templates():
        name = alv_tree.rel(q)
        if name == BASE:
            continue
        if name.replace(os.sep, '/') in skip:        # CS-2 - see above
            continue
        for sel, props in decls_of(now(q)).items():"""

B5_TAIL_OLD = """    print('      those three blocks were always in the head. Logged for a')
    print('      drift round of its own - mostly .btn-info carrying #0e7c8b')
    print('      and manual_pdf.html\\'s print badges.')"""

B5_TAIL_NEW = """    print('      those three blocks were always in the head.')
    print('      %d standalone template(s) are not counted - they have no'
          % len(skip))
    print('      {% extends %}, so base never reaches them and they cannot')
    print('      override it. manual_pdf is rendered to a PDF by xhtml2pdf')
    print('      and had six declarations counted here until CS-2.')
    print('      DR-2a took the 16 that said what base says in other words;')
    print('      what is left really does differ.                 [CS-2]')"""


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    edits = 0

    tree = read(TREE)
    if 'def standalone(' not in tree:
        n = tree.count(TREE_ANCHOR)
        if n != 1:
            raise SystemExit('CS-2: %s in %s matched %d times, expected 1'
                             % (TREE_ANCHOR, TREE, n))
        at = tree.index(TREE_ANCHOR)
        tree = tree[:at] + TREE_BLOCK + tree[at:]
        # THE HELPERS IT LEANS ON MUST ALREADY BE THERE, and above it.
        for need in ('def templates(', 'def code_only(', 'def rel('):
            if need not in tree:
                raise SystemExit('CS-2: %s has no %s' % (TREE, need))
        if tree.index('def standalone(') < tree.index('def code_only('):
            raise SystemExit('CS-2: standalone() would be defined before '
                             'code_only(), which it calls')
        edits += 1
        if not check:
            backup(TREE)
            write(TREE, tree)

    css = read(CSS)
    if 'CS-2, 5 Oct 2026' not in css:
        for old, new, what in ((C5_OLD, C5_NEW, 'section 5'),
                               (B5_OLD, B5_NEW, 'section 5b'),
                               (B5_TAIL_OLD, B5_TAIL_NEW, "5b's footer")):
            k = css.count(old)
            if k != 1:
                raise SystemExit('CS-2: %s of %s matched %d times, expected '
                                 '1 - it has changed since this was read'
                                 % (what, CSS, k))
            css = css.replace(old, new, 1)
        edits += 1
        if not check:
            backup(CSS)
            write(CSS, css)

    print('CS-2  files changed : %d' % edits)
    if check:
        if edits:
            print('CS-2  NOT APPLIED')
            return 1
        print('CS-2  applied')
        return 0
    print('CS-2  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
