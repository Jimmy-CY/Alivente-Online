.\Push-PendingChanges.ps1 -Push `
  -Message "The comment wash comes off: an author gets a name, not a colour - and a person's initials come out of two templates" `
  -Body @'
DECIDED 30 AUG: colour should not encode WHO wrote a comment. Amber means
"attention" in five other places in this system - --alv-warn, .alv-pill-attn,
.alv-age-2, .alv-grade-4, and the flagged stat tile - and on the Friday Status
Report an amber comment sat directly under a red "257 days open" with nothing
to say the amber was about authorship. Author identity is a CATEGORY, not a
verdict.

THREE FILES, SIX EXPRESSIONS OF ONE IDEA, AND THEY DISAGREED.

  comments_report.html  tr.admin-comment / tr.user-comment
                        #e3f2fd / #fff3e0, plus :hover, plus PRINT variants,
                        plus phone-card variants
  comments_report.html  .user-cell.admin-user / .regular-user
                        the author's NAME in #1565c0 / #e65100
  comments_report.html  .comment-item.admin-comment-item / .user-comment-item
                        the same two fills, DIFFERENT left borders
  comments_report.html  .color-legend, with two swatches explaining it
  fsr_details.html and  .detail-row.ss-comment / .regular-comment
  friday_status_report  the same two fills - AND they coloured the TEXT: date,
                        author and body all set to #ff8c00 or #0e7c8b at
                        weight 600

The last one paints the CONTENT rather than the container, so a comment's words
were orange or teal depending on who typed them. And .regular-comment took its
identity colour from #0e7c8b - the system ACCENT, which means "this is a
control" on every other screen.

THE PART THAT IS NOT COSMETIC. On two of the three screens the split was never
admin-versus-user at all. It was

    {% if detail.issues_details_user == 'SS' %}ss-comment{% else %}regular-comment{% endif %}

- a person's initials, compared as a string literal, in a template. Anyone else
who becomes an admin got the "regular" colour; if SS leaves, the rule points at
nobody. comments_report.html used a real item.is_admin flag for the same idea,
which is how the three screens came to disagree in the first place. Removing
the wash removes the literal.

The OTHER comparison in fsr_details.html - `== user_initials` - is a different
thing and stays: it decides whether YOU may edit YOUR own comment. The suite
requires it to still be there, so a later tidy-up cannot take both.

ONE NEUTRAL TONE, agreed 1 Sep. Every author gets the same quiet .alv-tag chip
carrying the initials that were already being printed, and the NAME does the
distinguishing. Two tones would have rebuilt the same split in miniature. The
trailing colon goes too - it separated an author from the text when the author
read "(SS)", and a chip does not need punctuation to say it has ended.

THE LEGEND GOES WITH IT. .color-legend and its two swatches existed only to
explain the wash. A legend for a colour that is no longer used is worse than no
legend.

80 checks in test_comment_tint.py. The rendered half asks the browser the only
question that matters: do two comments by DIFFERENT authors look the same - same
background, same left edge, same text colour, same weight - on all three
surfaces, the report rows, the history cards and the issue comments? A CONTROL
renders a deliberately washed row beside them, because every one of those
checks asserts an ABSENCE of difference and an absence is what a blind probe
reports for free. It also asserts every author chip is the same tone, and that
the chip is a real chip rather than transparent.

SECTION 4b, FOUND BY THE PUSH GATE - and it is the SCOPE GUARD variant, the
fourth kind we have seen.

test_sticky_sweep.py section 5 asserts that the sweep changed no MARKUP, by
comparing each page with its .bak_sticky snapshot. That is a good check and a
true claim. It is also a claim with an expiry date built in: it holds only
until some later round legitimately edits one of those pages, and this round
edits comments_report.html.

The claim is still provable - just not against the LIVE file. .bak_cmttint is
comments_report.html AS THE STICKY SWEEP LEFT IT, because this round is the
first to touch its markup since. So the comparison moves from

    live vs .bak_sticky           expires the next time anyone edits the page
    .bak_cmttint vs .bak_sticky   two snapshots, true for good

The sweep's historical claim becomes PERMANENTLY checkable instead of decaying,
which is better than it was. The other five pages keep comparing against the
live file, because nothing has touched them. Verified both ways here: the moved
comparison passes, the old one fails.

The patcher guards PER FILE, the same lesson as the print round: the gate found
this after the templates were already patched, and one guard for the whole
round would have left the patcher unable to finish itself.

WHAT THIS ROUND DOES NOT DO. The Comments Report page itself - its teal
gradient banner, its .stat-box figures, its .report-table, its red Delete - is
the next round. So is the Issues Analysis modal in fsr.html (five stat tiles,
the first real asker for the modal density .alv-stat deliberately did not ship,
and three tabs that are a segmented control by another name), and so are the
Friday Status Report's cards, Notify Now's entire-appearance-in-a-style-
attribute, and whether "257 days open" gets the ageing scale. This round is the
tint, in all three places at once, so they cannot go on disagreeing about it.

comments_report.html       23,313 -> 21,574 bytes.
friday_status_report.html  16,258 -> 15,839 bytes.
fsr_details.html           38,073 -> 37,899 bytes.
'@ `
  -Checks "python test_comment_tint.py","python test_sticky_sweep.py","python test_button_sweep.py","python test_print_media.py","python test_action_standard.py","python test_grade_tables.py","python test_ind_modal.py","python test_pl_drill.py","python test_alv_stat.py","python test_payment_days.py","python test_card_standard.py","python test_table_standard.py"
