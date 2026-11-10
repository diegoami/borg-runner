# DRUID — what four lives of a Druid taught me

*Written by the player of `minimaxflash-1`, `minimaxflash-1.2`,
`minimaxflash-1.3` and `minimaxflash-1.5`. Four lives of the same
High-Elf Druid on seed 23: CL1 → CL4, depth 1 → depth 2, alive at the end
of three and dead on the fourth.*

*Class-specific. Read [COMMON.md](COMMON.md) first for the screen-reading,
the pathfinding and the harness — this file assumes it.*

---

## 1. What the class actually is

From `lib/gamedata/class.txt`:

- **Hit die 2.** Level-1 HP is the race die + 2 + CON. For a High-Elf
  (race die 10) that is 13 HP at CL1 and 33 at CL4.
- **`magic:1:350:5`** — one spell, 350 experience to learn it, 5 spell
  points. That is the whole of the class's combat capability.
- **Kit: whip and a [Lesser Charms] nature book.** The whip is 1d1+1 at
  CL1 and 1d3+1 at CL4. **Against a 10 HP monster that is five blows.**
- **Armour allowance 35 lb** — not the Mage's 30, and not binding at 8 lb
  of soft leather.
- **No teleport spell at any level.** Ever.

**The class has no melee and no escape of its own.** The manual's Druid
block says *"oil (nothing else hits hard until CL3)"* and *"no escape when
surrounded"*. Both are right, and both are incomplete, because the manual
does not say what the *spell* costs, which is the number that decides
every fight.

### The spell list, with what each is worth

| Spell | CL | SP | Fail | What it is actually for |
|---|---|---|---|---|
| Detect Life | 1 | 1 | 23% | **The best 1 SP in the game** — see §3 |
| Fox Form | 1 | 2 | 20% | Escape that costs your offence; see §4 |
| Remove Hunger | 2 | 2 | 25% | Nothing — digestion is 1 unit per 100 turns |
| Stinking Cloud | 3 | 2 | 27% | Your gun; see §2 |
| Cure Poison | 4 | 4 | 30% | The answer to a mushroom patch, if you can pay |
| Confuse Monster | 5 | 3 | 30% | Crowd control |
| Slow Monster | 6 | 4 | 31% | Crowd control |
| Resist Poison | 7 | 6 | 32% | **The answer to mushroom patches, properly** |
| **Sense Surroundings** | **9** | **4** | **35%** | **`effect:MAP_AREA` — the druid's own Magic Mapping** |
| Turn Stone to Mud | 8 | 3 | 25% | Digging through rubble |

**Sense Surroundings is the one nobody mentions.** At CL9, 4 SP, it maps
`(PLAYER_LEVEL/30 + 1) × 22` rows by `(PLAYER_LEVEL/30 + 1) × 44` columns
— 22×44 at CL9, growing as you level. **A druid at CL9 can buy a Magic
Mapping for nothing.** I never got to CL9, but the line is in
`class.txt` and it is the natural answer to "how does a druid find the
staircase" that no earlier run of mine thought to look for.

### The spell-point economy is the real constraint

`player_regen_mana()` (`src/player-util.c:487`) gives

```
sp_gain = msp × PY_REGEN_NORMAL + PY_REGEN_MNBASE
        = msp × 197 + 524          (in 65536ths, player-util.h:27,31)
```

doubled while resting. With `msp = 5` (CL3) that is **0.023 spell points
per turn, 0.046 while resting**. So:

- **one spell point costs about 22 turns of rest**
- **Stinking Cloud costs two spell points ≈ 43 turns of rest**
- I rested 20 turns at ask 363 of `minimaxflash-1.2` and **gained
  nothing at all**

**For a class whose only good spell costs 2 SP, the spell book is nearly
decorative until the character can afford to sit still for a minute of
game time.** This is the single most important number for a druid and it
is in no manual. It also means: **resting is not free, it is a spell you
pay for in time**, and a monster that keeps you from resting has taken
your weapon.

---

### The druid cannot level on the level it is standing on — `minimaxflash-1.4`

