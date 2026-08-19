#!/usr/bin/env python3
"""
apply_reports_dropdown.py
=========================

Consolidates the report buttons on Tenants and Issues into a single desktop
"Reports" dropdown, and replaces the two duplicated copies of the mobile
"More" menu JavaScript with one shared component in base.html.

Why only those two pages
------------------------
Both carry four report buttons and both keep growing. Expenses has two, and
both open modals in place - folding two items behind a menu costs a click each
and saves no clutter, so Expenses is deliberately left alone. The working rule
is: three or more reports earns a dropdown.

Desktop only. Below 768px the reports already collapse into the existing
"More" menu, and nesting a submenu inside that would be worse. Mobile looks
exactly as it does today; only the code driving it changes.

The opt-in marker, and why it matters
-------------------------------------
The shared JS binds `[data-menu]`, NOT `.action-more-wrapper`.

That distinction is the whole safety argument. At least three templates carry
their own copy of `initializeMoreMenu()`, and there are ~130 templates in total
that have not been audited. A global binder matching `.action-more-wrapper`
would double-bind anywhere a local copy still exists - the menu would open and
instantly close, on pages nobody thought to test.

With the marker, only the wrappers converted here are driven by the shared
component. Every other template keeps its own copy and is provably untouched,
and the rest can migrate later by adding three attributes.

Why not Bootstrap's dropdown
----------------------------
base.html binds `.dropdown` to open on HOVER for the nav bar. Reusing it would
make Reports spring open as the pointer crossed it. An action menu should need
a deliberate click.

Files touched
-------------
  pages/templates/base.html      + shared dropdown CSS and JS
  pages/templates/tenant.html    4 report buttons -> one menu; local JS removed
  pages/templates/fsr.html       4 report buttons -> one menu; local JS removed

No view, model, URL or migration change.

Idempotent; backs each file up on first run (.bak_reportsmenu). Run from the
project root:

    python apply_reports_dropdown.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')

BASE = os.path.join(T, 'base.html')
TENANT = os.path.join(T, 'tenant.html')
FSR = os.path.join(T, 'fsr.html')

SENTINEL = 'data-menu-toggle'


# ---------------------------------------------------------------------------
# 1. base.html - the shared component
# ---------------------------------------------------------------------------

BASE_ANCHOR = '{% block extra_scripts %}{% endblock %}'

SHARED = '''<!-- ==================== SHARED ACTION DROPDOWN ==================== -->
<!-- Drives any element marked `data-menu`, with `data-menu-toggle` on the
     button and `data-menu-panel` on the panel. Deliberately NOT bound to
     `.action-more-wrapper`: several templates still carry their own copy of
     initializeMoreMenu(), and a class-wide binder would double-bind there -
     the menu would open and immediately close. Pages opt in by adding the
     three attributes; everything else is untouched.

     Also deliberately not Bootstrap's .dropdown, which is bound to open on
     HOVER further down this file for the nav bar. An action menu should need
     a click. -->
  <style>
  .ui-menu { position: relative; display: inline-block; }

  .ui-menu-toggle { white-space: nowrap; }
  .ui-menu-caret {
      margin-left: 6px;
      font-size: 11px;
      transition: transform 0.2s ease;
  }
  .ui-menu[data-open="true"] .ui-menu-caret { transform: rotate(180deg); }

  .ui-menu-panel {
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      min-width: 232px;
      background: #fff;
      border: 1px solid #dee2e6;
      border-radius: 8px;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
      padding: 6px 0;
      z-index: 1050;
      text-align: left;
  }

  .ui-menu-item {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 9px 16px;
      background: none;
      border: 0;
      text-align: left;
      font-size: 14px;
      color: #2c3e50;
      text-decoration: none;
      white-space: nowrap;
      cursor: pointer;
  }
  .ui-menu-item:hover,
  .ui-menu-item:focus {
      background: #f1f6f9;
      color: #17a2b8;
      text-decoration: none;
      outline: none;
  }
  .ui-menu-item i { width: 16px; text-align: center; color: #17a2b8; }

  /* Belt and braces. The pages that use it also tag the wrapper with the
     house `.action-secondary` class, but the component should not depend on
     the page remembering to do that. */
  @media (max-width: 768px) {
      .ui-menu { display: none; }
  }
  </style>

  <script>
  (function () {
      "use strict";

      function initActionMenus(root) {
          var scope = root || document;
          Array.prototype.forEach.call(
              scope.querySelectorAll('[data-menu]'), function (menu) {

              // Idempotent: safe to call again after injecting markup.
              if (menu.getAttribute('data-menu-bound') === '1') { return; }

              var toggle = menu.querySelector('[data-menu-toggle]');
              var panel = menu.querySelector('[data-menu-panel]');
              if (!toggle || !panel) { return; }
              menu.setAttribute('data-menu-bound', '1');

              function items() {
                  return Array.prototype.slice.call(
                      panel.querySelectorAll('a, button'));
              }

              function close() {
                  panel.setAttribute('hidden', '');
                  toggle.setAttribute('aria-expanded', 'false');
                  menu.setAttribute('data-open', 'false');
              }

              function open() {
                  // One at a time - two open panels overlap and confuse.
                  Array.prototype.forEach.call(
                      document.querySelectorAll('[data-menu][data-open="true"]'),
                      function (other) {
                          if (other !== menu) {
                              var p = other.querySelector('[data-menu-panel]');
                              var t = other.querySelector('[data-menu-toggle]');
                              if (p) { p.setAttribute('hidden', ''); }
                              if (t) { t.setAttribute('aria-expanded', 'false'); }
                              other.setAttribute('data-open', 'false');
                          }
                      });
                  panel.removeAttribute('hidden');
                  toggle.setAttribute('aria-expanded', 'true');
                  menu.setAttribute('data-open', 'true');
              }

              function isOpen() { return !panel.hasAttribute('hidden'); }

              toggle.addEventListener('click', function (e) {
                  e.preventDefault();
                  e.stopPropagation();
                  if (isOpen()) { close(); } else { open(); }
              });

              document.addEventListener('click', function (e) {
                  if (isOpen() && !menu.contains(e.target)) { close(); }
              });

              document.addEventListener('keydown', function (e) {
                  if (e.key === 'Escape' && isOpen()) {
                      close();
                      toggle.focus();
                  }
              });

              // Arrow keys, so the menu is usable without a mouse.
              menu.addEventListener('keydown', function (e) {
                  if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') { return; }
                  e.preventDefault();
                  if (!isOpen()) { open(); }
                  var list = items();
                  if (!list.length) { return; }
                  var at = list.indexOf(document.activeElement);
                  var next;
                  if (e.key === 'ArrowDown') {
                      next = at < 0 ? 0 : (at + 1) % list.length;
                  } else {
                      next = at <= 0 ? list.length - 1 : at - 1;
                  }
                  list[next].focus();
              });

              // A click on an item either navigates or opens a modal; either
              // way the panel should not be left hanging open behind it.
              panel.addEventListener('click', function (e) {
                  if (e.target.closest('a, button')) { close(); }
              });

              close();
          });
      }

      window.initActionMenus = initActionMenus;

      if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', function () {
              initActionMenus();
          });
      } else {
          initActionMenus();
      }
  })();
  </script>

'''


# ---------------------------------------------------------------------------
# 2. tenant.html
# ---------------------------------------------------------------------------

TEN_BTNS_OLD = """      <a href="{% url 'lease_timeline' %}" class="btn btn-info action-secondary">\U0001F4C5 Lease Timeline</a>
      <a href="{% url 'open_invoices_report' %}" class="btn btn-info action-secondary">Open Invoices</a>
      <a href="{% url 'lease_renewal_report' %}" class="btn btn-info action-secondary">Lease Renewals</a>
      <a href="{% url 'tenant_payment_days' %}" class="btn btn-info action-secondary">Payment Behaviour</a>
