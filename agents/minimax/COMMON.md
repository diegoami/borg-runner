# COMMON — what three lives of one character taught me about playing Angband

*Written by the player of `minimaxflash-1`, `minimaxflash-1-again` and
`minimaxflash-1.3`, from those three runs' reports and notebooks. Three
lives of a High-Elf Druid on seed 23: 610 asks, 4,219 keypresses, final
turn 17,281.*

*This file is for future sessions of mine. It is not a general manual —
`manuals/INSTRUCTIONS.md` and `knowledge/NOTES.md` are that. This is the
part that is **mine**: the things I measured, the things I got wrong, and
the judgement calls I would make differently. Where it contradicts the
manual or the notes, it is because I measured it, and it says so.*

*Class-specific material is in [DRUID.md](DRUID.md). Read both if your
character is a Druid; read this one alone otherwise.*

---

## 1. The shape of the problem, and why the asks go where they go

**A dungeon level is 198×66 and the map window is 66×22.** `constants.txt`
has `dungeon-wid:198`, `dungeon-hgt:66`; `ui-term.h` has `SCREEN_WID =
80-13-1 = 66`. A level is about **three screens wide and three tall**, and
`dungeon_profile.txt` ("classic", `params:11:50:200:2`) puts up to 50 rooms
in it. **This single fact explains every "I explored for ever and found no
stairs" report in this repository, including all three of mine.** When a
report says "I mapped a large part of the level", ask what fraction of
13,068 squares that is. My first life mapped the eastern third in 148 asks.

**There is exactly one down staircase per level, placed uniformly at random.**
`gen-cave.c:1584` allocates one `FEAT_MORE`; `gen-util.c:620` puts it on a
square with exactly three adjacent walls; `cave_find_get_grid()`
(`gen-util.c:202`) draws that square by `randint0` over the whole level.
**There is no "it is near the up staircase" or "it is in the biggest room"
rule.** I read this in the source at ask 285 of `minimaxflash-1-again` —
136 asks after the answer had been visible to me. **Read the generator before you
spend a hundred asks hunting.** If you are going to walk a level looking
for a staircase, you are committing to covering thousands of squares, and
you should know that when you start, not afterwards.

**So the staircase must be *seen*, not computed.** Everything the game
offers — the `>` jump to a known staircase, Magic Mapping, Detect Stairs —
requires the staircase to be known already. The only discovery route is
**reading every glyph on every map**. `minimaxflash-1-again` found depth
1's staircase in **one ask** (`l` on a square whose `>` glyph had been on the
map since ask 160) after 148 asks of the previous life had walked past it.

**A staircase you are standing on is not drawn.** When I stood on depth 1's
`>` in `minimaxflash-1-again`, the map drew `.@` with no glyph. On depth 2
I stood on an up staircase and the map drew `#@#` with no `<`. **Only the status line names the
staircase you are on.** A player scanning the map for `>` will never see
their own.

**The `>` jump cannot discover anything.** `path_nearest_known(...,
square_isdownstairs, ...)` (`ui-target.c:1506`) requires `square_isknown`.
On depth 2 it found nothing, because no staircase was known. It is a
convenience for going back to one you have already used.

**Correction to my own notebook, which I got wrong and have now checked
in the source.** I had written that the `>` jump exists *only* in
targeting mode (`*>`) and not in look mode (`l>`). It is not true.
`do_cmd_look` (`ui-knowledge.c:4169`) calls
`target_set_interactive(TARGET_LOOK, -1, -1, true)` — **look mode is a
targeting mode**, and the `true` is `allow_pathfinding`, so `l>`, `l<`
and `lg` all work exactly as the manual says. What I actually saw at
ask 475 of `minimaxflash-1.3` was `l>` producing **no message at all**,
and I read that as "the key is not handled here". It *was* handled: when
`path_nearest_known` finds nothing the code calls **`bell()`**
(`ui-target.c:1506`), and **a bell draws no text**. The cursor simply
did not move. **The manual was right and my note was wrong** — I turned
a silent failure into a missing feature. The lesson is the one in §7:
**the turn counter not moving, and the message line saying nothing,
means the game rejected the key quietly, not that the key does not
exist.**

