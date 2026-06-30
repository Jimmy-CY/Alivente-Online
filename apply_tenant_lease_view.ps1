# ==========================================================================
# apply_tenant_lease_view.ps1
# Step 1 of 2 - Lease End Date column.
#
# Edits: pages\views\tenants.py
#   - Adds a `today` + `tenant_rows` block to tenant_page() that orders the
#     filtered tenants by lease end date DESC (newest first) within each
#     property group and attaches a `lease_class` colour to each row.
#   - Adds 'tenant_rows' to the render context (leaves 'tenant' untouched,
#     so the Tenant filter dropdown stays alphabetical).
#
# Fail-loud: exact-once anchor, .prebak backup, ast.parse + manage.py check.
# Run from the repo root:  C:\users\demet\...\alivente-online
# ==========================================================================

& {
  $ErrorActionPreference = 'Stop'
  [Environment]::CurrentDirectory = (Get-Location).Path

  $path = 'pages\views\tenants.py'
  if (-not (Test-Path $path)) { throw "File not found: $path  (run from the repo root)" }

  $old = @'
    # Pass filter values back to template for form persistence
    context = {
        'tenant': filtered_tenants,
        'props': filtered_properties,
'@

  $new = @'
    # Build the table rows: secondary sort by lease end date (newest first,
    # oldest last) WITHIN each property group, and attach a colour class for
    # the new Lease End Date column.
    #   - Inactive tenant       -> red  (regardless of the date)
    #   - Active, end < today   -> red  (lease has passed)
    #   - Active, end >= today  -> green (today still counts as valid)
    #   - No end date           -> no colour
    # The property grouping itself is driven by the template's outer props
    # loop, so this ordering only sequences tenants inside each group.
    today = datetime.now().date()
    tenant_rows = list(
        filtered_tenants.order_by('-tenant_lease_end_date', 'tenant_name')
    )
    for _t in tenant_rows:
        _end = _t.tenant_lease_end_date
        if _t.tenant_current != 'Yes':
            _t.lease_class = 'lease-end-red'
        elif _end and _end < today:
            _t.lease_class = 'lease-end-red'
        elif _end:
            _t.lease_class = 'lease-end-green'
        else:
            _t.lease_class = ''

    # Pass filter values back to template for form persistence
    context = {
        'tenant': filtered_tenants,
        'tenant_rows': tenant_rows,
        'props': filtered_properties,
'@

  # Normalise CR/LF on both sides so a CRLF source file matches an LF anchor.
  $text   = [System.IO.File]::ReadAllText($path)
  $textLF = $text -replace "`r`n", "`n"
  $oldLF  = $old  -replace "`r`n", "`n"
  $newLF  = $new  -replace "`r`n", "`n"

  $count = ([regex]::Matches($textLF, [regex]::Escape($oldLF))).Count
  if ($count -ne 1) { throw "Anchor matched $count time(s) (expected exactly 1). No changes made." }

  # Backup, replace, restore CRLF, write UTF-8 (no BOM).
  Copy-Item $path "$path.prebak" -Force
  $outLF = $textLF.Replace($oldLF, $newLF)
  $out   = $outLF -replace "`n", "`r`n"
  [System.IO.File]::WriteAllText($path, $out, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "OK  -> patched $path  (backup: $path.prebak)" -ForegroundColor Green

  # Validate Python syntax, then Django system check.
  & python -c "import ast,sys; ast.parse(open(r'$path',encoding='utf-8').read()); print('ast.parse OK')"
  if ($LASTEXITCODE -ne 0) { throw "ast.parse FAILED - restore from $path.prebak" }
  & python manage.py check
  if ($LASTEXITCODE -ne 0) { throw "manage.py check FAILED - restore from $path.prebak" }

  Write-Host "Step 1 complete. Proceed to Step 2 (template)." -ForegroundColor Green
}