#!/usr/bin/env python
"""
install_pi_line_autocomplete_FIX.py  --  corrected installer for the physical-
invoice line autocomplete. Supersedes install_pi_line_autocomplete.py.

WHY THIS EXISTS
The first installer anchored the new `_build_line_suggestions()` helper on the
line `def physical_invoice_edit(...)` and inserted the helper just above it. But
that view is decorated:

    @login_required
    @permission_required('auth.can_edit_invoices', raise_exception=True)
    def physical_invoice_edit(request, physical_invoice_id):

so the helper landed BETWEEN the decorators and the def -> the decorators wrapped
the helper (giving "TypeError: _build_line_suggestions() missing 1 required
positional argument: 'request'") and the view itself lost its decorators. Result:
HTTP 500 on the edit page.

WHAT THIS DOES
View (pages/views/physical_invoices.py):
  1. NORMALISE — removes any prior insertion (whether the broken one from the
     first installer OR a correctly-placed one from a re-run) and the pi_suggest
     context line, returning the view region to its original text.
  2. APPLY — inserts the helper ABOVE the `@login_required` decorator, so the
     decorators stay on `physical_invoice_edit`, and re-adds the context line.
This is convergent (clean file and broken file both end identical) and idempotent.

Template (pages/templates/physical_invoice_edit.html):
  * ensures the json_script + datalist JS block is present (idempotent; skipped
    if already there). Unchanged from the first installer — the template edit was
    never the problem.

SAFE: `ast.parse` gate on the view (won't write if it wouldn't parse); template
tag-balance + <script> balance gate; preserves LF; backups .bak_autofix; and a
positive post-check that the decorators end up on the VIEW, not the helper.
--dry-run supported. No migration.

    python install_pi_line_autocomplete_FIX.py --dry-run
    python install_pi_line_autocomplete_FIX.py
Then restart the dev server / redeploy and open the edit page.

NOTE: if you already restored physical_invoices.py from the .bak_autocomplete
backup, that is fine — this script handles the clean original too.
"""
import ast, base64, os, re, sys

DRY = '--dry-run' in sys.argv

