#!/usr/bin/env python3
"""
apply_notification_settings_ui.py
=================================

Two changes to pages/templates/notification_settings.html:

 1. Add the missing "Expense Invoice Mismatch" card. The page does NOT loop
    over the notification types - every card is hardcoded - so registering the
    choice and the admin_types allow-list was not enough to make it appear.

 2. Collapse every section to its title. Each card becomes a clickable header
    with a chevron; the body is hidden until you open it. Done in JS by
    wrapping each card's contents at load time, so it applies automatically to
    any card added later and needs no edit to the other twelve blocks.

    Opened sections are remembered in sessionStorage, so saving a section
    (which reloads the page) leaves it open where you were working.

Idempotent; backs up to notification_settings.html.bak_collapse.
Run from the project root:

    python apply_notification_settings_ui.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, 'pages', 'templates', 'notification_settings.html')
SENTINEL = 'expense_mismatch'

# ---------------------------------------------------------------- 1. card ---
ANCHOR = '<!-- Friday Status Report - Supervisor Submits -->'

NEW_CARD = '''<!-- Expense Invoice Mismatch -->
<div class="notification-card">
    <h5><i class="fas fa-exclamation-triangle"></i> Expense Invoice Mismatch</h5>
    <p class="text-muted">Alert when an uploaded invoice total does not match the approved expense amount. Sent only on a confirmed mismatch, never on a routine upload.</p>

    <form method="post">
        {% csrf_token %}
        <input type="hidden" name="notification_type" value="expense_mismatch">

        <div class="form-group">
            <label><strong>TO:</strong> Primary Recipients</label>
            <textarea
                class="form-control"
                name="to_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.expense_mismatch.to_emails }}</textarea>
            <div class="field-hint">Person who approves expenses and can un-approve to allow a correction</div>
        </div>

        <div class="form-group">
            <label><strong>CC:</strong> Carbon Copy Recipients (optional)</label>
            <textarea
                class="form-control"
                name="cc_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.expense_mismatch.cc_emails }}</textarea>
            <div class="field-hint">Additional recipients who should be informed</div>
        </div>

        <button type="submit" class="btn btn-info">
            <i class="fas fa-save"></i> Save
        </button>
    </form>
</div>

'''

# ------------------------------------------------------------ 2. collapse ---
STYLE_ANCHOR = '.notification-card {'

COLLAPSE_CSS = '''.notification-card > h5 {
    cursor: pointer;
    user-select: none;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0;
}
.notification-card > h5 .collapse-chevron {
    margin-left: auto;
    font-size: 0.85em;
    opacity: 0.55;
    transition: transform 0.15s ease;
}
.notification-card.is-open > h5 .collapse-chevron { transform: rotate(90deg); }
.notification-card.is-collapsible > h5 { margin-bottom: 0; }
.notification-card .card-body-wrap { padding-top: 14px; }
.notification-card:not(.is-open) .card-body-wrap { display: none; }
.notification-toolbar {
    display: flex; gap: 10px; justify-content: flex-end;
    margin: 0 0 14px 0;
}
.notification-toolbar button {
    background: none; border: 0; color: #17a2b8;
    font-size: 0.9rem; cursor: pointer; padding: 4px 8px;
}
.notification-toolbar button:hover { text-decoration: underline; }
.notification-card {'''

SCRIPT_ANCHOR = '{% endblock %}'

COLLAPSE_JS = '''
<script>
// ---------------------------------------------------------------------
// Collapse each notification section to its title. Built at runtime by
// wrapping every card's contents, so the twelve existing cards need no edit
// and any card added later is picked up automatically.
// ---------------------------------------------------------------------
(function () {
    var KEY = 'notifSettingsOpen';

    function openSet() {
        try { return new Set(JSON.parse(sessionStorage.getItem(KEY) || '[]')); }
        catch (e) { return new Set(); }
    }
    function persist(set) {
        try { sessionStorage.setItem(KEY, JSON.stringify(Array.from(set))); }
        catch (e) { /* private mode - collapsing still works, just not remembered */ }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var cards = Array.prototype.slice.call(
            document.querySelectorAll('.notification-card'));
        if (!cards.length) { return; }

        var open = openSet();

        cards.forEach(function (card, index) {
            var head = card.querySelector('h5');
            if (!head || card.classList.contains('is-collapsible')) { return; }

            // Identify by the hidden notification_type, so the remembered
            // state survives cards being reordered or added.
            var typeInput = card.querySelector('input[name="notification_type"]');
            var id = typeInput ? typeInput.value : ('card-' + index);
            card.dataset.notifId = id;

            // Everything after the heading becomes the collapsible body.
            var wrap = document.createElement('div');
            wrap.className = 'card-body-wrap';
            while (head.nextSibling) { wrap.appendChild(head.nextSibling); }
            card.appendChild(wrap);

            var chevron = document.createElement('i');
            chevron.className = 'fas fa-chevron-right collapse-chevron';
            head.appendChild(chevron);

            card.classList.add('is-collapsible');
            if (open.has(id)) { card.classList.add('is-open'); }

            head.addEventListener('click', function () {
                card.classList.toggle('is-open');
                var set = openSet();
                if (card.classList.contains('is-open')) { set.add(id); }
                else { set.delete(id); }
                persist(set);
            });
        });

        // Expand / collapse all
        var bar = document.createElement('div');
        bar.className = 'notification-toolbar';
        bar.innerHTML =
            '<button type="button" data-act="all"><i class="fas fa-angle-double-down"></i> Expand all</button>' +
            '<button type="button" data-act="none"><i class="fas fa-angle-double-up"></i> Collapse all</button>';
        cards[0].parentNode.insertBefore(bar, cards[0]);

        bar.addEventListener('click', function (e) {
            var btn = e.target.closest('button');
            if (!btn) { return; }
            var wantOpen = btn.dataset.act === 'all';
            var set = new Set();
            cards.forEach(function (card) {
                card.classList.toggle('is-open', wantOpen);
                if (wantOpen) { set.add(card.dataset.notifId); }
            });
            persist(set);
        });

        // A save reloads the page - reopen whatever was open, and if the URL
        // names a section (?open=expense_mismatch) open that one too.
        var wanted = new URLSearchParams(window.location.search).get('open');
        if (wanted) {
            var target = cards.filter(function (c) { return c.dataset.notifId === wanted; })[0];
            if (target) {
                target.classList.add('is-open');
                var set = openSet(); set.add(wanted); persist(set);
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
})();
</script>

{% endblock %}'''


def main():
    if not os.path.exists(TARGET):
        print('! pages/templates/notification_settings.html not found')
        return 1
    with open(TARGET, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    src = raw.decode(enc).replace('\r\n', '\n')

    if SENTINEL in src:
        print('= already patched - nothing to do')
        return 0

    checks = [('card anchor', ANCHOR, 1),
              ('style anchor', STYLE_ANCHOR, None),
              ('endblock', SCRIPT_ANCHOR, None)]
    for name, token, expected in checks:
        n = src.count(token)
        if n == 0 or (expected is not None and n != expected):
            print('! %s matched %d times%s - aborting, nothing written'
                  % (name, n, '' if expected is None else ', expected %d' % expected))
            return 1

    src = src.replace(ANCHOR, NEW_CARD + ANCHOR, 1)
    src = src.replace(STYLE_ANCHOR, COLLAPSE_CSS, 1)
    # last {% endblock %} in the file is the content block's
    tail = src.rindex(SCRIPT_ANCHOR)
    src = src[:tail] + COLLAPSE_JS

    if CHECK:
        print('= check only: all anchors matched, nothing written')
        return 0

    bak = TARGET + '.bak_collapse'
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak)
    with open(TARGET, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)

    print('+ notification_settings.html patched (backup: .bak_collapse)')
    print('  - added the "Expense Invoice Mismatch" card')
    print('  - every section now collapses to its title, with Expand/Collapse all')
    print('  - open sections remembered across a save')
    return 0


if __name__ == '__main__':
    sys.exit(main())
