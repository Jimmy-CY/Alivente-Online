# -*- coding: utf-8 -*-
"""apply_label_fit.py - a label that does not fit its own column.

    python apply_label_fit.py --check     # dry run, writes nothing
    python apply_label_fit.py             # apply
    python test_label_fit.py              # the suite
    python Push-PendingChanges.ps1        # the gate

WHAT WENT WRONG, AND WHOSE FAULT IT WAS

  Push 2 rebuilt three panels under a rule I wrote:

      "A row whose membership does not change keeps its widths. A rebuilt
       row is three across at col-md-4, or four across at col-md-3 where a
       panel holds exactly four fields."

  That rule never asked whether the LABELS fit. On properties_edit the
  label 'Include in Occupancy Calculations' takes two lines inside a
  col-md-3, which pushes its <select> below the other three and the row
  reads as broken. It is my rule and it is what produced the defect.

  It went unseen because the fixture I measured it in HAD NO SIDEBAR. The
  real page has a fixed 240px sidebar plus 20px of padding either side, so

      content width = viewport - 280

  and a col-md-3 on a 1280-wide window is 240px, not 310. Measured with the
  sidebar in place the wrap reproduces exactly as reported.

  Two widths, and they are not the same number: .main-content's own box
  begins after the sidebar margin but still contains its padding, so it
  measures viewport - 240. What a column is laid out in is the wrapper
  inside that padding - viewport - 280. test_label_fit.py section 3
  asserts both, because asserting the wrong one is how a fixture passes
  while describing a page 40px wider than the real one.

  A second thing the correct fixture showed: the sidebar is display:none at
  <=991px, so this defect lives in a band of 992..1366 and NOWHERE ELSE,
  and its worst point is viewport 992 - a 168px column, narrower than
  anything the app renders on a phone.

THE AMENDED RULE

  Four across at col-md-3 is allowed only where every label in the panel
  fits ON ONE LINE at 168px. Measured by test_label_fit.py over the whole
  corpus, not judged per panel. Otherwise the panel is two across.

WHAT THIS ROUND CHANGES - FOUR LABELS, AND NOTHING ELSE

  No width changes. No CSS. No field moves. Only the text a human reads:

    properties_add, properties_edit
      'Include in Occupancy Calculations'  ->  'Include in Occupancy'
      Measured: fits at 240px AND at 168px, so it holds at every width the
      application renders, not only at the one that was reported.

    tenant_add   'Rental Payment Terms (Days)'  ->  'Payment Terms'
    tenant_edit  'Rental Payment Terms'         ->  'Payment Terms'
      The same field carried two different labels on the add and the edit
      screen. 'Payment Terms' is the ONLY candidate measured to fit at
      168px - 'Rental Payment Terms' and 'Payment Terms (Days)' both wrap
      there - and it is already what property_detail, tenant_report and
      open_invoices_report call this field, so the entry screens now agree
      with the rest of the system instead of disagreeing with it. The
      '(Days)' is not lost: both inputs already carry the placeholder
      'Payment Terms (Days)'.

WHAT THIS ROUND DELIBERATELY DOES NOT CHANGE

  * The Physical Invoice checkbox labels on tenant_add and tenant_edit.
    They wrap from 1366 down, and they were in scope until they were
    measured: the checkbox is inline BEFORE the text, so both checkboxes
    hold a common top at every width and nothing is out of line. What
    reflows is the explanatory clause after the em-dash, which is prose
    doing what prose does. Trimming it would delete information to fix a
    defect that is not there.

  * pages/models.py. prop_include_in_occupancy carries
    verbose_name="Include in Occupancy Metrics" - a THIRD wording for this
    one field. Aligning it is right, but a verbose_name change generates a
    migration, and a migration does not belong in a round about four
    strings. Logged.

  * base.html. Nothing in this round needs CSS, and a base edit re-opens
    every suite that asserts on base. A rule that can be met by writing a
    shorter label does not need a rule in the stylesheet.

  A bottom-align rule in base WAS tried, and it is why there is no CSS
  here. It fixes all thirteen wrapping labels at once and it breaks a
  textarea sitting beside an input - aligned today, not aligned after -
  because it bottom-aligns controls whose rows differ in height for
  reasons that have nothing to do with a label. base's own comment warned
  about exactly this: it "cannot disturb the pages that put something
  unusual inside a field". Measured, it was right.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_labelfit'
SUITE = 'test_label_fit.py'
PS1 = 'Push-PendingChanges.ps1'

report, problems = [], []


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


# (field id, old label text, new label text) - anchored on the label whose
# for= names the field, so the text alone can never be matched somewhere it
# was not meant to be.
EDITS = {
    'properties_add.html': [
        ('prop_include_in_occupancy',
         'Include in Occupancy Calculations', 'Include in Occupancy')],
    'properties_edit.html': [
        ('prop_include_in_occupancy',
         'Include in Occupancy Calculations', 'Include in Occupancy')],
    'tenant_add.html': [
        ('tenant_payment_terms',
         'Rental Payment Terms (Days)', 'Payment Terms')],
    'tenant_edit.html': [
        ('tenant_payment_terms',
         'Rental Payment Terms', 'Payment Terms')],
}


def fields(text):
    """Every control's name=, in order. Nothing here may change it."""
    out = []
    for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>', text, re.I):
        n = re.search(r'\bname\s*=\s*["\']([^"\']+)', m.group(2))
        out.append(n.group(1) if n else '-')
    return out