# ---- view payloads ----
CTX_NEW_B = "ICAgICAgICAiaXNfZWRpdGFibGUiOiBwaS5pc19lZGl0YWJsZSwKICAgICAgICAicGlfc3VnZ2VzdCI6IF9idWlsZF9saW5lX3N1Z2dlc3Rpb25zKCksCiAgICB9CiAgICByZXR1cm4gcmVuZGVyKHJlcXVlc3QsICJwaHlzaWNhbF9pbnZvaWNlX2VkaXQuaHRtbCIsIGNvbnRleHQp"
CTX_OLD_B = "ICAgICAgICAiaXNfZWRpdGFibGUiOiBwaS5pc19lZGl0YWJsZSwKICAgIH0KICAgIHJldHVybiByZW5kZXIocmVxdWVzdCwgInBoeXNpY2FsX2ludm9pY2VfZWRpdC5odG1sIiwgY29udGV4dCk="
# helper + decorators + def  (the CORRECT final layout / apply target)
HELP_DECODEF_B = "ZGVmIF9idWlsZF9saW5lX3N1Z2dlc3Rpb25zKCk6CiAgICAiIiJIaXN0b3J5IGZvciB0aGUgaW52b2ljZS1saW5lIGF1dG9jb21wbGV0ZTogZXZlcnkgZGlzdGluY3QgU2VydmljZSBldmVyCiAgICB1c2VkIG9uIGEgcGh5c2ljYWwtaW52b2ljZSBsaW5lLCBhbmQgZm9yIGVhY2ggU2VydmljZSB0aGUgZGlzdGluY3QgVW5pdHMgYW5kCiAgICBEZXNjcmlwdGlvbnMgY2FwdHVyZWQgYWdhaW5zdCBpdCAoYWNyb3NzIGFsbCBpbnZvaWNlcykuIFNlcnZpY2VzIGFuZCBVbml0cwogICAgYXJlIGNhc2UtZm9sZGVkIGZvciBkZS1kdXBsaWNhdGlvbjsgRGVzY3JpcHRpb25zIGtlZXAgbmV3ZXN0LWZpcnN0IG9yZGVyIHNvCiAgICB0aGUgbW9zdCByZWNlbnQgd29yZGluZyBpcyBvZmZlcmVkIGZpcnN0IGZvciBlZGl0aW5nLiIiIgogICAgc3ZjX2Rpc3BsYXksIGJ5X3NlcnZpY2UgPSB7fSwge30KICAgIHNlZW5fdSwgc2Vlbl9kID0ge30sIHt9CiAgICBhbGxfdW5pdHMsIGFsbF91bml0c19zZWVuID0gW10sIHNldCgpCiAgICByb3dzID0gKFBoeXNpY2FsSW52b2ljZUxpbmUub2JqZWN0cwogICAgICAgICAgICAuZXhjbHVkZShzZXJ2aWNlPSIiKQogICAgICAgICAgICAudmFsdWVzX2xpc3QoInNlcnZpY2UiLCAidW5pdF9vZl9tZWFzdXJlIiwgImRlc2NyaXB0aW9uIikKICAgICAgICAgICAgLm9yZGVyX2J5KCItcGh5c2ljYWxfaW52b2ljZV9saW5lX2lkIikpCiAgICBmb3Igc3ZjLCB1b20sIGRlc2MgaW4gcm93czoKICAgICAgICBzdmMgPSAoc3ZjIG9yICIiKS5zdHJpcCgpCiAgICAgICAgaWYgbm90IHN2YzoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBrZXkgPSBzdmMudXBwZXIoKQogICAgICAgIGlmIGtleSBub3QgaW4gYnlfc2VydmljZToKICAgICAgICAgICAgYnlfc2VydmljZVtrZXldID0geyJ1bml0cyI6IFtdLCAiZGVzY3JpcHRpb25zIjogW119CiAgICAgICAgICAgIHNlZW5fdVtrZXldLCBzZWVuX2Rba2V5XSA9IHNldCgpLCBzZXQoKQogICAgICAgICAgICBzdmNfZGlzcGxheVtrZXldID0gc3ZjCiAgICAgICAgdW9tID0gKHVvbSBvciAiIikuc3RyaXAoKQogICAgICAgIGRlc2MgPSAoZGVzYyBvciAiIikuc3RyaXAoKQogICAgICAgIGlmIHVvbSBhbmQgdW9tLnVwcGVyKCkgbm90IGluIHNlZW5fdVtrZXldOgogICAgICAgICAgICBzZWVuX3Vba2V5XS5hZGQodW9tLnVwcGVyKCkpCiAgICAgICAgICAgIGJ5X3NlcnZpY2Vba2V5XVsidW5pdHMiXS5hcHBlbmQodW9tKQogICAgICAgIGlmIGRlc2MgYW5kIGRlc2Mgbm90IGluIHNlZW5fZFtrZXldOgogICAgICAgICAgICBzZWVuX2Rba2V5XS5hZGQoZGVzYykKICAgICAgICAgICAgYnlfc2VydmljZVtrZXldWyJkZXNjcmlwdGlvbnMiXS5hcHBlbmQoZGVzYykKICAgICAgICBpZiB1b20gYW5kIHVvbS51cHBlcigpIG5vdCBpbiBhbGxfdW5pdHNfc2VlbjoKICAgICAgICAgICAgYWxsX3VuaXRzX3NlZW4uYWRkKHVvbS51cHBlcigpKQogICAgICAgICAgICBhbGxfdW5pdHMuYXBwZW5kKHVvbSkKICAgIGZvciBrIGluIGJ5X3NlcnZpY2U6CiAgICAgICAgYnlfc2VydmljZVtrXVsidW5pdHMiXS5zb3J0KGtleT1sYW1iZGEgczogcy5sb3dlcigpKQogICAgc2VydmljZXMgPSBzb3J0ZWQoc3ZjX2Rpc3BsYXkudmFsdWVzKCksIGtleT1sYW1iZGEgczogcy5sb3dlcigpKQogICAgYWxsX3VuaXRzLnNvcnQoa2V5PWxhbWJkYSBzOiBzLmxvd2VyKCkpCiAgICByZXR1cm4geyJzZXJ2aWNlcyI6IHNlcnZpY2VzLCAiYnlfc2VydmljZSI6IGJ5X3NlcnZpY2UsICJhbGxfdW5pdHMiOiBhbGxfdW5pdHN9CgoKQGxvZ2luX3JlcXVpcmVkCkBwZXJtaXNzaW9uX3JlcXVpcmVkKCdhdXRoLmNhbl9lZGl0X2ludm9pY2VzJywgcmFpc2VfZXhjZXB0aW9uPVRydWUpCmRlZiBwaHlzaWNhbF9pbnZvaWNlX2VkaXQocmVxdWVzdCwgcGh5c2ljYWxfaW52b2ljZV9pZCk6"
# helper + def  (BROKEN layout produced by the first installer; used to undo)
HELP_DEF_B = "ZGVmIF9idWlsZF9saW5lX3N1Z2dlc3Rpb25zKCk6CiAgICAiIiJIaXN0b3J5IGZvciB0aGUgaW52b2ljZS1saW5lIGF1dG9jb21wbGV0ZTogZXZlcnkgZGlzdGluY3QgU2VydmljZSBldmVyCiAgICB1c2VkIG9uIGEgcGh5c2ljYWwtaW52b2ljZSBsaW5lLCBhbmQgZm9yIGVhY2ggU2VydmljZSB0aGUgZGlzdGluY3QgVW5pdHMgYW5kCiAgICBEZXNjcmlwdGlvbnMgY2FwdHVyZWQgYWdhaW5zdCBpdCAoYWNyb3NzIGFsbCBpbnZvaWNlcykuIFNlcnZpY2VzIGFuZCBVbml0cwogICAgYXJlIGNhc2UtZm9sZGVkIGZvciBkZS1kdXBsaWNhdGlvbjsgRGVzY3JpcHRpb25zIGtlZXAgbmV3ZXN0LWZpcnN0IG9yZGVyIHNvCiAgICB0aGUgbW9zdCByZWNlbnQgd29yZGluZyBpcyBvZmZlcmVkIGZpcnN0IGZvciBlZGl0aW5nLiIiIgogICAgc3ZjX2Rpc3BsYXksIGJ5X3NlcnZpY2UgPSB7fSwge30KICAgIHNlZW5fdSwgc2Vlbl9kID0ge30sIHt9CiAgICBhbGxfdW5pdHMsIGFsbF91bml0c19zZWVuID0gW10sIHNldCgpCiAgICByb3dzID0gKFBoeXNpY2FsSW52b2ljZUxpbmUub2JqZWN0cwogICAgICAgICAgICAuZXhjbHVkZShzZXJ2aWNlPSIiKQogICAgICAgICAgICAudmFsdWVzX2xpc3QoInNlcnZpY2UiLCAidW5pdF9vZl9tZWFzdXJlIiwgImRlc2NyaXB0aW9uIikKICAgICAgICAgICAgLm9yZGVyX2J5KCItcGh5c2ljYWxfaW52b2ljZV9saW5lX2lkIikpCiAgICBmb3Igc3ZjLCB1b20sIGRlc2MgaW4gcm93czoKICAgICAgICBzdmMgPSAoc3ZjIG9yICIiKS5zdHJpcCgpCiAgICAgICAgaWYgbm90IHN2YzoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBrZXkgPSBzdmMudXBwZXIoKQogICAgICAgIGlmIGtleSBub3QgaW4gYnlfc2VydmljZToKICAgICAgICAgICAgYnlfc2VydmljZVtrZXldID0geyJ1bml0cyI6IFtdLCAiZGVzY3JpcHRpb25zIjogW119CiAgICAgICAgICAgIHNlZW5fdVtrZXldLCBzZWVuX2Rba2V5XSA9IHNldCgpLCBzZXQoKQogICAgICAgICAgICBzdmNfZGlzcGxheVtrZXldID0gc3ZjCiAgICAgICAgdW9tID0gKHVvbSBvciAiIikuc3RyaXAoKQogICAgICAgIGRlc2MgPSAoZGVzYyBvciAiIikuc3RyaXAoKQogICAgICAgIGlmIHVvbSBhbmQgdW9tLnVwcGVyKCkgbm90IGluIHNlZW5fdVtrZXldOgogICAgICAgICAgICBzZWVuX3Vba2V5XS5hZGQodW9tLnVwcGVyKCkpCiAgICAgICAgICAgIGJ5X3NlcnZpY2Vba2V5XVsidW5pdHMiXS5hcHBlbmQodW9tKQogICAgICAgIGlmIGRlc2MgYW5kIGRlc2Mgbm90IGluIHNlZW5fZFtrZXldOgogICAgICAgICAgICBzZWVuX2Rba2V5XS5hZGQoZGVzYykKICAgICAgICAgICAgYnlfc2VydmljZVtrZXldWyJkZXNjcmlwdGlvbnMiXS5hcHBlbmQoZGVzYykKICAgICAgICBpZiB1b20gYW5kIHVvbS51cHBlcigpIG5vdCBpbiBhbGxfdW5pdHNfc2VlbjoKICAgICAgICAgICAgYWxsX3VuaXRzX3NlZW4uYWRkKHVvbS51cHBlcigpKQogICAgICAgICAgICBhbGxfdW5pdHMuYXBwZW5kKHVvbSkKICAgIGZvciBrIGluIGJ5X3NlcnZpY2U6CiAgICAgICAgYnlfc2VydmljZVtrXVsidW5pdHMiXS5zb3J0KGtleT1sYW1iZGEgczogcy5sb3dlcigpKQogICAgc2VydmljZXMgPSBzb3J0ZWQoc3ZjX2Rpc3BsYXkudmFsdWVzKCksIGtleT1sYW1iZGEgczogcy5sb3dlcigpKQogICAgYWxsX3VuaXRzLnNvcnQoa2V5PWxhbWJkYSBzOiBzLmxvd2VyKCkpCiAgICByZXR1cm4geyJzZXJ2aWNlcyI6IHNlcnZpY2VzLCAiYnlfc2VydmljZSI6IGJ5X3NlcnZpY2UsICJhbGxfdW5pdHMiOiBhbGxfdW5pdHN9CgoKZGVmIHBoeXNpY2FsX2ludm9pY2VfZWRpdChyZXF1ZXN0LCBwaHlzaWNhbF9pbnZvaWNlX2lkKTo="
# decorators + def  (the clean anchor)
DECODEF_B = "QGxvZ2luX3JlcXVpcmVkCkBwZXJtaXNzaW9uX3JlcXVpcmVkKCdhdXRoLmNhbl9lZGl0X2ludm9pY2VzJywgcmFpc2VfZXhjZXB0aW9uPVRydWUpCmRlZiBwaHlzaWNhbF9pbnZvaWNlX2VkaXQocmVxdWVzdCwgcGh5c2ljYWxfaW52b2ljZV9pZCk6"

