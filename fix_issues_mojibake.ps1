# fix_issues_mojibake.ps1
# Repairs cp1252 mojibake in the Issues (Comments) template.
# Fixes: two console.log emoji (house, arrows), one "<=" in a CSS banner,
# and six em-dashes in CSS comments. Leaves the real bell emoji untouched.
#
# This script contains NO literal non-ASCII characters by design: every correct
# character is built from its Unicode codepoint, so the PowerShell console cannot
# corrupt it. Run from the repo root.

$ErrorActionPreference = 'Stop'

& {
  try {
    # ---------------------------------------------------------------
    # CONFIG: set this to the real template path (relative to repo root)
    # ---------------------------------------------------------------
    $path = 'pages\templates\fsr_details.html'   # <-- EDIT to the actual filename

    # Keep .NET's CWD in step with the PowerShell location
    [Environment]::CurrentDirectory = (Get-Location).Path

    if (-not (Test-Path $path)) { throw "File not found: $path  (fix the `$path variable)" }

    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    $original  = [System.IO.File]::ReadAllText($path, $utf8NoBom)   # strips BOM on read if present

    # Correct characters, from codepoints (no literals anywhere in this file)
    $house = [System.Char]::ConvertFromUtf32(0x1F3E0)   # house  (console.log)
    $recyc = [System.Char]::ConvertFromUtf32(0x1F504)   # arrows (console.log)
    $bell  = [System.Char]::ConvertFromUtf32(0x1F514)   # bell   (verify-only; must be preserved)
    $le    = [string][char]0x2264                        # <=
    $emd   = [string][char]0x2014                        # em dash

    $NA = '[^\x00-\x7F]+'   # one run of mojibake = one or more non-ASCII chars

    # [regex]::Replace is case-SENSITIVE by default (unlike the -replace operator),
    # which is what we want so ".status-card" never matches "Status card".
    function Repl([string]$s, [string]$pat, [scriptblock]$eval) {
        return [System.Text.RegularExpressions.Regex]::Replace($s, $pat, $eval)
    }

    # Count helper + baseline counts of the CLEAN target chars already in the file.
    # We assert exact DELTAS after repair, so any pre-existing clean character
    # (e.g. the legit em-dash in the "Notify Urgent button handler" JS comment)
    # is accounted for automatically instead of tripping a hardcoded total.
    function CountOf([string]$s, [string]$needle) {
        return ([System.Text.RegularExpressions.Regex]::Matches($s, [System.Text.RegularExpressions.Regex]::Escape($needle))).Count
    }
    $bH0 = CountOf $original $house
    $bR0 = CountOf $original $recyc
    $bB0 = CountOf $original $bell
    $bL0 = CountOf $original $le
    $bE0 = CountOf $original $emd

    $text = $original
    $text = Repl $text ("(console\.log\(')" + $NA + " *(Navigating back to Property Detail)") { param($m) $m.Groups[1].Value + $house + ' ' + $m.Groups[2].Value }
    $text = Repl $text ("(console\.log\(')" + $NA + " *(Restoring FSR filters)")             { param($m) $m.Groups[1].Value + $recyc + ' ' + $m.Groups[2].Value }
    $text = Repl $text ("(MOBILE \()"       + $NA + "(768px\))")                              { param($m) $m.Groups[1].Value + $le + $m.Groups[2].Value }
    $text = Repl $text ("(Back button )"    + $NA + " *(full-width on mobile)")               { param($m) $m.Groups[1].Value + $emd + ' ' + $m.Groups[2].Value }
    $text = Repl $text ("(Report container )"+ $NA + " *(minimal padding)")                   { param($m) $m.Groups[1].Value + $emd + ' ' + $m.Groups[2].Value }
    $text = Repl $text ("(Issue header )"   + $NA + " *(tighter, less indentation)")          { param($m) $m.Groups[1].Value + $emd + ' ' + $m.Groups[2].Value }
    $text = Repl $text ("(Status card )"    + $NA + " *(tighter)")                            { param($m) $m.Groups[1].Value + $emd + ' ' + $m.Groups[2].Value }
    $text = Repl $text ("(Add comment form )"+ $NA + " *(stacks)")                            { param($m) $m.Groups[1].Value + $emd + ' ' + $m.Groups[2].Value }
    $text = Repl $text ("(/\* Comments )"   + $NA + " *(tighter)")                            { param($m) $m.Groups[1].Value + $emd + ' ' + $m.Groups[2].Value }

    # ---------------- VERIFY (no write until all pass) ----------------

    # 1) Line count unchanged (we only swapped characters within lines)
    $lc0 = ($original -split "`n").Count
    $lc1 = ($text     -split "`n").Count
    if ($lc0 -ne $lc1) { throw "Line count changed: $lc0 -> $lc1 (aborting)" }

    # 2) Allowlist gate: the ONLY non-ASCII left may be these five codepoints.
    #    Any survivor outside this set is unrepaired mojibake -> fail + no write.
    $allowed = @(0x1F3E0, 0x1F504, 0x1F514, 0x2264, 0x2014)
    $bad = New-Object 'System.Collections.Generic.HashSet[int]'
    for ($i = 0; $i -lt $text.Length; $i++) {
        $c = $text[$i]
        if ([System.Char]::IsHighSurrogate($c) -and ($i + 1) -lt $text.Length) {
            $cp = [System.Char]::ConvertToUtf32($c, $text[$i + 1]); $i++
        } else {
            $cp = [int][char]$c
        }
        if ($cp -gt 127 -and ($allowed -notcontains $cp)) { [void]$bad.Add($cp) }
    }
    if ($bad.Count -gt 0) {
        $list = ($bad | Sort-Object | ForEach-Object { 'U+{0:X4}' -f $_ }) -join ', '
        throw "Unexpected non-ASCII remains (unmatched mojibake?): $list"
    }

    # 3) Exact deltas vs the original: +1 house, +1 arrows, +1 '<=', +6 em-dash,
    #    and bell must be untouched.
    $cH = CountOf $text $house; $cR = CountOf $text $recyc; $cB = CountOf $text $bell
    $cL = CountOf $text $le;    $cE = CountOf $text $emd
    if ($cH -ne ($bH0 + 1)) { throw "house: $bH0 -> $cH (expected +1)" }
    if ($cR -ne ($bR0 + 1)) { throw "arrows: $bR0 -> $cR (expected +1)" }
    if ($cB -ne  $bB0)      { throw "bell: $bB0 -> $cB (bell must be untouched)" }
    if ($cL -ne ($bL0 + 1)) { throw "'<=': $bL0 -> $cL (expected +1)" }
    if ($cE -ne ($bE0 + 6)) { throw "em-dash: $bE0 -> $cE (expected +6)" }

    # ---------------- WRITE (all checks passed) ----------------
    $bak = "$path.prebak"
    [System.IO.File]::WriteAllText($bak,  $original, $utf8NoBom)   # backup original
    [System.IO.File]::WriteAllText($path, $text,     $utf8NoBom)   # write fixed, no BOM

    # 4) Confirm no BOM landed
    $bytes = [System.IO.File]::ReadAllBytes($path)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        [System.IO.File]::WriteAllText($path, $original, $utf8NoBom)   # restore
        throw "BOM detected after write - restored original."
    }

    Write-Host "OK - mojibake repaired." -ForegroundColor Green
    Write-Host ("Lines: {0} (unchanged) | house={1} arrows={2} bell={3} '<='={4} em-dash={5}" -f $lc1, $cH, $cR, $cB, $cL, $cE)
    Write-Host "Backup: $bak  (delete after you've eyeballed the diff and committed)"
  }
  catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "File left unchanged (or restored). Nothing to commit." -ForegroundColor Yellow
  }
}