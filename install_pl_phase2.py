#!/usr/bin/env python
"""
install_pl_phase2.py  —  Phase 2: the P&L reads the budgeted-expense / revenue
HISTORY per year, and the old "Budget" dropdown entry becomes a Budget/Actuals
toggle.

Edits three files (all reversible; each backed up once to <file>.bak_phase2):
  1. pages/models.py        : appends resolve_year_months_bulk() (bulk year
                              resolver; one query). Append-only.
  2. pages/views/finance.py : in finance_pl_act — year is now always a real year
                              (default = current year); adds a `view` param
                              (budget|actuals); resolves every revenue/expense
                              row to the figure in force for that year; actuals
                              row + profit-with-actuals gated on view == actuals.
  3. pages/templates/finance_pl_act.html : year-only dropdown, a Budget/Actuals
                              toggle, actuals row/ratios gated on the toggle,
                              drill-down links always carry the year, JS keeps
                              both year and view across property re-selection.

SAFE: idempotent; newline-anchored matching; preserves each file's CRLF/LF;
re-parses the two .py files and aborts writing nothing on any syntax error;
--dry-run. Nothing about how history is RECORDED changes (Phase 1 untouched).

Run from the project root (folder with manage.py):
    python install_pl_phase2.py --dry-run
    python install_pl_phase2.py

No migration is needed (no new DB fields). Test on LOCAL — open the P&L, switch
years and toggle Budget/Actuals — then ship to Live via git the same way as
Phase 1 (commit models.py, finance.py, finance_pl_act.html; push; deploy).
"""
import ast
import base64
import os
import sys

DRY = '--dry-run' in sys.argv