The experience formula (`mon-util.c:1082`: `mexp * monster level / player
level`) and the druid's numbers make one thing plain: at character level 4
on depth 1 a kill is worth `mexp / 4`. A small kobold is 1.25 units, a grey
mould 0.75, a mushroom patch 0.25, a giant white centipede 0.5. Level 5
needs 36 more units (the ladder is 10/25/45/70 before the 145% race
factor, so CL4 is 65 and CL5 is 101 - corrected 2026-11-10, this block
said 28), so **a level-1 druid needs about thirty kills to level, and
the level has no thirty kills in it.** On depth 2 the same formula gives
`mexp * 2 / 4`: a giant black ant is 4 units, Grip 15, a giant green frog
3. **For this class the staircase is not a trophy, it is the only way the
character ever gets stronger** — and my three lives together earned two
experience units because all three of them were on depth 1.

### The gate is the staircase, not the killing — `minimaxflash-1.5`

The formula above has a clause this family had been reading past: **the
multiplier is the monster's OWN level, not the depth you are standing
on.** A depth-1 small kobold is worth `5 * 1 / 4` = 1.25 units at
character level 4 **wherever it is killed**. Only a monster native to the
depth you are on multiplies.

So the two facts fit together like this:

| where the kill happens | monster native to depth 1 | monster native to depth 2 |
|---|---|---|
| on depth 1 | 1.25 units (small kobold) | — |
| on depth 2 | 1.25 units (small kobold) | **4 units** (giant black ant), 3 (soldier), 5 (white harpy) |

**Which means a druid on depth 1 cannot level at any kill rate, and a
druid on depth 2 can.** This life killed an acolyte, a cutpurse, a white
harpy and a crow on depth 2 for thirteen experience units in about forty
decisions — **more than the first three lives of this character earned
altogether** — and it was still thirteen units short of level 5 when it
died. The whole difference between the lives is the staircase.

**And the reward for finding it is money as well as experience:** a
hundred and fifteen gold pieces lay on the floor of depth 2 (the average
pile is about nineteen), and 118 gold is a whole escape ladder, a full oil
supply, the healing this class needs, and the Scroll of Magic Mapping
that four lives of this family have wanted to buy and could not.

## 2. Stinking Cloud: the gun, and its two catches

**Catch one — it cannot hurt you.** Measured and read in
`minimaxflash-1.2`: a player-cast `BALL` sets
`PROJECT_THRU|PROJECT_STOP|PROJECT_GRID|PROJECT_ITEM|PROJECT_KILL` and
**not** `PROJECT_PLAY`, and `project()` only affects the player when
`PROJECT_PLAY` is set (`effect-handler-attack.c:594`, `project.c:519,996`).
**The radius-2 poison ball never hits the caster**, so you can fire it at
point-blank range. That turns the druid's CL3 spell from a liability into
a weapon, and it is why the class is viable at all.

Damage is `PLAYER_LEVEL/2 + 10`: 11 at CL3, 12 at CL4. Casting it is
`m`, book letter, verse letter, then **`5`** at the direction prompt (the
ball is centred on you).

**Catch two — almost everything resists poison.** Every monster has
`IM_POIS`. Against the grey mushroom patch, Stinking Cloud hit and the
game said *"The grey mushroom patch resists a lot"*; the patch was still
alive afterwards. Against Grip (25 hp, AC 36) it worked, because Grip has
no poison resistance.

**So the spell's value is not "12 damage".** It is 12 damage against the
few things that do not resist it, fired from a distance, for free of HP.
**Build the expectation around that, not around the number.** In
`minimaxflash-1.3` the spell's only target was a mushroom patch, and it
"resisted a lot".

**The spell cannot be cast while confused** (`player-util.c:1103`,
*"You are too confused!"*), which is the point of §4 — and which cost me
two casts in `minimaxflash-1.3`.

### What the cloud is actually worth, measured on depth 2 — `minimaxflash-1.5`

The spell's own list is on the screen when you press `m` and the book's
letter, and it is worth reading: **Detect Life 1 sp 9 %, Fox Form 2 sp
6 %, Remove Hunger 2 sp 14 %, Stinking Cloud 2 sp 19 % (damage 12, radius
2), Confuse Monster 3 sp 28 %, Slow Monster 4 sp 31 %.** So the druid's
best weapon fails a fifth of the time, and the whole of the class's
fighting power is two spell points.

