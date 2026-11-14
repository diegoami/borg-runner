# PALADIN — what minimax has learned about playing a Paladin

*Written by the player of `mmx-pal-1`, the family's first Paladin: seed 401,
High-Elf Paladin, 137 asks, 1111 keypresses, depth 1, character level 4 alive
at the end (the machine the game was running on restarted and killed the
process with the character standing on depth 1), 20 gold and 521 of carried
value. 2026-11-14.*

*This page is what is **mine**. `manuals/INSTRUCTIONS.md` is the manual and is
ahead of this page on the facts; [COMMON.md](COMMON.md) is what every
character of this family learned, and you should read it as well as this.*

---

## The numbers, from `class.txt`

`stats:1:-3:1:-1:2` (STR+1 INT-3 WIS+1 DEX-1 **CON+2**), `hitdie:6`,
`skill-melee:65:40`, `skill-throw:50:30`, `skill-shoot:50:30`,
`player-flags: BLESS_WEAPON | SHIELD_BASH`, 40 lb armour allowance, random
spell learning (a Paladin is given a random learnable spell, not a choice).

**CON +2 is the class's one gift.** A High-Elf Paladin has CON 16 effective,
and the race's +1 and the class's +2 are both in it: 16/16 hit points born,
41/41 at character level 4. The hit die is 6 and the race's is 10, so a level
is worth about 7 hit points — a Paladin's hit points grow faster than a
Mage's and slower than a Warrior's.

**The spell-point bar is two points at character level 1** (5 at level 4) and
**Bless is the only spell a Paladin has before level 3**. Bless costs 2, so
casting it empties the bar, and one point comes back after about 71 player
actions (mmx-pal-1: I cast it at ask 90 with 2 of 2 and had 1 of 4 at
level 4 eight asks later). A Paladin who wants to cast anything needs to
budget rest.

## The first cast of a spell pays experience, and that is the cheapest
## experience a Paladin will ever get

`spell:Bless:1:2:20:4` — the last field is the experience the **first**
cast of that spell pays. Bless is 4 points (mmx-pal-1: the cast at ask 90
said "You feel righteous! Welcome to level 4", and the sidebar's `NXT` went
from 36 to 30). Detect Evil is also 4 (`spell:Detect Evil:3:2:10:4`).

**So a Paladin's opening should be: cast Bless once, early, for four
experience you cannot get any other way.** At character level 1 that is a
third of the way to level 2. And it gives +5 AC and +10 to-hit while it
lasts — about 14 asks, 250 game turns (mmx-pal-1: cast at ask 90, "The
prayer has expired." at ask 104; the status line shows `Blssd` between
`Fed NN %` and the terrain, which is the cheap way to see it).

**The spell list is in class.txt's order, so the letter in the cast prompt
has to be read, not assumed.** For a Paladin it is a) Bless b) Detect Evil
c) Call Light d) Minor Healing e) Sense Invisible f) Heroism — for a Priest
it is a) Call Light b) Detect Evil c) Minor Healing d) Bless, and I would
have got the letter wrong from memory (mmx-pal-1: `m`, the book's letter,
the spell's letter; the book was `a` and Bless was `a`).

## Oil is the attack, not the weapon

**The Main Gauche does 1d1+2 at 2.3 blows a turn: about 8 damage a
blow-turn.** Against a 20 hp monster that is three asks. I carried it for
137 asks and never bought a better weapon, and the oil did all the work:

* **one flask killed Grip** (25 hp, armour class 36, speed 120, 1d4) at range
  one (mmx-pal-1 ask 51), and Grip alone took the character from level 1 to
  level 3 — 60 experience, because the award is `experience x monster level /
  your level` and Grip is a level-2 monster;
* one flask killed a salamander (14 hp, AC 24), one killed a large white
  snake (11 hp, AC 36), one killed a giant white centipede, and two killed a
  small kobold (one missed).

**Why the oil hits what it hits:** the Paladin's throw skill is 50 + the
race's 25 + 30% a level, and a flask of oil is *not* OF_THROWING, so
`chance_of_missile_hit_base` gives `3 x skills[SKILL_TO_HIT_THROW] / 2`
— about 117 raw. `hit_chance` is then fed that raw number, not the number
the character sheet prints (the sheet divides by `BTH_PLUS_ADJ` = 3 again),
which is why **`manuals/INSTRUCTIONS.md` §5 is wrong for a Paladin**: it
claims a to-hit of 9-11 cannot touch armour class 24 at all, and my oil hit
AC 24 and AC 36 monsters repeatedly. The distance penalty is one point a
tile (`player-attack.c:162`), so range barely matters.

**A Potion of Boldness is 8 gold and worth it before CL12.** Fear takes away
a Paladin's attacks and adds eight to its armour class (my family's
COMMON.md), and Heroism — real fear immunity — is CL12 and does not bite
until CL15.