"""

TEN_BTNS_NEW = """      <!-- Desktop: four reports behind one menu. `action-secondary` is the
           house marker that hides an item under 768px, where the "More"
           dropdown below takes over. -->
      <div class="ui-menu action-secondary" data-menu>
        <button type="button" class="btn btn-info ui-menu-toggle"
                data-menu-toggle aria-haspopup="true" aria-expanded="false">
          <i class="fas fa-chart-bar"></i> Reports
          <i class="fas fa-chevron-down ui-menu-caret"></i>
        </button>
        <div class="ui-menu-panel" data-menu-panel role="menu" hidden>
          <a href="{% url 'lease_timeline' %}" class="ui-menu-item" role="menuitem">
            <i class="fas fa-calendar-alt"></i> Lease Timeline
          </a>
          <a href="{% url 'open_invoices_report' %}" class="ui-menu-item" role="menuitem">
            <i class="fas fa-file-invoice-dollar"></i> Open Invoices
          </a>
          <a href="{% url 'lease_renewal_report' %}" class="ui-menu-item" role="menuitem">
            <i class="fas fa-sync-alt"></i> Lease Renewals
          </a>
          <a href="{% url 'tenant_payment_days' %}" class="ui-menu-item" role="menuitem">
            <i class="fas fa-stopwatch"></i> Payment Behaviour
          </a>
        </div>
      </div>
