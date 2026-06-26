# -*- coding: utf-8 -*-
"""
Option B - Step 4b: add the Physical Invoices entry button to Open Invoices.

  pages/templates/invoices.html
    Desktop : [Physical Invoices] [Help] [Back]
    Mobile  : [Physical Invoices (wide)] [More] [Back]   (Help -> More menu)

This re-homes the Physical Invoices entry point onto the Open Invoices screen
(its new module home), using the same Back+1 / More-menu pattern as the PI list
and Tenants screens. The Physical Invoices button is unguarded by design: the
page itself already requires can_access_invoices (middleware + view), so anyone
who can see this screen may use the button, and the mobile layout always has its
wide primary.

Four edits: action-row markup, desktop CSS (hide More wrapper), mobile CSS
(hide secondary, show/size More menu), and JS (More-menu toggle, injected into
the existing DOMContentLoaded so no new <script> tag is needed).

Fail-loud: every anchor exactly once, net brace balance unchanged, <script>/<style>
tag counts unchanged. Nothing written otherwise.

Run from the repo root:  python apply_pi_perms_step4b_invoices_button.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "invoices.html")

# ---- 1. action-row markup ------------------------------------------------ #
MARKUP_OLD = '''  <!-- Action Buttons (Help + Back, Back+1 standard on mobile) -->
  <div class="invoices-action-buttons">
    <button type="button" class="btn btn-info action-primary" data-toggle="modal" data-target="#invoicesHelpModal">
      <i class="fas fa-question-circle"></i> Help
    </button>
    <a href="{% url 'home' %}" class="btn btn-info action-back" aria-label="Back to home">
      <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
  </div>'''

MARKUP_NEW = '''  <!-- Action Buttons - Desktop: [Physical Invoices] [Help] [Back]
                         Mobile:  [Physical Invoices (wide)] [More] [Back] -->
  <div class="invoices-action-buttons">
    <a href="{% url 'physical_invoice_list' %}" class="btn btn-info action-primary">
      <i class="fas fa-file-invoice"></i> Physical Invoices
    </a>
    <button type="button" class="btn btn-info action-secondary" data-toggle="modal" data-target="#invoicesHelpModal">
      <i class="fas fa-question-circle"></i> Help
    </button>

    <!-- Mobile-only More dropdown (holds the secondary actions) -->
    <div class="action-more-wrapper">
      <button type="button" class="btn btn-info action-more-btn" id="actionMoreBtn"
              aria-label="More actions" aria-expanded="false" aria-haspopup="true">
        <i class="fas fa-ellipsis-v"></i>
      </button>
      <div class="action-more-menu" id="actionMoreMenu" role="menu" hidden>
        <button type="button" class="action-more-item" role="menuitem" data-toggle="modal" data-target="#invoicesHelpModal">
          <i class="fas fa-question-circle"></i> Help
        </button>
      </div>
    </div>

    <a href="{% url 'home' %}" class="btn btn-info action-back" aria-label="Back to home">
      <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
    </a>
  </div>'''

# ---- 2. desktop CSS: hide the More wrapper off mobile -------------------- #
DESKTOP_OLD = '''/* ==================== ACTION BUTTONS (DESKTOP) ==================== */
.invoices-action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-bottom: 20px;
}'''
DESKTOP_NEW = '''/* ==================== ACTION BUTTONS (DESKTOP) ==================== */
.invoices-action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-bottom: 20px;
}
/* The More dropdown is a mobile-only component; hidden on desktop. */
.action-more-wrapper { display: none; }'''

# ---- 3. mobile CSS: hide secondary, show/size the More menu -------------- #
MOBILE_OLD = '''    .action-back-label {
        display: none;
    }'''
MOBILE_NEW = '''    .action-back-label {
        display: none;
    }

    /* Secondary actions live in the More menu on mobile */
    .invoices-action-buttons .action-secondary { display: none; }
    .action-more-wrapper { display: block; position: relative; flex: 0 0 auto; }
    .action-more-btn {
        width: 44px; height: 38px; padding: 0; margin: 0;
        display: flex; align-items: center; justify-content: center;
    }
    .action-more-menu {
        position: absolute; top: calc(100% + 6px); right: 0; z-index: 200;
        background: white; border: 1px solid #dee2e6; border-radius: 8px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15); min-width: 220px; padding: 6px 0;
    }
    .action-more-menu[hidden] { display: none; }
    .action-more-item {
        display: flex; align-items: center; gap: 12px; width: 100%;
        background: none; border: none; text-align: left; cursor: pointer;
        padding: 12px 16px; font-size: 14px; color: #2c3e50; text-decoration: none;
    }
    .action-more-item i { color: #17a2b8; width: 18px; text-align: center; flex-shrink: 0; }
    .action-more-item:hover, .action-more-item:active, .action-more-item:focus {
        background: #f0f8ff; outline: none; color: #2c3e50; text-decoration: none;
    }'''

# ---- 4. JS: More-menu toggle, injected into the existing DOMContentLoaded #
JS_OLD = '''document.addEventListener('DOMContentLoaded', function() {
    updateActiveFilters();'''
JS_NEW = '''document.addEventListener('DOMContentLoaded', function() {
    updateActiveFilters();

    // Mobile More-menu (Help lives here on phones)
    (function () {
        var moreBtn = document.getElementById('actionMoreBtn');
        var moreMenu = document.getElementById('actionMoreMenu');
        if (!moreBtn || !moreMenu) return;
        function closeMenu() { moreMenu.hidden = true; moreBtn.setAttribute('aria-expanded', 'false'); }
        function openMenu() { moreMenu.hidden = false; moreBtn.setAttribute('aria-expanded', 'true'); }
        moreBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            if (moreMenu.hidden) { openMenu(); } else { closeMenu(); }
        });
        document.addEventListener('click', function (e) {
            if (!moreMenu.hidden && !moreMenu.contains(e.target) && e.target !== moreBtn) { closeMenu(); }
        });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeMenu(); } });
        moreMenu.querySelectorAll('.action-more-item').forEach(function (item) {
            item.addEventListener('click', function () { closeMenu(); });
        });
    })();'''

EDITS = [("markup", MARKUP_OLD, MARKUP_NEW),
         ("desktop css", DESKTOP_OLD, DESKTOP_NEW),
         ("mobile css", MOBILE_OLD, MOBILE_NEW),
         ("js", JS_OLD, JS_NEW)]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    if "action-more-wrapper" in src:
        sys.exit("ABORTED - More-menu markup already present; nothing written.")

    problems = []
    for name, old, _new in EDITS:
        c = src.count(old)
        if c != 1:
            problems.append("  %s: anchor found %d time(s) (expected 1)" % (name, c))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for _name, old, new in EDITS:
        new_src = new_src.replace(old, new, 1)

    if new_src.count("{") - src.count("{") != new_src.count("}") - src.count("}"):
        sys.exit("ABORTED - edit changes overall brace balance; nothing written.")
    if new_src.count("<script>") != src.count("<script>") or new_src.count("</script>") != src.count("</script>"):
        sys.exit("ABORTED - edit changes <script> tag count; nothing written.")
    if new_src.count("<style>") != src.count("<style>") or new_src.count("</style>") != src.count("</style>"):
        sys.exit("ABORTED - edit changes <style> tag count; nothing written.")

    with io.open(TPL + ".prebak4b", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak4b)" % (TPL, TPL))
    print("done. HARD-refresh Open Invoices (Ctrl+Shift+R); check desktop + a narrow viewport.")


if __name__ == "__main__":
    main()