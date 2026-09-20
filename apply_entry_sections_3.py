"""apply_entry_sections_3.py - entry sections, push 3 of 3: Issues, the
   Personal modals, and the Assets deferral.

    python apply_entry_sections_3.py --check     dry run
    python apply_entry_sections_3.py             apply

Run from the repo root, after apply_entry_sections_2.py. Idempotent.

TWO RULES THIS PUSH NEEDS, AND NEITHER IS A LIST

  A MODAL BODY IS ALREADY A PANEL. Five of these screens put their form in
  a .modal-body, which is a box with a border, a shadow and a header bar.
  A .form-card inside one is a panel inside a panel. So inside a modal, a
  section is a TITLE and nothing is wrapped round it.

  A SECTION TITLE THAT NEEDS A COMPANION IS AN .alv-card. base declares
  .alv-card properly - the card, its head, its title, its aside, its body,
  its lead variant and its own print rules - and seven pages wear it. It is
  the system's card with a header bar, where .form-card is the entry panel
  with the wash. Two components, on purpose. That is why cash_receipt_add
  is NOT in this push: it already has two titled sections, "The payment" and
  "Received from", and the first carries an aside saying which number the
  receipt will be issued as. Converting it would abandon a base-owned
  component to gain nothing and would cost the aside.

THE ASSETS LIFTS, AND WHY THEY ARE ANCHORED RATHER THAN INDEXED

  Push 2 rebuilt panels from their row blocks, which works when every field
  sits in a .form-row. purchase_invoice does not: it is a bare .form-group
  after the Warranty row, wrapped in {% if asset.purchase_invoice %} with a
  link to the existing file inside the conditional. So both Assets moves are
  made by anchor - cut the block, re-insert it as a row of its own above a
  named section title - and each anchor is asserted to appear exactly once.
  No width changes: brand_manufacturer keeps the col-md-6 it has, and
  purchase_price is left alone on the row it used to share.

PROJECTS IS NOT IN THIS PUSH, AND THE REASON IS NOT LAYOUT

  project_tasks_edit renders five controls twice - an auto-calculated
  read-only version and an editable one behind {% if not task.parent_task %}.
  Those auto-calculated values are computed for display and NEVER STORED:
  a parent task has all six get_calculated_* methods and nothing that calls
  them, while a Project has update_project_from_tasks() and a signal that
  fires it. The rollup exists one level up and was never implemented one
  level down.

  Sectioning those screens would rearrange the markup of a behaviour that is
  about to be fixed. Projects waits. See
  claude/projects_auto_calculated_rollup.md and Show-ProjectRollup.py.
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

CHECK = '--check' in sys.argv
VERBOSE = '--verbose' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_sect3'
TAG, CLS = 'h3', 'form-section-title'
SUITE = 'test_entry_sections.py'
PS1 = 'Push-PendingChanges.ps1'

problems = []
report = []


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def markup_only(text):
    """<script> and <style> bodies blanked to spaces, offsets preserved."""
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def close_of(mk, open_end):
    """The offset just past the </div> that closes the div opened before
    open_end. Counts <div> and </div> only - which is enough here because a
    Django template's conditional tags never open a div in one branch and
    close it in another on these screens, and the self-check re-counts the
    balance of the whole file afterwards."""
    depth, i = 1, open_end
    while depth and i < len(mk):
        m = re.compile(r'<div\b|</div>').search(mk, i)
        if not m:
            return None
        depth += -1 if m.group(0) == '</div>' else 1
        i = m.end()
    return i if not depth else None


def named(chunk):
    """The first control name inside this chunk, or None."""
    for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>', chunk, re.I):
        a = m.group(2)
        if re.search(r'type\s*=\s*["\'](?:hidden|submit|button|reset|image)'
                     r'["\']', a, re.I):
            continue
        n = re.search(r'\bname\s*=\s*["\']([^"\']+)', a)
        if n:
            return n.group(1)
    return None


def rows_of(mk, lo, hi):
    """Top-level .form-row elements in [lo, hi), as (start, end)."""
    out, i = [], lo
    while True:
        m = re.compile(r'<div class="form-row[^"]*">').search(mk, i, hi)
        if not m:
            return out
        e = close_of(mk, m.end())
        if e is None or e > hi:
            return out
        out.append((m.start(), e))
        i = e


def blocks_of(mk, r0, r1):
    """The column blocks directly inside one row, as (key, start, end).

    A block is either <div class="col-*"> wrapping a .form-group, or a
    <div class="form-group col-* ..."> that IS the column - cash_receipt_add
    and finance_valuations use the second shape and the first version of
    this walk saw none of their fields."""
    out, i = [], r0 + mk[r0:r1].index('>') + 1
    while i < r1:
        m = re.compile(r'<div class="([^"]*)"[^>]*>').search(mk, i, r1)
        if not m:
            break
        cls = m.group(1)
        if not re.search(r'(?<![-\w])col-(?:md-|sm-|lg-|xl-)?\d+(?![-\w])',
                         cls):
            i = m.end()
            continue
        e = close_of(mk, m.end())
        if e is None or e > r1:
            break
        out.append((named(mk[m.start():e]), m.start(), e))
        i = e
    return out


def region(mk, rel, spec):
    """(lo, hi, keep_from) - the span to restructure, and where the panel
    that this round keeps verbatim begins."""
    card = re.search(r'<div class="form-card"[^>]*>', mk)
    keep = None
    h3 = re.search(r'<%s class="%s">' % (TAG, CLS), mk)
    if card:
        end = close_of(mk, card.end())
        if end is None:
            return None
        lo, hi = card.end(), end - len('</div>')
        if h3 and lo < h3.start() < hi:
            keep = h3.start()
        return (card.start(), end, lo, hi, keep)
    # no panel yet: the region is the run of form-rows inside the form
    rs = rows_of(mk, 0, len(mk))
    if not rs:
        return None
    return (rs[0][0], rs[-1][1], rs[0][0], rs[-1][1], None)


def indent_at(text, pos):
    ls = text.rfind('\n', 0, pos) + 1
    return re.match(r'[ \t]*', text[ls:pos]).group(0)


def heading(icon, title, pad):
    return ('%s<%s class="%s"><i class="fas fa-%s"></i> %s</%s>\n'
            % (pad, TAG, CLS, icon, title, TAG))


def reindent(blk, pad):
    """A block re-laid at a new depth.

    A lifted block keeps the indentation of where it used to live, so a
    panel rebuilt without this reads like a ransom note - the first version
    of this tool prefixed eight spaces onto lines that already had fourteen.
    Templates get read by people."""
    lines = blk.strip('\n').rstrip().split('\n')
    rest = [l for l in lines[1:] if l.strip()]
    cut = min((len(l) - len(l.lstrip()) for l in rest), default=0)
    out = [pad + lines[0].strip()]
    for l in lines[1:]:
        out.append((pad + l[cut:].rstrip()) if l.strip() else '')
    return '\n'.join(out)


def set_width(block, want):
    """Rewrite a block's col-md-N, leaving every other class alone."""
    return re.sub(r'(?<![-\w])col-md-\d+(?![-\w])', want, block, count=1)



