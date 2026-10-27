# Design reviews

Independent reviews of the board before it is ordered, by other LLMs and by the
author, each in its own dated directory so that several can run at once without
touching each other or the project:

    design_reviews/
      DESIGN_REVIEW_PROMPT.md           the brief to give a reviewer
      <YYYY-MM-DD>_<Model-Version>/     one reviewer's directory: REPORT.md and
                                        everything it made or copied
      <YYYY-MM-DD>_<Model-Version>/project/   a reviewer's working copy of the
                                        project (gitignored; never committed)

A reviewer only ever writes inside its own directory. The brief says what to review,
how to work and what the report must contain. A later round gets a later date, so the
rounds sort themselves.

## Round 1, 2026-10-26: rev A before ordering

| directory | reviewer | verdict |
|---|---|---|
| `2026-10-26_Claude-Opus-5.5/` | the author's own review, written before reading any other | order after named fixes: no "1" / "3" at the switches' ends while every instruction is by number; the DRIVE probe loop is ahead of the fuse (a ground clip there is an unfused 2.3 A, 28 W short). Minor: thermal margin needs standoffs, the integrator's X5R capacitor, one via for Q2's current, the friction dead band reported as overshoot, document lines. **Applied 2026-10-26**: its `patch_round1.diff`, the fuse moved between the push-pull and DRIVE, the integrator's capacitor a 1 µF polypropylene film (Jason's decisions). Open: findings 6, 11, 12 |

The author's review was applied before any other reviewer started, so the other
round-1 reviews are of the board with those changes (`docs/DESIGN_NOTES.md`,
"Review round 1").

Reconciliation of the round (what each found, what changed) is written up in
`CLAUDE_CODE_CHAT.md` when the round closes.
