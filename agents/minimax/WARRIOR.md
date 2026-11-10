# COMMON - what minimax has learned about playing Angband

*Written by the player of `minimaxflash-3`. This file is for the next session of
minimax, not a general manual: `manuals/INSTRUCTIONS.md` and
`knowledge/<run>.md` are that. What belongs here is what is **mine** - what I
measured, what I got wrong, and the judgement I would apply again. Where it
contradicts the manual, it is because I measured it, and it says so.*

*Name the runs every claim came from. A playbook nobody can trace back to a
game is a style guide.*

---

## What I would tell myself before the first keypress

## What cost me the most asks

## What I got wrong

## What I would try next

## From `minimaxflash-3`, 2026-11-10

## minimaxflash-3 (seed 313): the Warrior cannot dig, and armour class is not armour

No family had written a Warrior page, so this is the first one, and it is
mine: seed 313, Human Warrior, 150 asks, depth 3, character level 4 at
death, 131 gold, killed by a cave spider on depth 2.

**A Warrior can never dig** (`class.txt:136-147`: `skill-dig:0:0`, no
points per level). `calc_digging_chances` (`player-calcs.c:1655`) needs
skill 21 for quartz and 11 for magma, so every mineral on a level is a
wall to this class for ever. That matters more than it looks: **the
`*` glyph on the map is a vein WITH TREASURE** (`MAGMA_K`/`QUARTZ_K` in
`terrain.txt`, plain veins are `%`), and digging one places a gold pile
worth about 100 at depth 3 — every `*` on a level is money this class
cannot touch. A Shovel carries only DIG_1 and does not help. For a
Warrior a treasure vein is a landmark and never a source of gold.

**Armour class buys much less than it looks.** A blow's damage is
multiplied by `1 − min(AC, 240)/400`, so at AC 10 armour removes 2.5% of
it; AC changes how often you are *hit* (`mon-attack.c:533` uses AC as the
defence value in the hit roll), so +2 AC is about 5% fewer hits. A
Studded Leather Armour at 100 gold for +4 AC is a poor trade for a class
that can fight at all. **The best early "armour" I wore was a Potion of
Berserk Strength**: it heals 30 and its berserk rage gives +75 to-hit
and fear immunity — and takes 10 off your armour class, so Cur AC fell
from 10 to 0 and I was still the safest thing in the room, because AC
barely matters at this level. Read the numbers before you buy a robe.

**What a kill is worth.** Experience is `(monster exp × monster level) /
player level` (`mon-util.c:1080`), so at CL2 a 3-experience soldier ant
pays 1 and at CL3 a 5-experience kobold pays 1 as well. Levelling a
Warrior is expensive: my level curve cost 4 ants, a lizard, a
centipede, five worm masses, a grey mould and a kobold shaman to reach
CL4. The hits that are worth taking are the ones that carry: the small
kobold (DROP_60) on depth 1, the kobold, soldier, acolyte and apprentice
on depth 2.

**How to play the first hundred asks.** Buy 15 flasks of oil and 3
Cure Light Wounds in the town and spend nothing else: at 2.77 blows a
dagger kills a 6-hp ant in one turn, and oil kills a 10-hp worm mass
without ever letting it multiply or poison me. Do not buy armour, do not
dig, and do not spend asks on your own routes when the game has
`l` + `>` + `g` (walk to a known staircase), `l` + `x` + `g` (walk to the
nearest unexplored edge) and `M` (the whole remembered level, which
finds staircases you have walked past).

**What killed me, so the next Warrior does not die of it.** At ask 149 I
read the Word of Recall in a dungeon I had just entered, and stood still
forty turns waiting for it. The Recall's timer ticks once every ten
turns, so the wait is 150-350 turns; a cave spider does 1d4 a turn and I
had 26 of 43 hit points. A Warrior with oil and a dagger should never
stand still in the dark: keep moving, keep the oil in your throwing
hand, and spend the Recall only when you can walk away from wherever you
read it.
