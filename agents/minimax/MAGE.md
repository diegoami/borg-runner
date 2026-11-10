# MAGE — what one life of a Gnome Mage taught me

*Written by the player of `minimaxflash-2` (seed 41, race gnome, class mage:
158 asks, 1163 keypresses, turn 8001, depth 1, character level 1, stopped
alive at 8/8 hit points).*

*Class-specific. Read [COMMON.md](COMMON.md) first for the screen-reading, the
pathfinding and the harness — this file assumes it.*

---

## 1. What the class is, in the numbers that decide fights

| | |
|---|---|
| Hit die | **0** (`class.txt`: `hitdie:0`). HP comes from the race and from 1d8 a level (`src/main-stats.c`: `player_hp[i] = player_hp[i-1] + randint1(hitdie)`) |
| Gnome HP | race die 8 → **8 HP at CL1**, 8+1d8 at CL2 |
| Mana | `magic:1:300:5` → one spell at CL1, **2 spell points**, and a spell point costs **71 actions** |
| Armour allowance | 30 lb; over that, one spell point per pound |
| Melee | rapier 1d6, **to-hit 9** — see §3, this is the class's real weakness |

The birth screen puts nine of the ten free points into INT and leaves CON at
15, so a Gnome Mage starts with **INT 30, CON 15, DEX 12, STR 13** and
**8/8 hit points**. The auto-allocation is the game's own recommendation and
it is wrong for this class in one specific way: **two points in CON would
have been two hit points**, and at 8 HP that is a quarter of the character.
(`minimaxflash-2` followed the rule and did not move the points; a mage
should know the trade before it accepts it.)

## 2. The spell points are the wall, and everything follows from that

`player_regen_mana()` (`src/player-util.c:487`) gives
`msp × 197 + 524` in 65536ths per player action — **0.014 spell points per
action** at CL1, so **one spell point costs about 71 actions**. Resting
doubles it (`percent *= 2`), so a full rest is worth about 36 actions.

Measured in `minimaxflash-2`: 4 experience in 158 asks, 11 casts of a 1-SP
spell, and the run's whole budget spent on the level's ground floor.

**A mage's budget is in spell points, not in asks.** One rest ask
(`R` + BACKSPACE + `*` + Enter) returns the bar to full, so the question is
never "can I afford this cast" but "can I afford to be in the right place
when the bar is full".

## 3. Find Traps, Doors & Stairs is a staircase detector — and it is the
only reason a mage is not hopeless at this level

`class.txt` gives it `effect:DETECT_TRAPS` / `DETECT_DOORS` /
`DETECT_STAIRS`, each with `effect-yx:22:40`.
`src/effect-handler-general.c:1467` (`effect_handler_DETECT_STAIRS`) scans
the **real grid**, not the remembered map, and calls `square_memorize()` +
`square_light_spot()` on every stair square it finds, so **it reveals the
down staircase even if the mage has never seen it**. The `>` jump
(`l>g`) then walks to it, because the spell made it *known*.

Three facts about it that cost me the run:

1. **The window is 45 rows × 81 columns** (`player->grid.y ± 22`,
   `player->grid.x ± 40`) and the level is the full 198×66
   (`classic_gen()` → `cave_new(dungeon_hgt, dungeon_wid)`). One cast covers
   about 28% of the level. **Covering the level takes three positions in x
   and two in y: six casts, about 430 actions of travel.** That is the whole
   150-ask budget, spent on the staircase alone.
2. **The spell only reports what it has not already reported.** Cast it twice
   within ten tiles and the second cast says *You sense no traps. You sense no
   doors.* **It scans unscanned ground, so the mage must MOVE between casts.**
   Nine of my eleven casts were worth nothing because I did not move.
3. **Silence is what "no staircase here" looks like.**
   `effect_handler_DETECT_STAIRS` prints "You sense no stairs." only when
   `context->aware` is set, and the first detection never has it. The
   message line after a cast is therefore *traps and doors only*, and a
   missing third message is the normal case.

The spell at CL1 costs 1 SP and **pays 2 experience on its first cast**
(`class.txt`'s `exp` field, 2 for Find Traps; the payment shrinks with
character level). At CL1 that is a sixth of the 12 needed for CL2, for one
cast.

**What I would learn first, in this order:** Find Traps, Doors & Stairs
(CL1), Phase Door (CL2, 2 SP, ten squares of escape), Electric Arc (CL2, 2 SP,
3d6). Magic Missile (CL1, 1 SP, 3d4, never resisted) is the best
*damage* in the game for one spell point, but oil is better still (§4) and
costs no mana.