**And those percentages are not the ones in `class.txt` — they are the
real ones, and they are much better.** `class.txt` gives the base failure
rates (Detect Life 23 %, Fox Form 20 %, Remove Hunger 25 %, Stinking
Cloud 27 %, Confuse Monster 30 %, Slow Monster 31 %), and the prompt
gives what this character will actually roll: the base minus the casting
stat adjustment (`player-spell.c`: `chance = spell->sfail; chance -=
fail_adjust(player, spell);`, floored at the minimum for the casting
stat level and never below 5 %). **A druid at INT 13 casting at CL4
fails a fifth less than the book says**, and the spell list on the screen
is the one to plan by.

**And here is the number that decides a druid's fight: damage per hit
point spent.** On depth 2 a cloud killed an acolyte (18 hp, AC 15, 1d5)
for two spell points and **no hit points at all**, where the same kill
with the whip would have taken about thirty hit points — twelve rounds of
1d5 for six rounds of 1d3+1 at a 51 % hit rate. The cloud is five times
better than the weapon. It is not a special occasion; **it is the fight.**

**Poison resistance is partial, not immunity.** One cloud took an acolyte
from half health to a tenth — about seven of its twelve damage — and the
second finished it. The grey mushroom patch "resists a lot"; an acolyte
resists about forty per cent. **The number to expect is between seven and
twelve, not twelve.**

**And the spell is not free of turns.** Two spell points is 43 turns of
rest to earn back (§1), and the character in this life had five spell
points and a hundred and fifteen gold and could not afford enough of them.

---

## 3. Detect Life is the best 1 SP in the game — but not for its effect

The spell detects living monsters in a 22×40 area (`effect-yx:22:40`) and
sets `MFLAG_MARK` + `MFLAG_SHOW` on each (`effect-handler-general.c`,
`detect_monsters`). **In a text dump the map highlight does not survive**
— you get *"You sense life!"* and the map may not have changed.

**The real value is that it makes the `[` list show out-of-sight
monsters.** One cast (1 SP) plus one `[` gives every living monster
within 22×40, with positions and sleep states. At ask 361 that gave me:
Grip 5S 3W, a green worm mass asleep 17S 3W, and two giant yellow
centipedes asleep — all invisible to the eye.

**This is the cheapest safety a 13-HP druid has, and I used it twice in
`minimaxflash-1` and twice in `minimaxflash-1.2`.** Detecting life in an
unfamiliar room *before entering it* should be reflex, not a response to
trouble.

The first cast also **earns experience** (2 units for Detect Life), and
the `exp` field in `class.txt` is the base of that first-cast award -
the award is `exp` × spell level (corrected 2026-11-10; this block read
the field as the whole cost, and said "cost" where it meant "earned" -
the game pays you, not the other way round) - not the learning cost:
studying a spell costs nothing at all, and the first cast
of Stinking Cloud earned me **12 experience** at CL3
(`minimaxflash-1.2`). That is why the first Detect Life earned 2 and a
first Fox Form would earn 10.

---

## 4. The mushroom patches are the druid's real difficulty

Three different things wear the mushroom name, and the manual lists them
without saying they are different:

| Name | HP | AC | Move | Blow | Exp |
|---|---|---|---|---|---|
| **grey mushroom patch** | 2 | 1 | NEVER_MOVE | `SPORE:CONFUSE:1d4` | 1 |
| **yellow mushroom patch** | 1 | 1 | NEVER_MOVE | `SPORE:TERRIFY:1d4` | 2 |
| **grey mould** | 2 | 1 | **mobile** | 2 × `SPORE:HURT:1d4` | 3 |

**The 1d4 is the effect DURATION, not damage.** The yellow patch
terrifies you for 1d4 turns; the grey patch confuses you for 1d4 turns.
The **mould** is the one that can chase you — no `NEVER_MOVE` — and it
did 2–3 damage a turn to me.

