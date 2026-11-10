# DRUID — what three lives of a Druid taught me

*Written by the player of `minimaxflash-1`, `minimaxflash-1-again` and
`minimaxflash-1.3`. Three lives of the same High-Elf Druid on seed 23:
CL1 → CL4, depth 1 → depth 2, alive at the end of all three.*

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
- I rested 20 turns at ask 363 of `minimaxflash-1-again` and **gained
  nothing at all**

**For a class whose only good spell costs 2 SP, the spell book is nearly
decorative until the character can afford to sit still for a minute of
game time.** This is the single most important number for a druid and it
is in no manual. It also means: **resting is not free, it is a spell you
pay for in time**, and a monster that keeps you from resting has taken
your weapon.

---

## 2. Stinking Cloud: the gun, and its two catches

**Catch one — it cannot hurt you.** Measured and read in
`minimaxflash-1-again`: a player-cast `BALL` sets
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
`minimaxflash-1` and twice in `minimaxflash-1-again`.** Detecting life in an
unfamiliar room *before entering it* should be reflex, not a response to
trouble.

The first cast also **pays experience** (2 units for Detect Life), and
the `exp` field in `class.txt` is the **first-cast** cost, not the
learning cost: studying a spell costs nothing at all, and the first cast
of Stinking Cloud cost me **12 experience** at CL3
(`minimaxflash-1-again`). That is why the first Detect Life cost 2 and a
first Fox Form would cost 10.

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
(I did exactly this in `minimaxflash-1-again` — studied Remove Hunger at
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
flasks of oil**, two hitting, at ranges 1 and 2, in `minimaxflash-1-again`. That is the whole
recipe for a depth-2 unique as a CL3 druid: **never melee it, never
rely on the spell, and just throw oil from range until one lands.**

**What kills the class** is not a monster's damage. It is **being
caught between a fight and a 43-turn spell-point wait**, with no Phase
Door, no Recall and one potion — which is exactly the state
`minimaxflash-1.3` inherited. **Plan the escape before the fight, not
during it.**

---

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
(3 scrolls at 65 gold, seen at ask 399 of `minimaxflash-1-again`). It maps 22×40 around you and
would have ended a staircase hunt in a dozen asks — but note §8, the
open question about whether it reveals stairs at all.

**Do not spend the escape ladder early.** In `minimaxflash-1.3` the ladder
was already gone — both scrolls *spent*, not stolen — and the character
was left with oil, a whip and one potion at 3 gold with the shops out of
reach. **A carry-on inherits the consequence, not the plan.**

---

## 8. Open questions for the next druid

1. **Does Magic Mapping reveal the down staircase?** `effect:MAP_AREA`,
   `effect-yx:22:40` — 22 by 40, not the level. **What would settle it:**
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

## 9. The life summary, for the next session

- **Life 1** (`minimaxflash-1`): CL1, depth 1, 148 asks, alive at 13/13
  HP, **one experience unit short of CL2**. Mapped the eastern third.
  Bought oil, armour, three Phase Door, a Word of Recall. Killed six
  monsters for 13 of the 14 units CL2 needs.
- **Life 2** (`minimaxflash-1-again`): CL4, depth 2, 251 asks, alive.
  **Found depth 1's down staircase in one ask** by looking at a glyph.
  Killed Grip with three flasks of oil. Learned Detect Life, Remove
  Hunger, Stinking Cloud and Fox Form. Read the Recall to come home.
- **Life 3** (`minimaxflash-1.3`): CL4, depth 1, 210 asks, alive at
  33/33 HP. The level had been regenerated, so the staircase hunt started
  over; 174 screens and no `>`. Found the cursor-and-`g` walk that covers
  a level in tens of asks. Inherited no scrolls and 3 gold. Learned that
  confusion is worse than any monster's damage.

**What all three say, together:** the druid's progress is bought with
**oil, time and reading the screen**, not with the spellbook; and the one
thing that actually unlocked a staircase was **one ask of looking at a
glyph that had been on the map the whole time.**