**Levels are regenerated.** `minimaxflash-1.3` came back to depth 1 after a
Word of Recall and found a **different level**: different terrain, the up
staircase elsewhere, and the `>` jump finding nothing because the staircase
was not merely unseen but not remembered. **So a carry-on that uses Recall
loses the level, and the staircase hunt starts over.**

**If you must cover a level, this is the way.** In targeting mode (`*` —
or in look mode, `l`, which is the same kind of mode as §1 explains)
the **digit keys move the cursor**, one tile per press, and the cursor is
clamped only to the level bounds — so you can aim it into ground you have
never seen. Then `g` asks for a path to that exact grid, and `find_path`
(`player-path.c:1069`) falls back from a known-only path to one crossing
unknown grids when the destination is unknown. **So the walk goes through
unexplored terrain and draws it as it goes.**

```
*  then N repetitions of a direction digit, then g
```

Measured in `minimaxflash-1.3`, one ask each: **170, 290, 310, 320, 330,
390 and 440 turns** (17–29 tiles). The aim must be **large — 30 to 70 tiles**. Aim short and
the destination lands inside a wall and nothing happens at all, with no
error message: six consecutive aims in four directions produced no movement
and no complaint, which is a trap for a player with no map to read.

Two details that cost me asks:

- **`g` leaves targeting mode** (`ui-target.c:1488` sets `done = true`),
  and the next key then cancels the run. `*xg*xg*xg` in one answer is
  **one** walk, not three; the extra keys are eaten by the run still going.
- **The manual's `x` step makes the walk shorter.** `x` is
  `path_nearest_unknown` from the *cursor*, so it snaps back to the
  nearest unexplored square — often right next to you. Drop the `x` and
  aim further.

---

## 2. Reading the screen: the map lies, and it lies in a specific way

**The map's left edge is drawn behind the sidebar.** The map window's
origin is fixed, but the sidebar text is drawn *over* it, so each row of
the map starts at a **different screen column** depending on how long that
row's sidebar text is. **A glyph's real column cannot be read off a row
whose sidebar text is long.** In `minimaxflash-1.3` I built a wrong picture
of where a door was and pathfound at a wall for several asks. This is worse than a stale map:
it looks like a map.

**The remembered map can show floor where there is a wall.** One case
(`minimaxflash-1`, asks 43–44): a square drawn as `.` was a wall, the walk
stopped with *"There is a wall in the way!"*, and the square was then
drawn correctly. An object was also drawn on a square I could not walk
onto. **A planned path is a hint, not a promise — one digit string wastes
one ask, not a fight.**

**`M` is not the whole level.** It is a scaled view of the *remembered*
region, and on depth 2 it was **smaller** than the main map could show (a
7×3 blob at ask 181 of `minimaxflash-1-again`, when the main map had just
drawn a 13-wide room). I spent 8 asks on `M` in that life and got nothing. **The manual's "whole-level
map" reads as if it revealed the level; it does not.**

**`[` is the best one-ask scan in the game.** It prints *"You can see N
monsters:"* with the glyph, the count, the name and the **exact relative
position** of each. After a Detect Life cast it gains a second section,
*"You are aware of N monsters:"*, listing monsters **out of sight** with
their positions and sleep states. The detection sets `MFLAG_SHOW` on every
living monster within 22 rows × 40 columns (`effect-handler-general.c`,
`detect_monsters`). **The spell's own map effect is nearly useless in a
text dump — the *list* is the point**, and the manual never says so.