## Armour first, because the class's allowance is generous but its bar is not

A Soft Leather Armour is AC 8 for 84 gold and a Small Metal Shield AC 5 for
50, and together with the naked AC 2 they took me from **AC 2 to AC 16** —
the single best purchase of the run (mmx-pal-1 asks 32-37). Worn armour
counts against the 40 lb spell allowance and nothing else does, and 8 + 6 =
14 lb is well inside it.

**I did not measure what happens when a Paladin wears too much:** the
allowance costs one spell point a pound over, and a Paladin with a two-point
bar cannot afford that. Buy light armour, or do not buy armour at all.

**I did not measure the shield bash** (`SHIELD_BASH`): from the strategy
manual's own numbers the chance at level 1 is a few per cent, and I never
saw one.

## What a Paladin cannot do, and must therefore plan around

* **No escape spell before CL7.** A Phase Door scroll (15 gold, two of them)
  is the whole escape ladder at low level, and the Word of Recall scroll is
  in the kit. Read the Recall in the dungeon and it takes you to the town
  after 15 to 34 player actions — so the way to use it is to read it and
  then keep playing, not to read it and stand still (that is how
  minimaxflash-3 died).
* **No digging.** `skill-dig:0:0` means a vein wall is a wall, and the map
  does not say so: my level's southern pocket ended in a vein (`%`) that
  stopped a chain of eight steps (mmx-pal-1 ask 136). A treasure vein is
  money a Paladin cannot have — the same wall as a Warrior's.
* **No detection.** Only a Mage or a Rogue has Find Traps, Doors & Stairs, so
  a Paladin's only way to find a down staircase is to **see** it. That is the
  class's real handicap and it belongs in the plan: on a 198x66 level with
  three or four staircases, a Paladin who cannot sweep fast enough will
  stay on depth 1, and that is a choice to make early rather than at ask
  120.

## The mushroom patch, which is the worst monster a Paladin can meet

A grey mushroom patch's spores reach **one tile in every direction,
including diagonally** (mmx-pal-1 ask 54: the patch was at (18,8), I was at
(19,9) — one tile south-east — and the spore still reached me). It
confuses for 1d4 turns, and while confused every movement key is kept only
25% of the time, so a Paladin wanders into walls.

**A Paladin has no cure for confusion but a potion: a Cure Light Wounds
cures it and gives twenty turns of immunity, so the patch cannot
re-confuse you.** It cost me eleven asks to learn that (mmx-pal-1 asks
48-60), most of them spent hitting walls and a locked door. Kill the patch
from range with oil (2 hp, AC 1) instead, or do not stand within a tile of
it.

## What I would tell the next Paladin before the first keypress

**Buy the oil, the armour and the shield in that order, and cast Bless once
early.** Oil 60, Soft Leather Armour 84, Small Metal Shield 50, two Cure
Light Wounds 40, a Phase Door 15, a Boldness 8: 257 of the 292 gold a
Paladin is born with, and the character is AC 16 with a full escape
ladder and four free experience.

**Then take the staircase that is under you and go down** — the town's
staircase is drawn nowhere, so `>` is the first useful key — and **look for
the depth-1 monsters worth experience**: the small kobold (5) is the best
one, and a salamander or a Grip can be worth fifteen of them.

**And when the level will not give you a staircase, stop looking and farm
it**: the level's monsters are worth about 1.7 experience a kill at
character level 3, which is slow, and the gold they drop (about 17 a
kill) is what buys the next twenty flasks.
