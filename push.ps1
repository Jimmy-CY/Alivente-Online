.\Push-PendingChanges.ps1 -Push `
  -Message "Matrix: open on the year the value changed, and mark a year that straddles one" `
  -Body @'
The year-on-year matrix derived its first year from the earliest NON-baseline
snapshot. On Live that truncated Company Tax to 2026-2027, hiding 2024 and 2025
which resolve perfectly well to 7,000.00 from the baseline. The day before, the
same function read the sentinel AS DATA and drew twenty-eight columns back to
2000. Both come from asking when snapshots exist instead of when the value
changes.

The rule is now arithmetic: floor = max(earliest snapshot INCLUDING the
baseline, earliest DATED change - 1); with no dated change at all it opens on
the current year. The first term is the floor that stops the table reaching
into years it cannot answer - before its earliest snapshot a row resolves to
nothing and the caller falls back to LIVE cells, so the table would print
today's figure under a past heading. An earlier attempt walked backwards while
the total kept changing and did exactly that, opening three line types on 2022.
The second term is what makes a change readable: one column showing what the
charge was before it moved.

Measured on Live before writing, with Show-MatrixRange.ps1: 20 of 21 line types
unaffected. Only Company Tax has a baseline, because _ensure_baseline fires the
first time a long-standing figure is edited. The fault reaches every line as
each acquires one.

Also marks a BLENDED year. Company Tax is charged in January and July and the
rate changed on 1 July 2026, so 2026 is 3,500.00 at the old rate plus 3,299.99
at the new = 6,799.99 - correct, and indistinguishable from a third charge.
That misreading cost a day and nearly shipped a round that would have restated
an instalment already paid.

Blendedness is decided by PROVENANCE, not by comparing figures: a line whose
months legitimately differ is not a blend. resolve_year_months_bulk gains an
optional with_sources flag returning which snapshot answered each month, so
there is one implementation rather than a second rule beside it. Decided per
ROW, not per line - pooling snapshot ids across properties blends every year of
any multi-property line. The snapshot pk is read ONLY inside the flag: a
default three-argument call must be able to take rows that have no primary key,
which is what test_effective_date_baseline.py legitimately hands it.

50 checks in test_matrix_range.py, including: the resolver still returns a bare
dict to its six existing three-argument callers; a year before the earliest
snapshot is never drawn; the pk is read in exactly one place and that place is
guarded; and both new CSS classes are DEFINED in base.html rather than merely
referenced - the first draft used visually-hidden, which exists nowhere in this
system and would have rendered as visible text in the column heading.
'@ `
  -Checks "python test_matrix_range.py","python test_effective_date_baseline.py","python test_expense_matrix.py","python test_spent_row.py","python test_delete_choice.py","python test_prorata_anchor.py","python test_act_expenses.py","python test_button_sweep.py"