**What confusion means for a druid is worse than for most classes, and
that is the whole point of this section.** [COMMON.md](COMMON.md) §3
covers what confusion does to any character: it blocks casting, blocks
running, and randomises every direction 75% of the time. For a druid
specifically that is catastrophic, because **Stinking Cloud is the only
weapon the class has that cannot hurt its user, and confusion takes it
away exactly when a fight needs it.** Two grey patches caught me in
`minimaxflash-1.3`; the first cost a Cure Light Wounds, 2 spell points
and about eight asks.

**What works, all measured:**

- **The whip kills the patch in one blow** (2–4 damage vs 2 HP at AC 1) —
  but confusion randomises the attack direction, so **twelve attacks in
  one answer** make a hit very likely and cost nothing when they miss
  into a wall.
- **A Cure Light Wounds cures confusion for 20 turns** and is worth more
  than its 20 healing when you are carrying one. **Keep one for this.**
- **Resting beside the patch does not work**: it re-spores you every
  turn, so the confusion never lifts, and it chips away at your HP.
- **Stinking Cloud barely dents it** (`IM_POIS`).
- **Resist Poison (CL7, 6 SP)** is the proper answer, and Cure Poison
  (CL4, 4 SP) is the cheap one. Both are far above the level a druid
  normally survives.

**The lesson for the class: a druid at CL3–6 has no answer to a mushroom
patch except a potion and a whip, and that is a fight the character
cannot win cheaply.** Avoid the patch's square; it cannot follow you.

---

### FEAR is the fourth way a druid can be turned off — `minimaxflash-1.5`

Confusion blocks casting, fear blocks *everything*, and for a druid the
second is worse than the first because the first still leaves you the
whip.

Measured: a crow's scare blow put the character in "Afraid", and while
afraid **the character's attacks did not happen at all** ("You are too
afraid to attack the crow!") and **its moves did not happen either** ("There
is a wall in the way!" with the turn counter unmoved). Two crows held a
druid at three hit points for eight decisions doing nothing.

The strange part is that **being afraid gave the character eight points of
armour class** — the sidebar read `Cur AC 20` while the fear lasted and
`Cur AC 12` the moment it ended ("You feel bolder now."), with the
equipment list unchanged. So the condition is worth a great deal of
defence and costs everything else. **I do not know the rule for the
bonus; I only know what the screen said.**

**Nothing cures fear but time.** Not a Cure Light Wounds (which cures
confusion and cuts, and which the druid had), not a scroll, not a spell.
A rest of ten turns let the timer run out. **The only defence is not to
stand next to the thing that frightens you**, and for a druid that means
never letting a crow or a harpy into melee range.

## 5. The rest of the class

**Fox Form** (`shape.txt`: combat −3 to-hit, −3 to-dam, +3 AC, STR −3,
`FREE_ACT`, `FEATHER`) is the only intrinsic escape. Its costs are real:
−3 to an already weak whip, −3 STR, **10 experience on the first cast**,
and **a shape cannot read, quaff or cast** — so you must change back
before using a scroll or a potion, and a chase that lasts one turn longer
than planned is a death. I never had the spell points to use it in any of
the three lives, so it is untested in practice.

**Remove Hunger is worth nothing.** Digestion is one unit per 100 turns
(`game-world.c`, `if (!(turn % 100))`), so a full stomach lasts 10,000+
turns. Do not spend a study on it at CL2 unless you have nothing else;
**Stinking Cloud arrives at CL3 and is a far better use of that verse.**
(I did exactly this in `minimaxflash-1.2` — studied Remove Hunger at
CL2, and it was the first thing I would take back.)

**Study is gated by character level, and the refusal is silent.** At CL2
pressing the Stinking Cloud key in the Study prompt did nothing and left
the prompt up, with no message. **One verse per character level**, and
you cannot study above your level.

**Confuse Monster (CL5) and Slow Monster (CL6) are 3 and 4 SP** — one
and a half to two Stinking Clouds. Given §1's economy, they are
unaffordable in practice for most of the game's early levels. Both are
`BOLT_AWARE`, so they single out one monster at a time — the opposite of
the area denial that Stinking Cloud gives.

---

### The druid's lock-picking skill, so a druid knows what a door costs — `minimaxflash-1.4`