**In look mode the cursor snaps to the next interesting square.** Press a
direction and it jumps to the next monster, item, door or staircase along
that line, skipping plain floor; press again and it goes further along the
same line. That enumerates the neighbourhood exactly, in one ask, with no
turn cost — in `minimaxflash-1-again` the room west of me came out as *"ant 5W, yellow patch 6W+1S,
book 9W+1N, closed door 10W; grey mould 4E"*. **This is how to reconstruct
geometry without reading a pixel of the map, and it is not in the manual.**

**Look mode stays active and eats your next key.** After `l`, the look mode
is still up and swallows the first key of whatever you send next. The tell
is **a look description in the message line and a turn counter that does
not move** — in `minimaxflash-1-again` I lost four asks to this, sending
`va'` and `va1`
while look mode was still up, watching nothing get thrown. **Press `\e`
first.**

**A `-more-` swallows the next key**, so end a key string with a space.
A stair descent and a Deep Descent each end in one.

**The Enter key is carriage return, not newline.** `R50` followed by `\n`
leaves the rest prompt sitting there with `50` in it and **no turn
passes**; the same command with `\r` rests 500 turns. Three asks in
`minimaxflash-1.3`, and it is in none of the manuals.

**Menu letters are labels, not positions.** Read them off the screen. The
**throw prompt has its own letters** (oil is `a` there, `c` in the pack);
the **quaff prompt uses the pack letters**, and `qdq` instead opens the
item menu's *Drop* option.

---

## 3. Fighting: what the numbers actually do

**AC decides what oil can hit, and it decides it hard.** Oil does 9–36
damage, but the throw is a to-hit roll against the monster's AC, and
`hit_chance()` needs `to_hit ≥ AC×2/3` to beat the flat 12% always-hit.
Measured in `minimaxflash-1-again`: a giant black ant and a small kobold
(AC 24) could be hit from one tile and **missed from two**; a small
kobold needed two flasks at range 1; **Grip (AC 36) could not be hurt by
oil at range 2** — one throw missed outright — but at range 1 the rate
is about 77% and two hits finished it.
**Low-AC targets are worth oil** (worm mass AC 1, mould AC 1, mushroom
patch AC 1, mouse AC 4); **a high-AC monster is only worth oil at one
tile.**

**Confusion is the most crippling condition in the game, whatever your
class.** A grey mushroom patch on depth 1 (`monster.txt`: 2 hp, AC 1,
`NEVER_MOVE`, `SPORE:CONFUSE:1d4` — the 1d4 is the confusion *duration*,
and it deals a point of damage a turn besides) confused me twice in
`minimaxflash-1.3`. Confusion blocks **casting**
(`player-util.c:1103`, *"You are too confused!"*), blocks **running and
exploring** (`cmd-cave.c:1503`), and randomises **every** direction you
give — movement, melee attack and missile throw — with **75% probability**
(`player_confuse_dir`, `player-util.c:1353`). **A confused character
attacks walls and throws oil at nothing, and cannot use a spell at all.**
A Cure Light Wounds cures it for 20 turns. **Do not stand next to one of
these, and keep a potion for it rather than for hit points.** (Why this
is worse for a druid than for other classes is in
[DRUID.md](DRUID.md) §4.)

**A monster's own hit dice are not its damage against you.** Grip bites
for 1d4 and did **2–4** against my AC 12, not 4. Armour class cuts most of
a small die. (`minimaxflash-1-again`.)

**The manual's class blocks are right about the weak points and silent
about the costs.** Each one says what kills the class; none of them says
what the class's *escape* costs, and that is the number that decides
fights.

**Never fight a monster you cannot kill with the weapon you can afford.**
`minimaxflash-1.3` had no Phase Door and no Recall, so every fight had to
be winnable with oil and a whip. I lost HP to a 2-hp mushroom patch because
the fight was not about HP.

**`MULTIPLY` means it breeds while alive.** In `minimaxflash-1`, three
white worm masses became eight in about thirty turns. Killing them stops the breeding; the
`experience` they give is small.

---

## 4. The town is not a safe place to keep things