# --------------------------------------------------------------------------
# THE PLAN
#
# A title in front of the block that starts each section: (icon, title,
# first_field). No panel is built and no row is rebuilt on any screen here.
#
# INSIDE A MODAL BODY, A SECTION IS A TITLE AND NOT A CARD. A modal is
# already a box with a border, a shadow and a header bar; a .form-card inside
# one is a panel inside a panel. Five of these screens put their form in a
# .modal-body and none of them gains a card.
# --------------------------------------------------------------------------
SIMPLE = {
    # --- Issues ---------------------------------------------------------
    'fsr_add.html': [
        ('exclamation-triangle', 'Issue', 'prop')],
    # fsr_details is NOT here. Its Edit Issue modal uses a dialect of its
    # own - .ei-modal-body, .ei-label, .ei-input - and no .form-group or
    # .form-control anywhere. A section title on it would be the only
    # standard thing on the form. It needs the FIELD components first, which
    # is the form-components round's work, not this one. Logged.

    # --- Personal, all in modal bodies ----------------------------------
    'celebration_management.html': [
        ('address-book', 'Contact', 'name'),
        ('calendar-day', 'Event', 'event_type'),
        ('bell', 'Notifications', 'notify_one_week')],
    'household_member_management.html': [
        ('user', 'Person', 'name')],
    'passport_management.html': [
        ('passport', 'Document', 'holder_name'),
        ('calendar-check', 'Validity', 'date_of_issue'),
        ('file-upload', 'File', 'document_file')],
    'view_meal_plan.html': [
        ('copy', 'Duplicate Meal Plan', 'new_plan_name')],
    # help_page is NOT here either. selected_modules is a checkbox inside a
    # selection tree - .manual-module-header with its own chevron and
    # count - not a field in a form. The proposal called it "a picker
    # rather than a record" and asked whether to leave it alone; the markup
    # answers that. A section title over a tree adds nothing.

    # --- Assets ---------------------------------------------------------
    # Warranty Information and Photos already carry the component; push 1
    # put them there. These two are the sections that were missing, and
    # Purchase is what the two lifts below exist for.
    'edit_asset.html': [
        ('box', 'Asset', 'category'),
        ('receipt', 'Purchase', 'purchase_date')],
    'property_assets.html': [
        ('box', 'Asset', 'category'),
        ('receipt', 'Purchase', 'purchase_date'),
        # edit_asset has a Photos title and property_assets never did.
        # Same four sections on both screens or neither.
        ('camera', 'Photos', 'photos')],
}