`SKILL_DISARM_PHYS` for a druid is 30 at level 1 plus 10 a level plus the
race's bonus (High-Elf 4), so 64 at level 4. The pick chance is
`MAX(2, skill - 4 * lock_power)` with the lock level 1 to 7, so **36 to 60
per cent, one attempt per ask** (a failure cancels the rest of the key
string), and the door does not open under you afterwards. A druid that
expects to cross a level's locked doors should budget two decisions a door
and should not expect to do it in one.

## 6. What the class can and cannot fight

**You cannot melee.** The whip is 1d3+1 with one blow per turn. Against
AC 24 (giant black ant, small kobold) my to-hit of 21 gives about a 12%
chance; against AC 36 (Grip) the same. **Oil decides everything**, and
the hit chance is a to-hit roll against AC:

- **AC 1** (worm mass, mould, mushroom patch, mouse): oil lands easily.
- **AC 24**: hit from one tile, **missed from two**.
- **AC 36** (Grip): missed at range 2; about 77% at range 1, two hits.

**The kill that made the class work** was Grip, Farmer Maggot's Dog — 25
HP, AC 36, 1d4, **speed 120 (+10)**, 30 experience — killed with **three
flasks of oil**, two hitting, at ranges 1 and 2, in `minimaxflash-1.2`. That is the whole
recipe for a depth-2 unique as a CL3 druid: **never melee it, never
rely on the spell, and just throw oil from range until one lands.**

**What kills the class** is not a monster's damage. It is **being
caught between a fight and a 43-turn spell-point wait**, with no Phase
Door, no Recall and one potion — which is exactly the state
`minimaxflash-1.3` inherited. **Plan the escape before the fight, not
during it.**

---

### A druid's whip is a real weapon once it is blessed — `minimaxflash-1.4`

Without a Blessing the whip's to-hit of about 19 cannot reach an armour
class of 36: `hit_chance` needs `to_hit >= 2 * AC / 3`, so 19 does not
reach 36 and the oil has to do it alone. A Scroll of Blessing takes the
to-hit to 29, and 29 reaches 36. Measured on this life: a giant white
centipede (9 hp, armour class 12) died in **three swings** blessed and
five unblessed, and the blessing is +5 armour class (12 to 17) on top.
The druid's own melee problem, which my DRUID.md has called hopeless
since the first life, is **a scroll away from being solved** — it lasts
about thirty turns, so it is a fight-scoped tool, not a plan.

## 7. Buying, for a druid specifically

**Buy, in this order:** oil (15–20 flasks), a **Cure Light Wounds** (keep
one for confusion, not for HP), **Phase Door scrolls**, and armour
(soft leather +8 and a metal cap +3 gets you to **AC 12** for 108 gold —
the shopping list of `minimaxflash-1`).
**Bought gear is not auto-worn** — `w` plus the pack letter, and the
sidebar still says `Cur AC 0` until you do it.

**The druid has no teleport spell at any level, so a Phase Door scroll is
not a luxury — it is the weapon.** One ask, 10 grids, no delay: `ier`
(pack, select scroll, read). It is bug-free for this job and it costs no
HP and no time. **Against Grip, the Phase Door scrolls were what saved
me, not Stinking Cloud.**

**Buy the Magic Mapping scroll the first day the Alchemist has one**
(3 scrolls at 65 gold, seen at ask 399 of `minimaxflash-1.2`). It maps ±22 rows and ±40 columns around you (44×80 - the `effect-yx:22:40` are half-extents, corrected 2026-11-10) and
would have ended a staircase hunt in a dozen asks — but note §8, the
open question about whether it reveals stairs at all.

**Do not spend the escape ladder early.** In `minimaxflash-1.3` the ladder
was already gone — both scrolls *spent*, not stolen — and the character
was left with oil, a whip and one potion at 3 gold with the shops out of
reach. **A carry-on inherits the consequence, not the plan.**

---

### What this life found for the druid's shopping list — `minimaxflash-1.4`

- **Four Potions of Cure Light Wounds on the floor of depth 1**, in a
  stack, marked `!`. The druid of the third life had none, and had no way
  to buy any. **A `!` may be a potion and the text screen cannot tell
  you** — the oil kind and the potions share the glyph and only the colour
  differs. Look before you walk over.
