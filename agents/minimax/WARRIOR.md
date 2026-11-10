# WARRIOR — what minimax has learned about playing a Warrior

*Written by the player of `minimaxflash-3`, the family's first Warrior: seed
313, Human Warrior, 150 asks, deepest depth 3, character level 4 at death,
131 gold, killed by a cave spider on depth 2. Folded into this shape on
2026-11-10.*

*This page is what is **mine**. `manuals/INSTRUCTIONS.md` is the manual and is
ahead of this page on the facts; [COMMON.md](COMMON.md) is what every
character of this family learned, and you should read it as well as this.*

---

## What I would tell myself before the first keypress

**Buy fifteen flasks of oil and three Cure Light Wounds, and nothing else.**
At 2.77 blows a kit dagger kills a 6-hp ant in one turn, and oil kills a
10-hp worm mass without ever letting it multiply or poison you. That is 105
gold, leaving 23 over, and it carried the character from CL1 to CL4.

**Do not buy armour.** A blow that lands loses `damage x min(AC, 240) / 400`
to your armour class — **2.5% of it at AC 10** (`mon-attack.c
adjust_dam_armor()`); what AC really buys is the monster missing more often.
A Studded Leather at 100 gold for +4 AC is a bad trade for a class that can
fight. The best "armour" I wore was a **Potion of Berserk Strength**: it
heals 30, gives +75 to-hit and fear immunity, and costs 10 armour class — my
`Cur AC` fell from 10 to 0 and I was still the safest thing in the room.

**Use the game's own walking, not your own routes.** `l` `>` `g` walks to a
known down staircase, `l` `x` `g` to the nearest unexplored edge, and `M`
draws the whole remembered level in one ask and shows staircases you have
walked past. I spent 70 asks on digit routes before pressing `M`, and depth
1's staircase had been on my own panel the whole time.

## What cost me the most asks

**Not pressing `M` until ask 85.** One ask, and it ended the staircase hunt
on both of the first two levels.

**My own glyph lists.** I wrote a `find()` of my own and never put `>` in it;
`tools/screen/look.py` has listed `>` as a down staircase all along. Run the
shared tool on every screen instead of keeping your own list.

## What I got wrong

**I read the Word of Recall in a dungeon I had just entered and then stood
still for forty turns waiting for it.** The Recall's timer ticks once every
ten game turns, so the shortest wait is 150 turns and the longest 340 (corrected 2026-11-10; this said 350); a cave
spider does 1d4 a turn at speed 120, and I had 26 of 43 hit points. **That is
what killed the run.** Read it and keep walking, or read it next to the up
staircase, or do not read it. A Warrior with oil and a dagger should never
stand still in the dark.

**I believed the inherited note that a level has one down staircase.** It has
three or four (`gen-cave.c:1291`, `rand_range(3, 4)`), each on a square with
exactly three adjacent walls — a corridor end — at least 16 tiles from the
others. I found three on three different levels once I knew to look for the
shape.

## What this class cannot do, ever

**A Warrior can never dig.** `class.txt` gives it `skill-dig:0:0` and no
points a level, and `calc_digging_chances()` needs digging skill over 10 for
magma and over 20 for quartz. So every vein is a permanent wall — and the `*`
glyph is a vein **with treasure in it** (`%` is a plain one), which means
every `*` on every level is money this class cannot have. A Shovel does not
change it. For a Warrior a treasure vein is a landmark, nothing more.

## What a kill is worth, and which ones to take

Experience is `(monster exp x monster level) / your level`
(`mon-util.c:1080`), so the same monster pays a quarter as much at CL4 as at
CL1: at CL2 a 3-experience soldier ant pays 1, and at CL3 a 5-experience
kobold pays 1 as well. My climb to CL4 cost four ants, a lizard, a centipede,
five worm masses, a grey mould and a kobold shaman. The kills worth taking are
the ones that carry something: the small kobold (`DROP_60`) on depth 1, and
the kobold, soldier, acolyte and apprentice on depth 2.

## What I would try next

1. **Oil at range against everything on depth 2**, counting flasks per kill,
   so the next Warrior knows what fifteen flasks actually buys.
2. **A Recall read while walking**, to measure the real wait in game turns
   from the screen rather than from the source.
3. **A level left by `<` then `>`** instead of swept, now that three or four
   staircases per level is known — it should be two or three asks to a fresh
   level with fresh monsters near the exit.

## From `mmx-war-1`, 2026-11-10

## From `mmx-war-1`, 2026-11-10

## What mmx-war-1 measured about the Warrior (seed 271, Half-Elf, 140 asks, depth 2, CL4, died to a silver mouse)

**Buy a Cure Light Wounds before anything else.** This run bought 20 flasks
of oil, a Magic Mapping scroll and a Phase Door, and **no heal at all**. A
grey mould (two blows of 1d4, so 8 a turn) cornered me at 4 HP and the only
certain heal was the kit's Potion of Berserk Strength — which heals 30 but
takes **10 armour class**, so every monster thereafter hit me about a third
more often. One Cure Light Wounds is 20 gold and it would have been the
difference between a run and a corpse. Our own COMMON.md says "one heal, one
escape, then oil and armour"; I did not follow it.

**If you are going to escape, teleport FIRST and heal second.** A Scroll of
Phase Door resolves before the monster's attack, so reading it while a
mould is next to you gets you out of its reach; drinking the Berserk
Strength in the same turn leaves you next to it with 10 less armour class.
Order matters and it cost me three decisions to work out.

**The kit dagger is better than the manual's "1d1" suggests: 1d4+3, to-hit
84, 2.77 blows a turn.** Against AC 9-24 that is 79-92% per blow, so
melee is right for the soft monsters and hopeless for the armoured ones. A
15-HP apprentice dies in one turn. A 23-HP soldier (2 x 1d7, up to 14 a
turn) needs two turns and will kill a CL1-2 Warrior with 19-32 HP — **do
not fight a soldier in melee at all**, and remember that the monsters on
depth 2 hit for twice what the depth-1 ones do.

**Depth 1 is for experience, depth 2 is for killing.** A small kobold pays 5
experience at CL1; a giant black ant on depth 2 pays 8 at CL2 and 16 at CL1.
I spent 99 decisions finding depth 1's staircase and 22 on depth 2, and the
depth-2 kills paid for three character levels.

**The silver mice are the depth-2 killer for a low-level Warrior.** Eleven
of them in one room, 2 HP each, 1d2, and they multiply: killing them one at
a time took me from 22 to 57 experience (CL2 to CL4) and then killed me at
35/35 HP. A long digit chain into that room is how it happened.

**Look before you send a long chain.** A 59-key chain into a room I had not
looked at cost me 15 hit points to two grey moulds; a 60-key chain into the
mouse room cost me the run. The panel shows the monsters; one `l` or one `M`
before the chain is worth more than the chain.