# --------------------------------------------------------------------------
# THE LIFTS - the deferral from push 2, done with anchors rather than with
# the block index.
#
# (field, before_this_title) - the block holding `field` is cut out of the
# row it is in and re-inserted as a row of its own immediately above the
# named section title.
#
# WHY NOT THE BLOCK INDEX. Push 2 rebuilt a panel from its blocks, which
# works when every field sits in a .form-row. purchase_invoice does not: it
# is a bare .form-group after the Warranty row, wrapped in
# {% if asset.purchase_invoice %} with a link to the existing file inside
# the conditional. Lifting it by anchor keeps that conditional whole, and
# each anchor is asserted to match exactly once.
#
# NO WIDTH CHANGES. brand_manufacturer becomes its own row at the col-md-6
# it already has; purchase_price is simply left where it was, alone on the
# row it used to share.
LIFTS = {
    'edit_asset.html': [
        ('brand_manufacturer', 'Purchase'),
        ('purchase_invoice', 'Warranty Information'),
    ],
    'property_assets.html': [
        ('brand_manufacturer', 'Purchase'),
        ('purchase_invoice', 'Warranty Information'),
    ],
}

MOVES = {
    'edit_asset.html': ['brand_manufacturer', 'purchase_invoice'],
    'property_assets.html': ['brand_manufacturer', 'purchase_invoice'],
}

# A LABEL THIS ROUND DID NOT BREAK, AND DID EXPOSE.
#
# The gate stopped push 3 on test_label_bold.py: edit_asset's
# "Purchase Invoice/Receipt" is a field label with no <strong> in it, which
# the label round made the standard on 9 Sep. It was already like that. It
# sat in a bare .form-group outside any row, where that suite's scan did not
# reach it, and lifting it into the Purchase section put it in scope.
#
# So it is debt this round UNCOVERED rather than damage it caused - and the
# fix is to meet the standard, not to add an exception to the suite. An
# exception would record that the rule does not apply here, and it does.
#
# property_assets' "Photos (up to 5 ...)" label is plain too and is NOT
# touched: that one is already named in test_label_bold.py's own exception
# list, so it is a decision somebody made, and undoing another round's
# decision is not this round's business.
BOLD_LABELS = {
    'edit_asset.html': ['Purchase Invoice/Receipt'],
}

# Projects is NOT in this push, and the reason is not layout.
#
# project_tasks_edit and projects_edit render five controls twice -
# task_status, task_start_date, task_expected_completion_date,
# task_budgeted_cost, task_actual_cost - as an auto-calculated read-only
# version and an editable one behind {% if not task.parent_task %}. Those
# auto-calculated values are computed for display and NEVER STORED: a parent
# task has all six get_calculated_* methods and nothing that calls them, so
# its stored columns are whatever was written when it was created.
#
# Sectioning those screens would rearrange the markup of a behaviour that is
# about to be fixed, and reviewing a behaviour fix on top of a rearrangement
# is harder than the other way round. Projects waits for
# claude/projects_auto_calculated_rollup.md.
NOT_IN_THIS_ROUND = {
    'cash_receipt_add.html': 'already sectioned in .alv-card, with an aside',
    'fsr_details.html': 'its modal uses .ei-label/.ei-input, not the field '
                        'components - form-components round first',
    'help_page.html': 'selected_modules is a selection tree, not a form',
    'generate_lease_agreement.html': 'its colour-coded headers stay, by '
                                     'decision',
}

