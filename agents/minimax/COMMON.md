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

**The town has a down staircase, and you start standing on it.** OBSERVED,
minimaxflash-2: the status line says `Down staircase` in town before you have
pressed anything, and `>` goes straight to depth 1. The source says why:
`src/gen-cave.c` `town_gen_layout()` ends with `square_set_feat(c, pgrid,
FEAT_MORE);` and then `player_place(c, p, pgrid);` — the player is placed on
the town's staircase, which sits on the north wall. **One less staircase hunt
than every report in this repository has assumed**, and the manual's list of
ways down does not mention it.

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

ADDED, minimaxflash-2: it is also **more than 16 tiles away from the level's up
staircase in x or y**. `src/gen-cave.c` `handle_level_stairs()` sets `minsep =
MAX(MIN(c->width, c->height) / 4, ...)` = 16 for a 198×66 level, and
`alloc_stairs()` refuses any square within 16 in both coordinates of an
existing staircase. So the down staircase is never in the up staircase's room —
but it can be anywhere else, and "anywhere else" is 13,000 squares.

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

**Where the aim lands decides whether the walk works at all.** CORRECTION,
minimaxflash-2: the paragraph above is right about the cursor and wrong about
the aim. `find_path()` sets `only_known = square_isknown(start) &&
square_isknown(dest)`, so an **unknown** destination takes the
"unknown grids are passable" fallback, and `patched_distances_to_path()`
reconstructs that path backwards from a destination whose distance was never
set — the result is a short, meaningless path. Measured in minimaxflash-2:
aim 3 tiles west → **3 steps**; aim 10 → **0 steps**; aim 20 → **0**; aim 40
→ **1**. Six aims in four directions produced no movement and no complaint,
exactly as `minimaxflash-1.3` reported. **An unknown destination does not
work, however far you aim it.** An aim at a **known** square is a different
command entirely: `only_known` is true, the path is computed properly over
remembered ground, and it is long. Measured in minimaxflash-2: aiming at the
level's up staircase, 26 tiles east and 8 south, gave **31 steps in one ask**
(310 turns). A staircase, a door, a piece of floor you have seen — anything
known is a good aiming point, and it is the only kind that works.

And the reliable way to move into new ground is `lxg` — look, jump the cursor
to the nearest unexplored square, walk there. Measured in minimaxflash-2:
**1 to 31 steps per ask**, and it never fails, because the square it aims at
is adjacent to ground you have already seen.

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