planned = {}

for rel, edits in sorted(EDITS.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    text = src
    done, already = [], []
    for field, old, new in edits:
        pat = re.compile(r'(<label\s+for="%s"[^>]*>\s*<strong>)%s(</strong>)'
                         % (re.escape(field), re.escape(old)))
        hits = list(pat.finditer(text))
        if not hits:
            newpat = re.compile(r'<label\s+for="%s"[^>]*>\s*<strong>%s'
                                r'</strong>' % (re.escape(field),
                                                re.escape(new)))
            if newpat.search(text):
                already.append(new)
                continue
            problems.append('%s: no label for=%r reading %r, and none '
                            'reading %r either' % (rel, field, old, new))
            continue
        if len(hits) != 1:
            problems.append('%s: the label for=%r reading %r appears %d '
                            'time(s), expected 1'
                            % (rel, field, old, len(hits)))
            continue
        text = pat.sub(lambda m: m.group(1) + new + m.group(2), text,
                       count=1)
        done.append('%r -> %r' % (old, new))
    if text == src:
        report.append('%-24s %s' % (rel, 'already done' if already
                                    else 'nothing to do'))
        continue
    planned[rel] = (path, src, text)
    report.append('%-24s %s' % (rel, '; '.join(done)))


# ==========================================================================
# THE COPIES OF THE LABEL
#
# A label that lives in two places drifts, and it drifted here before this
# round even ran: pages/models.py calls this field 'Include in Occupancy
# Metrics', the template called it 'Include in Occupancy Calculations', and
# tenant_add and tenant_edit gave ONE field two different names. Two tools
# hold a third and fourth copy:
#
#   test_entry_sections.py section 12 builds its rendered fixture from four
#   label strings typed into the suite. Left alone, it would go on
#   measuring 'Include in Occupancy Calculations' - a string the page no
#   longer has - and PASS. A fixture that carries its own copy of the page
#   is a second page, and a suite that measures the second one measures
#   nothing. So it is not retyped here: it is changed to READ the labels
#   out of properties_edit.html, which is the only version of this that
#   cannot go stale again.
#
#   Show-MobileForm.py reconstructs the Properties form from a field table
#   it carries. That table is a copy by design - the tool exists to render
#   a form that does not exist yet - so its string is simply corrected, and
#   the drift is logged rather than engineered away.
# ==========================================================================
TOOL_EDITS = {
    'test_entry_sections.py': [(
        """        four = ''.join(
            '<div class="col-md-3"><div class="form-group"><label><strong>'
            '%s</strong></label><select class="form-control"><option>Yes'
            '</option></select></div></div>' % t
            for t in ('Include in Occupancy Calculations', 'Status',
                      'Available For Rent', 'Title Deed Available'))""",
        """        # THE LABELS ARE READ, NOT RETYPED. This fixture used to
        # carry its own copy of the four, and the round that shortened one
        # of them would have left the copy behind - the fixture measuring
        # a string the page no longer has, and passing. properties_edit is
        # the only screen in the corpus with col-md-3 columns in it, and
        # they are exactly this row.
        _four_labels = re.findall(
            r'<div class="col-md-3">\s*<div class="form-group">\s*'
            r'<label[^>]*>\s*<strong>([^<]+)</strong>',
            markup_only(read(os.path.join(ROOT, 'properties_edit.html'))))
        four = ''.join(
            '<div class="col-md-3"><div class="form-group"><label><strong>'
            '%s</strong></label><select class="form-control"><option>Yes'
            '</option></select></div></div>' % t
            for t in _four_labels)""")],
    'Show-MobileForm.py': [(
        "    ('prop_include_in_occupancy', 'Include in Occupancy "
        "Calculations', 'select', 4),",
        "    # A COPY, and it is a copy on purpose - this tool renders a\n"
        "    # form that does not exist yet, so it cannot read one. Kept in\n"
        "    # step with properties_edit.html by hand, and logged as drift.\n"
        "    ('prop_include_in_occupancy', 'Include in Occupancy', "
        "'select', 4),")],
}

for rel, edits in sorted(TOOL_EDITS.items()):
    if not os.path.isfile(rel):
        report.append('%-24s not on disk - its copy is not corrected' % rel)
        continue
    src = read(rel)
    text, done = src, []
    for old, new in edits:
        if new in text:
            continue
        if text.count(old) != 1:
            problems.append('%s: the block to correct appears %d time(s), '
                            'expected 1' % (rel, text.count(old)))
            continue
        text = text.replace(old, new, 1)
        done.append('the four-across labels'
                    if rel.startswith('test_') else 'the field table')
    if text == src:
        report.append('%-24s %s' % (rel, 'already corrected'))
        continue
    planned[rel] = (rel, src, text)
    report.append('%-24s %s' % (rel, '; '.join(done)))


# ==========================================================================
# THE GATE
# ==========================================================================
GATE_NOTE = """    # Four labels that did not fit their own column, and the rule
    # that let them. Its rendered section measures a col-md-3 at 168px -
    # the narrowest this application ever draws one, a 992-wide window
    # with the sidebar open - and its CONTROL renders the OLD label at
    # the same width and requires it to WRAP. A guard whose control
    # cannot fail is not a guard. Newest, so most likely to be what
    # breaks.
    'test_label_fit.py'"""

ps1_new = None
if not os.path.isfile(PS1):
    report.append('%-24s not on disk - the suite is not wired' % PS1)
elif SUITE in read(PS1):
    report.append('%-24s already runs %s' % (PS1, SUITE))
else:
    ps1_src = read(PS1)
    i = ps1_src.find('$suites = @(')
    m = re.search(r'\n\)\s*?\n', ps1_src[i:]) if i >= 0 else None
    last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$", ps1_src[i:i + m.start()])
            if m else None)
    if not last:
        problems.append('%s: could not find the end of $suites' % PS1)
    else:
        j = i + m.start()
        ps1_new = ps1_src[:j] + ',\n' + GATE_NOTE + ps1_src[j:]
        report.append('%-24s + %s, after %s' % (PS1, SUITE, last.group(1)))