PROJECTS_WAITING = ('projects/projects_edit.html',
                    'projects/project_tasks_edit.html',
                    'projects/project_subtasks_add.html',
                    'projects/projects_add.html',
                    'projects/project_tasks_add.html')


def blocks_all(mk):
    """Every column block and every bare .form-group in the document, as
    (key, start, end). Assets needs the second kind: purchase_invoice is a
    .form-group that sits outside any row."""
    out, seen = [], set()
    for m in re.finditer(r'<div class="([^"]*)"[^>]*>', mk):
        cls = m.group(1)
        if not re.search(r'(?<![-\w])(?:col-(?:md-|sm-|lg-|xl-)?\d+'
                         r'|form-group)(?![-\w])', cls):
            continue
        if any(s <= m.start() < e for _k, s, e in out):
            continue
        e = close_of(mk, m.end())
        if e is None:
            continue
        key = named(mk[m.start():e])
        if key is None or key in seen:
            continue
        seen.add(key)
        out.append((key, m.start(), e))
    return out


planned = {}
# WHICH FILES THIS RUN ACTUALLY LIFTED. The move assertions below are about
# what THIS run did, not about what the tree looks like. A second run that
# only bolds a label must not be asked to prove that brand_manufacturer
# moved - it did move, one run ago, and the check said so then.
did_lift = set()

