# -*- coding: utf-8 -*-
"""apply_ra29_note_bubble.py - round RA29, 26 Nov 2026.

RELEASE RA29 - A SPEECH BUBBLE BESIDE A LISTING'S TITLE.

    - templatetags/acq.py: notetip - his comment in full, his Shortlist or
      Reject decision and its reason, his viewings; filled when there is a
      comment, outlined otherwise, absent when there is nothing of his.
    - _plot_row.html, _result_row.html: the bubble beside the title (the
      one-line comment under it stays).
    - _style.html: the bubble, painted from the tokens; hover, focus or a
      tap opens it, fixed so a scrolling table cannot clip it.
    - views.py: viewings fetched with the rows.
    - pages/help_content/acquisitions.html.
    - Registers test_ra29_note_bubble.py (shipped beside this file).

Stands on RA28. Idempotent. Edits backed up to .bak_ra29. No migration.
    python apply_ra29_note_bubble.py --check
    python apply_ra29_note_bubble.py
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




import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SUFFIX = '.bak_ra29'
SHIPPED = ('test_ra29_note_bubble.py',)
RETIRED = ()
# (file, the text it holds now, what it becomes) - exact, line endings
# included.
EDITS = json.loads('[["Push-PendingChanges.ps1", "    \'test_ra28_filters_and_outside_rules.py\'\\n", "    \'test_ra28_filters_and_outside_rules.py\',\\n    # RA29, 26 Nov 2026 - a speech bubble beside a listing\'s title: his comment, decision and viewings.\\n    \'test_ra29_note_bubble.py\'\\n"], ["acquisitions/templates/acquisitions/_plot_row.html", "  <td data-label=\\"Plot\\" style=\\"text-align: left\\"><a href=\\"{% url \'acquisitions:property\' p.pk %}?s={{ s.pk }}\\"><strong>{{ p.title }}</strong></a>{% if m.your_comments %}<div class=\\"acq-muted\\"><i class=\\"fas fa-comment\\" aria-hidden=\\"true\\"></i> {{ m.your_comments|truncatechars:90 }}</div>{% endif %}{% if m.failed_musts %}<div class=\\"acq-muted\\">fails {{ m.failed_musts|join:\\", \\" }}</div>{% endif %}{% if m.dupe_of %}<div class=\\"acq-muted\\">possibly the same plot as <a href=\\"{% url \'acquisitions:property\' m.dupe_of.pk %}?s={{ s.pk }}\\">{{ m.dupe_of.title }}</a></div>{% endif %}</td>\\r\\n", "  <td data-label=\\"Plot\\" style=\\"text-align: left\\"><a href=\\"{% url \'acquisitions:property\' p.pk %}?s={{ s.pk }}\\"><strong>{{ p.title }}</strong></a>{{ m|notetip }}{% if m.your_comments %}<div class=\\"acq-muted\\"><i class=\\"fas fa-comment\\" aria-hidden=\\"true\\"></i> {{ m.your_comments|truncatechars:90 }}</div>{% endif %}{% if m.failed_musts %}<div class=\\"acq-muted\\">fails {{ m.failed_musts|join:\\", \\" }}</div>{% endif %}{% if m.dupe_of %}<div class=\\"acq-muted\\">possibly the same plot as <a href=\\"{% url \'acquisitions:property\' m.dupe_of.pk %}?s={{ s.pk }}\\">{{ m.dupe_of.title }}</a></div>{% endif %}</td>\\r\\n"], ["acquisitions/templates/acquisitions/_result_row.html", "        <td data-label=\\"Property\\" style=\\"text-align: left\\"><a href=\\"{% url \'acquisitions:property\' p.pk %}?s={{ s.pk }}\\"><strong>{{ p.title }}</strong></a>{% if m.your_comments %}<div class=\\"acq-muted\\"><i class=\\"fas fa-comment\\" aria-hidden=\\"true\\"></i> {{ m.your_comments|truncatechars:90 }}</div>{% endif %}{% if m.dupe_of %}<div class=\\"acq-muted\\">possibly the same home as <a href=\\"{% url \'acquisitions:property\' m.dupe_of.pk %}?s={{ s.pk }}\\">{{ m.dupe_of.title }}</a></div>{% endif %}<div class=\\"acq-muted\\">{% if p.floor_level %}{{ p.floor_level }} &middot; {% endif %}{% if p.year_built %}{{ p.year_built }} &middot; {% endif %}{{ p.sources.all|length }} source{{ p.sources.all|length|pluralize }}</div></td>\\r\\n", "        <td data-label=\\"Property\\" style=\\"text-align: left\\"><a href=\\"{% url \'acquisitions:property\' p.pk %}?s={{ s.pk }}\\"><strong>{{ p.title }}</strong></a>{{ m|notetip }}{% if m.your_comments %}<div class=\\"acq-muted\\"><i class=\\"fas fa-comment\\" aria-hidden=\\"true\\"></i> {{ m.your_comments|truncatechars:90 }}</div>{% endif %}{% if m.dupe_of %}<div class=\\"acq-muted\\">possibly the same home as <a href=\\"{% url \'acquisitions:property\' m.dupe_of.pk %}?s={{ s.pk }}\\">{{ m.dupe_of.title }}</a></div>{% endif %}<div class=\\"acq-muted\\">{% if p.floor_level %}{{ p.floor_level }} &middot; {% endif %}{% if p.year_built %}{{ p.year_built }} &middot; {% endif %}{{ p.sources.all|length }} source{{ p.sources.all|length|pluralize }}</div></td>\\r\\n"], ["acquisitions/templates/acquisitions/_style.html", "</style>\\r\\n", "/* RA29, 26 Nov 2026 - the note bubble beside a listing\'s title: his\\r\\n   comment, his decision and reason, his viewings. Fixed, so a table that\\r\\n   scrolls sideways cannot clip it; placed by the script below. */\\r\\n.acq-note { display: inline-block; margin-left: 6px; }\\r\\n.acq-note-btn { border: 0; background: none; padding: 0 2px; color: var(--alv-accent); cursor: pointer; font-size: 14px; line-height: 1; }\\r\\n.acq-note-btn:focus-visible { outline: 2px solid var(--alv-accent-line); border-radius: var(--alv-radius-sm); }\\r\\n.acq-note-box { display: none; position: fixed; z-index: 1060; width: 300px; max-width: calc(100vw - 24px); padding: 10px 12px; background: var(--alv-paper); color: var(--alv-ink); border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm); font-size: 13px; font-weight: 400; text-align: left; white-space: normal; }\\r\\n.acq-note.is-open .acq-note-box { display: block; }\\r\\n.acq-note-h { display: block; font-weight: 600; color: var(--alv-ink-strong); margin-top: 6px; }\\r\\n.acq-note-h:first-child { margin-top: 0; }\\r\\n.acq-note-p { display: block; color: var(--alv-ink); }\\r\\n@media print { .acq-note { display: none; } }\\r\\n</style>\\r\\n<script>\\r\\n// RA29 - hover or focus opens the bubble; a tap pins it until a tap elsewhere.\\r\\n(function () {\\r\\n  // The bubble is drawn by the notetip filter, not by this template, so\\r\\n  // every look-up is checked before it is used.\\r\\n  function place(n) {\\r\\n    var btn = n.querySelector(\'.acq-note-btn\'), box = n.querySelector(\'.acq-note-box\');\\r\\n    if (!btn || !box) { return; }\\r\\n    var r = btn.getBoundingClientRect();\\r\\n    var w = Math.min(300, window.innerWidth - 24);\\r\\n    box.style.left = Math.max(12, Math.min(r.left, window.innerWidth - w - 12)) + \'px\';\\r\\n    box.style.top = (r.bottom + 6) + \'px\';\\r\\n    if (r.bottom + 6 + box.offsetHeight > window.innerHeight - 8) {\\r\\n      box.style.top = Math.max(8, r.top - 6 - box.offsetHeight) + \'px\';\\r\\n    }\\r\\n  }\\r\\n  function open(n, on) {\\r\\n    n.classList.toggle(\'is-open\', on);\\r\\n    var btn = n.querySelector(\'.acq-note-btn\');\\r\\n    if (btn) { btn.setAttribute(\'aria-expanded\', on ? \'true\' : \'false\'); }\\r\\n    if (on) { place(n); }\\r\\n  }\\r\\n  function shut(except) {\\r\\n    Array.prototype.forEach.call(document.querySelectorAll(\'.acq-note.is-open\'), function (n) {\\r\\n      if (n !== except) { n.classList.remove(\'is-pinned\'); open(n, false); }\\r\\n    });\\r\\n  }\\r\\n  document.addEventListener(\'mouseover\', function (e) {\\r\\n    var n = e.target.closest && e.target.closest(\'.acq-note\');\\r\\n    if (n && !n.classList.contains(\'is-open\')) { shut(n); open(n, true); }\\r\\n  });\\r\\n  document.addEventListener(\'mouseout\', function (e) {\\r\\n    var n = e.target.closest && e.target.closest(\'.acq-note\');\\r\\n    if (n && !n.contains(e.relatedTarget) && !n.classList.contains(\'is-pinned\')) { open(n, false); }\\r\\n  });\\r\\n  document.addEventListener(\'click\', function (e) {\\r\\n    var b = e.target.closest(\'.acq-note-btn\');\\r\\n    if (!b) { shut(null); return; }\\r\\n    var n = b.parentNode, pin = !n.classList.contains(\'is-pinned\');\\r\\n    shut(n);\\r\\n    n.classList.toggle(\'is-pinned\', pin);\\r\\n    open(n, pin);\\r\\n  });\\r\\n  document.addEventListener(\'focusin\', function (e) {\\r\\n    var n = e.target.closest && e.target.closest(\'.acq-note\');\\r\\n    if (n) { shut(n); open(n, true); }\\r\\n  });\\r\\n  document.addEventListener(\'keydown\', function (e) { if (e.key === \'Escape\') { shut(null); } });\\r\\n  window.addEventListener(\'scroll\', function () { shut(null); }, true);\\r\\n})();\\r\\n</script>\\r\\n"], ["acquisitions/templatetags/acq.py", "        return None\\r\\n", "        return None\\r\\n\\r\\n\\r\\n@register.filter\\r\\ndef notetip(m):\\r\\n    \\"\\"\\"RA29, 26 Nov 2026 - Demetri: \\"a little \\"i\\", where if I hover over, I\\r\\n    can see my general comments or rejected comments for a property\\". A\\r\\n    speech bubble beside the title, only when there is something of his to\\r\\n    read: his comment in full, his decision and its reason, his viewings.\\r\\n    Filled when there is a comment, outlined when there is only the rest.\\r\\n    Hover or focus shows it; a tap pins it (a phone has no hover).\\"\\"\\"\\r\\n    from django.utils.html import escape\\r\\n    from django.utils.safestring import mark_safe\\r\\n    said = (m.your_comments or \\"\\").strip()\\r\\n    parts = []\\r\\n    if said:\\r\\n        parts.append(format_html(\'<span class=\\"acq-note-h\\">Your comment</span><span class=\\"acq-note-p\\">{}</span>\',\\r\\n                                 mark_safe(escape(said).replace(\\"\\\\n\\", \\"<br>\\"))))\\r\\n    if m.status_set_by_user:\\r\\n        parts.append(format_html(\'<span class=\\"acq-note-h\\">{} by you</span>{}\', m.get_status_display(),\\r\\n                                 format_html(\'<span class=\\"acq-note-p\\">{}</span>\', m.decision_note)\\r\\n                                 if m.decision_note else \\"\\"))\\r\\n    views = list(m.property.viewings.all())\\r\\n    if views:\\r\\n        parts.append(format_html(\'<span class=\\"acq-note-h\\">Viewing{}</span>{}\', \\"s\\" if len(views) > 1 else \\"\\",\\r\\n                                 mark_safe(\\"\\".join(format_html(\'<span class=\\"acq-note-p\\">{}{}</span>\',\\r\\n                                                               \\"%d %s %d\\" % (v.viewed_on.day, v.viewed_on.strftime(\\"%b\\"), v.viewed_on.year),\\r\\n                                                               (\\" \\\\u2013 \\" + v.notes) if v.notes else \\"\\")\\r\\n                                                   for v in views))))\\r\\n    if not parts:\\r\\n        return \\"\\"\\r\\n    return format_html(\\r\\n        \'<span class=\\"acq-note\\"><button type=\\"button\\" class=\\"acq-note-btn\\" aria-label=\\"Your notes on this listing\\" \'\\r\\n        \'aria-expanded=\\"false\\"><i class=\\"{} fa-comment\\" aria-hidden=\\"true\\"></i></button>\'\\r\\n        \'<span class=\\"acq-note-box\\" role=\\"tooltip\\">{}</span></span>\',\\r\\n        \\"fas\\" if said else \\"far\\", mark_safe(\\"\\".join(parts)))\\r\\n"], ["acquisitions/views.py", "                .prefetch_related(\\"property__sources\\", \\"property__prices\\"))\\r\\n", "                .prefetch_related(\\"property__sources\\", \\"property__prices\\",\\r\\n                                  \\"property__viewings\\"))   # RA29 - the note bubble\\r\\n"], ["alv_rounds.py", "    \'.bak_ra28\',\\n", "    \'.bak_ra28\',\\n    # RA29, 26 Nov 2026 - a speech bubble beside a listing\'s title: his comment, decision and viewings.\\n    \'.bak_ra29\',\\n"], ["pages/help_content/acquisitions.html", "    <p>Open a scenario to see its latest written summary, its key numbers, <strong>what&rsquo;s holding listings back</strong> (the Musts most often failed or unconfirmed), and every listing within your rules. <strong>Filter</strong>, in the bar at the top, opens the filter panel, as elsewhere in the app: search by title or area, Area, Status (each with its count), price incl. VAT from and to, size (plot m&sup2; on a plot scenario) from and to, bedrooms on a home scenario, <strong>Opened</strong> (<em>Not opened yet</em>, or <em>Opened, no decision yet</em>) and <strong>Sort</strong> (score, price, date found, status, or <strong>&euro;/m&sup2;, low to high</strong>). Each filter that is on shows as a tag under the bar; its &times; clears it, and <strong>Clear All</strong> clears them all. A line under the bar says how many listings are <strong>outside your rules</strong> and not shown; <strong>Show them</strong> (or Status &rarr; Outside your rules) lists them. Search also looks through your own comments and reasons, so <em>kitchen</em> finds every listing you wrote that about. Under each title is your comment, shortened to a line; a listing you have not opened yet says <strong>Not opened</strong>.</p>\\r\\n", "    <p>Open a scenario to see its latest written summary, its key numbers, <strong>what&rsquo;s holding listings back</strong> (the Musts most often failed or unconfirmed), and every listing within your rules. <strong>Filter</strong>, in the bar at the top, opens the filter panel, as elsewhere in the app: search by title or area, Area, Status (each with its count), price incl. VAT from and to, size (plot m&sup2; on a plot scenario) from and to, bedrooms on a home scenario, <strong>Opened</strong> (<em>Not opened yet</em>, or <em>Opened, no decision yet</em>) and <strong>Sort</strong> (score, price, date found, status, or <strong>&euro;/m&sup2;, low to high</strong>). Each filter that is on shows as a tag under the bar; its &times; clears it, and <strong>Clear All</strong> clears them all. A line under the bar says how many listings are <strong>outside your rules</strong> and not shown; <strong>Show them</strong> (or Status &rarr; Outside your rules) lists them. Search also looks through your own comments and reasons, so <em>kitchen</em> finds every listing you wrote that about. Under each title is your comment, shortened to a line; the <strong>speech bubble</strong> beside the title shows it in full &mdash; hover over it, or tap it on a phone &mdash; with your Shortlist or Reject decision and its reason, and any viewings you logged (a filled bubble means there is a comment, an outlined one only a decision or a viewing); a listing you have not opened yet says <strong>Not opened</strong>.</p>\\r\\n"], ["test_pair_contrast.py", "EXPECT_PAIRS = 771   # RA22, 24 Nov 2026 - the wizard\'s chosen type card (.acq-wz-type:has(input:checked)) sets the accent fill and ink together, a house pair above AA (the table of named pairs is unchanged).   # (was 770)   # RA19, 23 Nov 2026 - the Acquisitions stylesheet: nine rules set a fill and an ink together, every pair on house tokens and none below AA (the table of named pairs is unchanged).   # (was 761)   # RA16, 23 Nov 2026 - meal_planner.html: the picker\'s eye, the Undo strip after a dropped meal and the Send dialog\'s preview each set a fill and an ink, all AA.   # (was 758)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page: its tabs, the usage grid\'s four shades and its pill each set a fill and an ink, all AA.   # (was 752)   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip\'s fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home\'s Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6\'s pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages\' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets\\n", "EXPECT_PAIRS = 772   # RA29, 26 Nov 2026 - the note bubble beside a listing\'s title (.acq-note-box) sets the paper fill and the ink together, a house pair above AA (the table of named pairs is unchanged).   # (was 771)   # RA22, 24 Nov 2026 - the wizard\'s chosen type card (.acq-wz-type:has(input:checked)) sets the accent fill and ink together, a house pair above AA (the table of named pairs is unchanged).   # (was 770)   # RA19, 23 Nov 2026 - the Acquisitions stylesheet: nine rules set a fill and an ink together, every pair on house tokens and none below AA (the table of named pairs is unchanged).   # (was 761)   # RA16, 23 Nov 2026 - meal_planner.html: the picker\'s eye, the Undo strip after a dropped meal and the Send dialog\'s preview each set a fill and an ink, all AA.   # (was 758)   # RA15, 23 Nov 2026 - user_activity.html, the Activity page: its tabs, the usage grid\'s four shades and its pill each set a fill and an ink, all AA.   # (was 752)   # RC-3, 12 Nov 2026 - cook mode on the recipe page: the full-screen step view sets the paper fill and its ink, and its Next button the accent fill and the on-accent ink. Two rules, pairs base already uses.   # (was 750)   # CR-2, 27 Oct 2026 - the receipt email pop-up, on Receipts and on Receipt Details: the message box and the Printed warning each set a fill and its ink, pairs base already uses.   # (was 746)   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip\'s fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home\'s Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6\'s pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages\' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets\\n"]]')


def refuse(msg):
    raise SystemExit('RA29 REFUSED: %s' % msg)


def load(rel):
    with open(os.path.join(ROOT, rel), 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw[:3] == b'\xef\xbb\xbf'


def main():
    check = '--check' in sys.argv[1:]
    ps1, _ = load('Push-PendingChanges.ps1')
    if "'test_ra29_note_bubble.py'" in ps1:
        print('RA29 already applied.')
        return 0
    if "'test_ra28_filters_and_outside_rules.py'" not in ps1:
        refuse('RA28 (apply_ra28_filters_and_outside_rules.py) is not applied - '
               'this round registers after it.')
    for rel in SHIPPED:
        if not os.path.isfile(os.path.join(ROOT, *rel.split('/'))):
            refuse('%s is not in place - it ships with this patcher; copy it '
                   'in first.' % rel)
    # A file's edits are made one after another on the same text, in the
    # order listed; every anchor must be found exactly once when its turn
    # comes, or nothing at all is written.
    texts, order = {}, []
    for rel, old, new in EDITS:
        if rel not in texts:
            texts[rel] = list(load(rel))
            order.append(rel)
        text = texts[rel][0]
        if text.count(old) != 1:
            refuse('%s: the anchor is found %d time(s), not once'
                   % (rel, text.count(old)))
        texts[rel][0] = text.replace(old, new)
    plan = [(rel, texts[rel][0], texts[rel][1]) for rel in order]
    for rel, text, bom in plan:
        if check:
            print('RA29 --check: %s would change' % rel)
            continue
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p + SUFFIX):
            shutil.copy2(p, p + SUFFIX)
        with open(p, 'wb') as f:
            f.write((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))
        print('  changed %s' % rel)
    for rel in RETIRED:
        p = os.path.join(ROOT, *rel.split('/'))
        if not os.path.isfile(p):
            continue
        if check:
            print('RA29 --check: %s would be moved to %s' % (rel, SUFFIX))
            continue
        if os.path.exists(p + SUFFIX):
            os.remove(p)
        else:
            os.rename(p, p + SUFFIX)
        print('  retired %s (kept as %s)' % (rel, SUFFIX))
    if not check:
        print('RA29 applied - the note bubble beside each listing. No migration.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
