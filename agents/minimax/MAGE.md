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
4d6+3). Magic Missile (CL1, 1 SP, 3d4+3, never resisted) is the best
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