# ---- template payloads (unchanged; the template edit was fine) ----
T_OLD_B = "ICBpZiAocm93KSByb3cucmVtb3ZlKCk7Cn0KPC9zY3JpcHQ+"
T_NEW_B = "ICBpZiAocm93KSByb3cucmVtb3ZlKCk7Cn0KPC9zY3JpcHQ+Cgp7eyBwaV9zdWdnZXN0fGpzb25fc2NyaXB0OiJwaS1zdWdnZXN0LWRhdGEiIH19CjxkaXYgaWQ9InBpLWRhdGFsaXN0LWhvc3QiIHN0eWxlPSJkaXNwbGF5Om5vbmU7Ij48L2Rpdj4KPHNjcmlwdD4KLyogUGh5c2ljYWwtaW52b2ljZSBsaW5lIGF1dG9jb21wbGV0ZS4gU2VydmljZSBmaWVsZCBvZmZlcnMgZXZlcnkgU2VydmljZSB1c2VkCiAgIGJlZm9yZSAodHlwZSB0byBuYXJyb3cpLiBQaWNrIGEgU2VydmljZSBhbmQgaXRzIFVuaXQgKyBEZXNjcmlwdGlvbiBmaWVsZHMgdGhlbgogICBvZmZlciB0aGUgdmFsdWVzIHVzZWQgZm9yIHRoYXQgU2VydmljZSBiZWZvcmUgLS0gc2VsZWN0YWJsZSBhbmQgZWRpdGFibGUuCiAgIFB1cmUgPGRhdGFsaXN0Piwgbm8gZGVwZW5kZW5jaWVzLCBkZWdyYWRlcyB0byBwbGFpbiB0ZXh0IGlucHV0cy4gKi8KKGZ1bmN0aW9uKCl7CiAgdmFyIERBVEEgPSB7fTsKICB0cnkgeyBEQVRBID0gSlNPTi5wYXJzZShkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgncGktc3VnZ2VzdC1kYXRhJykudGV4dENvbnRlbnQpIHx8IHt9OyB9CiAgY2F0Y2ggKGUpIHsgREFUQSA9IHt9OyB9CiAgdmFyIGJ5U2VydmljZSA9IERBVEEuYnlfc2VydmljZSB8fCB7fTsKICB2YXIgYWxsVW5pdHMgID0gREFUQS5hbGxfdW5pdHMgfHwgW107CiAgdmFyIGhvc3QgPSBkb2N1bWVudC5nZXRFbGVtZW50QnlJZCgncGktZGF0YWxpc3QtaG9zdCcpOwogIGlmICghaG9zdCkgcmV0dXJuOwogIHZhciBzZXEgPSAwOwoKICBmdW5jdGlvbiBlc2Mocyl7IHJldHVybiBTdHJpbmcocykucmVwbGFjZSgvJi9nLCcmYW1wOycpLnJlcGxhY2UoLzwvZywnJmx0OycpLnJlcGxhY2UoLz4vZywnJmd0OycpLnJlcGxhY2UoLyIvZywnJnF1b3Q7Jyk7IH0KICBmdW5jdGlvbiBvcHRpb25zKHZhbHMpeyB2YXIgaD0nJzsgKHZhbHN8fFtdKS5mb3JFYWNoKGZ1bmN0aW9uKHYpeyBoICs9ICc8b3B0aW9uIHZhbHVlPSInK2VzYyh2KSsnIj48L29wdGlvbj4nOyB9KTsgcmV0dXJuIGg7IH0KICBmdW5jdGlvbiBlbnN1cmVMaXN0KGlkKXsgdmFyIGRsPWRvY3VtZW50LmdldEVsZW1lbnRCeUlkKGlkKTsgaWYoIWRsKXsgZGw9ZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnZGF0YWxpc3QnKTsgZGwuaWQ9aWQ7IGhvc3QuYXBwZW5kQ2hpbGQoZGwpOyB9IHJldHVybiBkbDsgfQoKICBlbnN1cmVMaXN0KCdwaS1kbC1zZXJ2aWNlcycpLmlubmVySFRNTCA9IG9wdGlvbnMoREFUQS5zZXJ2aWNlcyB8fCBbXSk7CgogIGZ1bmN0aW9uIHJlZnJlc2gocm93KXsKICAgIHZhciBzdmMgID0gcm93LnF1ZXJ5U2VsZWN0b3IoJ2lucHV0W25hbWU9ImxpbmVfc2VydmljZSJdJyk7CiAgICB2YXIgdW9tICA9IHJvdy5xdWVyeVNlbGVjdG9yKCdpbnB1dFtuYW1lPSJsaW5lX3VvbSJdJyk7CiAgICB2YXIgZGVzYyA9IHJvdy5xdWVyeVNlbGVjdG9yKCdpbnB1dFtuYW1lPSJsaW5lX2Rlc2NyaXB0aW9uIl0nKTsKICAgIGlmKCFzdmMgfHwgIXVvbSB8fCAhZGVzYykgcmV0dXJuOwogICAgdmFyIHVEbCA9IGVuc3VyZUxpc3QodW9tLmdldEF0dHJpYnV0ZSgnbGlzdCcpKTsKICAgIHZhciBkRGwgPSBlbnN1cmVMaXN0KGRlc2MuZ2V0QXR0cmlidXRlKCdsaXN0JykpOwogICAgdmFyIGVudHJ5ID0gYnlTZXJ2aWNlWyhzdmMudmFsdWV8fCcnKS50cmltKCkudG9VcHBlckNhc2UoKV07CiAgICB1RGwuaW5uZXJIVE1MID0gb3B0aW9ucyhlbnRyeSAmJiBlbnRyeS51bml0cyAmJiBlbnRyeS51bml0cy5sZW5ndGggPyBlbnRyeS51bml0cyA6IGFsbFVuaXRzKTsKICAgIGREbC5pbm5lckhUTUwgPSBvcHRpb25zKGVudHJ5ID8gZW50cnkuZGVzY3JpcHRpb25zIDogW10pOwogIH0KCiAgZnVuY3Rpb24gd2lyZShyb3cpewogICAgdmFyIHN2YyAgPSByb3cucXVlcnlTZWxlY3RvcignaW5wdXRbbmFtZT0ibGluZV9zZXJ2aWNlIl0nKTsKICAgIHZhciB1b20gID0gcm93LnF1ZXJ5U2VsZWN0b3IoJ2lucHV0W25hbWU9ImxpbmVfdW9tIl0nKTsKICAgIHZhciBkZXNjID0gcm93LnF1ZXJ5U2VsZWN0b3IoJ2lucHV0W25hbWU9ImxpbmVfZGVzY3JpcHRpb24iXScpOwogICAgaWYoIXN2YyB8fCAhdW9tIHx8ICFkZXNjIHx8IHN2Yy5kYXRhc2V0LnBpV2lyZWQgPT09ICcxJykgcmV0dXJuOwogICAgc3ZjLmRhdGFzZXQucGlXaXJlZCA9ICcxJzsKICAgIHNlcSsrOwogICAgc3ZjLnNldEF0dHJpYnV0ZSgnbGlzdCcsJ3BpLWRsLXNlcnZpY2VzJyk7CiAgICB1b20uc2V0QXR0cmlidXRlKCdsaXN0JywncGktZGwtdW9tLScrc2VxKTsKICAgIGRlc2Muc2V0QXR0cmlidXRlKCdsaXN0JywncGktZGwtZGVzYy0nK3NlcSk7CiAgICBzdmMuYWRkRXZlbnRMaXN0ZW5lcignaW5wdXQnLCAgZnVuY3Rpb24oKXsgcmVmcmVzaChyb3cpOyB9KTsKICAgIHN2Yy5hZGRFdmVudExpc3RlbmVyKCdjaGFuZ2UnLCBmdW5jdGlvbigpeyByZWZyZXNoKHJvdyk7IH0pOwogICAgcmVmcmVzaChyb3cpOwogIH0KCiAgZnVuY3Rpb24gd2lyZUFsbCgpeyBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCcjbGluZXNCb2R5IHRyLmxpbmUtcm93JykuZm9yRWFjaCh3aXJlKTsgfQoKICB2YXIgYm9keSA9IGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKCdsaW5lc0JvZHknKTsKICBpZiAoYm9keSAmJiB3aW5kb3cuTXV0YXRpb25PYnNlcnZlcil7CiAgICBuZXcgTXV0YXRpb25PYnNlcnZlcihmdW5jdGlvbihtdXRzKXsKICAgICAgbXV0cy5mb3JFYWNoKGZ1bmN0aW9uKG0pewogICAgICAgIChtLmFkZGVkTm9kZXMgfHwgW10pLmZvckVhY2goZnVuY3Rpb24obil7CiAgICAgICAgICBpZiAobi5ub2RlVHlwZSA9PT0gMSAmJiBuLm1hdGNoZXMgJiYgbi5tYXRjaGVzKCd0ci5saW5lLXJvdycpKSB3aXJlKG4pOwogICAgICAgIH0pOwogICAgICB9KTsKICAgIH0pLm9ic2VydmUoYm9keSwge2NoaWxkTGlzdDp0cnVlfSk7CiAgfQoKICBpZiAoZG9jdW1lbnQucmVhZHlTdGF0ZSA9PT0gJ2xvYWRpbmcnKSBkb2N1bWVudC5hZGRFdmVudExpc3RlbmVyKCdET01Db250ZW50TG9hZGVkJywgd2lyZUFsbCk7CiAgZWxzZSB3aXJlQWxsKCk7Cn0pKCk7Cjwvc2NyaXB0Pg=="


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


