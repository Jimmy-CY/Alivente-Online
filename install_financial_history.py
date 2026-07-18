#!/usr/bin/env python
"""
install_financial_history.py  —  Phase 1 of the Financial-History feature.  (v3)

WHAT IT DOES (nothing else):
  1. pages/models.py        : appends the FinancialFigureHistory model + two
                              fail-safe write-hook helpers + a Phase-2 resolver.
                              (append-only; existing models untouched)
  2. pages/views/finance.py : extends the models import and inserts a post-commit
                              history hook after each budgeted-expense / revenue
                              save (8 spots). Saves work exactly as now; a
                              history-write can NEVER block a save.
  3. management command     : writes pages/management/commands/
                              seed_financial_history.py (baseline seeder).

SAFE: idempotent; backs each edited file up once to <file>.bak_finhist; re-parses
both edited files and aborts (writing nothing) on any syntax error; --dry-run.
Matching is newline-anchored (robust to blank-line formatting) and the ORIGINAL
line-ending style (CRLF/LF) of each edited file is preserved, so git diffs stay
minimal.

Run from the project root (folder with manage.py):
    python install_financial_history.py --dry-run
    python install_financial_history.py

AFTER APPLYING:
    python manage.py makemigrations pages    # (skips if model already migrated)
    python manage.py migrate
    python manage.py seed_financial_history --dry-run
    python manage.py seed_financial_history
"""
import ast
import base64
import os
import sys

DRY = '--dry-run' in sys.argv