## 4. The mage's weapon is a flask of oil, and its armour is the shopping
list

**Melee is nearly useless.** The character sheet gives to-hit 9; the hit
formula (`src/player-attack.c:196`) is
`hit% = 12% + 83% × (to_hit − 2·AC/3) / to_hit`, so against a monster of
AC 24 (a small kobold, a giant black ant) a to-hit of 9 can only ever hit
on the 12% floor. **Never walk into a monster as a mage.**

**Oil is the attack.** 9–36 damage, about 22, and it kills a 6 HP monster in
one throw. In `minimaxflash-2` one flask killed a white icky thing (6 HP,
AC 8) and a soldier ant (AC 4). But the throw is also a to-hit roll: my
throw skill was 11, so against AC 24 the flask is 12% as well. **A mage can
only kill what has low armour** — which is a bind, because the monsters that
give experience are exactly the ones with armour.

**Armour is the best money a mage can spend, and it is cheap.** For 200 gold
out of 334:

| Item | Gold | AC |
|---|---|---|
| Soft Leather Armour | 104 | 8 |
| Leather Shield | 66 | 8 |
| Metal Cap | 24 | 3 |
| Cloak | 6 | 1 |

That is **AC 21** (the sheet showed 21, one more than the sum). At AC 21 a
monster needs **to-hit ≥ 14** to touch the mage at all, and most of depth 1
does not. For 8 hit points this is the difference between one fight and
five, and it is better value than a second potion. **Buy armour before
potions; buy one potion and one escape, not two of each.**