for rel, secs in sorted(SIMPLE.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    mk = markup_only(src)
    have = {h.strip() for h in re.findall(
        r'<%s class="%s"><i[^>]*></i>\s*([^<]+)</%s>' % (TAG, CLS, TAG), mk)}
    todo = [s for s in secs if s[1] not in have]
    text = src
    placed = []

    # --- the titles -------------------------------------------------------
    for icon, title, first in reversed(todo):
        mk = markup_only(text)
        hit = None
        for r0, r1 in rows_of(mk, 0, len(mk)):
            if any(k == first for k, _a, _b in blocks_of(mk, r0, r1)):
                hit = r0
                break
        if hit is None:
            for key, b0, _b1 in blocks_all(mk):
                if key == first:
                    hit = b0
                    break
        if hit is None:
            problems.append('%s: no block holds %r' % (rel, first))
            break
        ls = text.rfind('\n', 0, hit) + 1
        text = (text[:ls] + heading(icon, title, indent_at(text, hit))
                + text[ls:])
        placed.append(title)
    if len(placed) != len(todo):
        continue

    # --- the lifts --------------------------------------------------------
    lifted = []
    for field, before in LIFTS.get(rel, []):
        mk = markup_only(text)
        # the block to move
        blk = next(((k, s, e) for k, s, e in blocks_all(mk) if k == field),
                   None)
        if blk is None:
            problems.append('%s: nothing holds %r to lift' % (rel, field))
            break
        # the title to put it in front of, asserted to appear exactly once
        pat = (r'[ \t]*<%s class="%s"><i[^>]*></i>\s*%s\s*</%s>\n'
               % (TAG, CLS, re.escape(before), TAG))
        anchors = list(re.finditer(pat, mk))
        if len(anchors) != 1:
            problems.append('%s: the title %r appears %d time(s) to lift '
                            '%r in front of, expected 1'
                            % (rel, before, len(anchors), field))
            break
        _k, b0, b1 = blk
        a0 = anchors[0].start()
        # ALREADY THERE? A SECOND RUN MUST DO NOTHING.
        # After the first lift the block sits inside a .form-row of its own
        # immediately above the title. blocks_all() finds the INNER block,
        # not that wrapper, so an unguarded second run wrapped it in another
        # row and left the first one empty - nesting a row per run. What
        # says it is already placed is that everything between the end of
        # the block and the title is closing tags and whitespace.
        if b1 <= a0 and not re.sub(r'</div>|\s+', '', text[b1:a0]):
            lifted.append('%s already above %s' % (field, before))
            continue
        if b0 < a0 < b1:
            problems.append('%s: %r already contains the %r title'
                            % (rel, field, before))
            break
        body = text[b0:b1]
        # cut, then re-measure the anchor on the shortened text
        cut = text[:b0] + text[b1:]
        shift = (b1 - b0) if b0 < a0 else 0
        a0 -= shift
        pad = indent_at(cut, a0)
        row = ('%s<div class="form-row">\n%s\n%s</div>\n'
               % (pad, reindent(body, pad + '    '), pad))
        text = cut[:a0] + row + cut[a0:]
        lifted.append('%s -> above %s' % (field, before))

    if rel in LIFTS and len(lifted) != len(LIFTS[rel]):
        continue
    if lifted and text != src:
        did_lift.add(rel)

    if text == src:
        report.append('%-34s already done' % rel)
        continue
    planned[rel] = (path, src, text)
    report.append('%-34s + %d title(s): %-42s%s'
                  % (rel, len(todo), ', '.join(t for _i, t, _f in todo),
                     '  lifted: ' + '; '.join(lifted) if lifted else ''))


# ==========================================================================
# the label the lift put in scope - runs even when the titles are done
# ==========================================================================
for rel, labels in sorted(BOLD_LABELS.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        continue
    text = planned[rel][2] if rel in planned else read(path)
    base_src = planned[rel][1] if rel in planned else text
    done = []
    for label in labels:
        old = '<label>%s</label>' % label
        new = '<label><strong>%s</strong></label>' % label
        if new in text:
            continue
        if text.count(old) != 1:
            problems.append('%s: the label %r appears %d time(s), expected 1'
                            % (rel, label, text.count(old)))
            continue
        text = text.replace(old, new, 1)
        done.append(label)
    if done:
        planned[rel] = (path, base_src, text)
        report.append('%-34s   bold: %s  (the label round\'s standard, and '
                      'the lift is what put it in scope)'
                      % ('', ', '.join(done)))


# ==========================================================================
# SELF-CHECK
# ==========================================================================
for rel, (path, src, text) in sorted(planned.items()):
    for tag in ('div', 'form'):
        d0 = len(re.findall(r'<%s\b' % tag, src)) - src.count('</%s>' % tag)
        d1 = len(re.findall(r'<%s\b' % tag, text)) - text.count('</%s>' % tag)
        if d1 != d0:
            problems.append('%s: <%s> balance moved %d -> %d'
                            % (rel, tag, d0, d1))
    for tag in ('<form', '</form>'):
        if text.count(tag) < src.count(tag):
            problems.append('%s: %s count fell %d -> %d'
                            % (rel, tag, src.count(tag), text.count(tag)))

    def names(t):
        # HIDDEN IS NOT EXCLUDED - a hidden input carries data, and push 2
        # learned that by deleting two of them.
        return [(re.search(r'\bname\s*=\s*["\']([^"\']+)', m.group(2))
                 or [None, '-'])[1]
                for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>',
                                     markup_only(t), re.I)
                if not re.search(r'type\s*=\s*["\'](?:submit|button|reset'
                                 r'|image)["\']', m.group(2), re.I)]
    a, b = names(src), names(text)
    if sorted(a) != sorted(b):
        problems.append('%s: the SET of controls changed - %d before, %d '
                        'after' % (rel, len(a), len(b)))
        continue
    allowed = set(MOVES.get(rel, [])) if rel in did_lift else set()
    ra = [x for x in a if x not in allowed]
    rb = [x for x in b if x not in allowed]
    if ra != rb:
        i = next((k for k, (x, y) in enumerate(zip(ra, rb)) if x != y),
                 min(len(ra), len(rb)))
        problems.append('%s: fields this round did not name changed order - '
                        'at %d, %r became %r'
                        % (rel, i, ra[i:i + 1], rb[i:i + 1]))
    for x in sorted(allowed):
        if a.index(x) == b.index(x):
            problems.append('%s: %r is named as moving and did not move'
                            % (rel, x))


# ==========================================================================
print('\n' + '=' * 74)
print('ENTRY SECTIONS, PUSH 3 - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('\n  Projects waits for the rollup fix - %d screen(s):'
      % len(PROJECTS_WAITING))
for p in PROJECTS_WAITING:
    print('      %s' % p)
print('\n  Out of the round, each with a reason:')
for rel_, why_ in sorted(NOT_IN_THIS_ROUND.items()):
    print('      %-32s %s' % (rel_, why_))

if problems:
    print('\n' + '!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned:
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

print('\n  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('\n  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
