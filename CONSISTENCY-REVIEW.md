# Consistency review of the player-facing documents — triaged proposal

Written 2026-11-10 by a maintainer session, from a read-only review of
`PLAYGAME.txt`, `CONTINUEGAME.txt`, `docs/BRIEF.md`, `manuals/INSTRUCTIONS.md`,
`manuals/INSTRUCTIONS_2.md`, `agents/minimax/`, and
`ACCUMULATED_KNOWLEDGE.md`, with every load-bearing claim checked against
`vendor/` at the pin. **Held until the live run (`mmf-mage.2`) finishes**;
nothing here is applied yet.

**Priority, per the owner: `ACCUMULATED_KNOWLEDGE.md` is the deliverable —
the reason this repository exists.** Its findings (A1, A2 below) come first.

## A. The export (`ACCUMULATED_KNOWLEDGE.md`)

- **A1 (finding 14). The edition-3 header disagrees with its own body.**
  Line 38 says "Fourteen runs, 3,755 asks"; the corpus table (lines 46-58)
  has 11 rows and omits the three edition-3 runs (minimaxflash-2.2,
  minimaxflash-1.4, minimaxflash-3). "what ten runs measured" (:18-19),
  "Nine of ten runs" (:67), "All eleven" (:90), "how both deaths here
  happened" (:106) vs section 6's title "How the four deaths happened".
  Fix: add the three rows, re-tally the counts. Note: `export --check`
  passes today — it checks edition, citations and consumer, **not** internal
  consistency. A check extension is the owner's call.
- **A2 (finding 1, shadow). Line 180's "one staircase placed uniformly per
  level"** contradicts the export's own edition-3 correction (:113-128).
  Strike the stale clause.

## B. Verified at the pin (checked twice: review agent, then me)

- **B1 (finding 1). The page contradicts itself on staircases.**
  `INSTRUCTIONS.md:260-266` and `:301-303` still teach "one down staircase
  per level, uniform, no rule to exploit" — the retracted labyrinth-generator
  model, misciting `gen-cave.c:1583` — while `:495` (section 8) has the
  correct 3-or-4-down / 1-or-2-up, corridor-end placement. The wrong version
  is in the section a player reads first. Fix: rewrite 260-266 and 301-303
  from section 8. Same stale clause in `agents/minimax/COMMON.md:729-731`
  (post-run fix).
- **B2 (finding 4). Lock-picking formula.** Door power is stored at
  generation: `gen-util.c:581` `square_set_door_lock(c, grid, randint1(7))`;
  picking uses it via `cmd-cave.c:188`. `cmd-cave.c:750` `m_bonus(7, depth)`
  is the door-*jamming* path (`:761`). So `agents/minimax/COMMON.md:389-393`'s
  "40% or 36%" is wrong, and `INSTRUCTIONS.md:333`'s "two attempts in five"
  contradicts its own cited formula (skill 40 vs randint1(7): ~24% average).
  Fix both (COMMON post-run).
- **B3 (finding 5). BRIEF.md:79's "a prompt saying 'Press Return' will not
  take a carriage return" is false.** `patch/src/main-agent.c:148` maps raw
  CR *and* LF to KC_ENTER; only a trailing LF is dropped (:146). The
  documented `\n` escape works regardless, so impact is mild. Fix: drop or
  correct the parenthetical.
- **B4 (finding 13). Every class is born with a Scroll of Word of Recall** —
  9× `equip:scroll:Word of Recall:1:1:birth_no_recall` in `class.txt`, and
  `birth_no_recall` is not in force. Section 9's per-class "Kit:" lines omit
  it; `MAGE.md:192-193` relies on it; the same scroll's mishandling killed
  minimaxflash-3. Fix: one sentence at the top of section 9, or add to each
  kit line.

## C. Rejected after verification — do NOT apply