- **A Scroll of Light is worth more to a sweeping druid than to a fighting
  one**: it makes a permanent light globe, and a torch shows two tiles, so
  every step of a sweep memorises about four squares instead of a few more.
- **The class still has no escape of its own, and the third life spent
  both Phase Door scrolls.** The scroll is the weapon; this life found
  none.

## 8. Open questions for the next druid

1. **Does Magic Mapping reveal the down staircase?** `effect:MAP_AREA`,
   `effect-yx:22:40` — ±22 rows, ±40 columns (44 by 80, not the level). **What would settle it:**
   buy one on depth 1, read it, and say whether a `>` appears in the
   window. The inherited note *"Magic Mapping (65 g) did not help"* is
   one run's negative result and does not answer it.
2. **Sense Surroundings at CL9 is `MAP_AREA` too** — is it bigger, and
   does it show stairs? It is the druid's own answer to the staircase
   hunt and nobody has reached CL9 to ask.
3. **Is a druid viable past CL5?** Hit die 2, a 1d3+1 whip, spells that
   cost 43 turns of rest each, and no teleport spell ever. I reached CL4
   and depth 2 alive and killed a unique with oil. **What would settle
   it:** a druid run that reaches CL5–CL6 and casts Stinking Cloud twice
   in a row without resting. If the spell still cannot keep up with the
   mana, the class's real answer is oil and the scroll — and the report
   should say so plainly.
4. **Which monsters do not resist poison?** The whole value of Stinking
   Cloud rests on this, and I only have Grip as a data point. A table of
   `flags:` per depth-1 and depth-2 monster would settle it.
5. **How does a druid survive a mushroom patch at CL4–CL6** with no
   Resist Poison, no Cure Poison, and one potion? A 2 HP AC 1 monster
   that disables every tool the class has is a design question, and the
   answer is worth having before a life is spent on it.

---

### What this life did not settle for the druid — `minimaxflash-1.4`

Whether a druid can reach character level 6 without a staircase: the
formula says the answer is no on depth 1 and yes on depth 2, and the way
to settle it is a druid run that reaches depth 2 and counts the
experience of seven ordinary kills. At four units a kill on depth 2, level
5 is nine kills away.

## 9. The life summary, for the next session

- **Life 1** (`minimaxflash-1`): CL1, depth 1, 148 asks, alive at 13/13
  HP, **one experience unit short of CL2**. Mapped the eastern third.
  Bought oil, armour, three Phase Door, a Word of Recall. Killed six
  monsters for 13 of the 14 units CL2 needs.
- **Life 2** (`minimaxflash-1.2`): CL4, depth 2, 251 asks, alive.
  **Found depth 1's down staircase in one ask** by looking at a glyph.
  Killed Grip with three flasks of oil. Learned Detect Life, Remove
  Hunger, Stinking Cloud and Fox Form. Read the Recall to come home.
- **Life 3** (`minimaxflash-1.3`): CL4, depth 1, 210 asks, alive at
  33/33 HP. The level had been regenerated, so the staircase hunt started
  over; 174 screens and no `>`. Found the cursor-and-`g` walk that covers
  a level in tens of asks. Inherited no scrolls and 3 gold. Learned that
  confusion is worse than any monster's damage.
- **Life 4** (`minimaxflash-1.5`): CL4, depth 2, 139 asks, **dead** at
  3/33 HP on depth 2, killed by an acolyte, with 118 gold and no escape
  in the pack. **Found a down staircase on depth 1 and went down**, which
  no life of this character had done deliberately before, and earned
  thirteen experience units on depth 2 — more than the first three lives
  earned together. Killed an acolyte and a cutpurse with Stinking Cloud
  for two spell points and no hit points, killed a white harpy with the
  whip, found a Scroll of Phase Door (and spent it to escape two crows),
  found a hundred and fifteen gold, and died to a crow's fear and the
  acolyte it called.

**What all four say, together:** the druid's progress is bought with
**the staircase first and everything else second** — oil, time and reading
the screen are the price of the staircase, and the staircase is what buys
experience, money and a chance of a fifth level. The one thing that
unlocked a staircase in every life was **one ask of looking at a glyph or
of pressing `M`**, and the one thing that killed this one was **spending
its escape scroll too late and its last healing potion too early**.

