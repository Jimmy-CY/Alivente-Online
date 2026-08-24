#!/usr/bin/env python3
"""
apply_status_block_modal.py
===========================

The deactivation block now stops you ON the Edit Property page, in a dialog,
instead of throwing a paragraph onto the Properties list.

What was wrong
--------------
The guard called `messages.error(...)` and re-rendered properties_edit.html.
But that template has no messages block, so the message was never displayed
there - it sat unread in the session and surfaced on the next page that DOES
render messages, which is the Properties list. Hence a long explanation
appearing somewhere it did not belong, after the fact, and auto-dismissing
before it could be read.

A stored message is shown by whatever page renders next. Re-rendering a
template that does not render messages is a silent hole.

What changes
------------
The blockers are computed when the Edit page LOADS, and carried into the
template. On Save, if the status is being moved away from Active and blockers
exist, a modal opens and the submit is cancelled - so it is seen before
anything is attempted, on the page where the fix starts, and it stays until it
is dismissed.

The server-side guard remains, because a client-side check is a courtesy and
not a control: the POST can be replayed, and another session could add a
distribution while this page sits open. Its refusal now renders the SAME modal
open on load, rather than storing a message that leaks elsewhere. So both paths
say the same thing in the same place.

`onsubmit` becomes `validatePropertyName() && checkStatusBlockers()`. The name
check runs first and short-circuits, exactly as before.

Files touched
-------------
  pages/views/properties.py                 blockers in context, no stored message
  pages/templates/properties_edit.html      the modal + the submit check

Requires apply_inactive_guard.py. Idempotent; backs each file up on first run
(.bak_blockmodal).

    python apply_status_block_modal.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

PROPS = os.path.join(ROOT, 'pages', 'views', 'properties.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'properties_edit.html')

PROPS_SENTINEL = 'show_blocker_modal'
TPL_SENTINEL = 'statusBlockModal'


# ---------------------------------------------------------------------------
# 1. properties.py
# ---------------------------------------------------------------------------

VIEW_OLD = '''def properties_edit(request, prop_id):
    # Get the current property being edited
    current_property = get_object_or_404(props, pk=prop_id)

    # Get all other property names (excluding the current one)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)

    return render(request, "properties_edit.html", {
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names)  # Add this for client-side validation
    })
'''

VIEW_NEW = '''def properties_edit(request, prop_id):
    # Get the current property being edited
    current_property = get_object_or_404(props, pk=prop_id)

    # Get all other property names (excluding the current one)
    existing_names = props.objects.exclude(prop_id=prop_id).values_list('prop_name', flat=True)

    # Worked out on load, so Save can refuse in a dialog on this page rather
    # than storing a message that surfaces on whatever renders next.
    return render(request, "properties_edit.html", {
        "props": [current_property],  # Maintain your existing structure
        "existing_names": list(existing_names),  # Add this for client-side validation
        "prorata_blockers": [{'name': n, 'amount': a}
                             for n, a in _prorata_blockers(prop_id)],
        "show_blocker_modal": False,
    })
'''

GUARD_OLD = '''                if _blockers:
                    _detail = ', '.join('%s %.2f' % (n, a) for n, a in _blockers)
                    messages.error(
                        request,
                        "This property cannot be set to %s yet: it still holds "
                        "a share of %d pro-rata distribution(s) \\u2014 %s. Those "
                        "shares would carry on being charged to it in every "
                        "future year, while the other properties kept shares of "
                        "a split that still counted it \\u2014 so the line would "
                        "stop adding up to the charge actually owed. Open "
                        "Financial Management > Expenses, edit each of those "
                        "lines, set \\u201cApplies from\\u201d to the date this "
                        "property leaves, and un-tick it: the others take up its "
                        "share, and this one stops from that date while keeping "
                        "its earlier years. Then come back and set it %s."
                        % (_new_status, len(_blockers), _detail, _new_status))
                    return render(request, "properties_edit.html", {
                        'props': [props.objects.get(pk=prop_id)],
                        'existing_names': list(existing_names)
                    })
'''

GUARD_NEW = '''                if _blockers:
                    # No messages.error here, deliberately. This template has no
                    # messages block, so a stored message would not appear on
                    # this page at all - it would sit in the session and surface
                    # on the next page that does render messages, which is the
                    # Properties list. The modal says it here instead, and the
                    # client-side check normally means we never get this far.
                    return render(request, "properties_edit.html", {
                        'props': [props.objects.get(pk=prop_id)],
                        'existing_names': list(existing_names),
                        'prorata_blockers': [{'name': n, 'amount': a}
                                             for n, a in _blockers],
                        'show_blocker_modal': True,
                    })
'''


# ---------------------------------------------------------------------------
# 2. properties_edit.html
# ---------------------------------------------------------------------------

FORM_OLD = ('<form action="{% url \'properties_edit_commit\' results.prop_id %}" '
            'method="post" onsubmit="return validatePropertyName()">')

FORM_NEW = ('<form action="{% url \'properties_edit_commit\' results.prop_id %}" '
            'method="post" id="property-edit-form" '
            'data-original-status="{{ results.prop_status }}" '
            'onsubmit="return validatePropertyName() &amp;&amp; checkStatusBlockers()">')

MODAL_ANCHOR = '''</form>
{% endfor %}
'''

MODAL_NEW = '''</form>
{% endfor %}

<!-- Raised by Save when the status is moving away from Active while pro-rata
     shares remain, and opened on load if the server refused the POST. Both
     paths land here, so the explanation is always on this page. -->
<div class="modal fade" id="statusBlockModal" tabindex="-1" role="dialog"
     aria-hidden="true" style="display:none;">
  <div class="modal-dialog modal-lg" role="document">
    <div class="modal-content" style="border-radius:12px; border:none;">
      <div class="modal-header" style="background:linear-gradient(135deg,#dc3545 0%,#c82333 100%); color:#fff; border-bottom:none;">
        <h5 class="modal-title" style="color:#fff; font-weight:600;">
          <i class="fas fa-exclamation-triangle"></i> This property is still in a pro-rata distribution
        </h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close"
                style="color:#fff; opacity:.9; text-shadow:none;">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body" style="font-size:14px;">
        <p>It cannot be made inactive yet. It still holds a share of:</p>
        <table class="table table-sm table-bordered" style="font-size:0.9rem;">
          <thead style="background:#f8f9fa;">
            <tr><th>Expense Line Type</th><th class="text-right">Its share, a year</th></tr>
          </thead>
          <tbody>
            {% for b in prorata_blockers %}
            <tr><td>{{ b.name }}</td><td class="text-right">&euro;{{ b.amount|floatformat:2 }}</td></tr>
            {% endfor %}
          </tbody>
        </table>
        <p>
          Those shares would carry on being charged to it in every future year,
          while the other properties kept shares of a split that still counted
          it &mdash; so each line would stop adding up to the charge actually owed.
        </p>
        <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
          <strong>To remove it properly</strong>
          <ol class="mb-0 mt-2">
            <li>Open <strong>Financial Management &rarr; Expenses</strong></li>
            <li>Edit each line above and set <strong>Applies from</strong> to the date this property leaves</li>
            <li><strong>Un-tick</strong> this property and recalculate &mdash; the others take up its share</li>
          </ol>
          <p class="mb-0 mt-2" style="font-size:13px;">
            Its earlier years keep the figures it really carried. Only from that
            date forward does it stop.
          </p>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">
          Back to the property
        </button>
        <a href="{% url 'finance_expense' %}" class="btn btn-info">
          <i class="fas fa-arrow-right"></i> Go to Expenses
        </a>
      </div>
    </div>
  </div>
</div>
'''

JS_ANCHOR = '''function validatePropertyName() {
'''

JS_NEW = '''// ---- Status change: refuse here, not two pages later --------------------
// The blockers are known when this page loads, so Save can stop and explain
// without a round trip. The server checks again regardless - this is a
// courtesy, not a control.
var PRORATA_BLOCKERS = {{ prorata_blockers|length|default:0 }};

function showStatusBlockModal() {
    var m = document.getElementById('statusBlockModal');
    if (!m) { return; }
    if (window.jQuery && jQuery.fn.modal) { jQuery(m).modal('show'); }
    else { m.style.display = 'block'; m.classList.add('show'); }
}

function checkStatusBlockers() {
    if (!PRORATA_BLOCKERS) { return true; }
    var form = document.getElementById('property-edit-form');
    var sel = document.getElementById('prop_status');
    if (!form || !sel) { return true; }
    var was = (form.getAttribute('data-original-status') || '').trim();
    if (was === 'Active' && sel.value !== 'Active') {
        showStatusBlockModal();
        return false;
    }
    return true;
}

document.addEventListener('DOMContentLoaded', function () {
    // The server refused a POST that got past the check above.
    {% if show_blocker_modal %}showStatusBlockModal();{% endif %}
    var m = document.getElementById('statusBlockModal');
    if (!m) { return; }
    Array.prototype.forEach.call(
        m.querySelectorAll('[data-dismiss="modal"]'), function (b) {
        b.addEventListener('click', function () {
            if (window.jQuery && jQuery.fn.modal) { jQuery(m).modal('hide'); }
            else { m.style.display = 'none'; m.classList.remove('show'); }
        });
    });
});

function validatePropertyName() {
'''


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_blockmodal'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (PROPS, TPL):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    v_src, v_enc, v_nl = sniff(PROPS)
    t_src, t_enc, t_nl = sniff(TPL)

    if '_prorata_blockers' not in v_src:
        print('! apply_inactive_guard.py has not been applied.')
        print('  Run that first - this changes how its refusal is shown.')
        return 1

    v_done = PROPS_SENTINEL in v_src
    t_done = TPL_SENTINEL in t_src
    if v_done and t_done:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not v_done:
        need('properties_edit view', v_src, VIEW_OLD)
        need('the guard refusal', v_src, GUARD_OLD)
    if not t_done:
        need('form tag', t_src, FORM_OLD)
        need('form close', t_src, MODAL_ANCHOR)
        need('validatePropertyName', t_src, JS_ANCHOR)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not v_done:
        v_src = v_src.replace(VIEW_OLD, VIEW_NEW, 1)
        v_src = v_src.replace(GUARD_OLD, GUARD_NEW, 1)
    if not t_done:
        t_src = t_src.replace(FORM_OLD, FORM_NEW, 1)
        t_src = t_src.replace(MODAL_ANCHOR, MODAL_NEW, 1)
        t_src = t_src.replace(JS_ANCHOR, JS_NEW, 1)

    try:
        compile(v_src, 'properties.py', 'exec')
    except SyntaxError as exc:
        print('! patched properties.py does not compile: %s (line %s)'
              % (exc.msg, exc.lineno))
        print('  Nothing written.')
        return 1

    # The whole point is that nothing is left in the session to surface later.
    # Match the CALL, not the word - the replacement's comment says
    # "No messages.error here, deliberately", which a bare substring test hits.
    if 'messages.error(' in GUARD_NEW:
        print('! the refusal still stores a message')
        return 1

    if CHECK:
        print('= check only: every anchor matched and properties.py compiles, '
              'nothing written')
        return 0

    if not v_done:
        write_back(PROPS, v_src, v_enc, v_nl)
        print('+ pages/views/properties.py           blockers in context, no stored message')
    if not t_done:
        write_back(TPL, t_src, t_enc, t_nl)
        print('+ pages/templates/properties_edit.html  the dialog + the submit check')

    print('')
    print('Backups: .bak_blockmodal alongside each file.')
    print('Try it: edit a property that holds pro-rata shares, set it Inactive,')
    print('press Save. The dialog should open and you should stay on the page.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