OBSERVED, minimaxflash-2: the game can also be left sitting in the
look/targeting mode **by a movement command that has just finished**, and the
reliable tell is the line `Press '?' for help.` at the very bottom of the
screen (the targeting mode's own prompt, `src/ui-target.c:1302`). While that
line is there every key is eaten until `\e` is pressed. The symptom I saw
was a `Direction or <click> (Escape to cancel)?` prompt: that is **`a` =
"Aim a wand"** (the keymap binds `a` to the wand command) asking for a
direction, with everything after it eaten. It cost five asks in
minimaxflash-2. **One command per ask after any movement, and `\e` first if
the screen shows `Press '?' for help.`**

**A `-more-` swallows the next key**, so end a key string with a space.
A stair descent and a Deep Descent each end in one.

**The Enter key is carriage return, not newline — but the reason is the
harness, not the game.** `R50` followed by `\n` leaves the rest prompt
sitting there with `50` in it and **no turn passes**; the same command with
`\r` rests 500 turns. Three asks in `minimaxflash-1.3`, and it is in none of
the manuals. CORRECTION, minimaxflash-2: the game is fine — `src/ui-input.c`
accepts `KC_ENTER` at that prompt, and the runner's frontend turns a
**two-character** `\n` (backslash, n) into `KC_ENTER` correctly. What the
frontend does with a **literal** newline byte is drop it when it is the last
byte of the file (`patch/src/main-agent.c`: `if (raw[i] == '\n' && i + 1 ==
read) continue;  /* the newline a text editor adds, not a key */`). A literal
CR is not dropped, which is why `\r` worked. **So the Enter is lost only when
it is a real newline at the end of the key string: write the two-character
escape `\n`, or put a space after it.** In bash, `"...\n"` gives the escape and
`$'...\n'` gives the real byte — minimaxflash-2 lost three asks to exactly
that difference.

**Menu letters are labels, not positions.** Read them off the screen. The
**throw prompt has its own letters** (oil is `a` there, `c` in the pack);
the **quaff prompt uses the pack letters**, and `qdq` instead opens the
item menu's *Drop* option.

**Buying is one ask, and selling out renumbers the list.** OBSERVED,
minimaxflash-2: `p`, the row letter, the quantity digits, Enter, and then
**another key** — the Enter is eaten by the quantity string prompt, so the
purchase is not made until you press one more key (the confirmation is
"[ESC, any other key to accept]"). And when the last of an item sells out,
**the whole list renumbers and every letter below it changes**: I bought the
only Soft Leather Armour in the Armoury, and the Wicker Shields below it moved
from `m` to `j`, the Metal Caps from `r` to `q`, and so on. **Read the letter
off the screen after every purchase, never from memory.**

**The rest prompt is pre-filled and one backspace clears it.**
`src/ui-command.c` opens "Rest (0-9999, '!' for HP or SP, '*' for HP and SP,
'&' as needed)" with `& ` already in the field, so `R*` types `& *` and
rests until *healed* rather than until spell points are full. One BACKSPACE
deletes the whole field ("if this is the first time round, backspace means
'delete all'", `src/ui-input.c:702`), so **`R` + BACKSPACE + `*` + Enter** is
the one-ask full rest, and it is how minimaxflash-2 recovered from 0 spell
points in a single ask.

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
string. CORRECTION, minimaxflash-2: **the store tiles are walkable.** I
walked onto the General Store's digit and the status line said `General
Store`; `src/cmd-cave.c` `do_cmd_hold()` (the `,` and `5` commands) tests
`square_isshop(cave, player->grid)` and opens the shop, so **stand on the
digit and press `,`**. The square orthogonally adjacent to the digit is the
way to *reach* the store, not the way to enter it.

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
   spell cost in turns of rest. ANSWERED in part, minimaxflash-2: an
   unknown destination gives a **bogus short path** and a known one gives a
   proper long walk (§1).
7. **Know where you are before you start a hunt.** minimaxflash-2 spent 158
   asks casting a spell that can see a staircase 81 tiles away, on a
   198-tile-wide level, and never found it — because the map panel scrolls
   and the full map (`M`) draws only the *remembered* region, so I could not
   tell whether I was at x = 20 or x = 120, and every cast landed in the same
   40-tile band. **Count tiles walked from the town's staircase, or calibrate
   against the level's 66 rows, before spending the budget on detection.**
   A detector without a position is a random walk.
8. **Spend the shopping money on escapes before you spend it on potions.**
   minimaxflash-2 bought two Cure Light Wounds and two Phase Door scrolls,
   then used neither: it ran out of mana, not out of hit points, and the one
   time it was hurt (a soldier ant, 5 damage) one potion was enough. **One
   heal, one escape, then oil and armour.**

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

**A literal newline at the end of your key string is thrown away.** The
frontend reads the keys file and drops a trailing LF
(`patch/src/main-agent.c`: `if (raw[i] == '\n' && i + 1 == read) continue;`),
so a final Enter sent as a real newline byte never reaches the game; a
literal CR is kept, and the two-character escape `\n` is turned into
`KC_ENTER` as it should be. That is the whole of the "`\n` is not Enter"
rule, and it cost me three asks in minimaxflash-2 to rediscover it: in bash,
`"...\n"` is the escape and `$'...\n'` is the real byte. **Write the escape,
and put a space after it if you are unsure.**
(The runner's `--reason` and `--note` want one line; keep them one line.)

**A `-more-` swallows the next key.** If a screen ends in `-more-`, the
first key of your next answer is eaten — and the rest of your string
misreads. In `minimaxflash-1.3` this cost two failed casts of Stinking
Cloud (`mad` became `d` → "Drop which item?").

**Watch the turn counter.** If it does not move, your keys went somewhere
else: look mode was still up, or a prompt was waiting, or you sent a
command the option does not enable. **The turn counter not moving is the
signal that something is wrong, and it is more reliable than the message
line.** A second tell, found in minimaxflash-2: the line `Press '?' for
help.` at the bottom of the screen means the game is sitting in the
look/targeting mode and eating keys; press `\e` before anything else.

**One command per ask after a movement command.** OBSERVED,
minimaxflash-2: after `*`+digits+`g` or `.`+direction, the keys that follow
are misread — `m` is swallowed by the targeting mode (it means "switch to
interesting mode" there) and the next key can open "Aim a wand", which asks
for a direction and eats the rest of the string. The cast prompt (`m`, the
book, the spell) only works when it is the first thing in an ask.

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

## From `minimaxflash-2.2`, 2026-11-10

### The detection spell breaks the game's own pathfinder

**This is the most expensive thing my family has learned, and it cost two
lives.** Read it before you cast any detection spell.

`Find Traps, Doors & Stairs` is the only spell in the game that can find a
staircase you have not seen. It is also the spell that **makes the game stop
walking you anywhere.**

`src/effect-handler-general.c:1321` (`effect_handler_DETECT_TRAPS`) scans the
`±22 × ±40` window around the player — 81×45 = 3,645 squares — and at line
1376 does:

```c
/* Mark as trap-detected */
sqinfo_on(square(cave, loc(x, y))->info, SQUARE_DTRAP);
```

**on every square in the window, whether or not there is a trap there.** (The
scan loop skips the level's outer border, so the window's own edge is never
marked.)

`src/cmd-cave.c:1146`, inside `run_step`, which is shared by `.` (run) and by
the pathfinder:

```c
/* Disturb player if the player is about to leave the area */
if (player->upkeep->running
        && !player->upkeep->running_firststep
        && old_dtrap && !new_dtrap) {
    disturb(player);
    player->upkeep->energy_use = 0;
    return;
}
```

`old_dtrap` is "the square I am standing on has SQUARE_DTRAP". **So every
time a walk steps off a trap-detected square, the walk stops.** Only the
*first* step of any walk is exempt (`running_firststep`).

Measured in minimaxflash-2.2: with the level marked by earlier casts, `l>g`
to a known staircase 36 tiles away moved **one or two tiles per ask, for a
hundred asks**. The prior life's eleven casts had left a mesh of unmarked
seams between the eleven 81×45 blocks, and every path across a seam stopped.

**What this means for you, in order of value:**

1. **Plain digit walking is immune.** `do_cmd_walk` (`cmd-cave.c:1277`) has no
   dtrap test, no running test and no object test. `44` moved me two tiles
   west in one ask, every time, with no interruption. **If a walk is being cut
   short, use digits.**
2. **A fresh level has no dtrap squares at all.** minimaxflash-2.2 cast Find
   Stairs once on depth 2 and found the depth-2 staircase **in one ask**; the
   path to it lay inside the block the spell had just made, and the walk went
   all the way. **This is the spell working as intended, and nobody in this
   family had ever tried it on a level the spell had not already broken.**
3. **The fix on a broken level costs one spell point.** Cast again from a
   position whose window covers the whole path: the second cast marks every
   square in the window again, seams included. minimaxflash-2.2 cast from 8
   tiles too far north (the staircase was 24 rows south, the window is ±22
   rows) and the walk still stopped; it cast again from closer and the path
   went through.
4. **The spell only reports ground it has not already scanned**, so a second
   cast says nothing — but it still marks the whole window. **A cast that
   "fails" (says "You sense no traps") has usually done its real work.**

`manuals/INSTRUCTIONS.md` §8 describes this spell and recommends casting,
aiming a `g`, and casting again. **That is the strategy the spell breaks.**

### CORRECTION to §5.7: the staircase hunt failed because of the spell, not the position

§5.7 says: *"Know where you are before you start a hunt… A detector without a
position is a random walk."* **That was wrong, and minimaxflash-2.2 proved
it in the first ask.** Pressing `M` — one ask — showed the depth-1 down
staircase *already remembered*, at box (49,17), about 36 tiles west and 16
south of where the character stood. The game had known it all along; nobody
had pressed `M`. **The real cause of the 158 asks was that the spell itself
breaks the game's pathfinding (above). The real cause of my own 100-ask hunt
was the same flag.** Do not spend asks counting tiles to find out where you
are; spend one ask on `M`.

### `M` is the one ask that finds a remembered staircase

§2 says `M` is "not the whole level" and that I spent 8 asks on it for
nothing. That was true of the *scaled box*, which is about **2.5 level tiles
per box tile** and cannot be used to plan a route. But `M` **draws a `>` that
was seen earlier**, even when the scrolling main panel has lost it: in
minimaxflash-2.2 the very first `M` of the run showed depth 1's down
staircase at box (49,17). **Press `M` before you cast anything.**

### `l>` is the only exact distance measurement in the game

In look mode, `>` calls `path_nearest_known(..., square_isdownstairs, ...)`
(`ui-target.c:1507`) and parks the cursor on the nearest *known* down
staircase, and the screen then prints the offset **from the player to that
square** as `"N N, N W"` (`target.c:370`, `coords_desc`). minimaxflash-2.2
used this every few asks to measure progress: *"You recall a down staircase,
18 S, 30 W"*. **This is the answer to "where am I" that no other screen
gives**, and it survives the panel scrolling, which is why the panel's own
coordinates are useless for measuring anything.

### Why the throw list has its own letters

§2 says the throw prompt has its own letters and that oil was `a` there and
`c` in the pack. **That note was right and I did not believe it; my first
attempt (`vc`) was wrong.** The reason (`ui-object.c:855`): the throw list is
built from `all_letters_nohjkl` — the same alphabet as the pack — but it
lists **only the throwable items**, so the letter is the item's *position
among the throwables*, not among everything. The screen says so: *"Throw
which item? (Throwing items: a-a, / for Inven, ESC)"*.

**And pack letters shift when an item is used.** minimaxflash-2.2 drank a
Potion of Cure Light Wounds (letter `d`), and the Scrolls of Phase Door
became `d` and the Scroll of Word of Recall became `e`. **At 2 hit points
with three monsters adjacent I nearly guessed a letter instead of reading
the prompt. Read the prompt.**

### Against AC 36 oil is not an attack, it is a lottery ticket

§3 says AC decides what oil can hit. Sharply: my thrown oil is to-hit 11 and
`hit_chance()` (`player-attack.c:196`) computes `numerator = MAX(0, to_hit -
2·AC/3)`, so against AC 36 that is `MAX(0, 11 - 24) = 0` and the roll lands
on the flat **12 %** floor. With 9–36 damage that is **2.7 expected damage
per throw**, so Fang (25 HP, AC 36) needed about nine flasks, during which a
cave spider and a centipede ate me down to 2/16 hit points. **A spell that
ignores armour is worth far more than oil against an armoured monster** —
Magic Missile is 1 SP for 6–15 damage and never resists. **Do not fight
AC-30 monsters with oil at all.**

### The class armour-weight allowance counts worn armour only, and it is one spell point per TEN pounds over

`player-calcs.c:1505` sums the weight of *worn* armour — the weapon, bow,
rings, amulet and light are all excluded — and then
`msp -= (cur_wgt - class->magic.spell_weight) / 10`. The Mage's `class.txt`
line is `magic:1:300:5`, so `spell_weight` is 300 tenths of a pound =
**30 lb**. My worn armour was 20.5 lb, so no penalty, and **the 36 lb of oil
in my pack cost nothing at all.** `manuals/INSTRUCTIONS.md` §2 says "one
spell point per pound over (Mage/Necromancer 30 lb)" — **the game divides by
ten, so the manual is out by a factor of ten.**

### A locked door at depth 1 is a 36–40 % roll, not a wall

Nothing in the manual or in this page mentions locked doors. `cmd-cave.c:186`
computes `MAX(2, skill - 4 * lock_power)` (`player-calcs.c:1676`), where
`skill` is disarm-phys and `lock_power` is `m_bonus(7, player->depth)`
(`cmd-cave.c:749`) — at depth 1 that is **0 or 1**, so the chance is 40 % or
36 %. My Mage/Gnome disarm-phys is 40 (class base 30 + race 10). **I opened a
locked depth-1 door in four attempts.** `no_light(player)` — the third
argument — asks whether **my own square** is lit, not whether I have seen
the lock, so standing in torchlight does not divide the skill by ten.

### When two monsters are adjacent and one of them is well armoured, the escape comes out before the flask

minimaxflash-2.2 died on depth 2 at 2/16 hit points with a Scroll of Phase
Door in the pack, fighting Fang (25 HP, AC 36) with thrown oil — a 12 % hit
rate against AC 36 — while a cave spider and a centipede ate it at the same
time. **The rule is not "the fight is hard"; it is "the fight costs you the
run".** Depth is recorded, not scored: a character that stops alive on depth
2 with full hit points and a full pack has done better than one that dies on
depth 2 having spent its escape ladder. **A scroll that teleports ten
squares is worth more than any number of flasks when the fight is not
winnable.**

## From `minimaxflash-1.4`, 2026-11-10

### The M map is the whole level, scaled down — and it is the only position you can trust

`display_map` (`vendor/angband/src/ui-map.c:761`) computes
`row = (y * map_hgt) / cave->height` and `col = (x * map_wid) / cave->width`
for **every square of the level**, so the M panel is a picture of the entire
198 × 66 dungeon at 78 × 22, not a window into it. My COMMON.md said "M is a
window onto the level"; that was wrong for three lives. What is right is
that it draws only `cave->memory`, so unexplored squares are blank.

The consequence is bigger than the correction: **the M map is the only
honest position in the game.** The main map panel scrolls, and its rows are
drawn *behind* the sidebar, so a row whose sidebar text is one character
short has every glyph on it one column out. I read a scroll as a teleport
(ask 683), and read the panel shift as a walk in the wrong direction twice
(asks 679 and 695). The M map has its own grid and no sidebar over it.

### The experience formula decides whether a character can level at all

`player_kill_monster` (`vendor/angband/src/mon-util.c:1082`):
`new_exp = (mon->race->mexp * mon->race->level) / p->lev`. On depth 1 at
character level 4 that is `mexp / 4` — a small kobold is 1.25 units, a
grey mould 0.75, a mushroom patch 0.25. Level 5 needs 28 units, so **a
depth-1 character at level 4 needs about 23 kills to level, and a level-1
player will never take that deal.** On depth 2 the same formula doubles
(`mexp * 2 / 4`): a giant black ant is 4 units and Grip is 15.

So the class of problem is not "which monster is worth fighting" but "which
depth pays for its kills". **A character that wants to level must go
deeper, and going deeper needs the one staircase the level is hiding.** My
three lives together earned 2 experience units because all three were on
depth 1.

### Lock picking: the formula, the cancel, and the door that does not open

`calc_unlocking_chance` (`vendor/angband/src/player-calcs.c:1676`) returns
`MAX(2, skill - 4 * lock_power)`; the lock level is `randint1(7)`
(`vendor/angband/src/gen-util.c:581`). For a CL4 High-Elf Druid
(`SKILL_DISARM_PHYS` = 30 + 10×3 + 4 = 64) that is **36 to 60 per cent**,
not the 26 per cent my notebook claimed.

Two costs the manual does not mention:

- **A failed pick cancels the rest of the key string.** The game prints
  *"You failed to pick the lock. Cancelled."* — "Cancelled" is the run
  cancel message — so a string of repeated presses is **one attempt per
  ask** against a lock.
- **A picked lock does not move you.** The press picks the lock and leaves
  the character on the near side, so every locked door costs two
  decisions: one to pick, one to step through.

### The aimed walk finds new ground only when its destination is unknown

`find_path` (`vendor/angband/src/player-path.c:1107`) sets
`only_known = square_isknown(start) && square_isknown(dest)`. An aim that
lands on a square you have already seen is pathed over remembered ground
only — a stroll along corridors you have walked. An aim that lands on a
square you have **not** seen is pathed through unknown ground, which the
pathfinder treats as passable, and the walk crosses new territory as it
goes. **Aim further than the edge of what you know.** This settles the
disagreement between my own lives two and three about the same recipe.

And the aimed walk is a slot machine: the cursor clamps to the level
bounds, so a big aim is a request for the **edge** of the level, and the
pathfinder answers with the cheapest route it can find, not the one you
pointed at. Measured over 141 decisions on the same recipe: 0, 1, 1, 3, 9,
23, 24, 26, 32, 33 tiles, wrong way about half the time — **about
seventeen tiles an ask, in no direction you chose.**

### The look-mode walk is the navigator, and it beats the aimed walk

In look mode a direction key does not move the cursor one tile: it
**snaps the cursor to the next interesting square** in that direction — a
door, a monster, an item or a staircase — and the message line names it
with its exact offset. So `l` + a direction + `g` walks you along the
corridor to the next door **in one ask**, six to twelve tiles every time.
`lxg` is the same idea with the frontier instead of the next door; on a
level with a corridor every third segment it advanced one tile an ask,
which is why my notes called it slow.

### `!` cannot be read from a text screen

`object.txt` gives the oil kind `graphics:!:y` **and** the potions
`graphics:!:d`. Only the colour tells them apart and a plain-text player
never sees colour. What I picked up expecting a flask of oil was **four
Potions of Cure Light Wounds**. A `!` on the floor must be looked at.

### Two harness rules that cost me decisions each

- **To leave two menus, send `\e\e`, not `\ee`.** `\ee` is Escape followed
  by the letter `e`. And a trailing key can undo the escape: my `g` re-
  selected the armour in the equipment list and reopened the context menu,
  so the screen came back identical and I wrongly concluded that Escape
  did not work.
- **The keypad is 7 8 9 / 4 5 6 / 1 2 3: 4 is left, 6 is right, 8 is up,
  2 is down.** I got it wrong three times in 141 decisions and each slip
  was invisible — the character moved, the turn counter moved and the map
  looked plausible. The M map is what caught it. If a walk seems to have
  gone nowhere, check the M map before sending another.

### Chests, gold and buffs on depth 1

- **Every chest on this level was empty** (`pval` 0 — "You see nothing
  there to open"), four of them over two lives.
- **A depth-1 gold drop averages about 17** (`make_gold`,
  `vendor/angband/src/obj-make.c:1296`: `(16 * lev) / 10 + 16`), so gold
  is earned by killing — and killing on depth 1 at level 4 pays a quarter
  of an experience unit a kill. A character with 3 gold and no way to earn
  more cannot shop, and that is worth knowing before it plans a trip.
- **A Scroll of Blessing lasts about thirty turns** ("The prayer has
  expired."). It is a minute of play, not a plan.
