# -*- coding: utf-8 -*-
"""
Apply: bring the Physical Invoices list header onto the Back+1 mobile standard.

Standard (as used by act_expense.html / celebrations):
  Desktop : [primary] [secondary...] [Back]   (all inline)
  Mobile  : [primary (wide)] [More v] [Back]   (secondaries hidden, in More menu)

Changes to pages/templates/physical_invoice_list.html:
  1. Action row markup:
       - Help            -> keep visible on desktop, class action-secondary
       - New Customer Invoice -> class action-primary (the wide primary on mobile)
       - Manage Customers     -> class action-secondary
       - add a mobile-only More dropdown (.action-more-wrapper) duplicating
         Help + Manage Customers as menu items
       - Back unchanged (action-back)
  2. Desktop CSS: hide .action-more-wrapper (mobile-only component)
  3. Mobile CSS: replace the previous wrap rule with the standard Back+1 rules
     (hide .action-secondary, widen .action-primary, show/size the More menu)
  4. JS: toggle for the More menu (open/close, outside-click, Esc)

Fail-loud: every anchor must appear exactly once or nothing is written.
Run from the repo root:  python apply_pi_list_back1_standard.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "templates", "physical_invoice_list.html")

# ---- 1. Action row markup ------------------------------------------------ #
MARKUP_OLD = '''    <!-- Action Buttons -->
    <div class="page-action-buttons">
      <button type="button" class="btn btn-info action-secondary" data-toggle="modal" data-target="#physical_invoicesHelpModal">
        <i class="fas fa-question-circle"></i> Help
      </button>
      {% if perms.auth.can_edit_tenants %}
        <a href="{% url 'customer_invoice_create' %}" class="btn btn-info action-secondary">
          <i class="fas fa-file-invoice-dollar"></i> New Customer Invoice
        </a>
      {% endif %}
      {% if perms.auth.can_access_tenants %}
        <a href="{% url 'customer_list' %}" class="btn btn-info action-secondary">
          <i class="fas fa-address-book"></i> Manage Customers
        </a>
      {% endif %}
      <a href="{% url 'tenant' %}" class="btn btn-info action-back" aria-label="Back to tenants">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
      </a>
    </div>'''

MARKUP_NEW = '''    <!-- Action Buttons - Desktop: [Help] [New Customer Invoice] [Manage Customers] [Back]
                          Mobile:  [New Customer Invoice (wide)] [More] [Back] -->
    <div class="page-action-buttons">
      <button type="button" class="btn btn-info action-secondary" data-toggle="modal" data-target="#physical_invoicesHelpModal">
        <i class="fas fa-question-circle"></i> Help
      </button>
      {% if perms.auth.can_edit_tenants %}
        <a href="{% url 'customer_invoice_create' %}" class="btn btn-info action-primary">
          <i class="fas fa-file-invoice-dollar"></i> New Customer Invoice
        </a>
      {% endif %}
      {% if perms.auth.can_access_tenants %}
        <a href="{% url 'customer_list' %}" class="btn btn-info action-secondary">
          <i class="fas fa-address-book"></i> Manage Customers
        </a>
      {% endif %}

      <!-- Mobile-only More dropdown (holds the secondary actions) -->
      <div class="action-more-wrapper">
        <button type="button" class="btn btn-info action-more-btn" id="actionMoreBtn"
                aria-label="More actions" aria-expanded="false" aria-haspopup="true">
          <i class="fas fa-ellipsis-v"></i>
        </button>
        <div class="action-more-menu" id="actionMoreMenu" role="menu" hidden>
          <button type="button" class="action-more-item" role="menuitem" data-toggle="modal" data-target="#physical_invoicesHelpModal">
            <i class="fas fa-question-circle"></i> Help
          </button>
          {% if perms.auth.can_access_tenants %}
            <a href="{% url 'customer_list' %}" class="action-more-item" role="menuitem">
              <i class="fas fa-address-book"></i> Manage Customers
            </a>
          {% endif %}
        </div>
      </div>

      <a href="{% url 'tenant' %}" class="btn btn-info action-back" aria-label="Back to tenants">
        <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
      </a>
    </div>'''

# ---- 2. Desktop CSS: hide the More wrapper off mobile -------------------- #
DESKTOP_OLD = '''.page-action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-bottom: 20px;
}'''
DESKTOP_NEW = '''.page-action-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-bottom: 20px;
}
/* The More dropdown is a mobile-only component; hidden on desktop. */
.action-more-wrapper { display: none; }'''

# ---- 3. Mobile CSS: replace the earlier wrap block with the standard ----- #
MOBILE_OLD = '''  .page-action-buttons {
    display: flex; flex-direction: row; gap: 8px; width: 100%;
    flex-wrap: wrap; align-items: stretch; margin-bottom: 14px;
    justify-content: flex-end;
  }
  .action-secondary {
    flex: 1 1 auto; min-width: 0; height: 38px;
    display: flex; align-items: center; justify-content: center;
    padding: 0 10px; font-size: 13px; white-space: nowrap; margin: 0;
    overflow: hidden; text-overflow: ellipsis;
  }
  .action-back {
    flex: 0 0 auto; width: 44px; height: 38px; padding: 0;
    display: flex; align-items: center; justify-content: center; margin: 0;
  }
  .action-back-label { display: none; }'''

MOBILE_NEW = '''  /* Back+1 standard: [New Customer Invoice (wide)] [More] [Back] */
  .page-action-buttons {
    display: flex; flex-direction: row; gap: 8px; width: 100%;
    flex-wrap: nowrap; align-items: stretch; margin-bottom: 14px;
    justify-content: flex-end;
  }
  /* Secondary actions are reached via the More menu on mobile */
  .page-action-buttons .action-secondary { display: none; }
  /* Primary action takes the leftover width */
  .page-action-buttons .action-primary {
    flex: 1 1 auto; min-width: 0; height: 38px;
    display: flex; align-items: center; justify-content: center;
    padding: 0 12px; font-size: 13px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; margin: 0; gap: 6px;
  }
  /* More dropdown — shown on mobile only */
  .action-more-wrapper { display: block; position: relative; flex: 0 0 auto; }
  .action-more-btn {
    width: 44px; height: 38px; padding: 0; margin: 0;
    display: flex; align-items: center; justify-content: center;
  }
  .action-more-menu {
    position: absolute; top: calc(100% + 6px); right: 0; z-index: 200;
    background: white; border: 1px solid #dee2e6; border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.14); padding: 6px; min-width: 210px;
  }
  .action-more-menu[hidden] { display: none; }
  .action-more-item {
    display: flex; align-items: center; gap: 10px; width: 100%;
    background: none; border: none; text-align: left; cursor: pointer;
    padding: 10px 12px; border-radius: 6px; font-size: 14px; color: #2c3e50;
    text-decoration: none;
  }
  .action-more-item i { color: #17a2b8; width: 18px; text-align: center; }
  .action-more-item:hover { background: #f1f3f5; color: #2c3e50; text-decoration: none; }
  .action-back {
    flex: 0 0 auto; width: 44px; height: 38px; padding: 0;
    display: flex; align-items: center; justify-content: center; margin: 0;
  }
  .action-back-label { display: none; }'''

# ---- 4. JS: More-menu toggle, injected before the filter-form script ----- #
JS_OLD = '''<script>
// Auto-submit the filter form when month or status changes.
document.addEventListener('DOMContentLoaded', function () {
    ['fromInput', 'toInput', 'statusSelect', 'typeSelect'].forEach(function (id) {'''
JS_NEW = '''<script>
// More-menu (mobile) open/close.
document.addEventListener('DOMContentLoaded', function () {
    var moreBtn = document.getElementById('actionMoreBtn');
    var moreMenu = document.getElementById('actionMoreMenu');
    if (moreBtn && moreMenu) {
        function closeMenu() { moreMenu.hidden = true; moreBtn.setAttribute('aria-expanded', 'false'); }
        function openMenu() { moreMenu.hidden = false; moreBtn.setAttribute('aria-expanded', 'true'); }
        moreBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            if (moreMenu.hidden) { openMenu(); } else { closeMenu(); }
        });
        document.addEventListener('click', function (e) {
            if (!moreMenu.hidden && !moreMenu.contains(e.target) && e.target !== moreBtn) { closeMenu(); }
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { closeMenu(); }
        });
        // A menu item that opens a modal should also close the menu.
        moreMenu.querySelectorAll('.action-more-item').forEach(function (item) {
            item.addEventListener('click', function () { closeMenu(); });
        });
    }
});
</script>

<script>
// Auto-submit the filter form when month or status changes.
document.addEventListener('DOMContentLoaded', function () {
    ['fromInput', 'toInput', 'statusSelect', 'typeSelect'].forEach(function (id) {'''

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
        sys.exit("ABORTED - More-menu markup already present in %s" % TPL)

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

    # Net brace balance must be unchanged at file level.
    if new_src.count("{") - src.count("{") != new_src.count("}") - src.count("}"):
        sys.exit("ABORTED - edit changes overall brace balance; nothing written.")

    with io.open(TPL + ".prebak3", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak3)" % (TPL, TPL))
    print("done. HARD-refresh the list on a narrow viewport (Ctrl+Shift+R).")


if __name__ == "__main__":
    main()