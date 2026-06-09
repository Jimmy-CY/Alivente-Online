# fix_fraction_map.ps1
# Repairs the mojibake in pages/models.py fraction_map literals.
# Idempotent: safe to run twice. Transactional: restores on any failure.

& {
    try {
        $ErrorActionPreference = 'Stop'

        # --- 1. Locate file & sync .NET CWD ---
        $path = "pages\models.py"
        if (-not (Test-Path $path)) {
            throw "Cannot find $path. Run from the alivente-online project root."
        }
        [Environment]::CurrentDirectory = (Get-Location).Path
        $fullPath = (Resolve-Path $path).Path

        # --- 2. Backup ---
        $backup = "$fullPath.prebak"
        Copy-Item $fullPath $backup -Force
        Write-Host "Backup: $backup"

        # --- 3. Read original ---
        $content    = [System.IO.File]::ReadAllText($fullPath)
        $origLength = $content.Length
        $origLines  = ($content -split "`r`n|`n").Count
        Write-Host "Original: $origLength bytes, $origLines lines"

        # --- 4. Build replacement block (ASCII-only: \u escapes survive any editor) ---
        $newBlock = @"
        fraction_map = {
            0.125: '\u215B',  # one-eighth
            0.25:  '\u00BC',  # one-quarter
            0.333: '\u2153',  # one-third
            0.375: '\u215C',  # three-eighths
            0.5:   '\u00BD',  # one-half
            0.625: '\u215D',  # five-eighths
            0.666: '\u2154',  # two-thirds
            0.75:  '\u00BE',  # three-quarters
            0.875: '\u215E',  # seven-eighths
        }
"@
        # Normalize replacement to CRLF to match Windows source convention
        $newBlock = ($newBlock -replace "`r`n", "`n") -replace "`n", "`r`n"

        # --- 5. Locate the dict block & verify uniqueness ---
        $pattern    = '(?ms)^( *)fraction_map\s*=\s*\{[^}]*\}'
        $dictHits   = [regex]::Matches($content, $pattern)
        if ($dictHits.Count -ne 1) {
            throw "Expected exactly 1 fraction_map dict; found $($dictHits.Count). Aborting (no changes written)."
        }
        Write-Host "fraction_map block found (1 match, good)."

        # --- 6. Replace ---
        $newContent = [regex]::Replace($content, $pattern, $newBlock)

        # --- 7. Strip BOM if present (audit flagged models.py as having one) ---
        if ($newContent.Length -gt 0 -and $newContent[0] -eq [char]0xFEFF) {
            $newContent = $newContent.Substring(1)
            Write-Host "BOM stripped from start of file."
        }

        # --- 8. Write back as UTF-8 no-BOM ---
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($fullPath, $newContent, $utf8NoBom)

        # --- 9. Verification ---
        $afterBytes = [System.IO.File]::ReadAllBytes($fullPath)
        $hasBom = ($afterBytes.Length -ge 3 -and $afterBytes[0] -eq 0xEF -and $afterBytes[1] -eq 0xBB -and $afterBytes[2] -eq 0xBF)
        $newLines = (Get-Content $fullPath -Encoding utf8).Count
        Write-Host ""
        Write-Host "=== Verification ==="
        Write-Host "BOM present:    $hasBom (expect False)"
        Write-Host "Line count:     $newLines (was $origLines)"

        # Check all 9 escapes landed
        $afterContent = [System.IO.File]::ReadAllText($fullPath)
        $expectedEscapes = @('\u215B','\u00BC','\u2153','\u215C','\u00BD','\u215D','\u2154','\u00BE','\u215E')
        $missing = @()
        foreach ($esc in $expectedEscapes) {
            if ($afterContent -notmatch [regex]::Escape($esc)) { $missing += $esc }
        }
        if ($missing.Count -gt 0) {
            throw "Missing escape(s) after write: $($missing -join ', '). Restoring backup."
        }
        Write-Host "Escapes present: all 9/9 (OK)"

        # Python parse
        Write-Host ""
        Write-Host "--- AST parse ---"
        python -c "import ast; ast.parse(open(r'$fullPath', encoding='utf-8').read()); print('AST OK')"
        if ($LASTEXITCODE -ne 0) { throw "Python AST parse failed." }

        # Django check
        Write-Host ""
        Write-Host "--- manage.py check ---"
        python manage.py check
        if ($LASTEXITCODE -ne 0) { throw "manage.py check failed." }

        Write-Host ""
        Write-Host "=== Fix applied successfully ==="
        Write-Host "Backup retained at: $backup"
        Write-Host "Next steps:"
        Write-Host "  1. Run in-shell test (see below)"
        Write-Host "  2. git diff pages/models.py    (eyeball the change)"
        Write-Host "  3. Commit + push to deploy to Live"
    }
    catch {
        Write-Host ""
        Write-Host "!!! ERROR: $_" -ForegroundColor Red
        if (Test-Path "$($fullPath).prebak") {
            Copy-Item "$($fullPath).prebak" $fullPath -Force
            Write-Host "Restored from backup." -ForegroundColor Yellow
        }
    }
}