RESOLVER_BLOCK = base64.b64decode("CgojIC0tLS0gUGhhc2UgMjogYnVsayB5ZWFyIHJlc29sdmVyIChvbmUgcXVlcnkpIGZvciB0aGUgUCZMIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tCmRlZiByZXNvbHZlX3llYXJfbW9udGhzX2J1bGsocHJvcF9pZHMsIGtpbmQsIHllYXIpOgogICAgIiIiQnVsayBmb3JtIG9mIGZpZ3VyZV9tb250aGx5X3ZhbHVlX2FzX29mIGZvciBhIHdob2xlIHllYXIuCgogICAgUmV0dXJucyB7c291cmNlX3BrOiBbdl9qYW4sIC4uLiwgdl9kZWNdfSDigJQgZm9yIGVhY2ggc291cmNlIHJvdyBiZWxvbmdpbmcgdG8KICAgIHByb3BfaWRzLCB0aGUgdHdlbHZlIGJ1ZGdldGVkIGZpZ3VyZXMgSU4gRk9SQ0UgZHVyaW5nIGB5ZWFyYCwgcmVzb2x2ZWQgbW9udGgKICAgIGJ5IG1vbnRoIChhIGNoYW5nZSB0YWtlcyBlZmZlY3QgZnJvbSBpdHMgb3duIG1vbnRoIGZvcndhcmQ7IGVhcmxpZXIgbW9udGhzCiAgICBhbmQgZWFybGllciB5ZWFycyBrZWVwIGVhcmxpZXIgdmFsdWVzKS4gT25lIERCIHF1ZXJ5LiBBIHNvdXJjZSB3aXRoIG5vCiAgICBoaXN0b3J5IGlzIHNpbXBseSBhYnNlbnQgZnJvbSB0aGUgZGljdCwgc28gdGhlIGNhbGxlciBrZWVwcyBpdHMgbGl2ZSBjZWxscy4KICAgICIiIgogICAgZnJvbSBjb2xsZWN0aW9ucyBpbXBvcnQgZGVmYXVsdGRpY3QKICAgIHJvd3MgPSAoRmluYW5jaWFsRmlndXJlSGlzdG9yeS5vYmplY3RzCiAgICAgICAgICAgIC5maWx0ZXIocHJvcF9pZF9faW49bGlzdChwcm9wX2lkcyksIGtpbmQ9a2luZCwKICAgICAgICAgICAgICAgICAgICBlZmZlY3RpdmVfZGF0ZV9fbHRlPV9maF9kYXRlKHllYXIsIDEyLCAzMSkpCiAgICAgICAgICAgIC5vcmRlcl9ieSgnc291cmNlX3BrJywgJ2VmZmVjdGl2ZV9kYXRlJywgJ2NoYW5nZWRfYXQnKSkKICAgIGJ5X3NyYyA9IGRlZmF1bHRkaWN0KGxpc3QpCiAgICBmb3IgciBpbiByb3dzOgogICAgICAgIGJ5X3NyY1tyLnNvdXJjZV9wa10uYXBwZW5kKHIpCiAgICBvdXQgPSB7fQogICAgZm9yIHNyYywgdmVyc2lvbnMgaW4gYnlfc3JjLml0ZW1zKCk6CiAgICAgICAgdmFscyA9IFtdCiAgICAgICAgZm9yIG0gaW4gcmFuZ2UoMSwgMTMpOgogICAgICAgICAgICBjaG9zZW4gPSBOb25lCiAgICAgICAgICAgIGZvciB2IGluIHZlcnNpb25zOiAgICAgICAgICAgICAgIyBhc2NlbmRpbmcgYnkgZWZmZWN0aXZlX2RhdGUKICAgICAgICAgICAgICAgIGlmICh2LmVmZmVjdGl2ZV9kYXRlLnllYXIsIHYuZWZmZWN0aXZlX2RhdGUubW9udGgpIDw9ICh5ZWFyLCBtKToKICAgICAgICAgICAgICAgICAgICBjaG9zZW4gPSB2CiAgICAgICAgICAgICAgICBlbHNlOgogICAgICAgICAgICAgICAgICAgIGJyZWFrCiAgICAgICAgICAgIHZhbHMuYXBwZW5kKGdldGF0dHIoY2hvc2VuLCBfRkhfTU9OVEhTW20gLSAxXSkgaWYgY2hvc2VuIGlzIG5vdCBOb25lIGVsc2UgTm9uZSkKICAgICAgICBvdXRbc3JjXSA9IHZhbHMKICAgIHJldHVybiBvdXQK").decode()
FIN = [['ICAgIEZpbmFuY2lhbEZpZ3VyZUhpc3RvcnksIHJlY29yZF9leHBlbnNlX2hpc3RvcnksIHJlY29yZF9yZXZlbnVlX2hpc3Rvcnks', 'ICAgIEZpbmFuY2lhbEZpZ3VyZUhpc3RvcnksIHJlY29yZF9leHBlbnNlX2hpc3RvcnksIHJlY29yZF9yZXZlbnVlX2hpc3RvcnksCiAgICByZXNvbHZlX3llYXJfbW9udGhzX2J1bGss'], ['ICAgICMgR2V0IHNlbGVjdGVkIHllYXIgZnJvbSByZXF1ZXN0IChkZWZhdWx0IHRvICdidWRnZXQnKQogICAgc2VsZWN0ZWRfeWVhciA9IHJlcXVlc3QuR0VULmdldCgneWVhcicsICdidWRnZXQnKQoKICAgICMgR2V0IHNlbGVjdGVkIHByb3BlcnRpZXMgZnJvbSByZXF1ZXN0CiAgICBzZWxlY3RlZF9wcm9wZXJ0aWVzID0gcmVxdWVzdC5HRVQuZ2V0bGlzdCgncHJvcGVydGllcycpCgogICAgIyBIYW5kbGUgeWVhciBwYXJhbWV0ZXIgLSBjYW4gYmUgJ2J1ZGdldCcgb3IgYSB5ZWFyIG51bWJlcgogICAgaWYgc2VsZWN0ZWRfeWVhciAhPSAnYnVkZ2V0JzoKICAgICAgICB0cnk6CiAgICAgICAgICAgIHNlbGVjdGVkX3llYXIgPSBpbnQoc2VsZWN0ZWRfeWVhcikKICAgICAgICAgICAgIyBFbnN1cmUgb25seSAyMDI0LCAyMDI1LCBvciAyMDI2IGlzIHNlbGVjdGFibGUKICAgICAgICAgICAgaWYgc2VsZWN0ZWRfeWVhciBub3QgaW4gWzIwMjQsIDIwMjUsIDIwMjZdOgogICAgICAgICAgICAgICAgc2VsZWN0ZWRfeWVhciA9ICdidWRnZXQnCiAgICAgICAgZXhjZXB0IChWYWx1ZUVycm9yLCBUeXBlRXJyb3IpOgogICAgICAgICAgICBzZWxlY3RlZF95ZWFyID0gJ2J1ZGdldCc=', 'ICAgICMgUGhhc2UgMjogdGhlIFAmTCBpcyBhbHdheXMgdmlld2VkIEZPUiBBIFlFQVIgbm93LiBUaGUgb2xkICJCdWRnZXQiIGRyb3Bkb3duCiAgICAjIGVudHJ5IGlzIHJlcGxhY2VkIGJ5IGEgQnVkZ2V0L0FjdHVhbHMgdG9nZ2xlIChgdmlld2ApOiAnYnVkZ2V0JyBzaG93cyB0aGUKICAgICMgYnVkZ2V0ZWQgcmV2ZW51ZS9leHBlbnNlcyBmb3IgdGhlIHllYXI7ICdhY3R1YWxzJyBhbHNvIGFkZHMgdGhhdCB5ZWFyJ3MKICAgICMgYWN0dWFsIGV4cGVuc2VzLiBCdWRnZXRlZCBmaWd1cmVzIGFyZSByZXNvbHZlZCBmcm9tIGhpc3RvcnkgcGVyIHllYXIuCiAgICBBVkFJTEFCTEVfWUVBUlMgPSBbMjAyNiwgMjAyNSwgMjAyNF0KCiAgICB2aWV3X21vZGUgPSByZXF1ZXN0LkdFVC5nZXQoJ3ZpZXcnLCAnYnVkZ2V0JykKICAgIGlmIHZpZXdfbW9kZSBub3QgaW4gKCdidWRnZXQnLCAnYWN0dWFscycpOgogICAgICAgIHZpZXdfbW9kZSA9ICdidWRnZXQnCgogICAgIyBHZXQgc2VsZWN0ZWQgcHJvcGVydGllcyBmcm9tIHJlcXVlc3QKICAgIHNlbGVjdGVkX3Byb3BlcnRpZXMgPSByZXF1ZXN0LkdFVC5nZXRsaXN0KCdwcm9wZXJ0aWVzJykKCiAgICAjIFllYXI6IGRlZmF1bHQgdG8gdGhlIGN1cnJlbnQgeWVhciwgZmFsbGluZyBiYWNrIHRvIHRoZSBuZXdlc3QgYXZhaWxhYmxlLgogICAgdHJ5OgogICAgICAgIHNlbGVjdGVkX3llYXIgPSBpbnQocmVxdWVzdC5HRVQuZ2V0KCd5ZWFyJykpCiAgICBleGNlcHQgKFR5cGVFcnJvciwgVmFsdWVFcnJvcik6CiAgICAgICAgc2VsZWN0ZWRfeWVhciA9IGRhdGUudG9kYXkoKS55ZWFyCiAgICBpZiBzZWxlY3RlZF95ZWFyIG5vdCBpbiBBVkFJTEFCTEVfWUVBUlM6CiAgICAgICAgc2VsZWN0ZWRfeWVhciA9IGRhdGUudG9kYXkoKS55ZWFyIGlmIGRhdGUudG9kYXkoKS55ZWFyIGluIEFWQUlMQUJMRV9ZRUFSUyBlbHNlIEFWQUlMQUJMRV9ZRUFSU1swXQ=='], ['ICAgIGZvciBwcm9wIGluIHByb3BlcnRpZXM6CiAgICAgICAgcmV2ZW51ZXMuZXh0ZW5kKHByb3AucmV2ZW51ZV9zZXQuYWxsKCkpCiAgICAgICAgZXhwZW5zZXMuZXh0ZW5kKHByb3AuZXhwZW5zZV9zZXQuYWxsKCkpCgogICAgIyA9PT09PT09PT0gUkVWRU5VRSBTRUNUSU9OID09PT09PT09PQ==', 'ICAgIGZvciBwcm9wIGluIHByb3BlcnRpZXM6CiAgICAgICAgcmV2ZW51ZXMuZXh0ZW5kKHByb3AucmV2ZW51ZV9zZXQuYWxsKCkpCiAgICAgICAgZXhwZW5zZXMuZXh0ZW5kKHByb3AuZXhwZW5zZV9zZXQuYWxsKCkpCgogICAgIyBQaGFzZSAyOiByZXNvbHZlIGV2ZXJ5IHJldmVudWUvZXhwZW5zZSByb3cgdG8gdGhlIGJ1ZGdldGVkIGZpZ3VyZSBpbiBmb3JjZQogICAgIyBkdXJpbmcgdGhlIHNlbGVjdGVkIHllYXIgKG1vbnRoIGJ5IG1vbnRoKSBieSBvdmVyd3JpdGluZyB0aGUgaW4tbWVtb3J5CiAgICAjIG1vbnRobHkgY2VsbHMuIEV2ZXJ5IHN1bSBiZWxvdyB0aGVuIHJlYWRzIHllYXItY29ycmVjdCBudW1iZXJzIHdpdGggbm8KICAgICMgZnVydGhlciBjaGFuZ2UuIFJvd3Mgd2l0aCBubyBoaXN0b3J5IGtlZXAgdGhlaXIgbGl2ZSBjZWxscy4KICAgIF9maF9leHBfbWFwID0gcmVzb2x2ZV95ZWFyX21vbnRoc19idWxrKHNlbGVjdGVkX3Byb3BfaWRzLCBGaW5hbmNpYWxGaWd1cmVIaXN0b3J5LktJTkRfQlVER0VULCBzZWxlY3RlZF95ZWFyKQogICAgZm9yIF9lIGluIGV4cGVuc2VzOgogICAgICAgIF92YWxzID0gX2ZoX2V4cF9tYXAuZ2V0KF9lLmV4cGVuc2VfaWQpCiAgICAgICAgaWYgX3ZhbHMgaXMgbm90IE5vbmU6CiAgICAgICAgICAgIGZvciBfaSwgX20gaW4gZW51bWVyYXRlKE1PTlRIUyk6CiAgICAgICAgICAgICAgICBzZXRhdHRyKF9lLCAnZXhwZW5zZV8nICsgX20sIF92YWxzW19pXSkKICAgIF9maF9yZXZfbWFwID0gcmVzb2x2ZV95ZWFyX21vbnRoc19idWxrKHNlbGVjdGVkX3Byb3BfaWRzLCBGaW5hbmNpYWxGaWd1cmVIaXN0b3J5LktJTkRfUkVWRU5VRSwgc2VsZWN0ZWRfeWVhcikKICAgIGZvciBfciBpbiByZXZlbnVlczoKICAgICAgICBfdmFscyA9IF9maF9yZXZfbWFwLmdldChfci5yZXZlbnVlX2lkKQogICAgICAgIGlmIF92YWxzIGlzIG5vdCBOb25lOgogICAgICAgICAgICBmb3IgX2ksIF9tIGluIGVudW1lcmF0ZShNT05USFMpOgogICAgICAgICAgICAgICAgc2V0YXR0cihfciwgJ3JldmVudWVfJyArIF9tLCBfdmFsc1tfaV0pCgogICAgIyA9PT09PT09PT0gUkVWRU5VRSBTRUNUSU9OID09PT09PT09PQ=='], ['ICAgIGlmIHNlbGVjdGVkX3llYXIgIT0gJ2J1ZGdldCc6CiAgICAgICAgIyBTaW5nbGUgcXVlcnkgdG8gZ2V0IGFsbCBhY3R1YWwgZXhwZW5zZXMgd2l0aCBtb250aCBncm91cGluZw==', 'ICAgIGlmIHZpZXdfbW9kZSA9PSAnYWN0dWFscyc6CiAgICAgICAgIyBTaW5nbGUgcXVlcnkgdG8gZ2V0IGFsbCBhY3R1YWwgZXhwZW5zZXMgd2l0aCBtb250aCBncm91cGluZw=='], ['ICAgICMgPT09PT09PT09IFBST0ZJVCBDQUxDVUxBVElPTiA9PT09PT09PT0KICAgIGlmIHNlbGVjdGVkX3llYXIgPT0gJ2J1ZGdldCc6', 'ICAgICMgPT09PT09PT09IFBST0ZJVCBDQUxDVUxBVElPTiA9PT09PT09PT0KICAgIGlmIHZpZXdfbW9kZSA9PSAnYnVkZ2V0Jzo='], ['ICAgICAgICAnc2VsZWN0ZWRfeWVhcic6IHNlbGVjdGVkX3llYXIsCiAgICAgICAgJ3NlbGVjdGVkX3Byb3BlcnRpZXMnOiBzZWxlY3RlZF9wcm9wZXJ0aWVzLAogICAgICAgICdhdmFpbGFibGVfeWVhcnMnOiBbMjAyNiwgMjAyNSwgMjAyNF0sCiAgICB9KQ==', 'ICAgICAgICAnc2VsZWN0ZWRfeWVhcic6IHNlbGVjdGVkX3llYXIsCiAgICAgICAgJ3ZpZXdfbW9kZSc6IHZpZXdfbW9kZSwKICAgICAgICAnY3VycmVudF95ZWFyJzogZGF0ZS50b2RheSgpLnllYXIsCiAgICAgICAgJ3NlbGVjdGVkX3Byb3BlcnRpZXMnOiBzZWxlY3RlZF9wcm9wZXJ0aWVzLAogICAgICAgICdhdmFpbGFibGVfeWVhcnMnOiBBVkFJTEFCTEVfWUVBUlMsCiAgICB9KQ==']]
TPL = [['ICAgICAgICAgICAgeyUgaWYgc2VsZWN0ZWRfeWVhciA9PSAnYnVkZ2V0JyAlfUJ1ZGdldHslIGVsc2UgJX17eyBzZWxlY3RlZF95ZWFyIH19eyUgZW5kaWYgJX0=', 'ICAgICAgICAgICAge3sgc2VsZWN0ZWRfeWVhciB9fQ==', 1], ['ICAgICAgICAgICAgPGEgY2xhc3M9ImRyb3Bkb3duLWl0ZW0geyUgaWYgc2VsZWN0ZWRfeWVhciA9PSAnYnVkZ2V0JyAlfWFjdGl2ZXslIGVuZGlmICV9IgogICAgICAgICAgICAgICBocmVmPSI/eWVhcj1idWRnZXR7JSBpZiBzZWxlY3RlZF9wcm9wZXJ0aWVzICV9JnslIGZvciBwcm9wX2lkIGluIHNlbGVjdGVkX3Byb3BlcnRpZXMgJX1wcm9wZXJ0aWVzPXt7IHByb3BfaWQgfX17JSBpZiBub3QgZm9ybG9vcC5sYXN0ICV9JnslIGVuZGlmICV9eyUgZW5kZm9yICV9eyUgZW5kaWYgJX0iPgogICAgICAgICAgICAgICAgQnVkZ2V0CiAgICAgICAgICAgIDwvYT4KICAgICAgICAgICAgeyUgZm9yIHllYXIgaW4gYXZhaWxhYmxlX3llYXJzICV9CiAgICAgICAgICAgICAgICA8YSBjbGFzcz0iZHJvcGRvd24taXRlbSB7JSBpZiB5ZWFyID09IHNlbGVjdGVkX3llYXIgJX1hY3RpdmV7JSBlbmRpZiAlfSIKICAgICAgICAgICAgICAgICAgIGhyZWY9Ij95ZWFyPXt7IHllYXIgfX17JSBpZiBzZWxlY3RlZF9wcm9wZXJ0aWVzICV9JnslIGZvciBwcm9wX2lkIGluIHNlbGVjdGVkX3Byb3BlcnRpZXMgJX1wcm9wZXJ0aWVzPXt7IHByb3BfaWQgfX17JSBpZiBub3QgZm9ybG9vcC5sYXN0ICV9JnslIGVuZGlmICV9eyUgZW5kZm9yICV9eyUgZW5kaWYgJX0iPgogICAgICAgICAgICAgICAgICAgIHt7IHllYXIgfX0KICAgICAgICAgICAgICAgIDwvYT4KICAgICAgICAgICAgeyUgZW5kZm9yICV9', 'ICAgICAgICAgICAgeyUgZm9yIHllYXIgaW4gYXZhaWxhYmxlX3llYXJzICV9CiAgICAgICAgICAgICAgICA8YSBjbGFzcz0iZHJvcGRvd24taXRlbSB7JSBpZiB5ZWFyID09IHNlbGVjdGVkX3llYXIgJX1hY3RpdmV7JSBlbmRpZiAlfSIKICAgICAgICAgICAgICAgICAgIGhyZWY9Ij95ZWFyPXt7IHllYXIgfX0mdmlldz17eyB2aWV3X21vZGUgfX17JSBpZiBzZWxlY3RlZF9wcm9wZXJ0aWVzICV9JnslIGZvciBwcm9wX2lkIGluIHNlbGVjdGVkX3Byb3BlcnRpZXMgJX1wcm9wZXJ0aWVzPXt7IHByb3BfaWQgfX17JSBpZiBub3QgZm9ybG9vcC5sYXN0ICV9JnslIGVuZGlmICV9eyUgZW5kZm9yICV9eyUgZW5kaWYgJX0iPgogICAgICAgICAgICAgICAgICAgIHt7IHllYXIgfX0KICAgICAgICAgICAgICAgIDwvYT4KICAgICAgICAgICAgeyUgZW5kZm9yICV9', 1], ['ICAgIDwvZGl2PgoKICAgIDwhLS0gSGVscCBidXR0b24gLS0+CiAgICA8YnV0dG9uIHR5cGU9ImJ1dHRvbiIgY2xhc3M9ImJ0biBidG4taW5mbyBwbC1oZWxwLWJ0biIgZGF0YS10b2dnbGU9Im1vZGFsIiBkYXRhLXRhcmdldD0iI2ZpbmFuY2VfcGxfYWN0SGVscE1vZGFsIj4=', 'ICAgIDwvZGl2PgoKICAgIDwhLS0gQnVkZ2V0IC8gQWN0dWFscyB0b2dnbGUgLS0+CiAgICA8ZGl2IGNsYXNzPSJidG4tZ3JvdXAgcGwtdmlldy10b2dnbGUiIHJvbGU9Imdyb3VwIiBhcmlhLWxhYmVsPSJCdWRnZXQgb3IgQWN0dWFscyI+CiAgICAgICAgPGEgY2xhc3M9ImJ0biB7JSBpZiB2aWV3X21vZGUgPT0gJ2J1ZGdldCcgJX1idG4taW5mb3slIGVsc2UgJX1idG4tb3V0bGluZS1pbmZveyUgZW5kaWYgJX0iCiAgICAgICAgICAgaHJlZj0iP3llYXI9e3sgc2VsZWN0ZWRfeWVhciB9fSZ2aWV3PWJ1ZGdldHslIGlmIHNlbGVjdGVkX3Byb3BlcnRpZXMgJX0meyUgZm9yIHByb3BfaWQgaW4gc2VsZWN0ZWRfcHJvcGVydGllcyAlfXByb3BlcnRpZXM9e3sgcHJvcF9pZCB9fXslIGlmIG5vdCBmb3Jsb29wLmxhc3QgJX0meyUgZW5kaWYgJX17JSBlbmRmb3IgJX17JSBlbmRpZiAlfSI+CiAgICAgICAgICAgIEJ1ZGdldAogICAgICAgIDwvYT4KICAgICAgICA8YSBjbGFzcz0iYnRuIHslIGlmIHZpZXdfbW9kZSA9PSAnYWN0dWFscycgJX1idG4taW5mb3slIGVsc2UgJX1idG4tb3V0bGluZS1pbmZveyUgZW5kaWYgJX0iCiAgICAgICAgICAgaHJlZj0iP3llYXI9e3sgc2VsZWN0ZWRfeWVhciB9fSZ2aWV3PWFjdHVhbHN7JSBpZiBzZWxlY3RlZF9wcm9wZXJ0aWVzICV9JnslIGZvciBwcm9wX2lkIGluIHNlbGVjdGVkX3Byb3BlcnRpZXMgJX1wcm9wZXJ0aWVzPXt7IHByb3BfaWQgfX17JSBpZiBub3QgZm9ybG9vcC5sYXN0ICV9JnslIGVuZGlmICV9eyUgZW5kZm9yICV9eyUgZW5kaWYgJX0iPgogICAgICAgICAgICBBY3R1YWxzCiAgICAgICAgPC9hPgogICAgPC9kaXY+CgogICAgPCEtLSBIZWxwIGJ1dHRvbiAtLT4KICAgIDxidXR0b24gdHlwZT0iYnV0dG9uIiBjbGFzcz0iYnRuIGJ0bi1pbmZvIHBsLWhlbHAtYnRuIiBkYXRhLXRvZ2dsZT0ibW9kYWwiIGRhdGEtdGFyZ2V0PSIjZmluYW5jZV9wbF9hY3RIZWxwTW9kYWwiPg==', 1], ['ICAgICAgICAgICAgICAgIHslIGlmIHNlbGVjdGVkX3llYXIgIT0gJ2J1ZGdldCcgYW5kIGFjdHVhbF9leHBlbnNlX3RvdGFscy55ZWFyID4gMCAlfQ==', 'ICAgICAgICAgICAgICAgIHslIGlmIHZpZXdfbW9kZSA9PSAnYWN0dWFscycgYW5kIGFjdHVhbF9leHBlbnNlX3RvdGFscy55ZWFyID4gMCAlfQ==', 1], ['eyUgaWYgc2VsZWN0ZWRfeWVhciAhPSAnYnVkZ2V0JyAlfXllYXI9e3sgc2VsZWN0ZWRfeWVhcnxmbG9hdGZvcm1hdDonMCcgfX0meyUgZW5kaWYgJX0=', 'eWVhcj17eyBzZWxlY3RlZF95ZWFyfGZsb2F0Zm9ybWF0OicwJyB9fSY=', -1], ['c2VsZWN0ZWRfeWVhciAhPSAnYnVkZ2V0Jw==', 'dmlld19tb2RlID09ICdhY3R1YWxzJw==', -1], ['ICAgICAgICB1cmxQYXJhbXMuc2V0KCd5ZWFyJywgJ3slIGlmIHNlbGVjdGVkX3llYXIgJX17eyBzZWxlY3RlZF95ZWFyIH19eyUgZWxzZSAlfWJ1ZGdldHslIGVuZGlmICV9Jyk7CiAgICAgICAgdXJsUGFyYW1zLnNldCgnc2VsZWN0aW9uX21hZGUnLCAndHJ1ZScpOw==', 'ICAgICAgICB1cmxQYXJhbXMuc2V0KCd5ZWFyJywgJ3t7IHNlbGVjdGVkX3llYXIgfX0nKTsKICAgICAgICB1cmxQYXJhbXMuc2V0KCd2aWV3JywgJ3t7IHZpZXdfbW9kZSB9fScpOwogICAgICAgIHVybFBhcmFtcy5zZXQoJ3NlbGVjdGlvbl9tYWRlJywgJ3RydWUnKTs=', 1]]

