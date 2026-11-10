# COMMON — what seven runs of minimax have learned about playing Angband

*Begun by the player of `minimaxflash-1`, `minimaxflash-1.2` and
`minimaxflash-1.3` — three lives of a High-Elf Druid on seed 23, 610 asks —
and folded together on 2026-11-10 with what `minimaxflash-2`,
`minimaxflash-2.2`, `minimaxflash-1.4` and `minimaxflash-3` added: a Gnome
Mage that died on depth 2, a fourth Druid life that swept a level for 140
asks, and the family's first Warrior, dead on depth 2 with a Word of Recall
unwalked. Every block names the run it came from; where two runs disagreed,
the later measurement is in the text and the older claim is corrected where
it stood.*

*This file is for future sessions of mine. It is not a general manual —
`manuals/INSTRUCTIONS.md` is that, and it is now ahead of this page on the
facts: read it first and treat it as the authority where the two differ. What
belongs here is what is **mine**: what I measured, what cost me asks, what I
got wrong.*

*Class-specific material is in [DRUID.md](DRUID.md), [MAGE.md](MAGE.md) and
[WARRIOR.md](WARRIOR.md). Read the one for the character you have, and this
one always.*

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

**CORRECTED: a level has THREE OR FOUR down staircases, not one.** This page
said "exactly one down staircase per level, placed uniformly at random" for
three lives, read at ask 285 of `minimaxflash-1.2` out of
`gen-cave.c:1584` — which is the **labyrinth** generator, and labyrinths are
not what this build plays at these depths. `classic_gen` and `modified_gen`,
the only two profiles with an `alloc` at depth 1 (90 and 97 in
`dungeon_profile.txt`), both ask for `rand_range(3, 4)` down staircases and
`rand_range(1, 2)` up (`gen-cave.c:1291`), each on an empty square with
exactly three adjacent walls and at least 16 tiles from the others
(`gen-util.c:620`). `minimaxflash-3` found three staircases on three
different levels and read the generator properly; see its block in §2.
**What survives of the old note:** there is no "near the up staircase" rule,
and the squares they sit on are corridor ends — which is a shape you can walk
to, and a better lead than any coverage argument. What dies with it is the
whole "I must cover 13,068 squares to find the one staircase" framing that
cost this family three lives of sweeping.

ADDED, minimaxflash-2: it is also **more than 16 tiles away from the level's up
staircase in x or y**. `src/gen-cave.c` `handle_level_stairs()` sets `minsep =
MAX(MIN(c->width, c->height) / 4, ...)` = 16 for a 198×66 level, and
`alloc_stairs()` refuses any square within 16 in both coordinates of an
existing staircase. So the down staircase is never in the up staircase's room —
but it can be anywhere else, and "anywhere else" is 13,000 squares.

**So the staircase must be *seen*, not computed.** Everything the game
offers — the `>` jump to a known staircase, Magic Mapping, Detect Stairs —
requires the staircase to be known already. The only discovery route is
**reading every glyph on every map**. `minimaxflash-1.2` found depth
1's staircase in **one ask** (`l` on a square whose `>` glyph had been on the
map since ask 160) after 148 asks of the previous life had walked past it.

**A staircase you are standing on is not drawn.** When I stood on depth 1's
`>` in `minimaxflash-1.2`, the map drew `.@` with no glyph. On depth 2
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

### The experience formula decides whether a character can level at all — `minimaxflash-1.4`

`player_kill_monster` (`vendor/angband/src/mon-util.c:1082`):
`new_exp = (mon->race->mexp * mon->race->level) / p->lev`. On depth 1 at
character level 4 that is `mexp / 4` — a small kobold is 1.25 units, a
grey mould 0.75, a mushroom patch 0.25. CL5 needs **36 more units** for this
High-Elf (the ladder is 10/25/45/70 before the race factor and High-Elf is
145%, so CL4 is 65 and CL5 is 101 — this block said 28, which was wrong and
made the deal look better than it was), so **a depth-1 character at level 4
needs about thirty kills to level, and a level-1 player will never take that
deal.** On depth 2 the same formula doubles
(`mexp * 2 / 4`): a giant black ant is 4 units and Grip is 15.

So the class of problem is not "which monster is worth fighting" but "which
depth pays for its kills". **A character that wants to level must go
deeper, and going deeper needs the one staircase the level is hiding.** My
three lives together earned 2 experience units because all three were on
depth 1.

### Chests, gold and buffs on depth 1 — `minimaxflash-1.4`

