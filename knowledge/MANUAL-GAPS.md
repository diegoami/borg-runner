# MANUAL-GAPS: what the manual should have said

Source: three notebooks (`sonnet-1` and `sonnet-2`, seed 7, a Half-Troll
Warrior; `sonnet-3`, seed 11, a Human Mage), filed in
[LEARNED.md](LEARNED.md). This is the **second version**; the first rested on
`sonnet-1` alone. Each cheat sheet below is text to paste into
`manuals/jev-1.md` (or its successor), in the manual's own voice, and says
underneath **why it is worth the space**: which run lost what without it.

**What changed since the first version, in one place.** Sheet 5 ("Finding the
way down") is rewritten: its recommendation of Magic Mapping was wrong on the
evidence (see the correction at the head of the sheet). Sheet 2 no longer says
"one purchase per ask"; it says what was actually eating keys. Sheet 1 gains
the observed Deep Descent, the first-use experience figures from a second run,
and a limit on drinking unknown potions late. Sheet 3 gains the throw menu's
own letters. Sheet 6 (disabled with something near: what killed `sonnet-3`)
and Sheet 7 (a Mage's first steps) are new.

How to read the labels inside the pasted text, which a player should keep:
- **OBSERVED** is what a run saw on its own screens. The item ids after it are
  in LEARNED.md, where `confirmed` means two different runs and `hypothesis`
  means one; the text says which (**seen in N runs** or **one run**);
- **GAME DATA** is read from the game files at the pin (`lib/gamedata/*.txt`,
  `src/*.c`), so it is what the game does, but no run has yet tested it;
- **UNTESTED** is a suggestion nobody has tried.

**Seed and character.** Gold figures, shop stock and prices, which monsters
appear on depth 1 and what a character can survive are one character's. The
Warrior (seed 7) had 146 gold and 23 hit points; the Mage (seed 11) 334 gold
and 10. Where a figure below is one character's the text says so; do not paste
a figure that is not labelled general into a manual meant for other characters.

The sheets are ordered by what they would have saved the most.

---

## Sheet 1. Unidentified objects: what using one costs, when it is safe, what it is worth

*Paste as a new section before the commands, so it is read before the first
`q` or `r`. LEARNED.md items: `unknown-scrolls-harmless`, `unknown-potion-level`,
`first-use-xp-shrinks` (confirmed), `bought-items-named` (confirmed),
`selling-pays-nothing` (confirmed), `deep-descent-observed`,
`deep-descent-five-below`, `unknown-potion-wastes-heal`,
`test-unknowns-when-safe`. All filed under `new:unidentified-objects` except
the last two, filed under ESC-01, and `selling-pays-nothing`, under `key:s`.*

> **Unknown potions and scrolls.** Every kind of potion and scroll has a
> random name or colour for the whole game ("a Blue Potion", "a Scroll titled
> 'sconus odia'"). You learn what it is by using it once, after which every
> object of that kind is named for the rest of the game. A potion or scroll is
> used up when tried, so identifying by use costs the item and one turn,
> nothing else.
>
> **What it is worth.** The first use of an unknown kind pays experience
> (GAME DATA, `obj-knowledge.c`):
> `(kind level + character level / 2) / character level`, rounded down, where
> the kind level is listed after the table below. At character level 1 that is the kind
> level itself; at level 3 a level-1 kind pays 0 and a level-5 kind pays 2.
> OBSERVED, **seen in 2 runs**: a Blue Potion drunk at character level 1 was
> Boldness (kind level 1, 1 experience) and that was exactly the 1 point the
> character needed for level 2; a Scroll of Blessing at level 1 moved the "NXT"
> counter from 7 to 6; a Scroll of Light (kind level 0) at level 3 moved it not
> at all; a Scroll of Deep Descent at level 4 moved it 14 to 11 (3), a Potion of
> Cure Serious Wounds at level 5 moved it 31 to 30 (1), and a Scroll of Blessing at
> level 6 moved it not at all. All of these agree with the formula. So it is worth a level in the first
> minutes and almost nothing after the character is level 5 or so. It is the
> same payment whether the object is a potion or a scroll.
>
> **What you buy is already named.** An item you *buy* is named in the pack,
> even though the purchase message may say "Scrolls titled ..." or "Misty
> Potions": the shop row loses its {unseen} and the pack lists "Scrolls of
> Phase Door". So using it pays nothing. OBSERVED, **seen in 3 runs**. Only
> things found on the floor are unknown, and only they pay. Selling is no use
> either way: a store pays **0 gold** for anything (OBSERVED, **seen in 2
> runs**: "Give which item? ... 0 au"), so the Word of Recall scroll in the
> starting kit is not money.
>
> **When it is safe.** Try an unknown potion or scroll when you are at full
> hit points, nothing is in view, and ideally you are standing on a staircase
> you could take at once. Scrolls cannot be read in the dark, while blind or
> while confused; potions can be drunk in all of these.
>
> The table below is **not a list of scrolls and potions** - the complete list
> is appendix A6 of the strategy manual, and `object.txt` is the data behind
> it. This is the subset that changes the decision you are actually making:
> only the kinds that can *hurt* you, only those generated at depth 5 or
> shallower, and with what to do if one happens. Anything else, look up when
> you meet it. (GAME DATA, `object.txt`; "depth" is the shallowest level a
> kind is generated on.)
>
> | Kind | Depth | What happens | What to do |
> |---|---|---|---|
> | Potion of Sleep | 0 | you are paralysed for a few turns | only matters if something is near: that is why nothing may be in view |
> | Potion of Blindness, Confusion | 0 | blind or confused for a while | wait it out; you cannot read scrolls meanwhile (Sheet 6) |
> | Potion of Poison, Slowness | 0 | poisoned or slowed for a while | wait it out; do not fight |
> | Potion of Salt Water | 3 | hunger drops to very low, paralysed briefly | eat a ration afterwards |
> | Scroll of Summon Monster | 1 | monsters appear next to you | take the staircase you are standing on |
> | Scroll of Darkness | 1 | the room goes dark and you are blinded | wait it out |
> | Scroll of Aggravate Monster | 5 | wakes and hastes everything in sight | leave by the stairs |
>
> Deep Descent is generated from depth 1 too, and it is the one unknown scroll
> that is *worth* finding; it has its own paragraph below rather than a row
> here, because it is not a hazard.
>
> Everything else that appears in the first levels is harmless or useful:
> Phase Door, Light, Blessing, Detect Invisible, Treasure Detection, Cure
> Light Wounds, Speed, Heroism, Berserk Strength, Boldness, Infravision, True
> Seeing, Neutralize Poison. From depth 5 the scrolls that matter most to
> descending start to appear: Magic Mapping (depth 5), Teleportation (10).
> OBSERVED: of the unknown objects the runs tried, three scrolls (Blessing,
> Light, Blessing) and three potions (Boldness, Neutralize Poison, Heroism) did no
> harm, one potion (Cure Serious Wounds) was a heal wasted at full health, and
> one scroll was Deep Descent.
>
> **Deep Descent, as it happened once.** OBSERVED, **one run, one scroll**:
> an unknown scroll picked up on depth 1 and read at full health (68 of 68, a
> character level 4 Warrior) showed "The air around you starts to swirl...", put
> "Descent" on the status bar, and about four or five turns later (during which
> the player walked a few squares toward some gold it did not reach) "The floor
> opens beneath you!"; depth 6, not on a staircase. That is what one scroll supports. **What it does
> not support:** how often an unknown scroll is Deep Descent (it was one of the
> four unknown scrolls the runs read, and the runs found no other); that depth 6
> is safe (a Warrior with 68 hit points lived there, with doorways and oil; a
> 10-hit-point Mage would not be expected to); and what "5 levels below" counts
> from, because that character's current and deepest depth were both 1 (the
> game data says the deepest). If you read an unknown scroll at low hit points
> or at character level 1, this is the one that can end the run.
>
> **So:** read unknown scrolls early, at full health, with nothing in view: they
> can be Deep Descent, Magic Mapping or Teleportation, and the bad ones are in
> the table. Drink an unknown potion the same way **while you are character level
> 1 to 3**, where it pays a level. Do not keep one for an emergency: of the
> potion kinds generated in the first levels only Cure Light Wounds heals
> properly (Heroism and Berserk Strength heal a little). But **later, at about
> level 5 and above, an unknown potion is worth drinking only when you are hurt**
> (OBSERVED, one run: a Clear Potion drunk at 89 of 89 hit points was Cure
> Serious Wounds, a 70-gold heal spent for about 1 experience). The one exception
> to "do not keep one" is the last rung of the escape ladder (ESC-01), when
> nothing else is left.

Kind levels for the things above, from `object.txt` (the number in the
experience formula): Cure Light Wounds 0, Light 0, Boldness 1, Blessing 1,
Phase Door 1, Speed 1, Heroism 1, Berserk Strength 3, Cure Serious Wounds 3,
True Seeing 3, Magic Mapping 5, Deep Descent 10, Teleportation 10.

**Why it is worth the space.** `sonnet-1` tested each unknown it picked up (two
scrolls and one potion), and its report ends with "I would read every unknown
scroll early (Deep Descent / Teleport / Magic Mapping would be found at
DL1-2)"; the first version of this sheet said so, and `sonnet-2`, which had it,
read its first unknown scroll at once, found Deep Descent, and went from depth
1 to depth 6 in four asks, where walking had found no staircase in 51 asks.
The same sheet said "drink unknown potions early" without a level limit, and
`sonnet-2` drank a Cure Serious Wounds at full health at level 5 (its report
lists it among the decisions to take back). `sonnet-3` found that the purchase message misleads (it says "Scrolls titled
...", the pack says "Scrolls of Phase Door"), which the first version did not say.
Without the sheet a player would keep an unknown potion for an emergency, and
would miss the one scroll that skips the whole stair-finding problem. The
cost of not knowing the bad list is not shown by any run: all were lucky, and
the table is there for the player who will not be.

---

## Sheet 2. Menu letters, buying, and what a `-more-` does to your keys

*LEARNED.md items: `store-purchase-sequence`, `purchase-in-one-ask`,
`more-swallows-next-key`, `space-clears-more`, `level-change-more`,
`store-letters-fixed`, `pack-letters-skip` (the last two `new:item-letters`),
`enter-opens-menu` (`new:dismissing-more`, one run). All but the last are
confirmed. The first version of this sheet said that keys chained after one
purchase "were not kept" and told the player to buy one thing per ask; that was
`store-purchase-prompts`, now `contradicted`, and the text below replaces it.*

> **Letters on a list are labels, not positions.** A list of things (a
> store's stock, your pack) is labelled from a fixed run of letters that
> leaves out the ones the screen uses for something else. Read the letter
> printed next to the thing you want and never count down the list.
>
> - **The pack** (`i`, and the prompt of `q`, `r`, `w`): the letters
>   skip `h`, `j`, `k` and `l`, so the first eight items are `a b c d e f g i`
>   and the next are `m n o p q r s t u v w x y z`. OBSERVED, **seen in 2
>   runs**: seven items read `a` to `g` and the eighth was `i`; nine items read
>   `a b c d e f g i m`. **The throw prompt (`v`) is not the pack**: it lists
>   only things you can throw, under letters of its own (Sheet 3).
> - **A store's stock** (original keys): `a c f h j m n o q r u v y z` and
>   then capitals, with `b d e g i k l p s t w x` left out because they are
>   store commands. OBSERVED, **seen in 3 runs**: the Alchemist's fourteen rows were
>   labelled exactly `a c f h j m n o q r u v y z`, and the General Store and
>   Armoury rows `a c f h j m ...` the same way. Which thing has which letter
>   changes with the shop's stock: oil was `h` in one General Store and `j` in
>   another. GAME DATA (`ui-menu.c`, `ui-store.c`) agrees.
>
> **Buying.** In a store, `p` then the row's letter starts a purchase. The
> game asks "Buy how many?" with 1 as the default: type the number and press
> Enter (just Enter keeps 1). It then shows the item and total and asks "[ESC,
> any other key to accept]": any key but Escape buys it. Leave with Escape.
> **A whole purchase is one ask**, as long as the confirming key is the last
> thing in the string and no `-more-` is waiting when the string starts:
> `pa\ny` buys one Cure Light Wounds, `ph10\ny` ten flasks of oil, `pj20\ny`
> twenty (OBSERVED, **seen in 2 runs**, three purchases; in two of them a space
> followed the `y`).
>
> **A `-more-` takes the next key.** A message that ends in `-more-` waits for
> a key, and the next key you send is that key: it does nothing else. So a
> command typed while one is up loses its first key and the rest is misread.
> That, and not chaining, is what went wrong when a second purchase followed a
> first in the same string: after the first purchase the game shows "You bought
> ... -more-", and the `p` of the second was eaten (OBSERVED, **seen in 3
> runs**: "Buy how many? (max 2) y"; an unanswered "Buy how many?"; ` mac`
> after a staircase running `aim` and `close`). **A space clears a `-more-` and
> does nothing when there is none**, so put one after the last key of a command
> that may end in one (`va'   `, three spaces for a throw that shows three
> `-more-`s; `pa\ny `) or at the start of the next string (` pa5\ny`): OBSERVED,
> **seen in 2 runs**, a throw or a purchase then took one ask rather than two or
> three.
>
> **Stairs end in a `-more-` too.** Taking a staircase shows "You enter a maze
> of down staircases. -more-" (and sometimes a second `-more-` after it), so any
> key sent in the same string after the stairs key is lost: `<>` in one ask left
> the character standing in the town (OBSERVED, **seen in 3 runs**). A reroll
> (`<` from depth 1, then `>` in the town) is therefore three asks: `<`, `>`,
> space. Deep Descent ends in one as well.
>
> **Enter is not "continue".** On the dungeon map Enter opens a command menu
> (OBSERVED, one run); it only dismisses something when a `-more-` is on screen.
> To get past a `-more-`, send a space or Escape, which do nothing if there is
> none. The menu is closed with Escape.

**Why it is worth the space.** `sonnet-1` spent about twelve asks (14 to 25) on
four purchases because one chained set of keys went wrong and had to be unpicked,
and concluded that chaining is eaten; the first version of this sheet repeated
that. `sonnet-2` and `sonnet-3` both disproved it (each bought whole purchases in
one ask), and `sonnet-2` lost asks 15 to 17 to a purchase typed over a `-more-` and
`sonnet-3` two asks to a cloak whose confirming key it left for the next ask.
The real rule, that a `-more-` eats the next key, also explains `sonnet-2`'s
`<>` (a test that did not shorten the reroll), `sonnet-3`'s ` mac` after arriving on depth 1 (which ran `aim` and
`close` instead of casting) and the three-ask reroll. The letter-skipping was
noted by `sonnet-1` twice and used by both later runs without a wrong
purchase. The compressed manual says only "p = buy". A wrong letter in a store
buys the wrong thing with the last gold; a wrong letter in the pack could quaff
a Berserk Strength instead of a Cure Light Wounds.

---

## Sheet 3. Throwing a flask of oil

*LEARNED.md items: `throw-closest-target` (confirmed), `throw-menu-own-letters`
(confirmed), `rethrow-target-5` (one run), `fang-corridor-oil`,
`dl1-dog-pack-levels`, `oil-one-shots-p` (one run each).*

> **Throwing.** `v`, then the letter of the thing to throw, then the target.
> **The letter is the one in the throw prompt, not the pack's**: the prompt
> says "Throw which item? (Throwing items: a-a ...)" and lists only the things
> you can throw, so flasks of oil were `a` there while `b` or `c` in the pack
> (OBSERVED, **seen in 2 runs**). Read the prompt. At "Direction?":
>
> - `'` throws at the nearest monster you can see (OBSERVED, **seen in 3
>   runs**; the prompt says "'" for closest");
> - `5` throws at the monster you last targeted, and is offered at the prompt
>   only once there is one (OBSERVED, one run; in two other runs it was not seen
>   to work);
> - `*` lets you choose among visible monsters; Escape cancels.
>
> So the first throw is `v`, `a`, `'` (if the oil is item `a` in the throw
> prompt) and a throw you repeat is `v`, `a`, `5`. Each throw may leave a
> `-more-` ("The flask of oil breaks", "X is targeted"); end the string with
> spaces, `va'   `, and a throw is one ask (Sheet 2). Each flask is one thrown
> action and does fire damage on impact; a thrown flask is used up, so count
> them (15 flasks weigh 30 lb on the item list).
>
> **Fast uniques on depth 1.** Fang and Grip, Farmer Maggot's dogs, are native
> to depth 2 and were met on depth 1 (GAME DATA, the same for both: speed +10, 25
> hit points, armour 36, a bite of 1d4, worth 30 experience times its level 2
> divided by your level). OBSERVED, **one run each, both Warriors on seed 7**:
> Fang killed at character level 2 in a corridor with two thrown flasks and then
> melee, for 11 of 31 hit points, which took the character from level 2 to 3; a
> pack of wild dogs and Grip, met in a lit room, took a level-1 Warrior from 23
> hit points to 12 and from character level 1 to 4, oil first and then melee in
> the open. A corridor means it comes at you from one side. The humans on depth 6
> (apprentice, gallant, tamer) died to one flask each, by one player's account.

**Why it is worth the space.** `sonnet-1` needed asks 81 to 83 to find the
`'` key from the prompt and 103 to 104 to find `5`; `sonnet-2` sent `vb'` (the
pack's letter) at ask 39 and had to look at the menu at ask 40; the game's own
manual (`playing.rst`, "Targeting") lists `'`, and the compressed manual's `v`
line leaves the third key out and says nothing about the menu's own letters.
The OIL-01 rule says oil matters but not how to throw it. The dog fights are
worth having because "look up a unique first" is the strategy manual's rule and
these are early fast uniques that a level-1 or 2 Warrior can beat and gain
three levels from (and, on the pack fight, nearly lose half its hit points to).

---

## Sheet 4. Walking cheaply

*LEARNED.md items: `runs-stop-at-openings`, `digit-strings-beat-runs`,
`digit-string-stops-at-wall` (all `key:.`, one run each).*

> **Run (`.` and a direction)** follows a corridor until you must choose
> between two ways or something disturbs you. It therefore stops at every side
> opening, door and treasure vein, and in a cave or an irregular room that is
> every few squares. OBSERVED, one run: in a twisty cave a run was worth two or
> three squares per ask. There, and in an open room, a plain string of eight to
> ten steps in one direction (`4444444444`) moves further per ask than a run.
> Use runs in straight corridors; use strings of steps in caves and rooms.
> **A string stops at a wall** ("There is a wall in the way!") and the rest of
> it does nothing: OBSERVED, one run, a nine-step string moved six squares, so in a cave
> a string longer than the passage is partly wasted. A string of steps is only
> as safe as the room is empty: look at the screen before sending ten steps
> into an unlit room (OBSERVED: a wild cat took 13 hit points from a character
> walking blind into one, `REPORT.md` section 2). The same goes, more so, for a
> string of anything else (Sheet 6).

**Why it is worth the space.** The compressed manual says a run is "far cheaper
than stepping", which is true in corridors and false in a cave. Asks 62 to 66 of
`sonnet-1` were five runs that stopped at once in a cave, and the player gave up
on the level at ask 67. `sonnet-1`'s whole run is walking: about 100 of its 125
asks; in `sonnet-2` 51 asks on depth 1 and 73 on depth 6 were exploring. The
wall rule is a smaller loss (`sonnet-2` noted it in its notebook).

---

## Sheet 5. Finding the way down (rewritten; the first version was wrong)

*LEARNED.md items: `dl1-no-stairs-100-asks` (confirmed), `arrival-staircase`
(confirmed), `reroll-costs-three-asks` (confirmed), `reroll-pays`
(contradicted), `reroll-different-level`, `magic-mapping-unaffordable`
(**contradicted**), `magic-mapping-no-stairs`, `stairs-spell-shows-stairs`,
`locate-scrolls-map`, `deep-descent-observed`, `deep-descent-paid-in-asks`,
`deep-descent-no-stairs-arrival`, `dl6-no-stairs-explored`.*

**Correction.** The first version of this sheet, written from one notebook,
listed Magic Mapping at 65 gold as the first thing that buys a `>`, and told the
player that a Magic Mapping scroll "is within reach if one fewer escape is
bought". `sonnet-2` followed it: it bought a Magic Mapping scroll with 65 of its
146 gold, read it on depth 1, and the map showed **no staircase of either kind**
in what the player looked at (the screen and the sector north of it, most of
the area the scroll maps). The 65 gold bought nothing it could use, and
`sonnet-2` listed it first among the decisions it would take back. The claim was
never tested when it was written, which the sheet said, and it was still the
recommendation. The text below is what the evidence now supports and nothing
more; the table says how much each line is worth.

> **Stairs.** The one fixed fact: every level has at least one staircase of
> each kind, and you arrive by `>` on an up staircase and by `<` on a down one
> (connected stairs). OBSERVED, **seen in 2 runs**: after `>` the status bar
> says "Up staircase", and after `<` from depth 1 you stand in the town on its
> down staircase. `<` then `>` is a fresh depth 1 for **three asks** (OBSERVED,
> **seen in 2 runs**: `<`, `>`, then a space for the `-more-`; Sheet 2). The new
> level begins with a corridor like the old one but is a different level, and
> was no quicker to find a staircase in (OBSERVED, one run): a reroll gets you a
> level you have not walked, not a better one. Do it when you have learned the
> level is bad (a cave), not as a way to find stairs. **It is not available
> after a Deep Descent**: you do not arrive on a staircase.
>
> **How much finding a `>` costs.** OBSERVED, **seen in 2 runs**: about 100 of
> 125 asks walking two depth-1 levels (no `>` found), and 51 asks on one depth-1
> level followed by 73 on depth 6 (none found on either). In all three runs
> **nobody ever took a down staircase in the dungeon**: every level below the
> town was reached by the town's staircase or by Deep Descent. Levels are large
> (up to 198 by 66 squares) and you see only what your light reaches.
>
> **What might help, and how far to believe it**
>
> | What | Cost | What the runs saw | Belief |
> |---|---|---|---|
> | *Magic Mapping* scroll | 65 gold; the Alchemist stocks it only some of the time (4 on one seed, 2 on another; "normal" stock) | read once on depth 1: **no staircase** in what was looked at | one scroll, one level. It maps walls, doors and stairs within 40 columns each side and 22 rows each way (GAME DATA), about a quarter of a level; nothing guarantees a `>` is inside. **Do not buy it as the answer to stairs.** UNTESTED: whether a scroll read from the middle of a level, or later at depth 5 and below where it is also found on the floor, does better |
> | *Stair detection*, for a Mage: the first-level spell Find Traps, Doors & Stairs (`mac`; Sheet 7) | 1 spell point | cast on arrival on depth 1, it drew a `>` about 13 columns west and 6 rows south of the arrival staircase and no floor between; the corridor the player ran led away from it | the same 22-by-40 box as the scroll (GAME DATA). It found one where the scroll found none, which is two draws, not a comparison. Whether the shown `>` is cheaper to reach than blind exploring is **not shown**: the run died 12 asks later |
> | *Deep Descent* scroll | found only, never sold; from depth 1 | read once, after a few turns it dropped a level-4 Warrior from depth 1 to depth 6 in four asks, not on a staircase | **one scroll in four unknowns read; no rate.** It is a draw you get by reading unknown scrolls early (Sheet 1), not something to plan on. At depth 6 a Warrior with 68 hit points lived by fighting in doorways with oil; a weaker character would be in trouble (UNTESTED). It goes to 5 below the deepest level reached (GAME DATA; the observation cannot tell this from 5 below the current level) |
> | `L` (locate) | free | scrolls the map a sector at a time ("Map sector [3,0], which is your sector. Direction?"); Escape leaves; used to read a mapped area that did not fit the screen | one run. Worth knowing before reading Magic Mapping: the screen shows about 33 columns and 5 rows north to 15 rows south of you, the scroll maps 40 and 22 each way |
> | autoexplore option ("Use autoexplore commands", `autoexplore_commands`, off by default) | an option | under it `>` walks to the nearest known down staircase and `p` to the nearest unexplored square | UNTESTED: no run has turned it on, and nothing here checked whether the harness lets the player set options. The compressed manual already says `p` does nothing while it is off |
> | rerolling (`<` then `>`) | 3 asks | a new level, no quicker | see above |
>
> **What the evidence supports, in order.** (1) Walking is where the asks go;
> spend them with runs in corridors and strings of steps in rooms (Sheet 4),
> and do not spend 65 gold on a map scroll hoping it saves them. (2) Read every
> unknown scroll you find, early and at full health (Sheet 1): one of four was
> Deep Descent, and the others were harmless. (3) If the character has a stair
> detection spell, cast it on arrival and look; head toward a `>` it shows
> (UNTESTED that this saves asks). (4) Do not reroll to look for stairs.
>
> **Gold.** The first version's arithmetic ("146 gold: oil, a cloak, three Phase
> Door and two Cure Light Wounds leaves 10 gold") was the Warrior's on seed 7
> and is not general: a Human Mage on seed 11 had **334**. TOWN-01 says what
> comes first and does not say what to do with the rest. The runs' own spending:
> the Warrior, 15 oil, a cloak, 3 Phase Door, 2 Cure Light Wounds (10 left), and
> then, following this sheet, Magic Mapping, 2 Phase Door, 1 Cure Light Wounds
> and 10 oil (1 left); the Mage, 20 oil, a cloak, a torch, 6 Phase Door, 5 Cure
> Light Wounds and a 66-gold Leather Shield (6 left). **None of the escapes or
> heals bought was ever used** in the two runs that lived (Sheet 6 for the
> third), so TOWN-01's order is untested, though it is not shown to be wrong.

**Why it is worth the space.** The first version of this sheet cost `sonnet-2`
65 of its 146 gold: it is the one place where an inherited manual line did
harm that the run could not have known about. That is the reason to keep the
rewrite short on promises and long on the grade of each line. The sheet is still
worth its space for what it records straight: that finding `>` was the dominant
cost in all three runs (`sonnet-1` ended at ask 124 with no `>` found after about
100 asks; `sonnet-2` had none in 124 asks of walking and got below depth 1 only
by a scroll; `sonnet-3` was shown a `>` and died before it could use it), that
a reroll is three asks and no better, and that Deep Descent exists and what it
does to a character that reads it.

---

## Sheet 6. Disabled with something near: how `sonnet-3` died

*LEARNED.md items (all one run, `sonnet-3`): `unseen-is-not-dead`,
`gas-trap-confusion`, `hold-key-is-comma`, `blind-batch-while-disabled`,
`confused-clw-unused`, `mage-ten-hp`, `batch-uninterruptible` (a lead about the
harness, not text for the player). The account of the death is in LEARNED.md,
"What killed a character". The compressed manual has no line that would have
stopped any step of it: it says "send several keys at once" and never when not to.*

*Paste as a new section after the strategy rules.*

> **A monster that has left view is not dead.** A kill shows in the message line
> ("You have slain ...", "... dies") and in the experience counter moving (the
> "NXT" figure on the left falls). A blank or dashed health bar (`[----------]`)
> and an empty square mean you cannot see it, not that it is gone. A monster you
> have hurt and lost in a corridor is near you. Wait a turn or two at the corridor
> mouth with a flask ready, or look for it, before walking on. OBSERVED, one run:
> one flask hit a small kobold, it left view, NXT stayed 8, and the player went
> on; the kobold killed it.
>
> **When you cannot act well, send one or two keys per ask.** Confused, blind,
> paralysed-then-recovering, afraid, slowed, or any state in which a monster
> could arrive and you could not answer it: send **one or two keys per ask, never
> a string of waits.** The keys of an ask are sent without looking at the screen,
> so a string cannot be interrupted by what the screen would have shown. A
> character with few hit points has no margin for a batch. OBSERVED, one run:
> ten holds (survived), then sixteen holds in one ask while confused with a
> wounded kobold unaccounted for; about seven turns into the second the kobold
> arrived and killed a full-health 10-hit-point Mage. This is the opposite of
> the advice to send several keys at once, which is for a screen you can see
> is empty and safe.
>
> **Holding a turn.** In this keyset `,` holds one turn (ten `,` were ten turns);
> `s` does not hold, it asks for a direction. `5` is listed as "stay still" in
> this manual and was not tried.
>
> **What confusion allows.** You can still drink potions; you cannot read
> scrolls, so Phase Door is not available (GAME DATA). A Potion of Cure Light Wounds
> reduces confusion by 20 turns and heals 20 hit points (GAME DATA,
> `object.txt`). UNTESTED: nobody has drunk one while confused. The Mage that
> died held five of them.
>
> **Traps.** A gas trap on depth 1 confuses (OBSERVED, one run: still confused
> ten turns later).
>
> **At 10 hit points two or three hits are the whole character.** A small kobold
> hits for 1d5 (GAME DATA). Do not let it close to melee range: read Phase Door
> while you can and throw from range, rather than throwing point-blank.

**Why it is worth the space.** A character died. Every line of it cost the run:
the belief that the kobold was gone (ask 43), the batch of waits (asks 46 and
47), the five Cure Light Wounds not drunk, the point-blank throw (ask 40). None
of it is in the compressed manual, ESC-01's ladder has no rung for "disabled
with something coming", and the harness gives the player no signal to stop (see
LEARNED.md, `batch-uninterruptible`). The sheet is the rule a player could
follow; the harness change, if the owner makes one, is separate.

---

## Sheet 7. A Mage's first steps (class-specific: Human Mage, seed 11)

*LEARNED.md items (one run, `sonnet-3`): `mage-study-cast-keys`,
`spell-first-cast-xp`, `mage-one-spell-no-attack`, `stairs-spell-shows-stairs`,
`start-gold-differs`, `armoury-prices-high` (all `new:spells`, TOWN-01 or
`new:stair-detection`). Paste only into a manual for a Mage; nothing here
applies to the Warrior.*

> **Starting out as a Mage.** A Human Mage has 10 hit points, 2 spell points and
> about 334 gold (a Warrior, 23 hit points and 146 gold, is a different game;
> whether the class, the race or the seed sets the gold is not shown). The
> first book lists, at level 1, Magic Missile (1 mana), Light Room (2) and Find
> Traps, Doors & Stairs (1). **Learn a spell** with `G`, the book's letter, then
> the spell's letter (`G`, `a`, `c`); **cast** with `m`, the book, the spell
> (`mac`). The first cast of a spell pays experience (OBSERVED, one run: 2 at
> level 1, NXT 10 to 8); a second cast of the same one pays none.
>
> **Choose the first spell with care**: the run learned one spell at level 1 and
> did not try for a second, so whether a Mage can learn two is not shown. With Find Traps, Doors & Stairs you have a detector and
> no spell attack, and oil is your only attack; with Magic Missile you have an
> attack and no detector (UNTESTED which is better; `sonnet-3` learned detection and
> named it among the decisions it would take back). With 10 hit points you
> cannot afford to be hit twice: see Sheet 6.
>
> **Shops.** The Armoury's prices differ by shopkeeper; one charged 66 for a
> Leather Shield [8], 36 for a Small Metal Shield and 150 for Studded Leather,
> far above the strategy manual's figures. Look at the price before buying
> (OBSERVED, one run: the Mage spent 66 of 334 gold on the shield and was left
> with 6).

**Why it is worth the space.** The Mage died on ask 47 and spent asks 9 to 13 on
the study and cast keys, which are in no manual here (`G` for study is not even
in the compressed command list). Whether it is worth it depends on whether the
repository will ever run a Mage again; if not, drop the sheet and keep only
Sheet 6.

---

## What is not here

- Nothing about Fang, oil, shops or stairs on any seed but 7 and 11: three runs,
  two seeds, two characters.
- Nothing about **escapes and cures actually used**: no run read a Phase Door or
  drank a Cure Light Wounds in an emergency. The Mage died holding five and six.
  TOWN-01's order is untested and no gap is claimed about it.
- Nothing about Deep Descent's frequency, its true reference depth, or what a
  weaker character does at depth 6: one scroll.
- Nothing about the monster list `[`, the `5` key as a hold, autoexplore, or
  rerolling in order to shop again: nobody tried them.
- Nothing from the `jev-*` runs: they have no notebook to consolidate.
