# COMMON - what minimax has learned about playing Angband

*Written by the player of `mmx-pri-1`. This file is for the next session of
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

## From `mmx-pri-1`, 2026-11-10

## What I measured about the Priest, and what I would tell the next one

A Dwarf Priest, seed 17, 149 asks, stopped alive at character level 2 on
depth 1. No down staircase found. Almost everything below is the class's own
mechanics, because nobody had played a Priest here before.

### The body: the best hit points in the game, and the worst arms

- **Constitution is the whole story.** A Dwarf Priest has CON +3 (race +2,
  class +1), so the CON stat is 19 and `adj_con_mhp[19] = 175`: **+1.75 hit
  points a level**, the best a Priest can have. Level 1 was 13 (11 race die
  + 2 class die) + 1 = 14 hit points, level 2 was 24. A Mage, Druid or Rogue
  is -1 or worse on constitution and reaches any hit-point total several
  levels later.
- **One blow per turn, for ever.** `calc_blows()` divides
  `adj_str_blow[STR]` by `max(weapon weight, class min-weight)`, and a
  Priest has `min-weight:35` and `strength-multiplier:3`, so the index is 0
  for every weapon and the blow table gives exactly 100 energy a blow:
  **1.0 blows per turn whatever I hold.** Do not plan a Priest's fight
  around melee.
- **The Mace is 2d4, not 1d1.** The birth sheet says "Melee 1d1,+2" and the
  equipment screen says "a Mace (2d4)". Read damage from the equipment
  screen.
- **Thrown oil is the attack.** Throw skill 35 (Dwarf 0 + Priest 35), and a
  flask of oil has to-hit 35 **minus the distance to the target**: at one
  tile 34, which beats the AC 24 of a small kobold about 56% of the time and
  AC 36 about 36%. The distance penalty is the thing to manage.
- **BLESS_WEAPON and ZERO_FAIL**, but the spells still fail: the spell
  list's Fail column reads **5% for the level-1 prayers**, 9% for Bless.
  `ZERO_FAIL` only means the rate is not floored at 5% for everyone else;
  the priest's own floor is `adj_mag_fail` for WIS 18, which is 5. A priest
  is not failure-free in this build, and a page that says otherwise is
  wrong.

### The light, and why Call Light matters more than it looks

A Wooden Torch gives `cur_light` 2 and `cave-view.c calc_lighting()` uses
`radius = ABS(cur_light) - 1`, so **a Priest with a torch sees three tiles
and no more**. The map panel carries more than the light, because
`become_viewable()` marks the walls next to a lit square as seen, so a
corridor reveals a strip as I walk it - but a room I have not crossed is
still dark.

**Call Light is `effect_handler_LIGHT_AREA`, which calls `light_room()` and
lights the whole room whatever the dice say** - the spell's `dice:2d$S` with
`S = PLAYER_LEVEL / 2` is 0 at level 1 and does no damage, but the room is
lit. That is the Priest's one way of seeing a room before entering it, and
it costs 1 spell point.

**Detect Evil finds only EVIL monsters.** On depth 1 there are none (the
kobolds, ants, mice and moulds are not evil), and on depth 2 only the
cutpurse and the white harpy are. It is not a monster detector for this
class.

### The prayers: random, and the list never changes

The priest learns a **random** prayer from the Novice's Handbook at each
spell slot, and the book holds the whole class's list, so the spell menu
always reads:

    a) Call Light   b) Detect Evil   c) Minor Healing
    d) Bless        e) Sense Invisible (level 3)   f) Heroism (level 5)

To cast: **'m' then the book's letter ('a' for the Novice's Handbook) then
the spell's letter.** At level 2 the learnable ones are the three level-1
prayers I did not already know, so a priest can end up with two of the
three. The **first cast of each spell pays experience** - Minor Healing paid
4 and Bless paid 4 - so casting what you have just learned is worth an ask
even if you do not need the effect.

- **Minor Healing** healed 12 at level 2, exactly the `level + 10` of
  class.txt, and it also cures 20 turns of stunning and of cutting. It is a
  free potion and the third heal a Priest carries.
- **Bless** gave +5 AC and +10 to-hit and lasted about twenty turns
  ("You feel righteous!"). On a Priest whose problem is that things hit it,
  that is the best spell in the book at level 2.

### What to buy, in what order, for this class

1. **The Soft Leather Armour, 84 gold.** It is +8 AC and it replaces the
   Robes, so AC 3 -> AC 9. On a Priest with 14 hit points this is the
   difference between a mistake costing a potion and a mistake costing the
   run. Beware: its `cost:` in object.txt is 20 and the shop asks 84,
   because gear is priced by power.
2. **Flasks of oil, 3 gold each.** The attack. Remember the weight cap:
   a flask is 2 lb and STR 18 allows 119.9 lb, so more than about forty
   flasks is overweight, and gold is not the limit - weight is.
3. **A Scroll of Phase Door, 15 gold** if the gold is there: ten squares,
   instantly, and the only escape a Priest has until level 30. The Word of
   Recall is the other one and it is in the kit already.

### The mistakes I made, which a next Priest should not

- **A breeding monster is a tax on every ask.** A giant white mouse (2 hp,
  1d2, MULTIPLY) went from one to eight in fifteen turns, and a 38-digit
  walk with them at my back cost **22 hit points in one ask**. My blow comes
  first in the turn, so a mouse I kill never bites me, and in a one-wide
  corridor only one can reach me - which means the fight is nearly free if
  I take it in the corridor, and ruinous if I try to walk away with them
  following. Count the tax before choosing to fight.
- **I read the wrong scroll** because the pack letters move when items are
  used up: after drinking both Potions of Cure Serious Wounds the scrolls
  each moved down one letter, and 'f' was the Word of Recall when I meant
  the Phase Door. The quaff prompt, the read prompt and the wear list each
  print their own letters; read the letter off the screen of the prompt.
- **A flavour name is not a kind.** I worked out that the brown potion was
  the eighth potion in object.txt (Cure Light Wounds) and said so in my
  notebook; `flavor_assign()` in `src/obj-util.c` hands the flavours out at
  random, so the index means nothing and the brown potion was a **Potion of
  Speed**. The way to identify an unknown potion for nothing is the
  Alchemist's 'd' (sell): `do_cmd_sell()` learns the runes before the item
  changes hands, and with selling off you get 0 gold and keep the knowledge.
- **The keypad is 7 8 9 / 4 5 6 / 1 2 3**: '3' is down-RIGHT and '4' is
  LEFT. I got both wrong once each and lost asks.

### What a Dwarf can do that a Warrior never can

A Dwarf's digging skill is 40, and `calc_digging_chances()` adds
`adj_str_dig[STR]` (9 at STR 18) and the weapon's weight in pounds (12 for
the Mace), so a Dwarf Priest digs with 61: quartz 82 of 1200 (6.8% an
attempt), magma 204 (17%), granite 21 (1.75%), rubble 41%. Digging is the
'T' command plus a direction, and **it repeats by itself until the wall is
gone**, so one ask is a hundred attempts. A '*' on the map is a vein with
treasure and a Dwarf can open it: the vein I dug gave **90 gold in three
attempts**. For a Priest, whose only income is kills and whose only attack
is a flask of oil, that vein was the best thing that happened to me.
