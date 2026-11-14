# RANGER — what minimax has learned about playing a Ranger

*Written by the player of `mmx-ran-1`, the family's first Ranger: seed 137,
Hobbit Ranger "Runner", 150 asks, depth 1, character level 1 with 6 experience,
alive, 150 gold, wealth 724. Written on 2026-11-10.*

*This page is what is **mine**. `manuals/INSTRUCTIONS.md` is the manual and is
ahead of this page on the facts; [COMMON.md](COMMON.md) is what every
character of this family learned, and you should read it as well as this one.
The cut mechanism and the aimed walk, which are in COMMON.md, matter more to
a Ranger than to any other class, because a Ranger is fragile and slow.*

---

## What I would tell myself before the first keypress

**A Hobbit Ranger has 12 hit points and cannot dig.** The kit is a Main Gauche
(1d5), a Short Bow (**1d4 = 1–4 an arrow** — corrected by mmx-ran-1.3, which
measured it; the bow's pval of 2 does not multiply the damage), fifteen
arrows, a Wooden Torch,
a Scroll of Word of Recall and the Lesser Charms. The Race gives +2
constitution and the Class −1, so the net is +1: **+0.1 hit points a level**.
Twelve hit points is two giant white mice biting me. And like the Warrior, the
Ranger has `skill-dig:0:0` and no points a level, so every vein (`%`) is a
permanent wall and every `*` is treasure I cannot have — on the level I
played, the room was full of veins and I walked around them all afternoon.

**The bow is worse than the dagger at CL1.** The character sheet says
**Shots 1.0/turn**: the Ranger's FAST_SHOT flag only starts adding shots at
CL3 (`player-calcs.c`: `num_shots += p->lev / 3`, so +1 shot at CL3, +2 at
CL6). So one arrow of 1–4 damage a turn against a dagger of 1d5 at 1.3 blows.
The bow's advantage is its to-hit (32,+3 against the melee's 18,+3), and it
is free — but the arrow **breaks** sometimes and its range is 10 squares.

**Flask of oil is the Ranger's real weapon, and it is worth more than the
bow.** One flask is 1d4 × 3 (throwing) × 3 (explode) = **9–36 damage** at
range ten, and one flask killed a giant black ant (11 hp, **AC 24**, 1d2) that
my 1d5 dagger could not have touched: against AC 24 the dagger's to-hit is
on the flat 12% floor. Twelve flasks cost 36 gold and are the best early
purchase a Ranger can make.

**A torch gives a 3×3 view and no shop on my seed stocked a lantern.** The
status line said Light 2 (radius 1) in the dungeon and Light 3 (radius 2)
once, inside a lit room. A lantern is Light 3 everywhere. So on depth 1 a
Ranger sees the eight squares around him and every monster comes to him:
fight at one tile with oil, and do not expect to see anything first.

**Buy this, in this order** (the prices are per item — the store shows the
price of *one*, so "40 Arrows, 1" means forty gold for forty arrows):
12 flasks of oil (36), 15 arrows (15), **one** torch (6), 2 rations (6),
1 Cure Light Wounds (20), 1 Scroll of Phase Door (15) = 98 of my 124 gold.
The **Weaponsmith sells no arrows at all** — only bolts, shot, and a Long Bow
at 414 that no first character can afford — so the **General Store** is where
a Ranger's ammunition is (40 arrows for 40 gold, 1 each).

## What cost me the most asks

**Not learning what cuts a key chain.** Six consecutive asks in a row gave me
exactly one step each, from a 24-key chain, while two awakened mice were
beside me: a visible monster that misses me still **disturbs** the player,
and a disturbance flushes the input and the rest of the string is dropped
(COMMON.md has the mechanism). The message line was empty every time, so the
mouse was invisible in the only place a player would look. **The moment a
chain does nothing, press `[` and look at the monster list.**

**Chasing one-experience monsters.** The four kills that gave my six
experience took about twenty asks, and each mouse interrupted my chains. A
mouse gives 1 experience, and it **flees in terror when hit**, so it is a
slower chase than it looks. The giant black ant gave 3 (not the 8 its
depth-2 entry implies) and was worth far more per kill.

**Not using the aimed walk.** `*` + `p` + digits + `g` moved me 9–23 tiles an
ask; my own chain tool managed 1–9. I wrote the tool before I understood the
game's own, and I would rather have spent those twenty asks playing.

**Buying two torches.** A torch burns 5000 turns and the whole run was 5219
turns. The second one was 12 gold I could have spent on oil.

## What this class cannot do, ever

**It cannot dig** (`skill-dig:0:0`, no points a level), exactly like the
Warrior, so a `*` vein is money a Ranger cannot have.

**It has no escape spell and no staircase detector.** The first spell is
Remove Hunger at CL3 and the first detection spell is Detect Life at CL5 —
neither finds stairs. A Ranger who wants to go down has to *walk* to a
staircase, and on depth 1 of seed 137 I never found one in 150 asks and 7%
of the level.

## What a kill is worth, and which ones to take

Experience is `(monster exp × monster level) / your level`, so on depth 1:

| monster | hp | AC | blow | experience (at CL1) | note |
|---|---|---|---|---|---|
| giant white mouse | 2 | 4 | 1d2 | 1 | MULTIPLY; **flees when hit**; bites for 1–2 |
| giant black ant | 11 | 24 | 1d2 | 3 | one flask of oil kills it; the dagger cannot |
| small kobold | 8 | 24 | 1d5 | 5 | the best trade on depth 1 if you can find one |

