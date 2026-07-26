#!/usr/bin/env python
"""
install_pi_line_autocomplete.py  --  add history-driven autocomplete to the
Physical Invoice line editor.

What it does, on the Edit Physical Invoice page (Invoice Lines table):
  * SERVICE field  -> type-ahead of every Service you have used before on any
    physical-invoice line. Typing "wat" narrows to "WATER", etc. You can still
    type a brand-new service.
  * Once a Service is chosen (or already present on a row), the UNIT and
    DESCRIPTION fields on THAT row offer the Units and Descriptions previously
    captured against that Service. Pick an old one and use it as-is, or edit it.
  * Works on the existing rows AND on rows added with "Add Line".

How it works (no new dependencies, no DB changes):
  1. views/physical_invoices.py gains a helper `_build_line_suggestions()` that
     collects, from all existing PhysicalInvoiceLine rows, the distinct Services
     and — per Service — the distinct Units and Descriptions. It is added to the
     edit view's context as `pi_suggest`.
  2. physical_invoice_edit.html emits that data with Django's `json_script` and a
     small vanilla-JS block wires native <datalist> autocompletes onto the
     Service / Unit / Description inputs, rebuilding the Unit+Description lists
     whenever the row's Service changes.

Units fall back to the full Unit list when a Service has no history yet (handy
for a new service); Descriptions are shown only for a known Service (they are
specific). Suggestions are drawn from ALL invoices, not just the current tenant.

Edits two files (backups .bak_autocomplete):
  * pages/views/physical_invoices.py
  * pages/templates/physical_invoice_edit.html

SAFE: idempotent (per-edit marker guards); exact-anchor (each verified unique);
preserves LF; `ast.parse` check on the view; template tag-balance + <script>
balance checks; --dry-run. No migration.

    python install_pi_line_autocomplete.py --dry-run
    python install_pi_line_autocomplete.py
Then restart the dev server (or redeploy) and open a draft physical invoice.
"""
import ast, base64, os, re, sys

DRY = '--dry-run' in sys.argv