The rest of the shopping, from what the shops actually charged in
`minimaxflash-2`: 15–20 flasks of oil (3 gold each), one Cure Light Wounds
(20), one Scroll of Phase Door (15), one Scroll of Word of Recall (125 in the
shop, and the mage's kit already has one). **Do not buy Magic Mapping (65):
Find Traps is better for the staircase, and it costs one spell point
instead of a quarter of the oil budget.**

## 5. What killed the run, and what would not have

The run stopped alive at depth 1, character level 1, with 4 gold. The
staircase was never found, and the reason was not the spell and not the
mana: **I did not know where on the level I was.** The map panel scrolls and
the full map (`M`) draws only the *remembered* region, so after 158 asks I
could not tell whether I stood at x = 20 or x = 120 — and every one of my
eleven casts landed inside the same 40-tile band, over ground the first cast
had already scanned. **A detector without a position is a random walk.**

The other two lessons:

* **The mage's melee is a trap**, and the map does not show which monsters
  are armoured until you have hit one. In this run the two monsters I
  could kill were lucky; a giant black ant (AC 24) would have been
  unhittable, and with 8 HP and 4 experience to gain, **an unhittable
  monster is a dead run.**
* **The letter glyph on the floor is a monster, not an item.** 'i' is the
  *icky thing* base (`monster_base.txt`), 'a' is an ant. Item glyphs are
  '!', '?', '(', '=', '"', '_', '\', '|'. I spent an ask wondering what an
  'i' was.

## 6. Open questions for the next mage

1. **Can the staircase hunt be done in fewer than six casts?** The staircase
   must be a dead end with exactly three adjacent walls, and the spell
   reveals 10–20 doors in its window, which is a map of the local
   structure. **What would settle it:** a run that uses the revealed doors to
   choose where to stand for the next cast, instead of a fixed grid.
2. **Can a mage afford to level at all?** 12 experience for CL2, and only
   low-armour monsters are killable with oil at to-hit 11. **What would
   settle it:** a mage that buys Magic Missile knowledge first and fights
   AC 24 monsters — but it needs CL2 to learn it, and CL2 needs experience,
   and experience needs a killable monster. That circularity is worth
   breaking deliberately.
3. **How much is a Scroll of Deep Descent worth to a mage?** `object.txt`
   gives it `alloc:20:1 to 100` — a 20% chance on any scroll, findable from
   depth 1 — and it drops you five levels below your deepest. One would
   have turned this run into a depth-6 run. **What would settle it:** a mage
   run that treats finding one scroll as the primary objective, since it
   beats the six-cast staircase hunt outright.
4. **Is the Spell Points table per class or per level?** CL1 gave 2 SP for
   the mage. **What would settle it:** read the table (it is not in
   `class.txt`) and compute the spell-point income at each level, so the
   hunt's cost can be stated in asks rather than in feelings.

## From `minimaxflash-2.2`, 2026-11-10

### CORRECTION to §3: the real cost of Find Traps, Doors & Stairs is not the mana, it is that it breaks the game's own pathfinding

§3 says the spell costs "the whole 150-ask budget" and tells the next mage to
cover the level with six casts from a six-position grid. **That plan is worse
than useless, and so is the reason I gave for it.**

`effect_handler_DETECT_TRAPS` sets `SQUARE_DTRAP` on **every square in the
81×45 window** (`effect-handler-general.c:1376`), whether or not a trap is
there, and `cmd-cave.c:1146` stops any walk that steps *off* such a square.
My previous life cast the spell eleven times from eleven places, so the level
was patched with overlapping blocks full of unmarked seams, and **every path
across a seam stopped after one tile**.

Measured in `minimaxflash-2.2`, with the level already patched:

| | asks | tiles |
|---|---|---|
| `l>g` (the game's pathfinder) | ~100 | 36 |
| `44` (plain digit walking) | 1 | 2 |

**Plain digit walking has no dtrap test, no running test and no object test
(`do_cmd_walk`, `cmd-cave.c:1277`), so it is never interrupted.** When a walk
stops short, use digits.

And on a **fresh** level — one the spell has not already broken — one cast
finds the staircase and the path to it lies inside the block the spell has
just made, so **the whole way is one ask**. That is the intended use, and my
previous life never got to try it.

Three more facts about the spell, measured:

1. **The spell only reports what it has not already reported.** Cast it twice
   within ten tiles and the second cast says *You sense no traps. You sense no
   doors.* **It scans unscanned ground, so the mage must MOVE between casts.**
   Nine of my eleven casts were worth nothing because I did not move.
2. **Silence is what "no staircase here" looks like.**
   `effect_handler_DETECT_STAIRS` prints "You sense no stairs." only when
   `context->aware` is set, and the first detection never has it. The
   message line after a cast is therefore *traps and doors only*, and a
   missing third message is the normal case.
3. **A cast that reports nothing has still done its work** — the dtrap flags
   are set whether or not the spell finds anything. That is how I fixed the
   broken level: cast again from a position whose window covers the whole
   path, and the seams weld shut. The staircase was 24 rows south and the
   window is ±22 rows, so the first re-cast missed it and the second, from
   closer, did not.

### The spell order I would use now

§3 said: Find Traps, Phase Door, Electric Arc, and that Magic Missile "is
the best *damage* in the game for one spell point, but oil is better still".
**Magic Missile first**, as of minimaxflash-2.2: it is 1 SP for 3d4 = 3–12
damage and **never resists**, so it is **the only damage in the game that
ignores armour** and the only thing that can hurt Fang's AC 36.

**Studying a spell costs nothing** — `do_cmd_study_spell` calls
`spell_learn()` and never touches `msp`; only casting does. So take both
slots at the first level that offers them: minimaxflash-2.2 studied Magic
Missile and Phase Door together and had 4 spell points at depth 2.

**Oil is still the best attack for the things oil can hit** and costs no
mana. **Magic Missile is the answer to the things oil cannot hit.**

**Corrected 2026-11-10, against the pinned `class.txt`:** this page gave
Magic Missile a damage bonus of three on top of its dice (6–15 damage), and
Electric Arc one as well. Both are misreadings of the same line: the dice are
`$Dd4` and `$Dd6` with the count
`(CL-1)/5+3`, so the 3 **is** the dice count and there is no bonus - 3d4 (3 to
12) at CL1 to CL5, 4d4 at CL6. The wrong number had already travelled into a
brief written for the next mage, which is why
`python -m borg_runner playbook --check` now reads a family page's spell
numbers against the game's data.

### CORRECTION to §5: the staircase hunt failed because of the spell, not because I did not know where I was

§5 says the reason the staircase was never found was that *"I did not know
where on the level I was"*. **That was wrong, and I have been wrong in the
same way for two lives.** The `M` whole-level view showed the depth-1
staircase on the first ask of the second life — it was remembered all along,
at box (49,17), and nobody had ever pressed `M`. And the reason my own
second life's hunt took a hundred asks was not my position either: it was
the SQUARE_DTRAP flag (above).

**So the two lessons from the first life are: press `M`, and cast the
detection spell once, on a level it has not already broken.** Both cost one
ask. The first life spent 158.

### The armour-weight penalty counts worn armour only, and it is one spell point per TEN pounds over

`player-calcs.c:1505` sums the weight of *worn* armour — the weapon, bow,
rings, amulet and light are all excluded — and then
`msp -= (cur_wgt - class->magic.spell_weight) / 10`. The Mage's allowance is
30 lb (`class.txt` `magic:1:300:5`). My 36 lb of oil was in the pack and
cost nothing at all. `manuals/INSTRUCTIONS.md` §2 says "one spell point per
pound over" — **the manual is out by a factor of ten.**

### What killed the second life

`minimaxflash-2.2` died on depth 2 at 2/16 hit points, killed by a metallic
green centipede, with **a Scroll of Phase Door and a Scroll of Word of
Recall still in the pack**. The sequence was: it killed a wild cat with one
flask of oil and became CL2 (16 HP, 4 SP); it found depth 2's staircase in
one cast of Find Stairs; it was terrified by a yellow mushroom patch (which
lasts only 3-4 turns and only stops you attacking — not worth a potion); it
read a Phase Door scroll to escape a spider and a dog, which worked; and then
it met **Fang, Farmer Maggot's Dog: 25 HP, AC 36, speed 120**, with a cave
spider and a centipede adjacent.

**Oil is 12 % against AC 36** (my throw is to-hit 11; AC 36 needs to-hit
24), so killing Fang with oil cost about nine flasks and nine turns of
three monsters biting. **Magic Missile — which the character had just
learned — is 1 SP for 6-15 damage that never resists**, and it had one
spell point. It spent that point on a centipede instead.

The three rules I would give the next mage:

1. **Against AC 30 or more, oil is not an attack.** Use a spell, or do not
   fight.
2. **The Scroll of Phase Door comes out when two monsters are adjacent and
   one of them is well armoured** — not when the hit points get low.
3. **Spend the budget on levelling, not on the staircase.** The prior life
   spent 158 asks to find depth 1's staircase and died at CL1 with 4
   experience; this life spent 100 asks, reached depth 2, and reached CL2.
   **A wild cat on depth 2 is 9 HP, AC 14 and gives 8 experience — one flask
   of oil — and there are more of them than there are staircases.**

### Answers to the open questions, and new ones

1. **ANSWERED: the staircase hunt takes ONE cast and ONE walk, on a level
   the spell has not already broken.** See §3 above. The "six casts on a
   six-position grid" plan is worse than useless. **What would settle the
   rest:** a mage that casts once on each new level and reports whether a
   `>` appeared, and how many tiles the walk covered afterwards.
2. **SOLVED: a mage can afford to level, and it is easier than I thought.** A
   wild cat on depth 2 is 9 HP, AC 14 and gives 8 experience; **one flask of
   oil kills it** (my throw is to-hit 11, AC 14 needs to-hit 10, so the
   chance is 12 + 83*(11-9)/11 = 27 %, and one hit for 9-36 damage usually
   finishes it). 12 experience for CL2 is one cat and a half. **The
   circularity I wrote about was a false one**: the monster that gives
   experience on depth 2 is killable with what the mage already has.
3. **PARTLY ANSWERED: the Spell Points table.** CL1 gave 2 SP, CL2 gave
   **4**, so it doubles with the level, and `player_regen_mana()` gives
   `msp x 197 + 524` in 65536ths per action — at 4 SP that is **0.02 SP an
   action, one spell point per 50 actions**, and resting doubles it. **One
   full rest (R, backspace, `*`, Enter) is about 400 game turns and fills the
   bar.**
4. **NEW: how many spell points does it take to kill a 25 HP AC-36 monster
   with Magic Missile?** Three to twelve damage a cast, 7.5 on average, means
   three or four casts. **What would settle it:** a mage that hunts Fang on depth 2 with
   Magic Missile and reports how many casts it took and how many hit points
   the mage had left afterwards.
5. **NEW: is a Scroll of Deep Descent findable on depth 2?** `object.txt`
   gives it `alloc:20:1 to 100` — a 20 % chance on any scroll — and it drops
   you five levels below your deepest. **What would settle it:** a mage that
   explores depth 2 deliberately looking for `?` glyphs and reports whether
   one is a Deep Descent. **If it is, a mage that finds it on depth 2 arrives
   on depth 7 with 16 hit points, which no other run in this repository has
   done.**
