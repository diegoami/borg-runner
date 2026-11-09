# MANUAL-GAPS: what the manual should have said

Source: the one notebook so far (`sonnet-1`, seed 7), filed in
[LEARNED.md](LEARNED.md). Each cheat sheet below is text to paste into
`manuals/jev-1.md` (or its successor), in the manual's own voice, and says
underneath **why it is worth the space**: which run lost what without it.

How to read the labels inside the pasted text, which a player should keep:
- **OBSERVED** is what `sonnet-1` saw on its own screens (one run, so a
  hypothesis in LEARNED.md, not a fact);
- **GAME DATA** is read from the game files at the pin (`lib/gamedata/*.txt`,
  `src/*.c`), so it is what the game does, but no run has yet tested it;
- **UNTESTED** is a suggestion nobody has tried.

The sheets are ordered by what they would have saved the most.

---

## Sheet 1. Unidentified objects: what using one costs, when it is safe, what it is worth

*Paste as a new section before the commands, so it is read before the first
`q` or `r`. LEARNED.md items: `unknown-scrolls-harmless`, `unknown-potion-level`,
`first-use-xp-shrinks`, `test-unknowns-when-safe`. All filed under
`new:unidentified-objects` except the last, filed under ESC-01.*

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
> OBSERVED: a Blue Potion drunk at character level 1 was Boldness (kind
> level 1, 1 experience) and that was exactly the 1 point the character
> needed for level 2; a Scroll of Blessing at level 1 moved the "NXT" counter
> from 7 to 6; a Scroll of Light (kind level 0) at level 3 moved it not at
> all. So it is worth a level in the first minutes and almost nothing after
> the character is level 5 or so. It is the same payment whether the object
> is a potion or a scroll.
>
> **What it does not pay.** An item you *buy* is already named, so using it
> pays nothing; so does one you sell to a store, which identifies it as
> well (GAME DATA, `store.c`). The shops sell Phase Door, Cure Light Wounds,
> Magic Mapping and the rest by their real names. Only things found on the
> floor are unknown, and only they pay.
>
> **When it is safe.** Try an unknown potion or scroll when you are at full
> hit points, nothing is in view, and ideally you are standing on a staircase
> you could take at once. Scrolls cannot be read in the dark, while blind or
> while confused; potions can be drunk in all of these. The bad kinds that can
> appear in the first few levels (GAME DATA, `object.txt`, "depth" is the
> shallowest level it is generated on):
>
> | Kind | Depth | What happens | What to do |
> |---|---|---|---|
> | Potion of Sleep | 0 | you are paralysed for a few turns | only matters if something is near: that is why nothing may be in view |
> | Potion of Blindness, Confusion | 0 | blind or confused for a while | wait it out; you cannot read scrolls meanwhile |
> | Potion of Poison, Slowness | 0 | poisoned or slowed for a while | wait it out; do not fight |
> | Potion of Salt Water | 3 | hunger drops to very low, paralysed briefly | eat a ration afterwards |
> | Scroll of Summon Monster | 1 | monsters appear next to you | take the staircase you are standing on |
> | Scroll of Darkness | 1 | the room goes dark and you are blinded | wait it out |
> | Scroll of Deep Descent | 1 | after about 5 turns you are taken **5 levels below the deepest level you have reached**, not 5 below where you stand | see the sheet on finding stairs; do not read it hurt |
> | Scroll of Aggravate Monster | 5 | wakes and hastes everything in sight | leave by the stairs |
>
> Everything else that appears in the first levels is harmless or useful:
> Phase Door, Light, Blessing, Detect Invisible, Treasure Detection, Cure
> Light Wounds, Speed, Heroism, Berserk Strength, Boldness, Infravision, True
> Seeing, Neutralize Poison. From depth 5 the scrolls that matter most to
> descending start to appear: Magic Mapping (depth 5), Teleportation (10).
> OBSERVED: two unknown scrolls on depth 1 (Blessing and Light) and one
> unknown potion (Boldness) were all harmless.
>
> **So:** do not keep an unknown potion for an emergency. Of the potion kinds
> generated in the first levels only Cure Light Wounds heals properly (Heroism
> and Berserk Strength heal a little), so as a gamble it is worth little, while
> drunk early it costs one turn and pays experience. Read unknown scrolls the
> same way. The one exception is the last rung of the escape ladder (ESC-01),
> when nothing else is left.

Kind levels for the things above, from `object.txt` (the number in the
experience formula): Cure Light Wounds 0, Light 0, Boldness 1, Blessing 1,
Phase Door 1, Speed 1, Heroism 1, Berserk Strength 3, Cure Serious Wounds 3,
True Seeing 3, Magic Mapping 5, Deep Descent 10, Teleportation 10.