# ---- view payloads ----
V_HELPER_OLD = "ZGVmIHBoeXNpY2FsX2ludm9pY2VfZWRpdChyZXF1ZXN0LCBwaHlzaWNhbF9pbnZvaWNlX2lkKTo="
V_HELPER_NEW = "ZGVmIF9idWlsZF9saW5lX3N1Z2dlc3Rpb25zKCk6CiAgICAiIiJIaXN0b3J5IGZvciB0aGUgaW52b2ljZS1saW5lIGF1dG9jb21wbGV0ZTogZXZlcnkgZGlzdGluY3QgU2VydmljZSBldmVyCiAgICB1c2VkIG9uIGEgcGh5c2ljYWwtaW52b2ljZSBsaW5lLCBhbmQgZm9yIGVhY2ggU2VydmljZSB0aGUgZGlzdGluY3QgVW5pdHMgYW5kCiAgICBEZXNjcmlwdGlvbnMgY2FwdHVyZWQgYWdhaW5zdCBpdCAoYWNyb3NzIGFsbCBpbnZvaWNlcykuIFNlcnZpY2VzIGFuZCBVbml0cwogICAgYXJlIGNhc2UtZm9sZGVkIGZvciBkZS1kdXBsaWNhdGlvbjsgRGVzY3JpcHRpb25zIGtlZXAgbmV3ZXN0LWZpcnN0IG9yZGVyIHNvCiAgICB0aGUgbW9zdCByZWNlbnQgd29yZGluZyBpcyBvZmZlcmVkIGZpcnN0IGZvciBlZGl0aW5nLiIiIgogICAgc3ZjX2Rpc3BsYXksIGJ5X3NlcnZpY2UgPSB7fSwge30KICAgIHNlZW5fdSwgc2Vlbl9kID0ge30sIHt9CiAgICBhbGxfdW5pdHMsIGFsbF91bml0c19zZWVuID0gW10sIHNldCgpCiAgICByb3dzID0gKFBoeXNpY2FsSW52b2ljZUxpbmUub2JqZWN0cwogICAgICAgICAgICAuZXhjbHVkZShzZXJ2aWNlPSIiKQogICAgICAgICAgICAudmFsdWVzX2xpc3QoInNlcnZpY2UiLCAidW5pdF9vZl9tZWFzdXJlIiwgImRlc2NyaXB0aW9uIikKICAgICAgICAgICAgLm9yZGVyX2J5KCItcGh5c2ljYWxfaW52b2ljZV9saW5lX2lkIikpCiAgICBmb3Igc3ZjLCB1b20sIGRlc2MgaW4gcm93czoKICAgICAgICBzdmMgPSAoc3ZjIG9yICIiKS5zdHJpcCgpCiAgICAgICAgaWYgbm90IHN2YzoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBrZXkgPSBzdmMudXBwZXIoKQogICAgICAgIGlmIGtleSBub3QgaW4gYnlfc2VydmljZToKICAgICAgICAgICAgYnlfc2VydmljZVtrZXldID0geyJ1bml0cyI6IFtdLCAiZGVzY3JpcHRpb25zIjogW119CiAgICAgICAgICAgIHNlZW5fdVtrZXldLCBzZWVuX2Rba2V5XSA9IHNldCgpLCBzZXQoKQogICAgICAgICAgICBzdmNfZGlzcGxheVtrZXldID0gc3ZjCiAgICAgICAgdW9tID0gKHVvbSBvciAiIikuc3RyaXAoKQogICAgICAgIGRlc2MgPSAoZGVzYyBvciAiIikuc3RyaXAoKQogICAgICAgIGlmIHVvbSBhbmQgdW9tLnVwcGVyKCkgbm90IGluIHNlZW5fdVtrZXldOgogICAgICAgICAgICBzZWVuX3Vba2V5XS5hZGQodW9tLnVwcGVyKCkpCiAgICAgICAgICAgIGJ5X3NlcnZpY2Vba2V5XVsidW5pdHMiXS5hcHBlbmQodW9tKQogICAgICAgIGlmIGRlc2MgYW5kIGRlc2Mgbm90IGluIHNlZW5fZFtrZXldOgogICAgICAgICAgICBzZWVuX2Rba2V5XS5hZGQoZGVzYykKICAgICAgICAgICAgYnlfc2VydmljZVtrZXldWyJkZXNjcmlwdGlvbnMiXS5hcHBlbmQoZGVzYykKICAgICAgICBpZiB1b20gYW5kIHVvbS51cHBlcigpIG5vdCBpbiBhbGxfdW5pdHNfc2VlbjoKICAgICAgICAgICAgYWxsX3VuaXRzX3NlZW4uYWRkKHVvbS51cHBlcigpKQogICAgICAgICAgICBhbGxfdW5pdHMuYXBwZW5kKHVvbSkKICAgIGZvciBrIGluIGJ5X3NlcnZpY2U6CiAgICAgICAgYnlfc2VydmljZVtrXVsidW5pdHMiXS5zb3J0KGtleT1sYW1iZGEgczogcy5sb3dlcigpKQogICAgc2VydmljZXMgPSBzb3J0ZWQoc3ZjX2Rpc3BsYXkudmFsdWVzKCksIGtleT1sYW1iZGEgczogcy5sb3dlcigpKQogICAgYWxsX3VuaXRzLnNvcnQoa2V5PWxhbWJkYSBzOiBzLmxvd2VyKCkpCiAgICByZXR1cm4geyJzZXJ2aWNlcyI6IHNlcnZpY2VzLCAiYnlfc2VydmljZSI6IGJ5X3NlcnZpY2UsICJhbGxfdW5pdHMiOiBhbGxfdW5pdHN9CgoKZGVmIHBoeXNpY2FsX2ludm9pY2VfZWRpdChyZXF1ZXN0LCBwaHlzaWNhbF9pbnZvaWNlX2lkKTo="

V_CTX_OLD = "ICAgICAgICAiaXNfZWRpdGFibGUiOiBwaS5pc19lZGl0YWJsZSwKICAgIH0KICAgIHJldHVybiByZW5kZXIocmVxdWVzdCwgInBoeXNpY2FsX2ludm9pY2VfZWRpdC5odG1sIiwgY29udGV4dCk="
V_CTX_NEW = "ICAgICAgICAiaXNfZWRpdGFibGUiOiBwaS5pc19lZGl0YWJsZSwKICAgICAgICAicGlfc3VnZ2VzdCI6IF9idWlsZF9saW5lX3N1Z2dlc3Rpb25zKCksCiAgICB9CiAgICByZXR1cm4gcmVuZGVyKHJlcXVlc3QsICJwaHlzaWNhbF9pbnZvaWNlX2VkaXQuaHRtbCIsIGNvbnRleHQp"