def fix_view(path):
    txt = read(path)
    ctx_new, ctx_old = d(CTX_NEW_B), d(CTX_OLD_B)
    help_decodef, help_def = d(HELP_DECODEF_B), d(HELP_DEF_B)
    decodef = d(DECODEF_B)

    # --- normalise: strip any prior insertion + context line ---
    txt = txt.replace(ctx_new, ctx_old)
    txt = txt.replace(help_decodef, decodef)   # undo a correctly-placed helper (re-run)
    txt = txt.replace(help_def, d("ZGVmIHBoeXNpY2FsX2ludm9pY2VfZWRpdChyZXF1ZXN0LCBwaHlzaWNhbF9pbnZvaWNlX2lkKTo="))  # undo broken helper -> bare def

    if "_build_line_suggestions" in txt:
        print('!! view still contains _build_line_suggestions after normalise; the'
              ' helper text does not match this file byte-for-byte. Nothing changed.')
        sys.exit(1)
    if txt.count(decodef) != 1:
        print('!! decorator+def anchor for physical_invoice_edit not found exactly'
              ' once (found %d). Nothing changed.' % txt.count(decodef)); sys.exit(1)
    if txt.count(ctx_old) != 1:
        print('!! context anchor not found exactly once (found %d). Nothing changed.'
              % txt.count(ctx_old)); sys.exit(1)

    # --- apply correctly: helper ABOVE the decorators, then context line ---
    txt = txt.replace(decodef, help_decodef, 1)
    txt = txt.replace(ctx_old, ctx_new, 1)

    # --- gates ---
    try:
        ast.parse(txt)
    except SyntaxError as e:
        print('!! resulting view would not parse (%s). Nothing changed.' % e); sys.exit(1)
    # positive check: decorators must be on the VIEW, not the helper
    if decodef not in txt:
        print('!! post-check failed: decorators not on physical_invoice_edit.'); sys.exit(1)
    if "raise_exception=True)\ndef _build_line_suggestions" in txt:
        print('!! post-check failed: decorators landed on the helper.'); sys.exit(1)
    if txt.index("def _build_line_suggestions") > txt.index(decodef):
        print('!! post-check failed: helper is not above the decorators.'); sys.exit(1)
    return txt