REPL = [['ZnJvbSBwYWdlcy5tb2RlbHMgaW1wb3J0ICgKICAgIHByb3BzLCBwcm9wX3ZhbHVlcywKICAgIHJldmVudWUsIHJldmVudWVfdHlwZXMsIHJldmVudWVfbGluZV90eXBlcywKICAgIGV4cGVuc2UsIGV4cGVuc2VfdHlwZXMsIGV4cGVuc2VfbGluZV90eXBlcywKICAgIHRlbmFudCwgYWN0X2V4cGVuc2UsIFZhY2FuY3lQZXJpb2QsCik=', 'ZnJvbSBwYWdlcy5tb2RlbHMgaW1wb3J0ICgKICAgIHByb3BzLCBwcm9wX3ZhbHVlcywKICAgIHJldmVudWUsIHJldmVudWVfdHlwZXMsIHJldmVudWVfbGluZV90eXBlcywKICAgIGV4cGVuc2UsIGV4cGVuc2VfdHlwZXMsIGV4cGVuc2VfbGluZV90eXBlcywKICAgIHRlbmFudCwgYWN0X2V4cGVuc2UsIFZhY2FuY3lQZXJpb2QsCiAgICBGaW5hbmNpYWxGaWd1cmVIaXN0b3J5LCByZWNvcmRfZXhwZW5zZV9oaXN0b3J5LCByZWNvcmRfcmV2ZW51ZV9oaXN0b3J5LAop'], ['bG9nZ2VyID0gbG9nZ2luZy5nZXRMb2dnZXIoX19uYW1lX18p', 'bG9nZ2VyID0gbG9nZ2luZy5nZXRMb2dnZXIoX19uYW1lX18pCgoKIyAtLS0tIEZpbmFuY2lhbCBoaXN0b3J5IChQaGFzZSAxKSA6IGVmZmVjdGl2ZSBkYXRlICsgdXNlciwgYm90aCBmYWlsLXNhZmUgLS0tLQpkZWYgX2ZoX2VmZl9kYXRlKHJlcXVlc3QpOgogICAgIiIiRWZmZWN0aXZlIGRhdGUgZm9yIGEgYnVkZ2V0ZWQvcmV2ZW51ZSBjaGFuZ2U6IHRoZSBmb3JtJ3MgJ2VmZmVjdGl2ZV9kYXRlJwogICAgKFlZWVktTU0tREQpIGlmIHN1cHBsaWVkLCBvdGhlcndpc2UgdG9kYXkuIE5ldmVyIHJhaXNlcy4iIiIKICAgIHJhdyA9IChyZXF1ZXN0LlBPU1QuZ2V0KCdlZmZlY3RpdmVfZGF0ZScpIG9yICcnKS5zdHJpcCgpCiAgICBpZiByYXc6CiAgICAgICAgdHJ5OgogICAgICAgICAgICByZXR1cm4gZGF0ZXRpbWUuc3RycHRpbWUocmF3LCAnJVktJW0tJWQnKS5kYXRlKCkKICAgICAgICBleGNlcHQgVmFsdWVFcnJvcjoKICAgICAgICAgICAgcGFzcwogICAgcmV0dXJuIGRhdGUudG9kYXkoKQoKCmRlZiBfZmhfdXNlcihyZXF1ZXN0KToKICAgIHUgPSBnZXRhdHRyKHJlcXVlc3QsICd1c2VyJywgTm9uZSkKICAgIHJldHVybiB1IGlmICh1IGlzIG5vdCBOb25lIGFuZCBnZXRhdHRyKHUsICdpc19hdXRoZW50aWNhdGVkJywgRmFsc2UpKSBlbHNlIE5vbmU='], ['ICAgICAgICAgICAgcmV2ZW51ZS5vYmplY3RzLnVwZGF0ZV9vcl9jcmVhdGUoCiAgICAgICAgICAgICAgICBwcm9wX2lkPXByb3BfaWQsCiAgICAgICAgICAgICAgICByZXZlbnVlX2xpbmVfdHlwZXNfaWQ9cmx0X2lkLAogICAgICAgICAgICAgICAgcmV2ZW51ZV90eXBlc19pZD1ydF9pZCwKICAgICAgICAgICAgICAgIGRlZmF1bHRzPW1vbnRobHlfZGF0YSwKICAgICAgICAgICAgKQ==', 'ICAgICAgICAgICAgX2ZoX3JldiwgXyA9IHJldmVudWUub2JqZWN0cy51cGRhdGVfb3JfY3JlYXRlKAogICAgICAgICAgICAgICAgcHJvcF9pZD1wcm9wX2lkLAogICAgICAgICAgICAgICAgcmV2ZW51ZV9saW5lX3R5cGVzX2lkPXJsdF9pZCwKICAgICAgICAgICAgICAgIHJldmVudWVfdHlwZXNfaWQ9cnRfaWQsCiAgICAgICAgICAgICAgICBkZWZhdWx0cz1tb250aGx5X2RhdGEsCiAgICAgICAgICAgICkKICAgICAgICAgICAgdHJhbnNhY3Rpb24ub25fY29tbWl0KGxhbWJkYSBvPV9maF9yZXY6IHJlY29yZF9yZXZlbnVlX2hpc3RvcnkobywgX2ZoX2VmZl9kYXRlKHJlcXVlc3QpLCBzb3VyY2U9J2RpcmVjdCcsIHVzZXI9X2ZoX3VzZXIocmVxdWVzdCkpKQ=='], ['ICAgICAgICAgICAgcmV2LnNhdmUoKQ==', 'ICAgICAgICAgICAgcmV2LnNhdmUoKQogICAgICAgICAgICB0cmFuc2FjdGlvbi5vbl9jb21taXQobGFtYmRhIG89cmV2OiByZWNvcmRfcmV2ZW51ZV9oaXN0b3J5KG8sIF9maF9lZmZfZGF0ZShyZXF1ZXN0KSwgc291cmNlPSdkaXJlY3QnLCB1c2VyPV9maF91c2VyKHJlcXVlc3QpKSk='], ['ICAgICAgICAgICAgICAgICAgICBleHBlbnNlLm9iamVjdHMudXBkYXRlX29yX2NyZWF0ZSgKICAgICAgICAgICAgICAgICAgICAgICAgcHJvcF9pZD1wcm9wZXJ0eV9kYXRhWydwcm9wX2lkJ10sCiAgICAgICAgICAgICAgICAgICAgICAgIGV4cGVuc2VfbGluZV90eXBlc19pZD1lbHRfaWQsCiAgICAgICAgICAgICAgICAgICAgICAgIGV4cGVuc2VfdHlwZXNfaWQ9ZXRfaWQsCiAgICAgICAgICAgICAgICAgICAgICAgIGRlZmF1bHRzPW1vbnRobHlfZGF0YSwKICAgICAgICAgICAgICAgICAgICAp', 'ICAgICAgICAgICAgICAgICAgICBfZmhfZXhwLCBfID0gZXhwZW5zZS5vYmplY3RzLnVwZGF0ZV9vcl9jcmVhdGUoCiAgICAgICAgICAgICAgICAgICAgICAgIHByb3BfaWQ9cHJvcGVydHlfZGF0YVsncHJvcF9pZCddLAogICAgICAgICAgICAgICAgICAgICAgICBleHBlbnNlX2xpbmVfdHlwZXNfaWQ9ZWx0X2lkLAogICAgICAgICAgICAgICAgICAgICAgICBleHBlbnNlX3R5cGVzX2lkPWV0X2lkLAogICAgICAgICAgICAgICAgICAgICAgICBkZWZhdWx0cz1tb250aGx5X2RhdGEsCiAgICAgICAgICAgICAgICAgICAgKQogICAgICAgICAgICAgICAgICAgIHRyYW5zYWN0aW9uLm9uX2NvbW1pdChsYW1iZGEgbz1fZmhfZXhwOiByZWNvcmRfZXhwZW5zZV9oaXN0b3J5KG8sIF9maF9lZmZfZGF0ZShyZXF1ZXN0KSwgc291cmNlPSdwcm9yYXRhJywgdXNlcj1fZmhfdXNlcihyZXF1ZXN0KSkp'], ['ICAgICAgICAgICAgZXhwZW5zZS5vYmplY3RzLnVwZGF0ZV9vcl9jcmVhdGUoCiAgICAgICAgICAgICAgICBwcm9wX2lkPXByb3BfaWQsCiAgICAgICAgICAgICAgICBleHBlbnNlX2xpbmVfdHlwZXNfaWQ9ZWx0X2lkLAogICAgICAgICAgICAgICAgZXhwZW5zZV90eXBlc19pZD1ldF9pZCwKICAgICAgICAgICAgICAgIGRlZmF1bHRzPW1vbnRobHlfZGF0YSwKICAgICAgICAgICAgKQ==', 'ICAgICAgICAgICAgX2ZoX2V4cCwgXyA9IGV4cGVuc2Uub2JqZWN0cy51cGRhdGVfb3JfY3JlYXRlKAogICAgICAgICAgICAgICAgcHJvcF9pZD1wcm9wX2lkLAogICAgICAgICAgICAgICAgZXhwZW5zZV9saW5lX3R5cGVzX2lkPWVsdF9pZCwKICAgICAgICAgICAgICAgIGV4cGVuc2VfdHlwZXNfaWQ9ZXRfaWQsCiAgICAgICAgICAgICAgICBkZWZhdWx0cz1tb250aGx5X2RhdGEsCiAgICAgICAgICAgICkKICAgICAgICAgICAgdHJhbnNhY3Rpb24ub25fY29tbWl0KGxhbWJkYSBvPV9maF9leHA6IHJlY29yZF9leHBlbnNlX2hpc3RvcnkobywgX2ZoX2VmZl9kYXRlKHJlcXVlc3QpLCBzb3VyY2U9J2J1ZGdldCcsIHVzZXI9X2ZoX3VzZXIocmVxdWVzdCkpKQ=='], ['ICAgICAgICAgICAgICAgICAgICBleHBlbnNlLm9iamVjdHMuY3JlYXRlKCoqbW9udGhseV9kYXRhKQ==', 'ICAgICAgICAgICAgICAgICAgICBfZmhfZXhwID0gZXhwZW5zZS5vYmplY3RzLmNyZWF0ZSgqKm1vbnRobHlfZGF0YSkKICAgICAgICAgICAgICAgICAgICB0cmFuc2FjdGlvbi5vbl9jb21taXQobGFtYmRhIG89X2ZoX2V4cDogcmVjb3JkX2V4cGVuc2VfaGlzdG9yeShvLCBfZmhfZWZmX2RhdGUocmVxdWVzdCksIHNvdXJjZT0ncHJvcmF0YScsIHVzZXI9X2ZoX3VzZXIocmVxdWVzdCkpKQ=='], ['ICAgICAgICAgICAgZXhpc3RpbmdfZXhwZW5zZS5zYXZlKCk=', 'ICAgICAgICAgICAgZXhpc3RpbmdfZXhwZW5zZS5zYXZlKCkKICAgICAgICAgICAgdHJhbnNhY3Rpb24ub25fY29tbWl0KGxhbWJkYSBvPWV4aXN0aW5nX2V4cGVuc2U6IHJlY29yZF9leHBlbnNlX2hpc3RvcnkobywgX2ZoX2VmZl9kYXRlKHJlcXVlc3QpLCBzb3VyY2U9J2J1ZGdldCcsIHVzZXI9X2ZoX3VzZXIocmVxdWVzdCkpKQ=='], ['ICAgICAgICAgICAgICAgICAgICBleHAuc2F2ZSgp', 'ICAgICAgICAgICAgICAgICAgICBleHAuc2F2ZSgpCiAgICAgICAgICAgICAgICAgICAgdHJhbnNhY3Rpb24ub25fY29tbWl0KGxhbWJkYSBvPWV4cDogcmVjb3JkX2V4cGVuc2VfaGlzdG9yeShvLCBfZmhfZWZmX2RhdGUocmVxdWVzdCksIHNvdXJjZT0ncHJvcmF0YV9saW5lJywgdXNlcj1fZmhfdXNlcihyZXF1ZXN0KSkp'], ['ICAgICAgICAgICAgICAgICAgICAgICAgZXhwLnNhdmUoKQ==', 'ICAgICAgICAgICAgICAgICAgICAgICAgZXhwLnNhdmUoKQogICAgICAgICAgICAgICAgICAgICAgICB0cmFuc2FjdGlvbi5vbl9jb21taXQobGFtYmRhIG89ZXhwOiByZWNvcmRfZXhwZW5zZV9oaXN0b3J5KG8sIF9maF9lZmZfZGF0ZShyZXF1ZXN0KSwgc291cmNlPSdwcm9yYXRhX3ZhbHVhdGlvbicsIHVzZXI9X2ZoX3VzZXIocmVxdWVzdCkpKQ==']]
MODELS_BLOCK = base64.b64decode("CgojID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CiMgRmluYW5jaWFsIEZpZ3VyZSBIaXN0b3J5IChQaGFzZSAxKSDigJQgYXBwZW5kLW9ubHkgcmVjb3JkIG9mIEJVREdFVEVEIGZpZ3VyZXMuCiMgSW5zdGFsbGVkIGJ5IGluc3RhbGxfZmluYW5jaWFsX2hpc3RvcnkucHkuICBOb3RoaW5nIGluIHRoZSBhcHAgUkVBRFMgdGhpcyBpbgojIFBoYXNlIDE7IGl0IG9ubHkgcmVjb3Jkcy4gVGhlIFAmTCBjb25zdW1lcyBpdCBpbiBQaGFzZSAyLgojCiMgT25lIHJvdyBwZXIgc2F2ZS9lZGl0IG9mIGEgYnVkZ2V0ZWQgZXhwZW5zZSBvciBhIGRpcmVjdC9zZWFzb25hbCByZXZlbnVlLgojIGVmZmVjdGl2ZV9kYXRlID0gdGhlIG1vbnRoIGEgdmFsdWUgdGFrZXMgZWZmZWN0IEZST00gKGRlZmF1bHRzIHRvIHRoZSBkYXkgb2YKIyB0aGUgZWRpdDsgdGhlIGVkaXQgZm9ybSBtYXkgb3ZlcnJpZGUgaXQpLiBUaGUgdHdlbHZlIG1vbnRobHkgY29sdW1ucyBtaXJyb3IKIyBleHBlbnNlX2phbi4uIC8gcmV2ZW51ZV9qYW4uLiBzbyBhIGhpc3Rvcnkgcm93IHJlYWRzIGV4YWN0bHkgbGlrZSBhIGxpdmUgcm93LgojID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09CmZyb20gZGF0ZXRpbWUgaW1wb3J0IGRhdGUgYXMgX2ZoX2RhdGUKaW1wb3J0IGxvZ2dpbmcgYXMgX2ZoX2xvZ2dpbmcKCl9maF9sb2cgPSBfZmhfbG9nZ2luZy5nZXRMb2dnZXIoX19uYW1lX18pCl9GSF9NT05USFMgPSBbJ2phbicsICdmZWInLCAnbWFyJywgJ2FwcicsICdtYXknLCAnanVuJywKICAgICAgICAgICAgICAnanVsJywgJ2F1ZycsICdzZXAnLCAnb2N0JywgJ25vdicsICdkZWMnXQoKCmNsYXNzIEZpbmFuY2lhbEZpZ3VyZUhpc3RvcnkobW9kZWxzLk1vZGVsKToKICAgIEtJTkRfUkVWRU5VRSA9ICdyZXZlbnVlJyAgICAgICAgICAjIGRpcmVjdCAvIHNlYXNvbmFsIHJldmVudWUgKHJldmVudWUgdGFibGUpCiAgICBLSU5EX0JVREdFVCA9ICdidWRnZXRfZXhwZW5zZScgICAgIyBidWRnZXRlZCBleHBlbnNlIChleHBlbnNlIHRhYmxlKQogICAgS0lORF9DSE9JQ0VTID0gWwogICAgICAgIChLSU5EX1JFVkVOVUUsICdSZXZlbnVlIChkaXJlY3QgLyBzZWFzb25hbCknKSwKICAgICAgICAoS0lORF9CVURHRVQsICdCdWRnZXRlZCBleHBlbnNlJyksCiAgICBdCgogICAgZmluYW5jaWFsX2ZpZ3VyZV9oaXN0b3J5X2lkID0gbW9kZWxzLkF1dG9GaWVsZChwcmltYXJ5X2tleT1UcnVlKQogICAgcHJvcCA9IG1vZGVscy5Gb3JlaWduS2V5KCdwcm9wcycsIG9uX2RlbGV0ZT1tb2RlbHMuQ0FTQ0FERSwgcmVsYXRlZF9uYW1lPSdmaWd1cmVfaGlzdG9yeScpCiAgICBraW5kID0gbW9kZWxzLkNoYXJGaWVsZChtYXhfbGVuZ3RoPTIwLCBjaG9pY2VzPUtJTkRfQ0hPSUNFUykKCiAgICAjIHBrIG9mIHRoZSBzb3VyY2UgY29uZmlnIHJvdyB0aGF0IGNoYW5nZWQgKGV4cGVuc2VfaWQgLyByZXZlbnVlX2lkKQogICAgc291cmNlX3BrID0gbW9kZWxzLkludGVnZXJGaWVsZChoZWxwX3RleHQ9J2V4cGVuc2VfaWQgb3IgcmV2ZW51ZV9pZCBvZiB0aGUgc291cmNlIHJvdycpCiAgICBsaW5lX3R5cGUgPSBtb2RlbHMuQ2hhckZpZWxkKG1heF9sZW5ndGg9MjU1LCBibGFuaz1UcnVlLCBudWxsPVRydWUsCiAgICAgICAgaGVscF90ZXh0PSdEZW5vcm1hbGlzZWQgbGluZS10eXBlIGxhYmVsLCBlLmcuIFJlbnRhbCAvIEluc3VyYW5jZS4nKQoKICAgIGVmZmVjdGl2ZV9kYXRlID0gbW9kZWxzLkRhdGVGaWVsZChoZWxwX3RleHQ9J0RhdGUgZnJvbSB3aGljaCB0aGVzZSB2YWx1ZXMgYXBwbHkuJykKICAgIGFtb3VudCA9IG1vZGVscy5EZWNpbWFsRmllbGQobWF4X2RpZ2l0cz0xMCwgZGVjaW1hbF9wbGFjZXM9MiwgYmxhbms9VHJ1ZSwgbnVsbD1UcnVlLAogICAgICAgIGhlbHBfdGV4dD0nQmFzZSBhbW91bnQgYXQgdGhpcyB2ZXJzaW9uIChtaXJyb3JzIGV4cGVuc2VfYW1vdW50IC8gcmV2ZW51ZV9hbW91bnQpLicpCgogICAgIyBNb250aGx5IHNuYXBzaG90IOKAlCBtaXJyb3JzIHRoZSB0d2VsdmUgY29sdW1ucyBvbiBleHBlbnNlIC8gcmV2ZW51ZS4KICAgIGphbiA9IG1vZGVscy5EZWNpbWFsRmllbGQobWF4X2RpZ2l0cz0xMCwgZGVjaW1hbF9wbGFjZXM9MiwgYmxhbms9VHJ1ZSwgbnVsbD1UcnVlKQogICAgZmViID0gbW9kZWxzLkRlY2ltYWxGaWVsZChtYXhfZGlnaXRzPTEwLCBkZWNpbWFsX3BsYWNlcz0yLCBibGFuaz1UcnVlLCBudWxsPVRydWUpCiAgICBtYXIgPSBtb2RlbHMuRGVjaW1hbEZpZWxkKG1heF9kaWdpdHM9MTAsIGRlY2ltYWxfcGxhY2VzPTIsIGJsYW5rPVRydWUsIG51bGw9VHJ1ZSkKICAgIGFwciA9IG1vZGVscy5EZWNpbWFsRmllbGQobWF4X2RpZ2l0cz0xMCwgZGVjaW1hbF9wbGFjZXM9MiwgYmxhbms9VHJ1ZSwgbnVsbD1UcnVlKQogICAgbWF5ID0gbW9kZWxzLkRlY2ltYWxGaWVsZChtYXhfZGlnaXRzPTEwLCBkZWNpbWFsX3BsYWNlcz0yLCBibGFuaz1UcnVlLCBudWxsPVRydWUpCiAgICBqdW4gPSBtb2RlbHMuRGVjaW1hbEZpZWxkKG1heF9kaWdpdHM9MTAsIGRlY2ltYWxfcGxhY2VzPTIsIGJsYW5rPVRydWUsIG51bGw9VHJ1ZSkKICAgIGp1bCA9IG1vZGVscy5EZWNpbWFsRmllbGQobWF4X2RpZ2l0cz0xMCwgZGVjaW1hbF9wbGFjZXM9MiwgYmxhbms9VHJ1ZSwgbnVsbD1UcnVlKQogICAgYXVnID0gbW9kZWxzLkRlY2ltYWxGaWVsZChtYXhfZGlnaXRzPTEwLCBkZWNpbWFsX3BsYWNlcz0yLCBibGFuaz1UcnVlLCBudWxsPVRydWUpCiAgICBzZXAgPSBtb2RlbHMuRGVjaW1hbEZpZWxkKG1heF9kaWdpdHM9MTAsIGRlY2ltYWxfcGxhY2VzPTIsIGJsYW5rPVRydWUsIG51bGw9VHJ1ZSkKICAgIG9jdCA9IG1vZGVscy5EZWNpbWFsRmllbGQobWF4X2RpZ2l0cz0xMCwgZGVjaW1hbF9wbGFjZXM9MiwgYmxhbms9VHJ1ZSwgbnVsbD1UcnVlKQogICAgbm92ID0gbW9kZWxzLkRlY2ltYWxGaWVsZChtYXhfZGlnaXRzPTEwLCBkZWNpbWFsX3BsYWNlcz0yLCBibGFuaz1UcnVlLCBudWxsPVRydWUpCiAgICBkZWMgPSBtb2RlbHMuRGVjaW1hbEZpZWxkKG1heF9kaWdpdHM9MTAsIGRlY2ltYWxfcGxhY2VzPTIsIGJsYW5rPVRydWUsIG51bGw9VHJ1ZSkKCiAgICBzb3VyY2UgPSBtb2RlbHMuQ2hhckZpZWxkKG1heF9sZW5ndGg9MzAsIGJsYW5rPVRydWUsIG51bGw9VHJ1ZSwKICAgICAgICBoZWxwX3RleHQ9J2J1ZGdldCB8IGRpcmVjdCB8IHByb3JhdGEgfCBwcm9yYXRhX2xpbmUgfCBwcm9yYXRhX3ZhbHVhdGlvbiB8IHNlZWQnKQogICAgY2hhbmdlZF9ieSA9IG1vZGVscy5Gb3JlaWduS2V5KFVzZXIsIG9uX2RlbGV0ZT1tb2RlbHMuU0VUX05VTEwsIG51bGw9VHJ1ZSwgYmxhbms9VHJ1ZSwgcmVsYXRlZF9uYW1lPScrJykKICAgIGNoYW5nZWRfYXQgPSBtb2RlbHMuRGF0ZVRpbWVGaWVsZChhdXRvX25vd19hZGQ9VHJ1ZSkKCiAgICBjbGFzcyBNZXRhOgogICAgICAgIGRiX3RhYmxlID0gJ2ZpbmFuY2lhbF9maWd1cmVfaGlzdG9yeScKICAgICAgICB2ZXJib3NlX25hbWUgPSAnRmluYW5jaWFsIEZpZ3VyZSBIaXN0b3J5JwogICAgICAgIHZlcmJvc2VfbmFtZV9wbHVyYWwgPSAnRmluYW5jaWFsIEZpZ3VyZSBIaXN0b3J5JwogICAgICAgIG9yZGVyaW5nID0gWydwcm9wX2lkJywgJ2tpbmQnLCAnLWVmZmVjdGl2ZV9kYXRlJywgJy1jaGFuZ2VkX2F0J10KICAgICAgICBpbmRleGVzID0gWwogICAgICAgICAgICBtb2RlbHMuSW5kZXgoZmllbGRzPVsncHJvcCcsICdraW5kJywgJ2VmZmVjdGl2ZV9kYXRlJ10pLAogICAgICAgICAgICBtb2RlbHMuSW5kZXgoZmllbGRzPVsna2luZCcsICdzb3VyY2VfcGsnXSksCiAgICAgICAgXQoKICAgIGRlZiBfX3N0cl9fKHNlbGYpOgogICAgICAgIHJldHVybiAnJXMg4oCUICVzIOKAlCBlZmYgJXMnICUgKHNlbGYuZ2V0X2tpbmRfZGlzcGxheSgpLCBzZWxmLmxpbmVfdHlwZSwgc2VsZi5lZmZlY3RpdmVfZGF0ZSkKCgojIC0tLS0gV3JpdGUtaG9vayBoZWxwZXJzLiBDYWxsZWQgQUZURVIgY29tbWl0IHZpYSB0cmFuc2FjdGlvbi5vbl9jb21taXQoKTsgdGhleQojICAgICAgTkVWRVIgcmFpc2UsIHNvIGEgaGlzdG9yeS13cml0ZSBwcm9ibGVtIGNhbid0IGJyZWFrIHRoZSB1c2VyJ3Mgc2F2ZS4gLS0tLS0KZGVmIHJlY29yZF9leHBlbnNlX2hpc3RvcnkoZXhwLCBlZmZlY3RpdmVfZGF0ZSwgKiwgc291cmNlPSdidWRnZXQnLCB1c2VyPU5vbmUpOgogICAgIiIiU25hcHNob3QgYSBidWRnZXRlZCBgZXhwZW5zZWAgcm93IGludG8gaGlzdG9yeS4gRmFpbC1zYWZlIChsb2dzLCByZXR1cm5zCiAgICBOb25lIG9uIGFueSBlcnJvcikuIiIiCiAgICB0cnk6CiAgICAgICAgbW9udGhzID0ge206IGdldGF0dHIoZXhwLCAnZXhwZW5zZV8nICsgbSkgZm9yIG0gaW4gX0ZIX01PTlRIU30KICAgICAgICByZXR1cm4gRmluYW5jaWFsRmlndXJlSGlzdG9yeS5vYmplY3RzLmNyZWF0ZSgKICAgICAgICAgICAgcHJvcD1leHAucHJvcCwga2luZD1GaW5hbmNpYWxGaWd1cmVIaXN0b3J5LktJTkRfQlVER0VULAogICAgICAgICAgICBzb3VyY2VfcGs9ZXhwLmV4cGVuc2VfaWQsIGxpbmVfdHlwZT1zdHIoZXhwLmV4cGVuc2VfbGluZV90eXBlcyksCiAgICAgICAgICAgIGVmZmVjdGl2ZV9kYXRlPWVmZmVjdGl2ZV9kYXRlLCBhbW91bnQ9ZXhwLmV4cGVuc2VfYW1vdW50LAogICAgICAgICAgICBzb3VyY2U9c291cmNlLCBjaGFuZ2VkX2J5PXVzZXIsICoqbW9udGhzLAogICAgICAgICkKICAgIGV4Y2VwdCBFeGNlcHRpb246CiAgICAgICAgX2ZoX2xvZy5leGNlcHRpb24oJ3JlY29yZF9leHBlbnNlX2hpc3RvcnkgZmFpbGVkIChzYXZlIGl0c2VsZiB3YXMgbm90IGFmZmVjdGVkKScpCiAgICAgICAgcmV0dXJuIE5vbmUKCgpkZWYgcmVjb3JkX3JldmVudWVfaGlzdG9yeShyZXYsIGVmZmVjdGl2ZV9kYXRlLCAqLCBzb3VyY2U9J2RpcmVjdCcsIHVzZXI9Tm9uZSk6CiAgICAiIiJTbmFwc2hvdCBhIGByZXZlbnVlYCByb3cgaW50byBoaXN0b3J5LiBGYWlsLXNhZmUuIiIiCiAgICB0cnk6CiAgICAgICAgbW9udGhzID0ge206IGdldGF0dHIocmV2LCAncmV2ZW51ZV8nICsgbSkgZm9yIG0gaW4gX0ZIX01PTlRIU30KICAgICAgICByZXR1cm4gRmluYW5jaWFsRmlndXJlSGlzdG9yeS5vYmplY3RzLmNyZWF0ZSgKICAgICAgICAgICAgcHJvcD1yZXYucHJvcCwga2luZD1GaW5hbmNpYWxGaWd1cmVIaXN0b3J5LktJTkRfUkVWRU5VRSwKICAgICAgICAgICAgc291cmNlX3BrPXJldi5yZXZlbnVlX2lkLCBsaW5lX3R5cGU9c3RyKHJldi5yZXZlbnVlX2xpbmVfdHlwZXMpLAogICAgICAgICAgICBlZmZlY3RpdmVfZGF0ZT1lZmZlY3RpdmVfZGF0ZSwgYW1vdW50PXJldi5yZXZlbnVlX2Ftb3VudCwKICAgICAgICAgICAgc291cmNlPXNvdXJjZSwgY2hhbmdlZF9ieT11c2VyLCAqKm1vbnRocywKICAgICAgICApCiAgICBleGNlcHQgRXhjZXB0aW9uOgogICAgICAgIF9maF9sb2cuZXhjZXB0aW9uKCdyZWNvcmRfcmV2ZW51ZV9oaXN0b3J5IGZhaWxlZCAoc2F2ZSBpdHNlbGYgd2FzIG5vdCBhZmZlY3RlZCknKQogICAgICAgIHJldHVybiBOb25lCgoKIyAtLS0tIFBoYXNlLTIgcmVzb2x2ZXIgKHVudXNlZCB1bnRpbCB0aGUgUCZMIHJld29yazsgc2FmZSB0byBzaGlwIG5vdykuIC0tLS0tLS0tCmRlZiBmaWd1cmVfbW9udGhseV92YWx1ZV9hc19vZihwcm9wLCBraW5kLCBzb3VyY2VfcGssIHllYXIsIG1vbnRoX2lkeCk6CiAgICAiIiJUaGUgbW9udGhseSBmaWd1cmUgaW4gZm9yY2UgZm9yIGBtb250aF9pZHhgICgxLTEyKSBvZiBgeWVhcmA6IHRoZSBsYXRlc3QKICAgIGhpc3Rvcnkgcm93IHdob3NlIGVmZmVjdGl2ZV9kYXRlIGZhbGxzIGluIHRoYXQgbW9udGggb3IgZWFybGllci4gQSBjaGFuZ2UKICAgIGRhdGVkIGFueSBkYXkgaW4gYSBtb250aCBhcHBsaWVzIHRvIHRoYXQgbW9udGggYW5kIGZvcndhcmQuIFJldHVybnMgTm9uZSBpZgogICAgbm8gaGlzdG9yeSBleGlzdHMgKGNhbGxlciBmYWxscyBiYWNrIHRvIHRoZSBsaXZlIHJvdykuIiIiCiAgICBueHQgPSBfZmhfZGF0ZSh5ZWFyICsgMSwgMSwgMSkgaWYgbW9udGhfaWR4ID49IDEyIGVsc2UgX2ZoX2RhdGUoeWVhciwgbW9udGhfaWR4ICsgMSwgMSkKICAgIHJvdyA9IChGaW5hbmNpYWxGaWd1cmVIaXN0b3J5Lm9iamVjdHMKICAgICAgICAgICAuZmlsdGVyKHByb3A9cHJvcCwga2luZD1raW5kLCBzb3VyY2VfcGs9c291cmNlX3BrLCBlZmZlY3RpdmVfZGF0ZV9fbHQ9bnh0KQogICAgICAgICAgIC5vcmRlcl9ieSgnLWVmZmVjdGl2ZV9kYXRlJywgJy1jaGFuZ2VkX2F0JykKICAgICAgICAgICAuZmlyc3QoKSkKICAgIGlmIHJvdyBpcyBOb25lOgogICAgICAgIHJldHVybiBOb25lCiAgICByZXR1cm4gZ2V0YXR0cihyb3csIF9GSF9NT05USFNbbW9udGhfaWR4IC0gMV0pCg==").decode()
SEED_CMD = base64.b64decode("IiIiCnNlZWRfZmluYW5jaWFsX2hpc3Rvcnkg4oCUIGxheSBkb3duIHRoZSBiYXNlbGluZSBoaXN0b3J5IHJvd3MuCgpDcmVhdGVzIE9ORSAnc2VlZCcgaGlzdG9yeSByb3cgZm9yIGV2ZXJ5IGV4aXN0aW5nIGJ1ZGdldGVkIGV4cGVuc2UgYW5kIGV2ZXJ5CmV4aXN0aW5nIGRpcmVjdC9zZWFzb25hbCByZXZlbnVlLCBzdGFtcGVkIHdpdGggYSBiYXNlbGluZSBlZmZlY3RpdmUgZGF0ZSBzbyB0aGUKUCZMIGNhbiByZXNvbHZlIHBhc3QgeWVhcnMgaW1tZWRpYXRlbHkuIElkZW1wb3RlbnQ6IGEgc291cmNlIHJvdyB0aGF0IGFscmVhZHkKaGFzIGEgJ3NlZWQnIHJvdyBpcyBza2lwcGVkLCBzbyByZS1ydW5uaW5nIGlzIHNhZmUuCgpXaHkgdGhlIGRlZmF1bHQgZGF0ZSBpcyAxIEphbiAyMDI0OiB0b2RheSB3ZSBob2xkIG9ubHkgdGhlIENVUlJFTlQgYnVkZ2V0CmZpZ3VyZXMsIHNvIGJvdGggMjAyNCBhbmQgMjAyNSBtdXN0IHJlc29sdmUgdG8gdGhhdCBzYW1lIGJhc2VsaW5lIHVudGlsIHJlYWwKY2hhbmdlcyBhY2N1bXVsYXRlIGdvaW5nIGZvcndhcmQuIFNlZWRpbmcgYXQgdGhlIHN0YXJ0IG9mIDIwMjQgbWFrZXMgdGhlCmltbWVkaWF0ZSAyMDI0LXZzLTIwMjUgY29tcGFyaXNvbiB3b3JrLiBPdmVycmlkZSB3aXRoIC0tZWZmZWN0aXZlIGlmIHlvdSB3YW50IGEKZGlmZmVyZW50IGFuY2hvciwgb3IgaGFuZC1hZGQgYW4gZWFybGllci1kYXRlZCByb3cgbGF0ZXIgdG8gbWFrZSBhIHllYXIgZGlmZmVyLgoKICAgIHB5dGhvbiBtYW5hZ2UucHkgc2VlZF9maW5hbmNpYWxfaGlzdG9yeSAtLWRyeS1ydW4KICAgIHB5dGhvbiBtYW5hZ2UucHkgc2VlZF9maW5hbmNpYWxfaGlzdG9yeQogICAgcHl0aG9uIG1hbmFnZS5weSBzZWVkX2ZpbmFuY2lhbF9oaXN0b3J5IC0tZWZmZWN0aXZlIDIwMjQtMDEtMDEKIiIiCmZyb20gZGF0ZXRpbWUgaW1wb3J0IGRhdGV0aW1lLCBkYXRlCgpmcm9tIGRqYW5nby5jb3JlLm1hbmFnZW1lbnQuYmFzZSBpbXBvcnQgQmFzZUNvbW1hbmQKZnJvbSBkamFuZ28uZGIgaW1wb3J0IHRyYW5zYWN0aW9uCgpmcm9tIHBhZ2VzLm1vZGVscyBpbXBvcnQgKAogICAgZXhwZW5zZSwgcmV2ZW51ZSwKICAgIEZpbmFuY2lhbEZpZ3VyZUhpc3RvcnksCiAgICByZWNvcmRfZXhwZW5zZV9oaXN0b3J5LCByZWNvcmRfcmV2ZW51ZV9oaXN0b3J5LAopCgpNT05USFMgPSBbJ2phbicsICdmZWInLCAnbWFyJywgJ2FwcicsICdtYXknLCAnanVuJywKICAgICAgICAgICdqdWwnLCAnYXVnJywgJ3NlcCcsICdvY3QnLCAnbm92JywgJ2RlYyddCgoKY2xhc3MgQ29tbWFuZChCYXNlQ29tbWFuZCk6CiAgICBoZWxwID0gIlNlZWQgYmFzZWxpbmUgRmluYW5jaWFsRmlndXJlSGlzdG9yeSByb3dzIGZyb20gY3VycmVudCBidWRnZXRlZCBleHBlbnNlcyBhbmQgcmV2ZW51ZS4iCgogICAgZGVmIGFkZF9hcmd1bWVudHMoc2VsZiwgcGFyc2VyKToKICAgICAgICBwYXJzZXIuYWRkX2FyZ3VtZW50KCctLWVmZmVjdGl2ZScsIHR5cGU9c3RyLCBkZWZhdWx0PScyMDI0LTAxLTAxJywKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGhlbHA9J0Jhc2VsaW5lIGVmZmVjdGl2ZSBkYXRlIChZWVlZLU1NLUREKS4gRGVmYXVsdCAyMDI0LTAxLTAxLicpCiAgICAgICAgcGFyc2VyLmFkZF9hcmd1bWVudCgnLS1kcnktcnVuJywgYWN0aW9uPSdzdG9yZV90cnVlJywKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGhlbHA9J1JlcG9ydCB3aGF0IHdvdWxkIGJlIHNlZWRlZDsgd3JpdGUgbm90aGluZy4nKQoKICAgIGRlZiBoYW5kbGUoc2VsZiwgKmFyZ3MsICoqbyk6CiAgICAgICAgdHJ5OgogICAgICAgICAgICBlZmYgPSBkYXRldGltZS5zdHJwdGltZShvWydlZmZlY3RpdmUnXSwgJyVZLSVtLSVkJykuZGF0ZSgpCiAgICAgICAgZXhjZXB0IFZhbHVlRXJyb3I6CiAgICAgICAgICAgIHNlbGYuc3RkZXJyLndyaXRlKCJCYWQgLS1lZmZlY3RpdmUgZGF0ZTsgdXNlIFlZWVktTU0tREQuIikKICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgZHJ5ID0gb1snZHJ5X3J1biddCgogICAgICAgIHNlZWRlZF9leHBfcGtzID0gc2V0KEZpbmFuY2lhbEZpZ3VyZUhpc3Rvcnkub2JqZWN0cwogICAgICAgICAgICAgICAgICAgICAgICAgICAgIC5maWx0ZXIoa2luZD1GaW5hbmNpYWxGaWd1cmVIaXN0b3J5LktJTkRfQlVER0VULCBzb3VyY2U9J3NlZWQnKQogICAgICAgICAgICAgICAgICAgICAgICAgICAgIC52YWx1ZXNfbGlzdCgnc291cmNlX3BrJywgZmxhdD1UcnVlKSkKICAgICAgICBzZWVkZWRfcmV2X3BrcyA9IHNldChGaW5hbmNpYWxGaWd1cmVIaXN0b3J5Lm9iamVjdHMKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAuZmlsdGVyKGtpbmQ9RmluYW5jaWFsRmlndXJlSGlzdG9yeS5LSU5EX1JFVkVOVUUsIHNvdXJjZT0nc2VlZCcpCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgLnZhbHVlc19saXN0KCdzb3VyY2VfcGsnLCBmbGF0PVRydWUpKQoKICAgICAgICBleHBfcm93cyA9IFtlIGZvciBlIGluIGV4cGVuc2Uub2JqZWN0cy5zZWxlY3RfcmVsYXRlZCgncHJvcCcsICdleHBlbnNlX2xpbmVfdHlwZXMnKS5hbGwoKQogICAgICAgICAgICAgICAgICAgIGlmIGUuZXhwZW5zZV9pZCBub3QgaW4gc2VlZGVkX2V4cF9wa3NdCiAgICAgICAgcmV2X3Jvd3MgPSBbciBmb3IgciBpbiByZXZlbnVlLm9iamVjdHMuc2VsZWN0X3JlbGF0ZWQoJ3Byb3AnLCAncmV2ZW51ZV9saW5lX3R5cGVzJykuYWxsKCkKICAgICAgICAgICAgICAgICAgICBpZiByLnJldmVudWVfaWQgbm90IGluIHNlZWRlZF9yZXZfcGtzXQoKICAgICAgICBzZWxmLnN0ZG91dC53cml0ZSgnJykKICAgICAgICBzZWxmLnN0ZG91dC53cml0ZSgnQmFzZWxpbmUgZWZmZWN0aXZlIGRhdGUgOiAlcycgJSBlZmYuaXNvZm9ybWF0KCkpCiAgICAgICAgc2VsZi5zdGRvdXQud3JpdGUoJ0J1ZGdldGVkIGV4cGVuc2VzIHRvIHNlZWQ6ICVkICAoc2tpcHBpbmcgJWQgYWxyZWFkeSBzZWVkZWQpJwogICAgICAgICAgICAgICAgICAgICAgICAgICUgKGxlbihleHBfcm93cyksIGxlbihzZWVkZWRfZXhwX3BrcykpKQogICAgICAgIHNlbGYuc3Rkb3V0LndyaXRlKCdSZXZlbnVlIHJvd3MgdG8gc2VlZCAgICAgOiAlZCAgKHNraXBwaW5nICVkIGFscmVhZHkgc2VlZGVkKScKICAgICAgICAgICAgICAgICAgICAgICAgICAlIChsZW4ocmV2X3Jvd3MpLCBsZW4oc2VlZGVkX3Jldl9wa3MpKSkKCiAgICAgICAgaWYgZHJ5OgogICAgICAgICAgICBmb3IgZSBpbiBleHBfcm93c1s6OF06CiAgICAgICAgICAgICAgICBzZWxmLnN0ZG91dC53cml0ZSgnICAgd291bGQgc2VlZCBFWFAgICUtMjJzICUtMjJzIGFtb3VudD0lcycKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICUgKChlLnByb3AucHJvcF9uYW1lIGlmIGUucHJvcCBlbHNlICc/JylbOjIyXSwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIHN0cihlLmV4cGVuc2VfbGluZV90eXBlcylbOjIyXSwgZS5leHBlbnNlX2Ftb3VudCkpCiAgICAgICAgICAgIGlmIGxlbihleHBfcm93cykgPiA4OgogICAgICAgICAgICAgICAgc2VsZi5zdGRvdXQud3JpdGUoJyAgIC4uLiBhbmQgJWQgbW9yZSBleHBlbnNlcycgJSAobGVuKGV4cF9yb3dzKSAtIDgpKQogICAgICAgICAgICBzZWxmLnN0ZG91dC53cml0ZSgnXG5bZHJ5LXJ1bl0gbm90aGluZyB3cml0dGVuLicpCiAgICAgICAgICAgIHJldHVybgoKICAgICAgICBtYWRlID0gMAogICAgICAgIHdpdGggdHJhbnNhY3Rpb24uYXRvbWljKCk6CiAgICAgICAgICAgIGZvciBlIGluIGV4cF9yb3dzOgogICAgICAgICAgICAgICAgaWYgcmVjb3JkX2V4cGVuc2VfaGlzdG9yeShlLCBlZmYsIHNvdXJjZT0nc2VlZCcsIHVzZXI9Tm9uZSk6CiAgICAgICAgICAgICAgICAgICAgbWFkZSArPSAxCiAgICAgICAgICAgIGZvciByIGluIHJldl9yb3dzOgogICAgICAgICAgICAgICAgaWYgcmVjb3JkX3JldmVudWVfaGlzdG9yeShyLCBlZmYsIHNvdXJjZT0nc2VlZCcsIHVzZXI9Tm9uZSk6CiAgICAgICAgICAgICAgICAgICAgbWFkZSArPSAxCiAgICAgICAgc2VsZi5zdGRvdXQud3JpdGUoc2VsZi5zdHlsZS5TVUNDRVNTKCdEb25lLiAlZCBiYXNlbGluZSBoaXN0b3J5IHJvdyhzKSB3cml0dGVuLicgJSBtYWRlKSkK").decode()