- **Every chest on this level was empty** (`pval` 0 — "You see nothing
  there to open"), four of them over two lives.
- **A depth-1 gold drop averages about 17** (`make_gold`,
  `vendor/angband/src/obj-make.c:1296`: `(16 * lev) / 10 + 16`), so gold
  is earned by killing — and killing on depth 1 at level 4 pays a quarter
  of an experience unit a kill. A character with 3 gold and no way to earn
  more cannot shop, and that is worth knowing before it plans a trip.
- **A Scroll of Blessing lasts about thirty turns** ("The prayer has
  expired."). It is a minute of play, not a plan.

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
7×3 blob at ask 181 of `minimaxflash-1.2`, when the main map had just
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
turn cost — in `minimaxflash-1.2` the room west of me came out as *"ant 5W, yellow patch 6W+1S,
book 9W+1N, closed door 10W; grey mould 4E"*. **This is how to reconstruct
geometry without reading a pixel of the map, and it is not in the manual.**

**Look mode stays active and eats your next key.** After `l`, the look mode
is still up and swallows the first key of whatever you send next. The tell
is **a look description in the message line and a turn counter that does
not move** — in `minimaxflash-1.2` I lost four asks to this, sending
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

### The detection spell breaks the game's own pathfinder — `minimaxflash-2.2`

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

### `M` is the one ask that finds a remembered staircase — `minimaxflash-2.2`

§2 says `M` is "not the whole level" and that I spent 8 asks on it for
nothing. That was true of the *scaled box*, which is about **2.5 level tiles
per box tile** and cannot be used to plan a route. But `M` **draws a `>` that
was seen earlier**, even when the scrolling main panel has lost it: in
minimaxflash-2.2 the very first `M` of the run showed depth 1's down
staircase at box (49,17). **Press `M` before you cast anything.**

### `l>` is the only exact distance measurement in the game — `minimaxflash-2.2`

In look mode, `>` calls `path_nearest_known(..., square_isdownstairs, ...)`
(`ui-target.c:1507`) and parks the cursor on the nearest *known* down
staircase, and the screen then prints the offset **from the player to that
square** as `"N N, N W"` (`target.c:370`, `coords_desc`). minimaxflash-2.2
used this every few asks to measure progress: *"You recall a down staircase,
18 S, 30 W"*. **This is the answer to "where am I" that no other screen
gives**, and it survives the panel scrolling, which is why the panel's own
coordinates are useless for measuring anything.

### A locked door at depth 1 is about a 24 % roll, not a wall — `minimaxflash-2.2`

Nothing in the manual or in this page mentions locked doors. `cmd-cave.c:186`
computes `MAX(2, skill - 4 * lock_power)` (`player-calcs.c:1676`), where
`skill` is disarm-phys and `lock_power` is stored at generation by
`gen-util.c:581` `square_set_door_lock(c, grid, randint1(7))` — so **1 to 7**,
and the chance at skill 40 is 36 % down to 12 %, about 24 % on average.
(Corrected 2026-11-10: this block said `m_bonus(7, player->depth)` at
`cmd-cave.c:749`, so 0 or 1 and "40 % or 36 %" — that call is the
door-*jamming* path, not the lock being picked.) My Mage/Gnome disarm-phys is
40 (class base 30 + race 10). **I opened a locked depth-1 door in four
attempts.** `no_light(player)` — the third argument — asks whether **my own
square** is lit, not whether I have seen
the lock, so standing in torchlight does not divide the skill by ten.

### The M map is the whole level, scaled down — and it is the only position you can trust — `minimaxflash-1.4`

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

### The M map cannot hide a staircase, and the panel is 1:1 but jumps — `minimaxflash-1.5`

Two halves of the same instrument, both measured, and the second one cost
this life several decisions because I had it wrong for a week.

**The map panel is one tile to one with the level.** It shows 66 × 22 of a
198 × 66 dungeon, so within one screen every distance is exact. What is not
exact is the *offset*: `verify_panel_int` (`vendor/angband/src/ui-output.c:587`)
scrolls the window when the player comes within three squares of an edge,
and it scrolls to `px - panel_wid`, i.e. in jumps of 33 columns and 11 rows.
So panel columns are not level columns and they move under you. The fix is
to compare the two maps once: take the M map, find the player in it, and
find the player on the panel, and the difference is the offset. (I read
panel columns as level columns for a week and wrote the wrong figure into
my own notebook twice; the previous life's "level column ten" was two
columns out, and the M map proves level columns 0 to 50 had never been
seen.)

**The M map cannot hide a down staircase.** `display_map` keeps a priority
array `mp[row][col]` and only overwrites a cell when the new square has a
*higher* priority — `if (mp[row][col] < tp)` — and in `terrain.txt` both
`LESS` and `MORE` carry `priority:25`, the highest of any terrain (floor
5, open door 15, closed door 17, store 20, magma 12). **A remembered
staircase always wins its cell.** So "there is no `>` on the M map" is
evidence about the level, not about the drawing, and the M map is the one
instrument in the game that can answer "have I been past one?".

The M map is also the cheapest coverage instrument there is: I rebuilt the
whole 198 × 66 level from it cell by cell and read off the percentage of
the level that had been remembered — 18.4 % when this life inherited the
character, 29.6 % when it died. **A player who never presses `M` cannot
know whether the sweep is going anywhere.**

### Lock picking: the formula, the cancel, and the door that does not open — `minimaxflash-1.4`

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

### The aimed walk finds new ground only when its destination is unknown — `minimaxflash-1.4`

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

### The look-mode walk is the navigator, and it beats the aimed walk — `minimaxflash-1.4`

In look mode a direction key does not move the cursor one tile: it
**snaps the cursor to the next interesting square** in that direction — a
door, a monster, an item or a staircase — and the message line names it
with its exact offset. So `l` + a direction + `g` walks you along the
corridor to the next door **in one ask**, six to twelve tiles every time.
`lxg` is the same idea with the frontier instead of the next door; on a
level with a corridor every third segment it advanced one tile an ask,
which is why my notes called it slow.

### A DIGIT STRING RUNS THROUGH EVERY TURN — this is how a level gets crossed — `minimaxflash-1.5`

The single most expensive mistake this family has made with the movement
keys, and it is not in any manual: **a string of direction digits keeps
going through every turn it can.** It stops at the first wall and the rest
of the string is dropped — so `"666222"` walks east three and then south
two, in one ask, provided the path is clear tile by tile.

The fourth life of the druid (`minimaxflash-1.4`) sent **one direction at
a time**, called every corridor end a wall, and spent a hundred and forty
decisions sweeping two thirds of a level with a rate of about two tiles an
ask. This life wrote a beam search over the panel
(`runs/minimaxflash-1.5/g.py`, kept in the run) that plans a chain of up to
24 keys through floor and into the dark, and the rate went to fifteen
tiles an ask. **A player who writes one chain of keys instead of one
direction per ask covers a level five times faster.**

Two rules the planner needed, both paid for:

- **The first step of a chain must be known floor.** An unknown square may
  be a wall, and a chain whose first step is a wall moves the character
  nowhere at all: sixteen asks of exactly nothing before I saw it. A
  blank on the map is not a floor.
- **Revisiting a square in a chain is worthless**, and a planner that
  maximises *steps* will walk down two and up two for ever.

### The aimed walk's message is about the target, not the walk — `minimaxflash-1.5`

`"Target Aborted."` is `textui_target`'s own message
(`vendor/angband/src/ui-target.c:1028`) and it is printed when the
*targeting* loop ends without selecting a target. **It says nothing about
the pathfind that ran inside it.** The character moved ten tiles on the ask
that printed it, and ten tiles later it was standing beside a down
staircase. The recipe that worked here was `*`, then `p` to put the cursor
in free mode, then forty direction digits, then `g`; without `p` a digit
picks the next *monster* and the walk walks to that instead.

### `!` cannot be read from a text screen — `minimaxflash-1.4`

`object.txt` gives the oil kind `graphics:!:y` **and** the potions
`graphics:!:d`. Only the colour tells them apart and a plain-text player
never sees colour. What I picked up expecting a flask of oil was **four
Potions of Cure Light Wounds**. A `!` on the floor must be looked at.

### `M` costs one ask and finds staircases you have already walked past — `minimaxflash-3`

**`M` costs one ask and finds staircases you have already walked past.**
On depth 1 I explored for 70 asks and the down staircase was drawn on my
own panel the whole time. At ask 85 I pressed `M` and it was there. The
`M` view is the whole remembered level, drawn once, with everything seen
in it — including staircases you have walked by. I found depth 1's `>`
this way and depth 2's `>` on the same screen. **But I missed it for
70 asks because my own glyph lists never checked for `>`** — the shared
`tools/screen/look.py` does list `>` as a down staircase, and my hand
written `find()` lists did not. Run look.py on every screen; do not keep
your own list.

### A level has THREE OR FOUR down staircases, not one — `minimaxflash-3`

**A level has THREE OR FOUR down staircases, not one** (asks 103, 119,
147 — three staircases found on three different levels). `gen-cave.c:1291`
calls `handle_level_stairs(..., rand_range(3, 4), rand_range(1, 2))`, and
`alloc_stairs` (`gen-util.c:620`) puts each one on an empty square with
EXACTLY THREE adjacent walls — a corridor end — at least 16 tiles from
the others. The inherited note "exactly ONE down staircase per level,
uniform over 13,068 squares" comes from the labyrinth generator
(`gen-cave.c:1584`, alloc −1, only chosen by hard-coded tests); the
levels this build actually plays at depth 1-14 are 'classic' (alloc 90)
and 'modified' (alloc 97), and both have several. **A corridor end is a
shape you can walk to; that is a better lead than any coverage
argument.**

### The aim-walk, and the key that breaks it — `minimaxflash-3`

**The aim-walk, and the key that breaks it.** `*` opens the targeting
mode; `p` puts it in free mode, where a digit moves the CURSOR one tile
instead of picking the next interesting grid (without `p` a digit picks
the next monster and the walk walks to it — that is what my first aim
did). Then `g` pathfinds the player to the cursor. Because
`find_path` sets `only_known = (start known AND dest known)`, an unknown
destination makes the whole unknown passable, so the walk crosses ground
nobody has seen; it stops at the first real wall, which is usually one
tile away, because most of a level is wall. **A keypress after `g`
interrupts the walk** (ask 143: my `l>g>` reached the staircase and the
trailing `>` cancelled it). A staircase walk must be the last thing in
an ask.

## 3. Fighting: what the numbers actually do

**AC decides what oil can hit, and it decides it hard.** Oil does 9–36
damage, but the throw is a to-hit roll against the monster's AC, and
`hit_chance()` needs `to_hit ≥ AC×2/3` to beat the flat 12% always-hit.
Measured in `minimaxflash-1.2`: a giant black ant and a small kobold
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
a small die. (`minimaxflash-1.2`.)

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

### Against AC 36 oil is not an attack, it is a lottery ticket — `minimaxflash-2.2`

§3 says AC decides what oil can hit. Sharply: my thrown oil is to-hit 11 and
`hit_chance()` (`player-attack.c:196`) computes `numerator = MAX(0, to_hit -
2·AC/3)`, so against AC 36 that is `MAX(0, 11 - 24) = 0` and the roll lands
on the flat **12 %** floor. With 9–36 damage that is **2.7 expected damage
per throw**, so Fang (25 HP, AC 36) needed about nine flasks, during which a
cave spider and a centipede ate me down to 2/16 hit points. **A spell that
ignores armour is worth far more than oil against an armoured monster** —
Magic Missile is 1 SP for 3d4 (3–12) damage and never resists (corrected 2026-11-10; this line said 6–15, reading the dice count 3 as a bonus). **Do not fight
AC-30 monsters with oil at all.**

### The class armour-weight allowance counts worn armour only — `minimaxflash-2.2`, with its arithmetic corrected

`player-calcs.c:1505` sums the weight of *worn* armour — the weapon, bow,
rings, amulet and light are all excluded — and then
`msp -= (cur_wgt - class->magic.spell_weight) / 10`. The Mage's `class.txt`
line is `magic:1:300:5`, so `spell_weight` is 300 tenths of a pound =
**30 lb**. My worn armour was 20.5 lb, so no penalty, and **the 36 lb of oil
in my pack cost nothing at all** — that part holds, and it is the useful
part: a pack full of oil never costs a spell point.

**CORRECTION, 2026-11-10.** This block went on to say that
`manuals/INSTRUCTIONS.md` was "out by a factor of ten" for saying one spell
point per pound over. It is not: `cur_wgt` is in **tenths of a pound** too —
`object.txt` gives a Flask of oil `weight:20` and the screen shows 21 of them
as 42.0 lb — so `(cur_wgt - 300) / 10` is pounds over the allowance, and the
manual's "one spell point per pound over" is exactly right. The lesson is the
one this page keeps learning: check the units before calling the page wrong,
and `playbook --check` now reads a page's spell numbers against `class.txt`
for the same reason.

### FEAR gives eight points of armour class and takes your attacks away — `minimaxflash-1.5`

The most expensive condition in this life, and it is in no manual and in
none of our notes. A crow's scare blow put the druid into "Afraid", and:

- **the character's armour class went from 12 to 20** and went back to 12
  the moment the fear ended ("You feel bolder now."), with the equipment
  list unchanged the whole time. So **being afraid is worth eight points
  of armour class** — and I could not find the rule for it; all I know is
  what the screen said.
- **the character could not attack at all**: "You are too afraid to attack
  the crow!"
- **the character could not move either**: a step gave "There is a wall in
  the way!" and the turn counter did not move.

Two crows held a druid at three hit points for about eight decisions
because the character was doing nothing at all, and the whole of it was
cured by *time* — a rest of ten turns let the timer run out. **Fear in
this game is a timer, and nothing else cures it: not a potion of Cure
Light Wounds (which the druid had and used on hit points instead), not a
scroll, and not a spell.** The only defence is not to be next to the thing
that frightens you.

### The depth-2 monster table, from `monster.txt` — `minimaxflash-1.5`

The numbers a player needs to decide whether to fight, for the four `p`
monsters of depth 2 (all worth 6 experience, so **three experience units
each** at character level 4 on depth 2):

| Monster | hp | AC | blow | note |
|---|---|---|---|---|
| soldier | 23 | 24 | 2 × 1d7 (up to 14 a round) | the whip cannot touch it |
| cutpurse | 20 | 18 | 1d6 + steals gold | |
| acolyte | 18 | 15 | 1d5 | the one the druid killed twice |
| apprentice | 15 | 9 | 1d4 | the only one the whip likes |

And the level-2 natives that pay properly: a **giant black ant** is 11 hp,
armour class 24, 1d2 and 8 experience (four units at level 4) — **the best
trade on the level, because it hits for one or two.** A white harpy is
armour class 24 with 10 experience (five units) and dies to about twelve
whip swings.

## 4. The town is not a safe place to keep things

**Thieves take gold and items, and they can take nearly all of it.** In
`minimaxflash-1.2` a filthy street urchin took 8 of my 26 gold (ask
394); in `minimaxflash-1.3` the same urchin took **15 more** (18 → 3,
ask 412), and a cutpurse took a flask of oil (*"One of your Flasks of oil
(c) was stolen!"*). The countermeasure does not exist, because with
`birth_no_selling` on, selling pays zero. **The practical rule: spend your
gold before you walk far, and do not carry a fortune around town.**

**The Alchemist restocks daily and the stock rotates.** `store_update()`
(`store.c:1422`) runs once per game day and the shopkeeper shuffles on a
1-in-`store_shuffle` chance. In `minimaxflash-1.2` the Alchemist had
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
c15 ESC-04 says — not an escape. But in `minimaxflash-1.2` arriving
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
   problem on depth 1 was solved in **one ask** in `minimaxflash-1.2`,
   and I spent that life's first three asks on inventory, equipment and
   character screens whose contents I already knew from the inherited
   notes. `i` and `e` are worth one ask each, not six.
2. **Buy the Magic Mapping scroll the first day it is in stock.** It maps
   ±22 rows × ±40 columns around you (44×80; corrected 2026-11-10, this
   block read the half-extents as the window). **But note the correction from
   `minimaxflash-1.2`: it maps an area, it does not reveal the whole
   198×66 level, and the earlier note "Magic Mapping (65 g) did not help"
   is not evidence against it.** Whether a `>` appears in the 44×80 window is still
   untested — and it is worth one run to settle, because 65 gold is 2.5
   days of a run's oil income.
3. **Do not spend the escape ladder early.** `minimaxflash-1.3`
   inherited a character with **no Phase Door and no Word of Recall** —
   both *spent*, not stolen: `minimaxflash-1.2` burned two Phase Door
   scrolls escaping Grip and read the Recall to come home. **The advice to buy scrolls stops
   being true the moment you use them**, and a carry-on inherits the
   consequence, not the plan. **If you are going to use a scroll, know
   that the next life has one fewer.**
4. **Do not rest against a monster you cannot kill.** In
   `minimaxflash-1.2` I spent about twelve asks trying to regain 1
   spell point while a +10-speed dog chewed on me, took 30 damage, and had
   to burn two Phase Door scrolls to break away. **The oil was working; I simply used the spell as if it
   were free.**
5. **Keep to the budget.** The prompt says about 150 decisions.
   `minimaxflash-1.2` used 251 and `minimaxflash-1.3` used 210. The
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

### CORRECTION to §5.7: the staircase hunt failed because of the spell, not the position — `minimaxflash-2.2`

§5.7 says: *"Know where you are before you start a hunt… A detector without a
position is a random walk."* **That was wrong, and minimaxflash-2.2 proved
it in the first ask.** Pressing `M` — one ask — showed the depth-1 down
staircase *already remembered*, at box (49,17), about 36 tiles west and 16
south of where the character stood. The game had known it all along; nobody
had pressed `M`. **The real cause of the 158 asks was that the spell itself
breaks the game's pathfinding (above). The real cause of my own 100-ask hunt
was the same flag.** Do not spend asks counting tiles to find out where you
are; spend one ask on `M`.

### When two monsters are adjacent and one of them is well armoured, the escape comes out before the flask — `minimaxflash-2.2`

minimaxflash-2.2 died on depth 2 at 2/16 hit points with a Scroll of Phase
Door in the pack, fighting Fang (25 HP, AC 36) with thrown oil — a 12 % hit
rate against AC 36 — while a cave spider and a centipede ate it at the same
time. **The rule is not "the fight is hard"; it is "the fight costs you the
run".** Depth is recorded, not scored: a character that stops alive on depth
2 with full hit points and a full pack has done better than one that dies on
depth 2 having spent its escape ladder. **A scroll that teleports ten
squares is worth more than any number of flasks when the fight is not
winnable.**

### The Word of Recall is not an escape — `minimaxflash-3`

**The Word of Recall is not an escape** (ask 150, and it killed me). Its
timer ticks once every ten turns, so the shortest wait is 150 turns and
the longest 340 (corrected 2026-11-10; the timer is randint0(20) + 15 = 15-34 ticks of ten game turns). I read it and stood still for forty turns, and a cave
spider killed the character (26/43 HP, 1d4 a turn). Read it and then
walk, or not at all.

## 6. What I could not settle, and what would

1. **Is the down staircase findable by walking?** Three or four per level
   (corrected 2026-11-10; this block said one per level, uniform over 13,068
   squares - that is the labyrinth generator, not what we play), at corridor
   ends, 16 tiles apart. **What would settle it:** a run that spends its
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

### A level you leave is regenerated — `minimaxflash-3`

**A level you leave is regenerated** (ask 148). The `M` view of the depth
2 I came back up to showed 0% remembered — one tile, my own — after 25
asks on that level. The plain version of our standing question 3, and it
costs one ask to re-measure.

### Magic Mapping's window is 44 by 80, not 22 by 40 — `minimaxflash-3`

**Magic Mapping's window is 44 by 80, not 22 by 40** (`object.txt:2609`
`effect-yx:22:40` are half-extents; `effect-handler-general.c:1201`
scans centre ± 22 rows and ± 40 columns) — 3,520 tiles, 27% of a 198×66
level. With three or four staircases per level, one scroll covers one
with about 27% probability and three with about 63%. Our own summary
"22 rows × 40 columns" is the half-extent, so the inherited note
"MM (65 g) did not help" is not evidence against the scroll. Still
unmeasured: buy one, read it on depth 1, and count the `>`.

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

### Why the throw list has its own letters — `minimaxflash-2.2`

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

### Two harness rules that cost me decisions each — `minimaxflash-1.4`

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

### Small things, all measured — `minimaxflash-3`

**Small things, all measured.** A Wooden Torch gives a 3×3 view
(`cave-view.c:658`, radius = |cur_light| − 1). The throw prompt numbers
its own list: oil was `c` in the pack and `a` in the prompt. The rune of
rubble `:` is NOT walkable (`terrain.txt:257` has no PASSABLE) although
`tools/screen/map.py` treats it as walkable, so its routes can be wrong
in the town — I wrote `runs/minimaxflash-3/tools/route.py` to route only
over `.` and `'`. `5` is "stay", and a turn passes. Item kinds get a
flat allocation weight over their whole level range (`obj-make.c:88`),
so on depth 2 the scroll weights are Treasure Detection 50, Light 50,
Phase Door 50, Detect Invisible 50, Blessing 50, Deep Descent 20,
Summon Monster 10, Darkness 10, and Magic Mapping cannot appear before
depth 5.

### Four keys of the harness, each of which cost a decision — `minimaxflash-1.5`

- **The pick-up key is `g`. `,` is "stay a turn".** I spent three
  decisions assuming otherwise, because an earlier life found that `,`
  picked an item up *in look mode*. The proof that a pick-up failed is the
  inventory screen: the scroll was not in it.
- **The pack letters MOVE when items are used up.** A Scroll of Phase Door
  was picked up at letter `e`; after the last two Potions of Cure Light
  Wounds were drunk, the potions' slot was freed and the scroll became
  letter `d`. **A druid that drinks its last potion changes every letter
  above it.**
- **The read prompt lists the FLOOR as well as the pack** — "Read which
  scroll? (Floor: a-a, ESC)" — so an item can be used where it lies, and
  the pick-up is not needed to read it.
- **A `-more-` swallows the next key.** It is in the manual; it cost this
  life one ask anyway, because a quaff message ended in `-more-` and the
  `4` that was supposed to move the character went into it. **Any ask
  that follows a screen ending in `-more-` must begin with a space.**

## From `mmf-mage.2`, 2026-11-10

## What mmf-mage measured (a Gnome Mage, seed 1, 145 asks)

- **A level holds about fifty monsters, so the problem is finding them,
  not fighting them.** `classic_gen` places `level_monster_min +
  randint1(8) + k` of them (`gen-cave.c`, k = `MAX(MIN(depth/3,10),2)`)
  with `pick_and_place_distant_monster(c, p->grid, 0, true, depth)`: the
  "distant" is `dis = 0`, so they are placed at any distance from the up
  staircase, and they start asleep. Fifty on 198x66 is one per 250
  squares, so a ten-tile corridor holds a monster about four per cent of
  the time and a 10x10 room about a third. **A room is worth ten
  corridors, and the detection spell's doors are a map of where the
  rooms are.**
- **On a level you have just entered, the game's own pathfinder cannot
  walk you anywhere.** `find_path` sets `only_known = square_isknown(start)
  && square_isknown(dest)`, so a *known* destination with unknown ground
  in between has no path over remembered ground: `l>g` covered 3, 3, 12
  and 1 tiles on four levels, and an aimed walk with an unknown
  destination one tile. Plain digit strings walk the whole way and stop
  only at a wall, so on a fresh level **digits are the only way to move**
  — and `lxg` was one tile an ask.
- **A failed detection cast prints nothing.** After one cast my
  character sheet read `Cur Exp 0` and the message line was empty,
  while a success prints "You sense ..." and pays the spell's first-use
  experience (2 for Find Traps, the last field of its `class.txt` line).
  **Read `C` after every cast** before you spend another point on the
  same window.
- **The store's `s` command identifies a kind for nothing.** The store
  menu prints only `l`, `p` and `o`, so the trick in §6b of
  INSTRUCTIONS looks unavailable; `s` (or `d`) opens a "Give which
  item?" prompt and `do_cmd_sell` learns the runes even with selling
  off. My unknown potion came back as a Potion of Boldness
  (`CURE:AFRAID`) — worth more as a measurement than as a potion.
- **The staircases are paired against the direction you want.** `<`
  ascends only from an *up* staircase and lands you on a *down*
  staircase of the level above; `>` descends only from a down one (from
  a down staircase `<` did nothing at all and the turn counter did not
  move). The town's down staircase therefore pairs with depth 1's up
  staircase, and leaving depth 2 for the town takes **two** up
  staircases — the Scroll of Word of Recall (read in the dungeon: it
  takes you to the town after 15 to 34 player actions, and a rest of 61
  actions covers the longest wait) is the cheap way home.
- **The `]` glyph is used by boots as well as helms** (`object.txt`: the
  Iron Shod Boots are `graphics:]:U`, the Metal Cap `graphics:]:s`), and
  a text screen cannot tell them apart: I picked up a pair of Leather
  Sandals expecting a helm.
- **A store swallows keys.** A ten-key route sent while the Armoury
  list was still on the screen lost nine of them to the store, and the
  tenth was read as movement ("There is a wall in the way!"); a trailing
  `y` meant as a purchase confirmation landed on the row whose letter
  is `y` and opened that item instead. **Escape out of a store before
  you send a route.**
- **The Character sheet and the monster list are menus that eat keys**:
  `C` leaves a sheet where `c` means "change name", and `[` leaves a
  "press any key" prompt. Each cost me a decision.
- **The shops did not restock inside my game day.** Two visits to the
  same Armoury on the same day showed the same list minus what I had
  bought (the Studded Leather Armour gone, the gloves 16 to 15, the
  gauntlets 6 to 5). The daily restock is real but it did not happen
  between two shopping trips hours apart in game time.

## From `minimaxflash-1.5`, 2026-11-10

## From `mmx-war-1`, 2026-11-10

## What mmx-war-1 measured (seed 271, Half-Elf Warrior, 140 asks, depth 2, CL4, died to a silver mouse)

**A tool that slices the map panel out of a raw screen dump must pad it.**
The dump **strips trailing whitespace**, so a map row that is entirely blank
(unknown ground) comes back as a short line, and every tile on that row reads
as a WALL. Our own beam-search tool (`minimaxflash-1.5/g.py`) had this bug:
it reported "0 unknown squares memorised" and refused to plan into the dark
until I added `.ljust(66)`. The shared `tools/screen/screen.py` already pads
its rows. This cost me most of one run's exploration: the tool was working
perfectly on the screen and I was reading its output as "there is no dark
near me". (ask 34)

**The read and quaff prompts use the PACK letters; the throw prompt renumbers.**
At ask 21 the read prompt said "Read which scroll? (Inven: d-f)" and the
scrolls were at `d`, `e`, `f` — the pack letters, with three other pack
items before them. The quaff prompt is the same. The throw prompt is not: it
lists only the throwables and numbers them from `a`, so my oil was `a` there
and `b` in the pack. **Worn equipment takes no pack letter at all** — the
dagger and the soft leather armour live in the equipment list, so the pack
starts at `a`. My pack, measured on the inventory screen at ask 109:
`a` 3 rations, `b` 20 flasks of oil, `c` Potion of Berserk Strength,
`d` 5 unknown potions, `e` Scroll of Phase Door, `f` Scroll of Word of
Recall, `g` an unknown scroll, `i` Wooden Torch (h, j, k, l are skipped).
Letters MOVE when an item is used or picked up. (asks 21, 52, 109)

**The throw prompt did not finish for me, and it cost four decisions.**
`v` `a` `'` printed "The apprentice is targeted." and then nothing I sent
(`g`, Enter, a direction key) took the shot; only Escape got me out. Before
spending four decisions on a throw, spend one on `[`, which lists the visible
monsters by name — that is what told me the `p` was an apprentice. (asks
129-132)

**The rest command works in one decision and it is far too slow to plan
with.** `R` backspace `*` Enter rests until healed (the backspace really does
clear the whole pre-filled "& " field). But it healed **3 hit points in 100
turns** — 18/32 to 21/32. Resting is not a way to heal inside 150
decisions. (ask 119)

**The Magic Mapping window is 44 rows by 80 columns, and on this seed it held
no down staircase.** Read on depth 1 at the arrival point, the `M` view
afterwards showed 280 of 1716 box tiles with terrain — **16% of the level** —
and no `>`; the staircase turned up on the `M` map at ask 92, 24 boxes
outside the mapped area. That is the third run to read a Magic Mapping
scroll and find no staircase in it (the others: `minimaxflash-1.4`,
`sonnet-2`). The scroll is probably a coin flip, not a fix.

**The depth-1 unknown scroll pool, computed from `object.txt` alloc bands**
(the only scrolls whose band includes depth 1): Phase Door 50, Treasure
Detection 50, Detect Invisible 50, Light 50, Blessing 50, Deep Descent 20,
Summon Monster 10, Darkness 10 — total 290. So an unknown scroll on depth 1
is 17% Phase Door, 17% Treasure Detection, 17% Detect Invisible, 17% Light,
17% Blessing, **6.9% Deep Descent**, 3.4% Summon Monster, 3.4% Darkness.
Magic Mapping and Word of Recall cannot appear before depth 5, which
confirms our own note about the scroll.

**Two monsters the manual's table does not give the reader, both measured on
depth 2.** The **silver mouse** is `depth:4` in `monster.txt` but it spawns
on depth 2 in this build, in a pack of eleven, with `MULTIPLY` and an
`EAT_LIGHT` blow: 2 HP, AC 4, 1d2, one experience each. Killing them one
at a time is how the pack grows. The **grey mould** has **two** blows of
1d4, so it is 8 damage a turn, not 4.

**A letter is a monster only if the monster's colour says so: the glyph is
in `monster_base.txt`.** The `C` on my depth-1 screen was the *canine* base
(wild dog), not a centipede; `monster.txt` has no `color:C` at all. Look the
base up before you decide what a letter is.

**A `-more-` swallows the first key of the next ask** (confirmed again: my
`g` pickup was eaten at ask 33 and the rest of the chain still ran). And a
digit chain walks into whatever is standing in the dark: the chain of ask 140
killed about thirty-five silver mice in one decision and then killed me.
## From `mmx-pri-1`, 2026-11-10

## What I measured, 2026-11-10 (seed 17, a Dwarf Priest, 149 asks, stopped alive on depth 1)

### A breeding monster is a tax on every ask, and it is arithmetic

A giant white mouse has 2 hit points, 1d2 of damage and the MULTIPLY flag;
one of them became eight in about fifteen turns. I fought them in a one-wide
corridor, where only the mouse in front of me could reach me, and the first
four cost me **nothing**: my blow happens first in the turn, so a mouse I
kill never bites me. Then I walked a 38-digit route west with them at my
back and it cost **22 hit points in one ask**.

The lesson is the one I keep having to learn in a new shape: **the cost of
a monster is per ASK, not per kill.** A run with 50 asks left and 24 hit
points cannot pay two hit points an ask for fifty asks. Before I fight
anything that breeds or multiplies, I have to know what it costs per
decision, and I have to kill it where only one can reach me.

### The flavour name does not identify a kind

I worked out that the brown potion was the eighth potion in object.txt,
which is Cure Light Wounds, and wrote it in my notebook as a fact.
`flavor_assign()` in `src/obj-util.c` hands the flavours to the kinds **at
random** (`choice = randint0(flavor_count)`), so the index means nothing at
all, and the brown potion was a **Potion of Speed**. The safe way to
identify an unknown consumable is the shop's 'd' (sell): `do_cmd_sell()`
learns the runes before the item changes hands, so with selling off you get
0 gold, lose the item, and know the kind for the rest of the game.

This is the second time in this family that a number which looked like it
must mean something turned out to mean nothing (the other was the belief
that a priest never miscasts: the spell list's Fail column reads 5% for the
level-1 prayers). **Check the code before a page says a number.**

### The store's keys, and that gear's price is not in object.txt

- `p` then the item's letter then the quantity then Enter then any other
  key buys in one ask.
- Pressing an item's letter **without** `p` opens that item's own menu
  (l Examine / p Buy / o Buy one), and the letters in that menu are the
  store's, not the pack's.
- ESC leaves the store, and leaving takes a turn.
- **Gear is priced by power, not by object.txt's `cost:`.** A Soft Leather
  Armour has `cost:20` and the Armoury asks **84**. I nearly built the
  whole shopping list out of the data file and it would have been wrong.

### The aiming recipe, and the way an unknown destination betrays you

`*` then **p** then direction digits then `g`: the `p` is essential, because
in the default "interesting" mode a direction key snaps the cursor to the
next MONSTER and the walk goes to that, not to the tile you aimed at. An
aim at a tile the map has already drawn is a real walk (7 tiles in one ask
for me, 30 to 44 in other runs); an aim at a tile the map has not drawn
is a lottery - one aim twelve tiles east moved me **one tile west**. Aim
only at drawn tiles, and use a digit string for everything else.

A digit string stops at the first wall and the rest is dropped, and in a
38 to 41 digit string I lost one digit once - so **check the position after
every long route**, not just the message line.

### Digging is one ask and a hundred attempts

Digging is the `T` command plus a direction, and it **repeats by itself
until the wall is gone**: one ask was a hundred attempts, and the turn
counter rises by a thousand each time. Walking into a wall does **not**
dig ("There is a wall in the way!"). The chances are out of 1200 and the
skill is `race + adj_str_dig[STR] + weapon_weight/10`, so for a Dwarf with
STR 18 and a 12 lb weapon it is 61: quartz 82 (6.8%), magma 204 (17%),
granite 21 (1.75%), rubble 41%. A '*' on the map is a vein with treasure,
and the vein I dug gave **90 gold in three attempts**.

### The turn counter advances by ten per player action

Every action is ten game turns, so a hundred digging attempts cost a
thousand turns and a rest of about sixty actions is the longest useful
sleep. Two rests of "R" and Enter heal about four hit points each in the
town and are interrupted by townfolk.

### A screen that is a menu eats the first key of the next ask

The M map, a store and the equipment list all took a key from me: my 'T6'
went to closing the map and only the '6' reached the game. The same thing
happens with a `-more-`.

### The Word of Recall fires wherever you are, and it does not heal

Its timer is 15 to 34 **player actions** and it takes you to the town
mid-walk - mine fired in the middle of a corridor walk with "There is a wall
in the way!" as the message. It healed nothing; the heal in
`minimaxflash-1.2`'s report was a **rest** in the town.

### The keypad is 7 8 9 / 4 5 6 / 1 2 3

'3' is down-**right** and '4' is **left**. I got both wrong once each and
lost asks, which is the cheapest lesson on this page and the one I am most
likely to repeat.