"""

TEN_WRAP_OLD = """<div class="action-more-wrapper">
        <button type="button" class="btn btn-info action-more-btn" id="actionMoreBtn" aria-label="More actions" aria-expanded="false" aria-haspopup="true">
          <i class="fas fa-ellipsis-v"></i>
        </button>
        <div class="action-more-menu" id="actionMoreMenu" role="menu" hidden>
"""

TEN_WRAP_NEW = """<div class="action-more-wrapper" data-menu>
        <button type="button" class="btn btn-info action-more-btn" id="actionMoreBtn" data-menu-toggle aria-label="More actions" aria-expanded="false" aria-haspopup="true">
          <i class="fas fa-ellipsis-v"></i>
        </button>
        <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
"""

TEN_CALL_OLD = """
    // Initialize the mobile "More" dropdown menu
    initializeMoreMenu();
"""

TEN_CALL_NEW = """
    // The "More" dropdown is driven by the shared component in base.html.
"""

TEN_FUNC_START = '// Mobile-only "More" actions dropdown'
TEN_FUNC_END = """            closeMenu();
        });
    });
}
"""


# ---------------------------------------------------------------------------
# 3. fsr.html (Issues)
# ---------------------------------------------------------------------------

FSR_BTNS_OLD = """        <button class="btn btn-info action-secondary" data-toggle="modal" data-target="#commentsReportModal">
            Comments Report
        </button>
        <button class="btn btn-info action-secondary" data-toggle="modal" data-target="#dateRangeModal">
            Resolved Issues Report
        </button>
        <button class="btn btn-info action-secondary" data-toggle="modal" data-target="#issuesAnalysisModal">
            <i class="fas fa-chart-bar"></i> Analysis
        </button>
        <button class="btn btn-info action-secondary" data-toggle="modal" data-target="#fridayReportModal">
            Friday Status Report
        </button>
"""

FSR_BTNS_NEW = """        <!-- Desktop: four reports behind one menu. `action-secondary` is the
             house marker that hides an item under 768px, where the "More"
             dropdown below takes over. Every item here opens a modal rather
             than navigating, so the page stays put. -->
        <div class="ui-menu action-secondary" data-menu>
            <button type="button" class="btn btn-info ui-menu-toggle"
                    data-menu-toggle aria-haspopup="true" aria-expanded="false">
                <i class="fas fa-chart-bar"></i> Reports
                <i class="fas fa-chevron-down ui-menu-caret"></i>
            </button>
            <div class="ui-menu-panel" data-menu-panel role="menu" hidden>
                <button type="button" class="ui-menu-item" role="menuitem"
                        data-toggle="modal" data-target="#commentsReportModal">
                    <i class="fas fa-comments"></i> Comments Report
                </button>
                <button type="button" class="ui-menu-item" role="menuitem"
                        data-toggle="modal" data-target="#dateRangeModal">
                    <i class="fas fa-calendar-alt"></i> Resolved Issues Report
                </button>
                <button type="button" class="ui-menu-item" role="menuitem"
                        data-toggle="modal" data-target="#issuesAnalysisModal">
                    <i class="fas fa-chart-line"></i> Analysis
                </button>
                <button type="button" class="ui-menu-item" role="menuitem"
                        data-toggle="modal" data-target="#fridayReportModal">
                    <i class="fas fa-file-alt"></i> Friday Status Report
                </button>
            </div>
        </div>
"""

FSR_WRAP_OLD = """<div class="action-more-wrapper">
            <button type="button" class="btn btn-info action-more-btn" id="actionMoreBtn" aria-label="More actions" aria-expanded="false" aria-haspopup="true">
                <i class="fas fa-ellipsis-v"></i>
            </button>
            <div class="action-more-menu" id="actionMoreMenu" role="menu" hidden>
"""

FSR_WRAP_NEW = """<div class="action-more-wrapper" data-menu>
            <button type="button" class="btn btn-info action-more-btn" id="actionMoreBtn" data-menu-toggle aria-label="More actions" aria-expanded="false" aria-haspopup="true">
                <i class="fas fa-ellipsis-v"></i>
            </button>
            <div class="action-more-menu" id="actionMoreMenu" data-menu-panel role="menu" hidden>
"""

FSR_CALL_OLD = """
    // Initialize the mobile "More" dropdown menu
    initializeMoreMenu();
"""

FSR_CALL_NEW = """
    // The "More" dropdown is driven by the shared component in base.html.