# ---- template payloads ----
T_OLD = "ICBpZiAocm93KSByb3cucmVtb3ZlKCk7Cn0KPC9zY3JpcHQ+"
T_NEW = "ICBpZiAocm93KSByb3cucmVtb3ZlKCk7Cn0KPC9zY3JpcHQ+Cgp7eyBwaV9zdWdnZXN0fGpzb25fc2NyaXB0OiJwaS1zdWdnZXN0LWRhdGEiIH19CjxkaXYgaWQ9InBpLWRhdGFsaXN0LWhvc3QiIHN0eWxlPSJkaXNwbGF5Om5vbmU7Ij48L2Rpdj4KPHNjcmlwdD4KLyogUGh5c2ljYWwtaW52b2ljZSBsaW5lIGF1dG9jb21wbGV0ZS4gU2VydmljZSBmaWVsZCBvZmZlcnMgZXZlcnkgU2VydmljZSB1c2VkCiAgIGJlZm9yZSAodHlwZSB0byBuYXJyb3cpLiBQaWNrIGEgU2VydmljZSBhbmQgaXRzIFVuaXQgKyBEZXNjcmlwdGlvbiBmaWVsZHMgdGhlbgogICBvZmZlciB0aGUgdmFsdWVzIHVzZWQgZm9yIHRoYXQgU2VydmljZSBiZWZvcmUgLS0gc2VsZWN0YWJsZSBhbmQgZWRpdGFibGUuCiAgIFB1cmUgPGRhdGFsaXN0Piwgbm8gZGVwZW5kZW5jaWVzLCBkZWdyYWRlcyB0byBwbGFpbiB0ZXh0IGlucHV0cy4gKi8KKGZ1bmN0aW9uKCl7CiAgdmFyIERBVEEgPSB7fTsKICB0cnkgeyBEQVRBID0gSlNPTi5wYXJzZShkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgncGktc3VnZ2VzdC1kYXRhJykudGV4dENvbnRlbnQpIHx8IHt9OyB9CiAgY2F0Y2ggKGUpIHsgREFUQSA9IHt9OyB9CiAgdmFyIGJ5U2VydmljZSA9IERBVEEuYnlfc2VydmljZSB8fCB7fTsKICB2YXIgYWxsVW5pdHMgID0gREFUQS5hbGxfdW5pdHMgfHwgW107CiAgdmFyIGhvc3QgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgncGktZGF0YWxpc3QtaG9zdCcpOwogIGlmICghaG9zdCkgcmV0dXJuOwogIHZhciBzZXEgPSAwOwoKICBmdW5jdGlvbiBlc2Mocyl7IHJldHVybiBTdHJpbmcocykucmVwbGFjZSgvJi9nLCcmYW1wOycpLnJlcGxhY2UoLzwvZywnJmx0OycpLnJlcGxhY2UoLz4vZywnJmd0OycpLnJlcGxhY2UoLyIvZywnJnF1b3Q7Jyk7IH0KICBmdW5jdGlvbiBvcHRpb25zKHZhbHMpeyB2YXIgaD0nJzsgKHZhbHN8fFtdKS5mb3JFYWNoKGZ1bmN0aW9uKHYpeyBoICs9ICc8b3B0aW9uIHZhbHVlPSInK2VzYyh2KSsnIj48L29wdGlvbj4nOyB9KTsgcmV0dXJuIGg7IH0KICBmdW5jdGlvbiBlbnN1cmVMaXN0KGlkKXsgdmFyIGRsPWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKGlkKTsgaWYoIWRsKXsgZGw9ZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnZGF0YWxpc3QnKTsgZGwuaWQ9aWQ7IGhvc3QuYXBwZW5kQ2hpbGQoZGwpOyB9IHJldHVybiBkbDsgfQoKICBlbnN1cmVMaXN0KCdwaS1kbC1zZXJ2aWNlcycpLmlubmVySFRNTCA9IG9wdGlvbnMoREFUQS5zZXJ2aWNlcyB8fCBbXSk7CgogIGZ1bmN0aW9uIHJlZnJlc2gocm93KXsKICAgIHZhciBzdmMgID0gcm93LnF1ZXJ5U2VsZWN0b3IoJ2lucHV0W25hbWU9ImxpbmVfc2VydmljZSJdJyk7CiAgICB2YXIgdW9tICA9IHJvdy5xdWVyeVNlbGVjdG9yKCdpbnB1dFtuYW1lPSJsaW5lX3VvbSJdJyk7CiAgICB2YXIgZGVzYyA9IHJvdy5xdWVyeVNlbGVjdG9yKCdpbnB1dFtuYW1lPSJsaW5lX2Rlc2NyaXB0aW9uIl0nKTsKICAgIGlmKCFzdmMgfHwgIXVvbSB8fCAhZGVzYykgcmV0dXJuOwogICAgdmFyIHVEbCA9IGVuc3VyZUxpc3QodW9tLmdldEF0dHJpYnV0ZSgnbGlzdCcpKTsKICAgIHZhciBkRGwgPSBlbnN1cmVMaXN0KGRlc2MuZ2V0QXR0cmlidXRlKCdsaXN0JykpOwogICAgdmFyIGVudHJ5ID0gYnlTZXJ2aWNlWyhzdmMudmFsdWV8fCcnKS50cmltKCkudG9VcHBlckNhc2UoKV07CiAgICB1RGwuaW5uZXJIVE1MID0gb3B0aW9ucyhlbnRyeSAmJiBlbnRyeS51bml0cyAmJiBlbnRyeS51bml0cy5sZW5ndGggPyBlbnRyeS51bml0cyA6IGFsbFVuaXRzKTsKICAgIGREbC5pbm5lckhUTUwgPSBvcHRpb25zKGVudHJ5ID8gZW50cnkuZGVzY3JpcHRpb25zIDogW10pOwogIH0KCiAgZnVuY3Rpb24gd2lyZShyb3cpewogICAgdmFyIHN2YyAgPSByb3cucXVlcnlTZWxlY3RvcignaW5wdXRbbmFtZT0ibGluZV9zZXJ2aWNlIl0nKTsKICAgIHZhciB1b20gID0gcm93LnF1ZXJ5U2VsZWN0b3IoJ2lucHV0W25hbWU9ImxpbmVfdW9tIl0nKTsKICAgIHZhciBkZXNjID0gcm93LnF1ZXJ5U2VsZWN0b3IoJ2lucHV0W25hbWU9ImxpbmVfZGVzY3JpcHRpb24iXScpOwogICAgaWYoIXN2YyB8fCAhdW9tIHx8ICFkZXNjIHx8IHN2Yy5kYXRhc2V0LnBpV2lyZWQgPT09ICcxJykgcmV0dXJuOwogICAgc3ZjLmRhdGFzZXQucGlXaXJlZCA9ICcxJzsKICAgIHNlcSsrOwogICAgc3ZjLnNldEF0dHJpYnV0ZSgnbGlzdCcsJ3BpLWRsLXNlcnZpY2VzJyk7CiAgICB1b20uc2V0QXR0cmlidXRlKCdsaXN0JywncGktZGwtdW9tLScrc2VxKTsKICAgIGRlc2Muc2V0QXR0cmlidXRlKCdsaXN0JywncGktZGwtZGVzYy0nK3NlcSk7CiAgICBzdmMuYWRkRXZlbnRMaXN0ZW5lcignaW5wdXQnLCAgZnVuY3Rpb24oKXsgcmVmcmVzaChyb3cpOyB9KTsKICAgIHN2Yy5hZGRFdmVudExpc3RlbmVyKCdjaGFuZ2UnLCBmdW5jdGlvbigpeyByZWZyZXNoKHJvdyk7IH0pOwogICAgcmVmcmVzaChyb3cpOwogIH0KCiAgZnVuY3Rpb24gd2lyZUFsbCgpeyBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCcjbGluZXNCb2R5IHRyLmxpbmUtcm93JykuZm9yRWFjaCh3aXJlKTsgfQoKICB2YXIgYm9keSA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdsaW5lc0JvZHknKTsKICBpZiAoYm9keSAmJiB3aW5kb3cuTXV0YXRpb25PYnNlcnZlcil7CiAgICBuZXcgTXV0YXRpb25PYnNlcnZlcihmdW5jdGlvbihtdXRzKXsKICAgICAgbXV0cy5mb3JFYWNoKGZ1bmN0aW9uKG0pewogICAgICAgIChtLmFkZGVkTm9kZXMgfHwgW10pLmZvckVhY2goZnVuY3Rpb24obil7CiAgICAgICAgICBpZiAobi5ub2RlVHlwZSA9PT0gMSAmJiBuLm1hdGNoZXMgJiYgbi5tYXRjaGVzKCd0ci5saW5lLXJvdycpKSB3aXJlKG4pOwogICAgICAgIH0pOwogICAgICB9KTsKICAgIH0pLm9ic2VydmUoYm9keSwge2NoaWxkTGlzdDp0cnVlfSk7CiAgfQoKICBpZiAoZG9jdW1lbnQucmVhZHlTdGF0ZSA9PT0gJ2xvYWRpbmcnKSBkb2N1bWVudC5hZGRFdmVudExpc3RlbmVyKCdET01Db250ZW50TG9hZGVkJywgd2lyZUFsbCk7CiAgZWxzZSB3aXJlQWxsKCk7Cn0pKCk7Cjwvc2NyaXB0Pg=="


