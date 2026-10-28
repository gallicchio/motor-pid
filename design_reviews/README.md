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
| `2026-10-26_Claude-Opus-5.5/` | the author's own review, written before reading any other | order after named fixes: no "1" / "3" at the switches' ends while every instruction is by number; the DRIVE probe loop is ahead of the fuse (a ground clip there is an unfused 2.3 A, 28 W short). Minor: thermal margin needs standoffs, the integrator's X5R capacitor, one via for Q2's current, the friction dead band reported as overshoot, document lines. **Applied 2026-10-26**: its `patch_round1.diff`, the fuse moved between the push-pull and DRIVE, the integrator's capacitor a 1 µF polypropylene film (Jason's decisions). Finding 6 closed 2026-10-27; open: 11, 12 |
| `2026-10-27_Gemini-4-Argon/` | Gemini 4 Argon, on the patched board | order after named fixes: RV1's JLCPCB rotation 180° out and its datum swapped; the full-drive stall (0.63 A) below the PTC's 0.70 A trip, not "seconds"; one rail alone reverse-biases a bulk electrolytic; motor current through D1/D2 shifts POSITION (a rest offset with TARGET from the jack); "any probe loop" wrongly said to be fused; build: KiCad 9 on PATH beats the AppImage, sim before the netlist exists. Minor: silk overlaps, missing dots, stale sheet numbers, the "measure your gains" recipe, the step metric. **Applied 2026-10-27**, except the rail-sag fix (documented: the knob cancels it) and C11's place |
| `2026-10-27_KimiK3/` | Kimi K3 (named itself "Claude Fable 5"; Jason to confirm the model) | order after named fixes: the 0.35 A fuse does not open the 0.63 A stall "in seconds" (six places, the back included); minor: kienv ignores KICAD_APPIMAGE with a kicad-cli on PATH, the sheet contradicts itself (ranges, ±0.5 V), the LM321's swing overstated, ×10 probes, R21/R22's unfused ground-clip hazard quantified; nits: check messages, the trimmers are BOCHEN's, the schematic not deterministic. Confirmed the RV1 rotation (wrongly, as Gemini showed). **Applied 2026-10-27**, the fuse kept at 0.35 A as it recommended |

The author's review was applied before the other two started, so theirs are of the
board with those changes; theirs were applied on 2026-10-27 (`docs/DESIGN_NOTES.md`,
"Review round 1", lists every change and what was left as it was).

Round 1 is closed: the reconciliation (what each found, what changed, what did
not and why) is in `CLAUDE_CODE_CHAT.md`, Response 12.