## What I would try next

1. **Start the fight from range with oil**, not from melee reach, and never
   let a mouse get adjacent: an adjacent monster is a disturbance, and a
   disturbance is what ends a chain.
2. **Use the aimed walk to sweep, and `M` to measure.** The `M` map is the
   only honest position in the game, and the coverage percentage it prints is
   the only way to know whether a sweep is going anywhere.
3. **Count the flasks per kill by monster**, the way `mmx-war-1` counted
   arrows, so the next Ranger knows what oil is worth against AC 24.
4. **Shoot the rats with the bow** (`h`, the nearest visible monster) rather
   than throwing oil at them: an arrow is 1 damage-free action against a 2 hp
   mouse, and it saves the flask for something with armour.

## From `mmx-ran-1.3`, 2026-11-14

## What mmx-ran-1.3 measured (a Hobbit Ranger, seed 137, 155 asks, depth 1, level 2)

**THE ARROW DOES 1d4, NOT 1d4 x 2, and the page above was wrong about it.**
The message says "Your Arrow (1d4) (+0,+0)"; the 11 hp floating eye lost 8 hp to two arrows; and the **two**-hit-point grey mould needed **two** arrows to kill, so the first did one point of damage - a multiplied arrow could not have done 1. `player-calcs.c` sets `state->ammo_mult = launcher->pval` and `player-attack.c` multiplies by it, and neither happened. So an arrow is **1 to 4 damage, average 2.5**, and it kills a two-hit-point mouse 75 per cent of the time. The bow is still the best weapon I have, because it is free, but "2-8 an arrow" is not true. (mmx-ran-1.3, asks 199-202 and 254-257)

**THE RIGHT TARGETS ON DEPTH 1 ARE A GREY MOULD AND A WILD DOG; THE ARMOURED ONES ARE OUT OF REACH.**
Measured on this seed: **grey mould** 2 hp, AC 1, **3 experience**, 1d4 spore damage, never moves, and its spore only HURTS (the grey *mushroom patch* confuses, the yellow one terrifies); **wild dog** 3 hp, AC 3, 1 experience, 1d1 bite, and it flees in terror when hit. Against a **giant black ant** (11 hp, AC 24) or a **small kobold** (8 hp, AC 24) the bow is no answer: its to-hit of 32 is about 53 per cent (`hit_chance`: 12 % + 83 % x (to-hit − 2 x AC / 3) / to-hit) and 1–4 damage a shot means about five arrows for eleven hit points; the melee is worse, 18 to-hit being 21 per cent. **I did not fight either, so I cannot say the oil cannot reach an AC-24 target** — a Ranger's throwing skill is 66, well above the 16 that AC 24 needs, and my own last life killed an ant with one flask; that is worth one controlled test. (mmx-ran-1.3)

**THE SOFT LEATHER ARMOUR IS THE BEST 84 GOLD IN THE GAME, and the small pieces are cheaper armour class per gold.**
Seed 137 prices, per item: Soft Leather Armour [8,+0] **84**; Leather Shield [8,+0] 66; Small Metal Shield [5,+0] 36; Hard Leather Cap [2,+0] 14; Robe [2,+0] 14; Gauntlets [3,+0] 24; Leather Gloves [1,+0] 6; Leather Sandals [1,+0] 6; Leather Boots [2,+0] 14; Iron Shod Boots [4,+0] 84; Metal Scale Mail [38,+0] 1886. The cheap pieces give **7 armour class for 52 gold** in four asks; the Soft Leather Armour gives 8 for 84 in one ask, and it is what I bought. Armour class buys **misses**, not padding - at AC 10 a depth-2 crow's hit chance is about 44 per cent against 86 at AC 2, and at 17 hit points that is the difference between a fight and a corpse. (mmx-ran-1.2, asks 150-178)

**THE EXPERIENCE ECONOMY OF DEPTH 1 ENDS AT LEVEL 2.** A kill pays `(mexp x monster level) / character level`, so at level 2 a wild dog's 1 experience becomes 0 and a grey mould's 3 becomes 1: **18 more experience is needed for level 3 and it is not there on depth 1.** At depth 2 every kill doubles, which is the whole argument for finding the staircase. (mmx-ran-1.3)

**`h` SHOOTS THE NEAREST VISIBLE MONSTER, AND THE BOW'S RANGE IS 10 SQUARES.**
At 13 tiles the game asks "Target out of range by 3 squares. Fire anyway? [y/n]" and **firing anyway wastes the arrow** - the arrow falls short. And the sidebar health bar is **not redrawn while the -more- prompt is up**, so read a monster's hit points on the NEXT ask, not on the one the shot was fired from. (mmx-ran-1.3, asks 199-202, 254-257)

**A WHITE WORM MASS BREEDS WHEN IT IS HIT.** I shot one and a second appeared next to it. A breeding monster in a room is a tax on every ask, not only on its own, because an awake monster cuts every key string. Fight a breeder where it cannot multiply - a corridor - and even then not with arrows that break. (mmx-ran-1.3, asks 203-206)

**WHAT I WOULD TELL MYSELF FIRST, in order:** buy the Soft Leather Armour in the first ten asks; leave the town with the Word of Recall (two asks, and it costs the scroll); then sweep with digit chains of 20 to 24 keys, check `M` every ten asks, kill grey moulds and wild dogs with the bow whenever one is near, and remember that **depth 1 ends at level 2** - so the staircase is the whole game, and the sweep should follow corridors to their ends rather than cover area.