**Thieves take gold and items, and they can take nearly all of it.** In
`minimaxflash-1-again` a filthy street urchin took 8 of my 26 gold (ask
394); in `minimaxflash-1.3` the same urchin took **15 more** (18 → 3,
ask 412), and a cutpurse took a flask of oil (*"One of your Flasks of oil
(c) was stolen!"*). The countermeasure does not exist, because with
`birth_no_selling` on, selling pays zero. **The practical rule: spend your
gold before you walk far, and do not carry a fortune around town.**

**The Alchemist restocks daily and the stock rotates.** `store_update()`
(`store.c:1422`) runs once per game day and the shopkeeper shuffles on a
1-in-`store_shuffle` chance. In `minimaxflash-1-again` the Alchemist had
**3 Scrolls of Magic Mapping at 65 gold** (ask 399); in `minimaxflash-1`
the same shop had none, and that one visit is why that life concluded
"the Alchemist did not stock one this seed". **That was true of that day only.** The Black Market's
stock is a random object of level `max_depth + 5 … + 20` at **150% of
true value** (`store.c:1164`, `store.c:618`).

**Word of Recall is a free trip and a free heal — if nothing is chasing
you.** Read in the dungeon it sets a timer (`randint0(20) + 15` turns,
`effect-handler-general.c:1145`), shows "Recall" on the status line, and
fires with *"You feel yourself yanked upwards!"*. **The timer is a plain
countdown and is not interrupted by damage**, so it is exactly what
c15 ESC-04 says — not an escape. But in `minimaxflash-1-again` arriving
in town healed me from 28/33 to 33/33 and gave back 2 spell points, and
the character regenerates there.

**Read it in town and you go to depth 1, not your deepest level.**
`src/player-util.c`: "Players who haven't left town before go to level 1",
and `src/game-world.c` decrements the counter once every **ten game
turns**, so 15+1d20 ticks is **150–340 game turns**. One earlier run gave
up after a quarter of the minimum and wrote the scroll off as a dud.

**The town map fits on one screen** (66×22 in two panels), so the stores
are at known coordinates and any shop is reachable by a planned key
string. **The store tiles are not walkable** — the walkable square is the
one orthogonally adjacent to the digit.

---

## 5. Judgement: what I would do differently

These are the decisions I would take back, and they are the same three
mistakes in different clothes.

1. **Look at every glyph, from the first ask.** The whole staircase
   problem on depth 1 was solved in **one ask** in `minimaxflash-1-again`,
   and I spent that life's first three asks on inventory, equipment and
   character screens whose contents I already knew from the inherited
   notes. `i` and `e` are worth one ask each, not six.
2. **Buy the Magic Mapping scroll the first day it is in stock.** It maps
   22 rows × 40 columns around you. **But note the correction from
   `minimaxflash-1-again`: it maps an area, it does not reveal the whole
   198×66 level, and the earlier note "Magic Mapping (65 g) did not help"
   is not evidence against it.** Whether a `>` appears in the 22×40 window is still
   untested — and it is worth one run to settle, because 65 gold is 2.5
   days of a run's oil income.
3. **Do not spend the escape ladder early.** `minimaxflash-1.3`
   inherited a character with **no Phase Door and no Word of Recall** —
   both *spent*, not stolen: `minimaxflash-1-again` burned two Phase Door
   scrolls escaping Grip and read the Recall to come home. **The advice to buy scrolls stops
   being true the moment you use them**, and a carry-on inherits the
   consequence, not the plan. **If you are going to use a scroll, know
   that the next life has one fewer.**
4. **Do not rest against a monster you cannot kill.** In
   `minimaxflash-1-again` I spent about twelve asks trying to regain 1
   spell point while a +10-speed dog chewed on me, took 30 damage, and had
   to burn two Phase Door scrolls to break away. **The oil was working; I simply used the spell as if it
   were free.**
5. **Keep to the budget.** The prompt says about 150 decisions.
   `minimaxflash-1-again` used 251 and `minimaxflash-1.3` used 210. The
   overrun went on a staircase I could not find, against a generator I did
   not read until ask 285 — by which time the answer was already in the
   source.
6. **Read the source early, for the question you actually have.** Every
   hard-won fact in this file came from `vendor/angband/src/`, not from
   more walking. The questions worth asking the source: how many staircases
   does a level have, where are they placed, what does the pathfinder do
   with an unknown destination, what does confusion block, what does a
   spell cost in turns of rest.

---

## 6. What I could not settle, and what would

1. **Is the down staircase findable by walking?** One per level, uniform
   over 13,068 squares. **What would settle it:** a run that spends its
   whole budget on the cursor-and-`g` walk above and scans every map for
   `>`, reporting where it appeared. Nobody has done that with the fast
   walk.
2. **Does Magic Mapping reveal a staircase?** `effect:MAP_AREA`,
   `effect-yx:22:40` — 22 by 40, not the level. **What would settle it:**
   buy one, read it on depth 1, and say whether a `>` appears in the
   window.
3. **Does a level persist across a Word of Recall?** The evidence from
   `minimaxflash-1.3` says **no**. **What would settle it:** record a distinctive
   feature of a level, take the Recall, come back and look for it.
4. **Is a staircase on a rerolled level likely to be findable?** The
   generator places it uniformly on every level, so a reroll is as likely
   to fail as the walk — but it costs one ask and replaces a half-mapped
   level.
5. **How common is a Deep Descent scroll?** `object.txt` gives it
   `level:10` with `alloc:20:1 to 100`, and the manual says "found from
   DL1" — one of the two is wrong. One run read one on depth 1 and went to
   depth 6. **What would settle it:** read the allocation code in
   `obj-make.c` for whether `alloc_min/alloc_max` or `level` governs the
   depth, and run several levels looking for `?` on the floor.

---

## 7. The harness, so the next session does not repeat my mistakes

These cost me real time and are about the tooling, not the game.

**`\n` is not Enter — `\r` is.** The rest prompt will sit there with your
number in it and no turn will pass. Three asks in `minimaxflash-1.3`.
(Also: the runner's `--reason` and `--note` want one line; keep them one
line.)

**A `-more-` swallows the next key.** If a screen ends in `-more-`, the
first key of your next answer is eaten — and the rest of your string
misreads. In `minimaxflash-1.3` this cost two failed casts of Stinking
Cloud (`mad` became `d` → "Drop which item?").

**Watch the turn counter.** If it does not move, your keys went somewhere
else: look mode was still up, or a prompt was waiting, or you sent a
command the option does not enable. **The turn counter not moving is the
signal that something is wrong, and it is more reliable than the message
line.**

**`>` off a staircase prints "I see no down staircase here."** It does not
auto-navigate, because `autoexplore_commands` is **off by default** and
`manuals/INSTRUCTIONS.md` says plainly that options may not be changed
here. So bare `>` is not a substitute for `*>` or `l>`.

**The `>` jump to a known staircase works in look mode (`l>`) as well as
targeting mode (`*>`),** because look mode is a targeting mode
(`do_cmd_look` → `target_set_interactive(TARGET_LOOK, …, true)`). Both
need the staircase to be **known**; when it is not, the game rings a
**bell**, which in a text dump prints nothing at all — so a silent screen
is what a failed jump looks like.

**The targeting cursor is drawn as a literal `*` in the map**, so a
plain-text player can *see* it move. That is the only position in the game
I would trust over reading the map.

**`archive` copies `runs/<run>/REPORT.md` into `records/<run>/REPORT.md`.**
If you write the report *after* `archive`, it is not in the archive, and
`runs/` is not in git — so the account of your own run is simply gone, and
a later session will conclude it never existed. **This happened to
`minimaxflash-1.3`**: a later session read the gap, decided the report had
never existed, and wrote a reconstruction over it. **Write the report before
you run the finishing commands, or write it into `records/` directly.**
(The prompts now say this first; the first two of my lives did not, and
the third lost its report to exactly this.)
