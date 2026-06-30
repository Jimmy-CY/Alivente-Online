# ==========================================================================
# apply_tenant_lease_template.ps1
# Step 2 of 2 - Lease End Date column.
#
# Edits: pages\templates\tenant.html  (4 exact-once anchored edits)
#   1. thead - insert "Lease End Date" <th>, rebalance column widths so the
#      Edit/Delete/Report/Agreement columns stop hogging space.
#   2. inner table loop  {% for tresults in tenant %} -> tenant_rows
#      (dropdown keeps using 'tenant', so it stays alphabetical).
#   3. body - insert the Lease End Date <td> after the Active/Status cell.
#   4. <style> - add .lease-end-cell / .lease-end-red / .lease-end-green.
#
# Fail-loud: every anchor must match exactly once or the whole script aborts
# before writing. One .prebak backup is taken up front.
# Run from the repo root AFTER Step 1 has reported clean.
# ==========================================================================

& {
  $ErrorActionPreference = 'Stop'
  [Environment]::CurrentDirectory = (Get-Location).Path

  $path = 'pages\templates\tenant.html'
  if (-not (Test-Path $path)) { throw "File not found: $path  (run from the repo root)" }

  # ---- edit pairs (LF-normalised at match time) ----
  $edits = @(
    @{
      name = '1/4 thead + widths'
      old  = @'
        <tr>
          <th style="text-align: left; width: 35%">Tenant</th>
          <th style="width: 25%">Property</th>
          <th style="width: 12%">Active</th>
          <th style="width: 8%">Edit</th>
          <th style="width: 8%">Delete</th>
          <th style="width: 6%">Report</th>
          <th style="width: 6%">Agreement</th>
        </tr>
'@
      new  = @'
        <tr>
          <th style="text-align: left; width: 26%">Tenant</th>
          <th style="width: 20%">Property</th>
          <th style="width: 10%">Active</th>
          <th style="width: 14%">Lease End Date</th>
          <th style="width: 7.5%">Edit</th>
          <th style="width: 7.5%">Delete</th>
          <th style="width: 7.5%">Report</th>
          <th style="width: 7.5%">Agreement</th>
        </tr>
'@
    },
    @{
      name = '2/4 inner loop -> tenant_rows'
      old  = @'
        {% for results in props %}
          {% for tresults in tenant %}
            {% if tresults.prop_id == results.prop_id %}
'@
      new  = @'
        {% for results in props %}
          {% for tresults in tenant_rows %}
            {% if tresults.prop_id == results.prop_id %}
'@
    },
    @{
      name = '3/4 Lease End Date cell'
      old  = @'
                <td data-label="Status">
                  <span class="status-badge {% if tresults.tenant_current == 'Yes' %}status-active{% else %}status-inactive{% endif %}">
                    {% if tresults.tenant_current == 'Yes' %}Active{% else %}Inactive{% endif %}
                  </span>
                </td>
'@
      new  = @'
                <td data-label="Status">
                  <span class="status-badge {% if tresults.tenant_current == 'Yes' %}status-active{% else %}status-inactive{% endif %}">
                    {% if tresults.tenant_current == 'Yes' %}Active{% else %}Inactive{% endif %}
                  </span>
                </td>
                <td data-label="Lease End Date" class="lease-end-cell {{ tresults.lease_class }}">
                  {% if tresults.tenant_lease_end_date %}{{ tresults.tenant_lease_end_date|date:"d M Y" }}{% else %}&mdash;{% endif %}
                </td>
'@
    },
    @{
      name = '4/4 colour CSS'
      old  = @'
.status-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.status-active { background: #d4edda; color: #155724; }
.status-inactive { background: #f8d7da; color: #721c24; }
'@
      new  = @'
.status-badge { padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
.status-active { background: #d4edda; color: #155724; }
.status-inactive { background: #f8d7da; color: #721c24; }
.lease-end-cell { font-weight: 600; }
.lease-end-red { color: #dc3545; }
.lease-end-green { color: #1e7e34; }
'@
    }
  )

  $text   = [System.IO.File]::ReadAllText($path)
  $textLF = $text -replace "`r`n", "`n"

  # Pass 1: verify EVERY anchor matches exactly once before touching anything.
  foreach ($e in $edits) {
    $oldLF = $e.old -replace "`r`n", "`n"
    $c = ([regex]::Matches($textLF, [regex]::Escape($oldLF))).Count
    if ($c -ne 1) { throw "Anchor '$($e.name)' matched $c time(s) (expected 1). No changes made." }
  }

  # Backup once, then apply all four.
  Copy-Item $path "$path.prebak" -Force
  foreach ($e in $edits) {
    $oldLF = $e.old -replace "`r`n", "`n"
    $newLF = $e.new -replace "`r`n", "`n"
    $textLF = $textLF.Replace($oldLF, $newLF)
    Write-Host "  applied $($e.name)" -ForegroundColor DarkGray
  }

  $out = $textLF -replace "`n", "`r`n"
  [System.IO.File]::WriteAllText($path, $out, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "OK  -> patched $path  (backup: $path.prebak)" -ForegroundColor Green
  Write-Host "Step 2 complete. Hard-refresh the Tenants page to view." -ForegroundColor Green
}