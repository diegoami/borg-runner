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
(1d5), a Short Bow (1d4 × 2 = 2–8 an arrow), fifteen arrows, a Wooden Torch,
a Scroll of Word of Recall and the Lesser Charms. The Race gives +2
constitution and the Class −1, so the net is +1: **+0.1 hit points a level**.
Twelve hit points is two giant white mice biting me. And like the Warrior, the
Ranger has `skill-dig:0:0` and no points a level, so every vein (`%`) is a
permanent wall and every `*` is treasure I cannot have — on the level I
played, the room was full of veins and I walked around them all afternoon.

**The bow is worse than the dagger at CL1.** The character sheet says
**Shots 1.0/turn**: the Ranger's FAST_SHOT flag only starts adding shots at
CL3. So one arrow of 2–8 damage a turn against a dagger of 1d5 at 1.3 blows.
The bow's advantage is its to-hit (32,+3 against the melee's 18,+3).

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