MODELS_MARKER = 'def resolve_year_months_bulk('
FINANCE_MARKER = "view_mode = request.GET.get('view'"
TEMPLATE_MARKER = 'pl-view-toggle'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def detect_nl(p):
    with open(p, 'rb') as f:
        return '\r\n' if f.read().count(b'\r\n') else '\n'


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
    bak = path + '.bak_phase2'
    if not os.path.exists(bak):
        write(bak, read(path), nl)


def apply_newline_anchored(text, old, new, label):
    key = '\n' + old
    c = text.count(key)
    if c != 1:
        return None, '(%d x) %s' % (c, old.splitlines()[0][:64])
    return text.replace(key, '\n' + new, 1), None


def main():
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, 'manage.py')):
        print('!! Run from the project root (the folder with manage.py).')
        sys.exit(1)
    pages = os.path.join(root, 'pages')

    models_py = os.path.join(pages, 'models.py')
    if not os.path.exists(models_py):
        models_py = find_py(pages, 'class FinancialFigureHistory(')
    finance_py = find_py(pages, 'def finance_pl_act(')
    template = os.path.join(pages, 'templates', 'finance_pl_act.html')
    for label, path in [('models.py', models_py), ('finance.py', finance_py), ('template', template)]:
        if not path or not os.path.exists(path):
            print('!! Could not find %s. Nothing changed.' % label)
            sys.exit(1)

    print('models.py : ' + models_py)
    print('finance.py: ' + finance_py)
    print('template  : ' + template + ('   (dry run)' if DRY else ''))
    print('')

    # ---- 1. models.py : append resolver ----
    mtext = read(models_py)
    if MODELS_MARKER in mtext:
        print('[skip] models.py already has resolve_year_months_bulk.')
    else:
        new_mtext = mtext.rstrip('\n') + '\n' + RESOLVER_BLOCK.lstrip('\n')
        if not new_mtext.endswith('\n'):
            new_mtext += '\n'
        try:
            ast.parse(new_mtext)
        except SyntaxError as e:
            print('!! Appending resolver would break models.py: %s. Nothing changed.' % e)
            sys.exit(1)
        if DRY:
            print('[dry-run] would append resolve_year_months_bulk to models.py.')
        else:
            nl = detect_nl(models_py); backup_once(models_py, nl); write(models_py, new_mtext, nl)
            print('[OK] models.py updated (backup: models.py.bak_phase2).')

    # ---- 2. finance.py : the 6 view edits ----
    ftext = read(finance_py)
    if FINANCE_MARKER in ftext:
        print('[skip] finance.py finance_pl_act already Phase-2.')
    else:
        work = ftext; miss = []
        for ob, nb in FIN:
            old = base64.b64decode(ob).decode(); new = base64.b64decode(nb).decode()
            work2, err = apply_newline_anchored(work, old, new, 'fin')
            if err: miss.append(err)
            else: work = work2
        if miss:
            print('!! finance.py did not match cleanly:')
            for m in miss: print('     ' + m)
            print('   Nothing changed to finance.py.'); sys.exit(1)
        try:
            ast.parse(work)
        except SyntaxError as e:
            print('!! finance.py result would not parse: %s. Nothing changed.' % e); sys.exit(1)
        if DRY:
            print('[dry-run] would apply %d edits to finance_pl_act.' % len(FIN))
        else:
            nl = detect_nl(finance_py); backup_once(finance_py, nl); write(finance_py, work, nl)
            print('[OK] finance.py updated (backup: finance.py.bak_phase2).')

    # ---- 3. template ----
    ttext = read(template)
    if TEMPLATE_MARKER in ttext:
        print('[skip] finance_pl_act.html already has the Budget/Actuals toggle.')
    else:
        work = ttext; miss = []
        for ob, nb, n in TPL:
            old = base64.b64decode(ob).decode(); new = base64.b64decode(nb).decode()
            if n == -1:
                if work.count(old) < 1:
                    miss.append('(0 x replace-all) ' + old[:60].replace('\n', ' '))
                else:
                    work = work.replace(old, new)
            else:
                work2, err = apply_newline_anchored(work, old, new, 'tpl')
                if err: miss.append(err)
                else: work = work2
        if miss:
            print('!! finance_pl_act.html did not match cleanly:')
            for m in miss: print('     ' + m)
            print('   Nothing changed to the template.'); sys.exit(1)
        # balance sanity
        import re
        if len(re.findall(r'{%\s*if\b', work)) != len(re.findall(r'{%\s*endif\s*%}', work)):
            print('!! template if/endif unbalanced after edit — aborting, nothing written.'); sys.exit(1)
        if DRY:
            print('[dry-run] would apply %d edit-rules to finance_pl_act.html.' % len(TPL))
        else:
            nl = detect_nl(template); backup_once(template, nl); write(template, work, nl)
            print('[OK] finance_pl_act.html updated (backup: finance_pl_act.html.bak_phase2).')

    print('')
    if DRY:
        print('Dry run only — nothing written.')
    else:
        print('Phase 2 installed. No migration needed. Restart the dev server and open the P&L:')
        print('  - pick a year (2024/2025/2026); budgeted figures now reflect that year')
        print('  - toggle Budget / Actuals to show/hide that year\'s actual expenses')


if __name__ == '__main__':
    main()