"""

FSR_FUNC_START = '// Mobile-only "More" actions dropdown'
FSR_FUNC_END = """    console.log('✅ Mobile "More" menu initialized');
}
"""


def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def cut_function(src, start_marker, end_marker, label):
    """Remove the local initializeMoreMenu() block, start marker to end marker.

    Bounded by an explicit tail rather than brace counting: the tails differ
    between the two files (one ends with a console.log) and a miscounted brace
    would silently eat the next function.
    """
    i = src.find(start_marker)
    if i == -1:
        return None, '%s: function start marker not found' % label
    j = src.find(end_marker, i)
    if j == -1:
        return None, '%s: function end marker not found' % label
    j += len(end_marker)
    block = src[i:j]
    if 'function initializeMoreMenu()' not in block:
        return None, '%s: the block found is not initializeMoreMenu' % label
    # Count TOP-LEVEL declarations only - `\nfunction ` at column zero. Counting
    # bare "function " would include the nested closeMenu/openMenu closures and
    # every anonymous handler, and the guard would fire on a correct cut.
    top_level = block.count('\nfunction ')
    if top_level != 1:
        return None, ('%s: the block spans %d top-level functions - refusing to cut'
                      % (label, top_level))
    # Trim the blank line that preceded the comment, so no gap is left.
    k = i
    while k > 0 and src[k - 1] == '\n':
        k -= 1
    return src[:k] + '\n' + src[j:], None


def patch_base(src):
    n = src.count(BASE_ANCHOR)
    if n != 1:
        return None, 'base.html: extra_scripts anchor matched %d times' % n
    return src.replace(BASE_ANCHOR, SHARED + BASE_ANCHOR, 1), None


def patch_page(src, label, btns_old, btns_new, wrap_old, wrap_new,
               call_old, call_new, func_start, func_end):
    for name, anchor in (('report buttons', btns_old),
                         ('more-menu wrapper', wrap_old),
                         ('init call', call_old)):
        n = src.count(anchor)
        if n != 1:
            return None, '%s: %s anchor matched %d times, expected 1' % (label, name, n)
    src = src.replace(btns_old, btns_new, 1)
    src = src.replace(wrap_old, wrap_new, 1)
    src = src.replace(call_old, call_new, 1)
    src, err = cut_function(src, func_start, func_end, label)
    if err:
        return None, err
    if 'initializeMoreMenu' in src:
        return None, '%s: a reference to initializeMoreMenu survived the cut' % label
    return src, None


def main():
    for path in (BASE, TENANT, FSR):
        if not os.path.exists(path):
            print('! %s not found - run from the project root'
                  % os.path.relpath(path, ROOT))
            return 1

    files = {}
    for key, path in (('base', BASE), ('tenant', TENANT), ('fsr', FSR)):
        files[key] = sniff(path)

    if all(SENTINEL in files[k][0] for k in files):
        print('= already applied - nothing to do')
        return 0

    results = {}

    out, err = patch_base(files['base'][0])
    if err:
        print('! ' + err)
        return 1
    results['base'] = out

    out, err = patch_page(files['tenant'][0], 'tenant.html',
                          TEN_BTNS_OLD, TEN_BTNS_NEW, TEN_WRAP_OLD, TEN_WRAP_NEW,
                          TEN_CALL_OLD, TEN_CALL_NEW, TEN_FUNC_START, TEN_FUNC_END)
    if err:
        print('! ' + err)
        print('  Aborting - nothing written.')
        return 1
    results['tenant'] = out

    out, err = patch_page(files['fsr'][0], 'fsr.html',
                          FSR_BTNS_OLD, FSR_BTNS_NEW, FSR_WRAP_OLD, FSR_WRAP_NEW,
                          FSR_CALL_OLD, FSR_CALL_NEW, FSR_FUNC_START, FSR_FUNC_END)
    if err:
        print('! ' + err)
        print('  Aborting - nothing written.')
        return 1
    results['fsr'] = out

    if CHECK:
        print('= check only: every anchor matched in all three files, nothing written')
        return 0

    paths = {'base': BASE, 'tenant': TENANT, 'fsr': FSR}
    for key, text in results.items():
        path = paths[key]
        _, enc, nl = files[key]
        bak = path + '.bak_reportsmenu'
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
        with open(path, 'w', encoding=enc, newline='') as fh:
            fh.write(text.replace('\n', nl) if nl == '\r\n' else text)
        print('+ pages/templates/%s patched' % os.path.basename(path))

    print('')
    print('  base.html    shared dropdown, binds [data-menu] only')
    print('  tenant.html  Add New | Help | Reports v | Back   (4 reports in the menu)')
    print('  fsr.html     Add New | Help | Reports v | Back   (4 reports in the menu)')
    print('  Mobile unchanged; act_expense.html untouched.')
    print('')
    print('Backups: .bak_reportsmenu alongside each file.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