**Why it is worth the space.** `sonnet-1` found all of this out by trying,
which is the cheap way: it tested each unknown it picked up (two scrolls and
one potion), and its report ends with "I would read every unknown scroll early
(Deep Descent / Teleport / Magic Mapping would be found at DL1-2)". A player
who had this sheet would (a) not treat drinking an unknown potion as a last
resort, (b) know that the potion's payoff is largest at character level 1 and
nearly gone by 3, so it should happen at once and not after the walk, and (c)
know that buying a scroll to read it earns nothing, so gold should buy
things that work, not things to learn from. The run lost nothing by testing;
it would have lost a level at the moment it needed one if it had saved the
Blue Potion for an emergency that never came (its lowest HP was 20 of 31). The
cost of not knowing the bad list is not shown by this run: it was lucky, and
the table is there for the player who will not be (for example an unknown
Scroll of Deep Descent read at low health).

---

## Sheet 2. Menu letters, and the shop transaction

*LEARNED.md items: `store-purchase-prompts`, `store-letters-fixed`
(`new:item-letters`), `pack-letters-skip` (`new:item-letters`),
`enter-opens-menu` (`new:dismissing-more`).*

> **Letters on a list are labels, not positions.** A list of things (a
> store's stock, your pack) is labelled from a fixed run of letters that
> leaves out the ones the screen uses for something else. Read the letter
> printed next to the thing you want and never count down the list.
>
> - **The pack** (`i`, and the prompt of `q`, `r`, `v`, `w`): the letters
>   skip `h`, `j`, `k` and `l`, so the first eight items are `a b c d e f g i`
>   and the next are `m n o p q r s t u v w x y z`. OBSERVED: seven items
>   read `a` to `g` and the eighth was `i`.
> - **A store's stock** (original keys): `a c f h j m n o q r u v y z` and
>   then capitals, with `b d e g i k l p s t w x` left out because they are
>   store commands. OBSERVED: the Alchemist's fourteen rows were labelled
>   exactly `a c f h j m n o q r u v y z`. GAME DATA (`ui-menu.c`,
`ui-store.c`) agrees with both lists.
>
> **Buying.** In a store, `p` then the row's letter starts a purchase. The
> game asks "Buy how many?" with 1 as the default: type the number and press
> Enter. It then shows the item and total and asks "[ESC, any other key to
> accept]": any key but Escape buys it. Leave with Escape. A purchase is
> several prompts, so one purchase is one decision: keys typed after the
> last prompt of a purchase were not kept (OBSERVED: the chained keys
> `po3\nypa2\ny` bought the three Phase Door, but the second purchase
> arrived as "Buy how many? (max 2) y" and had to be cancelled with Escape
> and redone in three separate asks).
>
> **Enter is not "continue".** On the dungeon map Enter opens a command menu;
> it only dismisses something when a `-more-` is on screen. To get past a
> `-more-`, send a space or Escape, which do nothing if there is none. The
> menu is closed with Escape.

**Why it is worth the space.** `sonnet-1` spent about twelve asks (14 to 25) on
four purchases because one chained set of keys was eaten and had to be
unpicked, and it noted the letter-skipping twice (at asks 25 and 57), which it
needed in order not to buy or drink the wrong row. The compressed manual says
only "p = buy". At ask 103 an Enter opened the menu in the middle of a fight
and cost an ask to close (the screen at ask 103 is the menu). A wrong letter in a store buys the wrong thing with
its last gold; a wrong letter in the pack could have quaffed a Berserk
Strength instead of a Cure Light Wounds.

---

## Sheet 3. Throwing a flask of oil

*LEARNED.md items: `throw-closest-target`, `rethrow-target-5`,
`fang-corridor-oil`.*

> **Throwing.** `v`, then the letter of the thing to throw (here the flasks were
> in the pack), then the target. At "Direction?":
>
> - `'` throws at the nearest monster you can see;
> - `5` throws at the monster you last targeted, and is offered at the prompt
>   only once there is one;
> - `*` lets you choose among visible monsters; Escape cancels.
>
> So the first throw is `v`, `a`, `'` (if the oil is item `a`; read the
> letter), and the rest of a fight is `v`, `a`, `5`. Each throw may leave a
> `-more-` ("The flask of oil breaks", "X is targeted"); clear it with space.
> Each flask is one thrown action and does fire damage on impact; a thrown
> flask is used up, so count them (15 flasks weigh 30 lb on the item list).
>
> **A fast unique on depth 1.** Fang, Farmer Maggot's Dog,
> is native to depth 2 and was met on depth 1 (GAME DATA: speed +10, 25 hit
> points, armour 36, a bite of 1d4, worth 30 experience times its level 2
> divided by your level, so 30 points to a character of level 2). OBSERVED: killed at character level 2 in a corridor
> with two thrown flasks and then melee, for 11 of 31 hit points, and the
> kill took the character from level 2 to level 3. A corridor means it comes
> at you from one side.