- **Finding 7 ("walking onto a store doesn't open it") is wrong.**
  `player_handle_post_move` (`player-util.c:1601-1616`) fires `USE_STORE` on
  any move onto a shop square, and `move_player` calls it
  (`cmd-cave.c:1185`). Observed in vivo: `mmf-mage#16-17` walked onto store 1
  and bought oil on the next ask. The page's "walk onto one" is correct;
  `agents/minimax/COMMON.md:626-633`'s "stand on the digit and press `,`" is
  an alternative, not a correction. No change. (Lesson recorded: grep-based
  verification misses cross-file call chains; every rejected finding gets a
  source check too.)

## D. Not yet independently re-verified (plausible; doc-internal or already
cross-confirmed inside the corpus)

- **D1 (f2).** Rest-to-full keypress: page :476 (`R` `*` Enter) contradicts
  page :108-112 (prompt is pre-filled with `& `; the one-ask full rest is
  `R` backspace `*` Enter; measured minimaxflash-2#91). Fix :476.
- **D2 (f3).** Recall from town: :463's keep-table says "does nothing from
  the town"; :366 and `INSTRUCTIONS_2.md:128` say it takes you to DL1
  (`player_set_recall_depth` floors at 1). Fix the table cell; add the caveat
  at :502.
- **D3 (f12).** Scroll pool tail: :386 table "7% against you" vs :413 "8%".
  Weights: 20/290 = 6.9%. Fix :413 to 7%.
- **D4 (f16).** :185-186 "Volume two has the same number for every band
  below depth 5" over-promises; vol 2 has no per-band worst-round figure.
  Soften the pointer or add the numbers.
- **D5 (f6, f8, f9, f10, f11, f17) — all in `agents/minimax/`, post-run:**
  WARRIOR.md:16-19 garbled "105 gold of the 23 I had left over"; DRUID.md:84-86
  stale "28 units / 23 kills" (corrected value: 36, ~30 kills; DRUID:350's own
  "nine kills away" agrees with 36); COMMON.md:569 and MAGE.md:263 stale
  "Magic Missile 6-15" (correct: 3d4 = 3-12, per MAGE.md:61-65's own
  correction); DRUID.md:293,321 and COMMON.md:650-651 Magic Mapping "22x40"
  (correct: +/-22 rows, +/-40 cols = 44x80); WARRIOR.md:47-48 and
  COMMON.md:722-723 "longest 350" (correct: 340; `randint0(20)+15` ticks x10);
  MAGE.md:100-102 and DRUID.md:144-146 first-cast exp (correct: `exp` x spell
  level, fixed — the shrinking formula is the unknown-item one).
- **D6 (f15).** BRIEF.md:170 "three lives of one character" vs seven runs.
  Fix wording.

## E. New addition, from live play (owner's tap)

- **E1. Pickup is not automatic in this build.** `mmf-mage.2#43` spent an ask
  learning it. FACT at the pin: stepping onto an object only *notices* it
  ("You see X" — `square_know_pile` via `player_handle_post_move`);
  `CMD_AUTOPICKUP` picks nothing up because `pickup_always` is off
  (`cmd-pickup.c:169`) and no birth option turns it on. You must press `g`.
  The page lists "`g` pick up" (:324) but never says stepping doesn't do it.
  Fix: one sentence in the movement section. (Exact wording settled at edit
  time so the page check parses it; it has doctored rows and fails loudly.)

## Order of work, when the run ends

1. This branch: `manuals/` + `docs/BRIEF.md` + `ACCUMULATED_KNOWLEDGE.md`
   (A1, A2, B1-page, B3, B4, D1-D4, D6, E1) — page edits written to survive
   the claim parser.
2. `agents/minimax/` corrections where they stand (B1-shadow, B2, D5) —
   full edits allowed once no run is playing; run named in each correction,
   per the reconcile's pattern.
3. Full battery in this worktree before the PR: `pytest -q`,
   `borg_runner prompts`, `playbook --check`, `consolidate --check`,
   `export --check`, `audit --all`. Explicit git paths; never `git add -A`.