# ==========================================================================
# SELF-CHECK - a label round may change TEXT and nothing else
# ==========================================================================
for rel, (path, src, text) in sorted(planned.items()):
    if rel not in EDITS:
        # A TOOL IS NOT A TEMPLATE. The checks below are about markup; the
        # two corrected tools are Python, and their guard is that they run
        # - test_entry_sections.py and Show-MobileForm.py are both on the
        # gate, so a syntax error in either stops the push.
        import ast as _ast
        try:
            _ast.parse(text)
        except SyntaxError as e:
            problems.append('%s: the correction does not parse - %s'
                            % (rel, e))
        continue
    for tag in ('div', 'form', 'label', 'strong'):
        d0 = len(re.findall(r'<%s\b' % tag, src)) - src.count('</%s>' % tag)
        d1 = len(re.findall(r'<%s\b' % tag, text)) - text.count('</%s>' % tag)
        if d1 != d0:
            problems.append('%s: <%s> balance moved %d -> %d'
                            % (rel, tag, d0, d1))
    a, b = fields(src), fields(text)
    if a != b:
        problems.append('%s: the controls changed - %d before, %d after'
                        % (rel, len(a), len(b)))
    # A LABEL POINTS AT A CONTROL. Changing what a label SAYS must not
    # change what it is FOR: a for= that stops matching an id is a label
    # that stops being a label for anyone using a screen reader.
    for what, pat in (('for=', r'<label[^>]*\bfor="([^"]+)"'),
                      ('id=', r'\bid="([^"]+)"'),
                      ('name=', r'\bname="([^"]+)"'),
                      ('placeholder=', r'\bplaceholder="([^"]*)"')):
        if re.findall(pat, src) != re.findall(pat, text):
            problems.append('%s: the set of %s changed' % (rel, what))
    # and the only difference is inside a <strong> in a <label>
    stripped_a = re.sub(r'(<label[^>]*>\s*<strong>)[^<]*(</strong>)',
                        r'\1@\2', src)
    stripped_b = re.sub(r'(<label[^>]*>\s*<strong>)[^<]*(</strong>)',
                        r'\1@\2', text)
    if stripped_a != stripped_b:
        problems.append('%s: something outside a label\'s own text changed'
                        % rel)
    # the new text is not longer than the old - the point of the round
    for field, old, new in EDITS[rel]:
        if len(new) > len(old):
            problems.append('%s: %r is LONGER than %r' % (rel, new, old))


# ==========================================================================
print('\n' + '=' * 74)
print('LABEL FIT - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)

print('\n  Measured, at the two widths that matter:')
print('      viewport 1280  columns lay out in 1000px  col-md-3 = 240px')
print('      viewport  992  columns lay out in  712px  col-md-3 = 168px')
print('                     - the narrowest a col-md-3 is ever drawn, the')
print('                       sidebar being display:none at 991 and below')
print('  Not changed, with the reason recorded in this file\'s docstring:')
print('      the Physical Invoice checkboxes  - measured, nothing misaligns')
print('      models.py verbose_name           - would generate a migration')
print('      base.html                        - the bottom-align rule was')
print('                                         tried and it breaks a')
print('                                         textarea beside an input')

if problems:
    print('\n' + '!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned and ps1_new is None:
    print('\n  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('\n  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

for path, src, text in planned.values():
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as f:
            f.write(src)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

if ps1_new is not None:
    bak = PS1 + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as f:
            f.write(read(PS1))
    with open(PS1, 'w', encoding='utf-8', newline='') as f:
        f.write(ps1_new)

print('\n  %d file(s) written, backups at *%s'
      % (len(planned) + (1 if ps1_new is not None else 0), SUFFIX))
print('\n  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