def fix_template(path):
    txt = read(path)
    if 'pi-suggest-data' in txt:
        print('   [skip] template already has the autocomplete block.')
        return None
    old, new = d(T_OLD_B), d(T_NEW_B)
    c = txt.count(old)
    if c != 1:
        print('!! template anchor not matched (found %d). Template unchanged.' % c); sys.exit(1)
    txt = txt.replace(old, new, 1)
    if not tag_balanced(txt) or txt.count('<script') != txt.count('</script>'):
        print('!! template tag/script balance broke. Nothing changed.'); sys.exit(1)
    return txt


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

    print('view:  normalise + re-apply helper above the decorators')
    v_txt = fix_view(view)
    print('template:')
    t_txt = fix_template(tpl)

    if DRY:
        print(''); print('[dry-run] would rewrite the view correctly'
              + (' and add the template block.' if t_txt is not None else ' (template already OK).'))
        return

    nl = detect_nl(view); b = view + '.bak_autofix'
    if not os.path.exists(b): write(b, read(view), nl)
    write(view, v_txt, nl)
    print(''); print('[OK] physical_invoices.py fixed (.bak_autofix).')
    if t_txt is not None:
        nlt = detect_nl(tpl); bt = tpl + '.bak_autofix'
        if not os.path.exists(bt): write(bt, read(tpl), nlt)
        write(tpl, t_txt, nlt)
        print('[OK] physical_invoice_edit.html updated (.bak_autofix).')

    print('')
    print('Fixed. The helper now sits ABOVE the @login_required/@permission_required'
          ' decorators, so physical_invoice_edit keeps them. Restart the dev server'
          ' / redeploy and open the edit page.')


if __name__ == '__main__':
    main()