**Why it is worth the space.** The run needed asks 81 to 83 to find the
`'` key from the prompt, and ask 103 to 104 to find `5`; the game's own manual
(`playing.rst`, "Targeting") lists both, and the compressed manual's `v` line
leaves the third key out. The OIL-01 rule says oil matters but not how to throw
it. The Fang numbers are worth having because "look up a unique first" is
the strategy manual's rule and this one is an early, fast unique that a
level-2 character can beat.

---

## Sheet 4. Walking cheaply

*LEARNED.md items: `runs-stop-at-openings`, `digit-strings-beat-runs`
(both `key:.`).*

> **Run (`.` and a direction)** follows a corridor until you must choose
> between two ways or something disturbs you. It therefore stops at every side
> opening, door and treasure vein, and in a cave or an irregular room that is
> every few squares. OBSERVED: in a twisty cave a run was worth two or three
> squares per ask. There, and in an open room, a plain string of eight to ten
> steps in one direction (`4444444444`) moves further per ask than a run.
> Use runs in straight corridors; use strings of steps in caves and rooms.
> A string of steps is only as safe as the room is empty: look at the screen
> before sending ten steps into an unlit room (OBSERVED: a wild cat took 13
> hit points from a character walking blind into one, `REPORT.md` section 2).

**Why it is worth the space.** The compressed manual says a run is "far cheaper
than stepping", which is true in corridors and false in a cave. Asks 62 to 66
were five runs that stopped at once in a cave, and the player gave up on the
level at ask 67. The whole run is walking: about 100 of its 125 asks.

---

## Sheet 5. Finding the way down

*LEARNED.md items: `arrival-staircase`, `reroll-costs-three-asks`,
`reroll-pays` (contradicted), `reroll-different-level`,
`dl1-no-stairs-100-asks` (`goal:descend`), `magic-mapping-unaffordable`
(TOWN-01).*

> **Stairs.** The manual's one fixed fact: every level has at least one
> staircase of each kind, and you arrive by `>` on an up staircase and by `<`
> on a down one (connected stairs). From depth 1, `<` takes you to the town,
> where you stand on its only down staircase, so `<` then `>` is a fresh
> depth 1 for three asks. OBSERVED: the new level began with a corridor like
> the old one but was a different level, and was no quicker to find a
> staircase in. A reroll gets you a level you have not walked, not a better
> one; do it when you have learned the level is bad (a cave),
> not as a way to find stairs.
>
> **How much finding a `>` costs.** OBSERVED: about 100 of 125 asks walking two
> depth-1 levels, no `>` found. Levels are large (up to 198 by 66 squares) and you
> see only what your light reaches.
>
> **What buys a `>`, from the shops and the floor** (GAME DATA):
>
> - *Magic Mapping* scroll, 65 gold, sold by the Alchemist **only some of the
>   time** (it is "normal" stock, not "always"): it maps the walls, doors and
>   stairs within 40 squares sideways and 22 up or down of you, which is about
>   a quarter of a level. It does not mark floor as seen. OBSERVED: the
>   Alchemist had four in stock on this seed.
> - *Deep Descent* scroll: **not sold in any shop**; found in the dungeon only,
>   from depth 1. After 4 to 7 turns it takes you to the level five below your
>   *deepest* level so far, not your current one, and you do not arrive on a
>   staircase. At character level 3 and 52 hit points, depth 6 is a hard
>   place to land; at character level 1 it is far worse.
> - The game has an option, "Use autoexplore commands" (`autoexplore_commands`,
>   off by default), under which `>` walks you to the nearest known down
>   staircase and `p` walks you to the nearest unexplored square. UNTESTED: no
>   run has turned it on, and this consolidation did not check whether the
>   harness lets the player set options. The compressed manual already says
>   `p` does nothing while it is off.
>
> **Gold.** At 146 gold the first shopping of oil, cloak, three Phase Door and
> two Cure Light Wounds leaves 10 gold, and a Magic Mapping scroll is 65. TOWN-01
> says what comes first; it does not say what to do with what is left, nor that
> a Magic Mapping scroll is within reach if one fewer escape is bought.

**Why it is worth the space.** This is `sonnet-1`'s one real loss: ask 124, no
`>` found, after the run's own report said "the real cost was walking asks".
The sheet does not promise a fix (nothing here is tested) but it puts in front
of the player, before its first walking ask, the three costed alternatives
the run only thought of afterwards, and the one trap (Deep Descent's target).
The reroll lines also stop the next player repeating the mistaken
impression that a rerolled level is the same level.

---

## What is not here

- Nothing about Fang, oil, shops or stairs on any seed but 7: one run.
- Nothing about **escapes and cures actually used**: `sonnet-1` never read a
  Phase Door or drank a Cure Light Wounds, so TOWN-01's order (escapes, then a
  heal, then oil) is untested and no gap is claimed about it.
- Nothing from the `jev-*` runs: they have no notebook to consolidate.