def read(p):
    with open(p, encoding='utf-8') as f: return f.read()
def detect_nl(p):
    with open(p, 'rb') as f: return '\r\n' if f.read().count(b'\r\n') else '\n'
def write(p, s, nl):
    with open(p, 'w', encoding='utf-8', newline=nl) as f: f.write(s)
def d(s): return base64.b64decode(s).decode()
def tag_balanced(t):
    pairs = [(r'{%\s*if\b', r'{%\s*endif\s*%}'), (r'{%\s*for\b', r'{%\s*endfor\s*%}'),
             (r'{%\s*block\b', r'{%\s*endblock\s*%}')]
    return all(len(re.findall(a, t)) == len(re.findall(b, t)) for a, b in pairs)


def apply_edits(path, edits, kind):
    """edits: list of (old_b64, new_b64, marker). Returns (changed, txt)."""
    txt = read(path)
    changed = False
    for old_b, new_b, marker in edits:
        if marker in txt:
            print('   [skip] already applied: %s' % marker)
            continue
        old, new = d(old_b), d(new_b)
        c = txt.count(old)
        if c != 1:
            print('!! anchor not matched (found %d) in %s. Nothing changed.' % (c, os.path.basename(path)))
            print('   anchor head: %r' % old[:60])
            sys.exit(1)
        txt = txt.replace(old, new, 1)
        changed = True
    if changed:
        if kind == 'py':
            try:
                ast.parse(txt)
            except SyntaxError as e:
                print('!! %s would not parse (%s). Nothing changed.' % (os.path.basename(path), e)); sys.exit(1)
        else:
            if not tag_balanced(txt):
                print('!! template tag balance broke in %s. Nothing changed.' % os.path.basename(path)); sys.exit(1)
            if txt.count('<script') != txt.count('</script>'):
                print('!! <script> balance broke in %s. Nothing changed.' % os.path.basename(path)); sys.exit(1)
    return changed, txt


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print('!! Run from the project root (where manage.py lives).'); sys.exit(1)
    view = os.path.join(root, 'pages', 'views', 'physical_invoices.py')
    tpl = os.path.join(root, 'pages', 'templates', 'physical_invoice_edit.html')
    for p in (view, tpl):
        if not os.path.exists(p):
            print('!! Could not find %s' % p); sys.exit(1)

    print('view    :', view)
    print('template:', tpl + ('   (dry run)' if DRY else ''))
    print('')

    print('view:')
    v_changed, v_txt = apply_edits(view, [
        (V_HELPER_OLD, V_HELPER_NEW, 'def _build_line_suggestions'),
        (V_CTX_OLD, V_CTX_NEW, '"pi_suggest": _build_line_suggestions()'),
    ], 'py')
    print('template:')
    t_changed, t_txt = apply_edits(tpl, [
        (T_OLD, T_NEW, 'pi-suggest-data'),
    ], 'html')

    if not (v_changed or t_changed):
        print(''); print('[nothing to do] autocomplete already installed.'); return

    if DRY:
        print(''); print('[dry-run] would update:'
              + ('\n   - physical_invoices.py (helper + context)' if v_changed else '')
              + ('\n   - physical_invoice_edit.html (json_script + datalist JS)' if t_changed else ''))
        return

    if v_changed:
        nl = detect_nl(view); b = view + '.bak_autocomplete'
        if not os.path.exists(b): write(b, read(view), nl)
        write(view, v_txt, nl); print(''); print('[OK] physical_invoices.py updated (.bak_autocomplete).')
    if t_changed:
        nl = detect_nl(tpl); b = tpl + '.bak_autocomplete'
        if not os.path.exists(b): write(b, read(tpl), nl)
        write(tpl, t_txt, nl); print('[OK] physical_invoice_edit.html updated (.bak_autocomplete).')

    print('')
    print('Autocomplete installed. Restart the dev server / redeploy, open a draft'
          ' physical invoice, and start typing in a Service field — prior services'
          ' appear; picking one fills the Unit/Description suggestions for it.')


if __name__ == '__main__':
    main()