MODELS_MARKER = 'class FinancialFigureHistory('
FINANCE_MARKER = 'record_expense_history'


def read(p):
    with open(p, encoding='utf-8') as f:      # text mode: normalises newlines to \n
        return f.read()


def detect_nl(p):
    with open(p, 'rb') as f:
        raw = f.read()
    return '\r\n' if raw.count(b'\r\n') else '\n'


def write(p, s, nl='\n'):
    with open(p, 'w', encoding='utf-8', newline=nl) as f:
        f.write(s)


def find_py(root, needle):
    for dp, _, files in os.walk(root):
        if '__pycache__' in dp:
            continue
        for fn in sorted(files):
            if fn.endswith('.py'):
                p = os.path.join(dp, fn)
                try:
                    if needle in read(p):
                        return p
                except Exception:
                    pass
    return None


def backup_once(path, nl):
    bak = path + '.bak_finhist'
    if not os.path.exists(bak):
        write(bak, read(path), nl)


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print('!! Run from the project root (the folder with manage.py).')
        sys.exit(1)

    pages = os.path.join(root, 'pages')
    models_py = os.path.join(pages, 'models.py')
    if not os.path.exists(models_py):
        models_py = find_py(pages, 'def project_document_upload_path')
    if not models_py:
        print('!! Could not find pages/models.py. Nothing changed.')
        sys.exit(1)
    finance_py = find_py(pages, 'def finance_expense_commit(')
    if not finance_py:
        print('!! Could not find the finance views file. Nothing changed.')
        sys.exit(1)

    print('models.py : ' + models_py)
    print('finance.py: ' + finance_py + ('   (dry run)' if DRY else ''))
    print('')

    # ---- 1. models.py ----
    mtext = read(models_py)
    if MODELS_MARKER in mtext:
        print('[skip] models.py already has FinancialFigureHistory.')
    else:
        new_mtext = mtext.rstrip('\n') + '\n' + MODELS_BLOCK.lstrip('\n')
        if not new_mtext.endswith('\n'):
            new_mtext += '\n'
        try:
            ast.parse(new_mtext)
        except SyntaxError as e:
            print('!! Appending the model block would break models.py: %s. Nothing changed.' % e)
            sys.exit(1)
        if DRY:
            print('[dry-run] would append FinancialFigureHistory + helpers to models.py.')
        else:
            nl = detect_nl(models_py)
            backup_once(models_py, nl)
            write(models_py, new_mtext, nl)
            print('[OK] models.py updated (backup: models.py.bak_finhist).')

    # ---- 2. finance.py (newline-anchored replacements) ----
    ftext = read(finance_py)
    if FINANCE_MARKER in ftext:
        print('[skip] finance.py already has the history hooks.')
    else:
        work = ftext
        missing = []
        for old_b64, new_b64 in REPL:
            old = base64.b64decode(old_b64).decode()
            new = base64.b64decode(new_b64).decode()
            key = '\n' + old
            if work.count(key) != 1:
                missing.append((work.count(key), old.splitlines()[0][:66]))
                continue
            work = work.replace(key, '\n' + new, 1)
        if missing:
            print('!! finance.py did not match cleanly — these anchors were not found exactly once:')
            for c, head in missing:
                print('     (%d x) %s' % (c, head))
            print('   Nothing changed to finance.py.')
            sys.exit(1)
        try:
            ast.parse(work)
        except SyntaxError as e:
            print('!! Result would not parse: %s. Nothing changed to finance.py.' % e)
            sys.exit(1)
        if DRY:
            print('[dry-run] would extend the import and insert 8 history hooks into finance.py.')
        else:
            nl = detect_nl(finance_py)
            backup_once(finance_py, nl)
            write(finance_py, work, nl)
            print('[OK] finance.py updated (backup: finance.py.bak_finhist).')

    # ---- 3. seed command ----
    cmd_dir = os.path.join(pages, 'management', 'commands')
    cmd_path = os.path.join(cmd_dir, 'seed_financial_history.py')
    if os.path.exists(cmd_path):
        print('[skip] seed_financial_history command already present.')
    elif DRY:
        print('[dry-run] would write ' + cmd_path)
    else:
        os.makedirs(cmd_dir, exist_ok=True)
        for init in (os.path.join(pages, 'management', '__init__.py'),
                     os.path.join(cmd_dir, '__init__.py')):
            if not os.path.exists(init):
                write(init, '')
        write(cmd_path, SEED_CMD)
        print('[OK] wrote ' + cmd_path)

    print('')
    if DRY:
        print('Dry run only — nothing written. Re-run without --dry-run to apply.')
    else:
        print('Phase 1 installed. Next:')
        print('   python manage.py makemigrations pages')
        print('   python manage.py migrate')
        print('   python manage.py seed_financial_history --dry-run')
        print('   python manage.py seed_financial_history')


if __name__ == '__main__':
    main()