# INSTRUCTIONS 2: Angband 4.2.6, depth 5 to 20, for a character that survived volume 1

**No run has reached depth 8. Volume 1 carries OBSERVED lines because earlier runs tested it; this volume has none and cannot have any yet.** Every line below is extraction from the game's data and source, or a strategy-manual rule, so it is a hypothesis about how to play depth 5 to 20, not knowledge. A run that gets here should expect to correct it, and `knowledge/NOTES.md` wins over this page as it does over volume 1. Read volume 1 first: the method, keys and class notes are not repeated. "Character level 8 to 25" is the manual's rough figure (c12 12.6, 12.7: typical CL 8-22 and 18-32), not a game rule.

Sources, so any line can be checked. Volume 1's shorthand holds and adds: `monster_spell`/`monster_base`/`projection`/`curse`/`ego_item`/`constants`/`player_timed` = `vendor/angband/lib/gamedata/<name>.txt`; `c8`/`c12`/`c13` = strategy chapters. Labels are volume 1's: **FACT** is in game data or source, **POLICY** is a chapter 15 rule (a starting policy to be measured, not truths), **UNTESTED** means no run has tried it. Nothing here is OBSERVED.

## 1. What changes at depth 5 (`monster`, `monster_spell`)
FACT, counted from `monster` (the `<player>` entry is not a monster): kinds per depth band, and how many of them breathe (a `BR_` spell) or summon (an `S_` spell).

| Depth | 0-4 | 5-9 | 10-14 | 15-19 | 20-24 |
|---|---|---|---|---|---|
| kinds | 80 | 60 | 51 | 45 | 45 |
| breathe | 0 | 11 | 2 | 5 | 9 |
| summon | 0 | 0 | 6 | 0 | 3 |

- **Breath** (from DL5): damage is a fraction of the breather's *current* hit points, armour does not reduce it (`hit:100`, `monster_spell`; acid is the one exception, section 4) and there is no saving throw (no `message-save` line on any `BR_` spell). You resist it or leave its line of sight. Section 4.
- **Summoning** (from DL10): the fight you are winning gets more monsters in it. Section 5.
- **Paralysis** (from DL13): the druid and the illusionist cast HOLD (section 2). It is not a breath or a summon, but it ends runs the same way.
- Unchanged: a staircase under you is still the one exit that cannot fail (volume 1, section 6).

## 2. The kit gates (c15 DEPTH-02, c12 12.5-12.6)
**POLICY**: c15 DEPTH-02 lists a minimum kit per depth, "each gate anchored to specific monsters". The rows in this volume's range, against `monster`:

| Depth | Required (c15 DEPTH-02) | Anchor monsters |
|---|---|---|
| 5 | Word of Recall, 3+ cure potions, ranged attack | Bullroarer (DL5) |
| 15 | 100 max hp, Phase x10 | Wormtongue (DL8), Boldor (DL13), druid (DL13) |
| 20 | Free Action | illusionist (DL13), Old Man Willow (DL19), carrion crawler (DL25), ghoul (DL26) |

- **DL5.** **Bullroarer** (DL5, +10, 60 hp, 2 x 1d8: up to 32 per turn) is the anchor, and the chapter's "+20" for him is +10 in `monster`. Cure Light Wounds heals 20, so one of them does not outpace his 32 (c15 HEAL-04): carry 3+ and leave rather than trade. Word of Recall is in your kit unless `birth_no_recall` is on (`class`).
- **DL15, 100 hp.** The druid's BO_FIRE at spell power 13 is up to 76 (`monster_spell`: `$B+9d8`, B = power / 3; power is the monster's depth unless `spell-power` says otherwise); 76 + the 20-point reserve (c15 `K_HP_RESERVE`, max(20, 10%)) = 96. So 100 is the round number above that bolt, UNTESTED as a gate. Average maximum hp at CL n is hit die + (n-1) x (hit die + 1)/2 plus CON (`src/player-birth.c roll_hp`: each level rolls 1 to the hit die): hit die 10 (Human Mage) has 87 at CL15 and needs CL18 for 100; hit die 21 (Half-Troll Warrior) has 175 at CL15. Casters' worst bolts at their native depths: **Wormtongue** (DL8, 250 hp, 1 in 5) BO_COLD up to 50 and BA_POIS up to 28, plus SLOW and TRAPS; druid BO_FIRE 76; ironfist priest WOUND 40; blacklock mage BA_POIS 32; dark dwarven lord BO_FIRE 78.
- **DL20, Free Action.** HOLD paralyses for 3+1d4 turns (`monster_spell`); Free Action blocks it (`fail:1:FREE_ACT`, `player_timed`) and so does a saving throw (`message-save`, your Saving Throw on the `C` sheet). **The gate sits seven levels after its own first anchor:** the **druid** (DL13, 78 hp, 1 in 3) and the **illusionist** (DL13, +10, 54 hp, 1 in 3) already cast it, and c15 DEPTH-01 looks at monsters native to d-2 to d+5, so DL13 is inside that window from DL8. Which depth is right is UNTESTED. **No store sells it** (`store`): found as a ring (found from DL20, 1500, `object`) or as an ego on gloves (found from DL1 to 60) or boots (1 to 40) (`ego_item`). Without it, kill HOLD casters at range or avoid them; the homunculus (DL15), the evil eye (DL18, gaze, never moves) and Old Man Willow (DL19, never moves, touch) paralyse too.
- The next gate, DL25, wants See Invisible or ESP and Teleport x5 (c15 DEPTH-02); that is volume 3's. Invisible things start before it: moaning spirit (DL12, passes walls), quasit (DL16), imp (DL17).

## 3. Escapes that still work (c13 13.1, c15 ESC)
FACT (`src/effect-handler-general.c TELEPORT`, `object`):

| Escape | `cost:` | `level:` | found from | where | distance |
|---|---|---|---|---|---|
| Scroll of Phase Door | 15 | 1 | 1 | Alchemist, always | 10 |
| Scroll of Teleportation | 40 | 10 | 10 | no store | 60% of the span |
| Scroll of Teleport Level | 800 | 20 | 20 | no store | up or down one level |
| Staff of Teleportation | 2000 | 20 | 20 | Magic shop, sometimes | 60% of the span |

- **Phase Door stops being enough** for three reasons. (1) It lands you 9 to 11 squares away; a +10 monster has energy 20 to your 10 (`src/game-world.c extract_energy`) and so closes it in 5 of your turns, a +20 monster (energy 30) in 4. c13 13.3 says "in 1 turn": the arithmetic does not. (2) Anything that needs only line of sight (breath, a bolt, an arrow) is not stopped by 10 squares in a room. (3) TELE_TO pulls you back next to the caster: Orfax and tengu (DL10), quasit (16), imp (17), blink dog and evil eye (18), Old Man Willow (19).
- **Teleportation** distance is 60% of the longer of your farthest vertical and farthest horizontal edge distance. From the middle of a full 198 x 66 level (`constants`) that is 59, then a random quarter either way: 46 to 72 squares; near an edge, more. A scroll cannot be read blind, confused or in the dark; the staff (8+... no: 5+d4 charges) is a device and needs none of that. UNTESTED: the staff's failure rate; read it off the screen.
- **Teleport Level** goes up or down at random, even odds; it cannot go up from the town (`src/effect-handler-general.c TELEPORT_LEVEL`). It is the way out of a level you cannot cross, not a way to choose. The quasit and imp cast it on you; a nexus resist saves you.
- **Never works** with the anti-teleportation curse (boots, cloak, armour, amulet or ring, `curse`): both effects print "Teleportation forbidden!" and do nothing, Phase Door included. A curse is learned by wearing the item, so an unknown ring or amulet is a gamble with the staff. On a no-teleport square (some vault grids) only a teleport of 10 or less works.
- **Deep Descent is not an escape** (volume 1, section 8; c15 ESC-04): it drops you to 5 levels below your deepest, which from DL15 is DL20.
- **Class spells** (section 6): Mage Teleport Self CL7 in the third town book; Necromancer Shadow Shift CL15; Rogue Teleport Self CL17 and Priest Portal CL10 are in dungeon-only books, so you cannot buy them. Druid, Ranger, Paladin and Blackguard have no teleport spell (`class`).
- **POLICY** c15 ESC-01 ladder still applies: staircase, Phase Door for one monster, Teleportation, heal, last. ESC-03b: after escaping, leave the level.

## 4. Breath attacks (`src/mon-spell.c breath_dam`, `projection`)
FACT: damage = the breather's current hit points / divisor, capped. `hit-points` in `monster` is the average; damaging the breather weakens its breath. Resistance divides what is left.

| Element | divisor | cap | besides damage |
|---|---|---|---|
| acid | 3 | 1600 | destroys pack items; halved if your armour is worn down by it |
| lightning | 3 | 1600 | destroys pack items |
| fire | 3 | 1600 | destroys pack items |
| cold | 3 | 1600 | destroys pack items |
| poison | 3 | 800 | poisons |
| light | 6 | 500 | blinds |
| dark | 6 | 500 | blinds |
| sound | 6 | 500 | stuns |
| shards | 6 | 500 | cuts |

- **Resist** (`src/project-player.c adjust_dam`): acid, lightning, fire, cold and poison are x1/3 per resist level; light, dark, sound and shards x6/(8+1d4) per level. A temporary resist adds one level and no more than 2 count (`src/player-calcs.c`), so the potion alone is 1/3 and a permanent resist plus the potion is 1/9. Sources are in section 7: potions for fire, cold and poison only; amulet of Resist Acid at the Magic shop; Mage Resistance CL20.
- **Distance does not help the way c15 says.** FACT (`src/effect-handler-attack.c BREATH`, `src/project.c`): every breath here is a 30-degree cone (`BREATH:...:0:30`), full strength out to 7 squares and then 8/(distance + 1) of it: 73% at 10 squares, 50% at 15. c8 says this; c15 15.3's "D = 4" and FIGHT-04's "halves at 7" do not. Break line of sight instead: a monster needs a projectable path to cast (`src/mon-attack.c monster_can_cast`), and a corner or a closed door gives none.
- Chance per monster turn is 1 in N (`innate-freq`, `monster` header), doubled at the monster's preferred range, and a +10 monster has two turns to your one. Breath comes before melee in the monster's turn.

Every breather of DL5-20, breath at full hit points (FACT, `monster`):

| Monster | DL | hp | element | breath | 1 in N |
|---|---|---|---|---|---|
| giant white dragon fly | 5 | 14 | cold | 4 | 10 |
| giant green dragon fly | 5 | 14 | poison | 4 | 10 |
| giant black dragon fly | 6 | 14 | acid | 4 | 10 |
| giant gold dragon fly | 6 | 14 | sound | 2 | 10 |
| giant salamander | 8 | 24 | fire | 8 | 9 |
| baby blue dragon | 9 | 88 | lightning | 29 | 12 |
| baby white dragon | 9 | 88 | cold | 29 | 12 |
| baby green dragon | 9 | 88 | poison | 29 | 12 |
| baby black dragon | 9 | 88 | acid | 29 | 12 |
| baby red dragon | 9 | 88 | fire | 29 | 12 |
| baby gold dragon | 9 | 88 | sound | 14 | 12 |
| pseudo-dragon | 10 | 176 | dark, light | 29 | 20 |
| baby multi-hued dragon | 11 | 114 | acid, cold, lightning, fire, poison | 38 | 12 |
| light hound | 15 | 21 | light | 3 | 5 |
| dark hound | 15 | 21 | dark | 3 | 5 |
| fire hound | 18 | 35 | fire | 11 | 10 |
| cold hound | 18 | 35 | cold | 11 | 10 |
| energy hound | 18 | 35 | lightning | 11 | 10 |
| earth hound | 20 | 68 | shards | 11 | 10 |
| air hound | 20 | 68 | poison | 22 | 10 |
| water hound | 20 | 68 | acid | 22 | 10 |
| chimaera | 20 | 160 | fire | 53 | 10 |

- The largest breath in the range is the chimaera's 53; the baby dragons' 29 to 38 are the first that matters (c8 8.x: "a real threat at DL5-10"). **Hounds come in packs**: each has 2d7 companions of its kind (`friends`, `monster`), all breathing. In a corridor only the ones with a line to you can; a room gives all of them one.
- **POLICY** c15 DANGER-04, FIGHT-04: estimate a breath from the breather's health bar, and do not stand at its preferred range. UNTESTED: a baby dragon at half health breathes half as much, so oil first is the manual's advice.

## 5. Summoners (`monster`, `monster_spell`, `src/effect-handler-general.c SUMMON`)
FACT, every summoner of DL5-20 (`spell-freq` is 1 in N monster turns):

| Monster | DL | speed | hp | 1 in N | calls |
|---|---|---|---|---|---|
| Orfax, Son of Boldor | 10 | +10 | 120 | 4 | `S_MONSTER` |
| druadan mage | 11 | +0 | 52 | 4 | `S_MONSTER` |
| master yeek | 12 | +0 | 60 | 4 | `S_MONSTER` |
| priest | 12 | +0 | 54 | 3 | `S_KIN` |
| Boldor, King of the Yeeks | 13 | +10 | 180 | 3 | `S_KIN`, `S_MONSTER` |
| druid | 13 | +0 | 78 | 3 | `S_ANIMAL` |
| quylthulg | 20 | +0 | 27 | 4 | `S_MONSTER` |
| ranger | 20 | +0 | 90 | 5 | `S_ANIMAL` |

- **How many.** The `dice:` on each spell is the number of attempts: `S_MONSTER` 1, `S_KIN` 8, `S_ANIMAL` 12. The loop adds the square of each summoned monster's level and stops when the sum reaches your depth x the summoner's own level, or the attempts run out. So a lone `S_MONSTER` brings one monster, and a summoner standing deeper than its native level brings more. `S_KIN` calls monsters of the summoner's own base (a priest calls other `p`), `S_ANIMAL` any animal. They appear next to you.
- **Why leaving is the answer** (**POLICY**, c12 12.6: "kill quickly or leave"; c13 13.3 G: break line of sight, then leave). Each cast adds a monster of the summoner's level to a fight that was already about one monster; the master yeek, Boldor, the illusionist and others also blink or teleport (TPORT, BLINK), so you cannot pin them; Orfax and Boldor arrive with 2d5 and 2d6 servants (`friends`). Against that, the casters have 27 to 78 hp, an oil flask averages about 22 (volume 1, section 5), and a +0 summoner casts at most once in 4 turns. Which is cheaper is UNTESTED. If it summons twice, take the stairs.
- Unknown items summon too: the scroll of Summon Monster and the staff of Summoning have `cost:0` (volume 1, section 6b); the scroll of Summon Undead (`cost:0`, found from DL15) is new at this depth.

## 6. Spells and books (`class`; c15 SPELL-01, SPELL-04)
FACT: second and third town books are bought at the Bookseller (kind cost shown; the shop adds its own markup, so read the price). Dungeon books are not sold. Spells in range, level, mana and base failure from `class`:

**Mage**: [Attacks and Knowledge] (kind cost 400): Frost Bolt CL13 (5 sp, 40% base failure), Reveal Monsters CL15, Acid Spray CL20 (5 sp, 30% base failure). [Magical Defences] (kind cost 1600): Teleport Self CL7 (6 sp, 35% base failure), Teleport Other CL15 (10 sp), Resistance CL20 (20 sp, 65% base failure). Fire Ball CL6 (5 sp) in volume 1's book.
**Druid**: [Gifts of Nature] (kind cost 400): Resist Poison CL7 (6 sp), Sense Surroundings CL9 (4 sp), Lightning Strike CL12 (6 sp), Earth Rising CL14.
**Priest**: [Cleansing Power] (kind cost 100): Orb of Draining CL7 (7 sp), Dispel Evil CL12, Protection from Evil CL14 (8 sp). No escape or recall until [Healing and Sanctuary] (dungeon only, kind cost 10000: Portal CL10, Word of Recall CL25).
**Necromancer**: [Dark Rituals] (kind cost 400): Crush CL10 (6 sp), Shadow Shift CL15 (10 sp). [Fear and Torment] (kind cost 1600): Frighten CL17, Vampire Strike CL20, Dark Spear CL25.
**Paladin**: no second town book; Heroism CL12 (5 sp) is the last spell of [Novice's Handbook]. Protection from Evil CL15 is in [Healing and Sanctuary] (dungeon only).
**Rogue**: [First Spells]: Object Detection CL10, Detect Stairs CL12 (3 sp, 50% base failure), Recharging CL20. Teleport Self CL17 is in [Arcane Control] (dungeon only).
**Ranger**: [Lesser Charms]: Resist Poison CL12 (10 sp), Turn Stone to Mud CL15, Sense Surroundings CL20 (8 sp). Nothing else in town.
**Blackguard**: [Into the Shadows]: Leap into Battle CL10, Grim Purpose CL13 (8 sp). [Fear and Torment]: Maim Foe CL15, Howl of the Damned CL18, Relentless Taunting CL24.

- **Failure** (`src/player-spell.c spell_chance`): the base falls 3 per level above the spell's level, never below 5% (the floor can be higher for a low casting stat) and never above 50%. A Mage's Teleport Self (35%) is down to the 5% floor at CL17 before stat adjustment. A spell cast at too little mana adds 5 per missing point (volume 1, section 5: do not).
- **Teleport Self** moves you (CL x 9/5)% of the span (`class`): CL7 is 12%, about 11 squares from the middle of a level, no better than Phase Door; CL20 is 36%, about 35; CL25 is 45%, about 44. The staff is better until CL30 (c13 13.1).
- **First cast pays experience x spell level** (`src/player-spell.c`): Mage Resistance 20 x 20 = 400, Mage Acid Spray 12 x 20 = 240, Mage Teleport Self 5 x 7 = 35, Druid Lightning Strike 8 x 12 = 96. CL15 needs 1400 x race exp / 100, CL20 4400 and CL25 12500 (`src/player.c player_exp`). UNTESTED as a way to level.
- **POLICY** c15 SPELL-01: learn escapes first, then detection, then attack (Priests and Paladins do not choose). SPELL-04: keep the mana for one escape.

## 7. Back to town (c15 TOWN, c12 12.6)
- **Word of Recall** (FACT, `src/effect-handler-general.c RECALL`, `src/game-world.c`): 15-34 turns after reading, in the dungeon it takes you up, in town down to your recall depth. **Read in town before you have ever left it, it takes you to DL1** (`src/player-util.c player_set_recall_depth` makes it at least 1): a wasted 125 gold, not a no-op, whatever volume 1 says. Read in the dungeon on a level shallower than your deepest it asks "Set recall depth to current depth?": **y also sets your deepest depth to this one**, which moves Deep Descent's target up with it; n keeps both. c15 TOWN-05 calls y "upward-safe".
- **POLICY** c12 12.6: recall when you are out of Cure potions, down to under 3 Phase Door, or the pack is full; buy the replacement scroll first; keep a spare.
- **Gold** (FACT, `src/obj-make.c make_gold`): a pile averages (16 x depth / 10 + 16) x 5 with selling off: 120 at DL5, 160 at DL10, 200 at DL15, 240 at DL20. UNTESTED what a run will pick up; the 2000 for the staff is about ten piles at DL10.

FACT, `object` (the shop adds its own markup; read the price). "found from" is the `alloc:` minimum:

| Item | `cost:` | `level:` | found from | where |
|---|---|---|---|---|
| Potion of Cure Critical Wounds | 200 | 5 | 12 | Alchemist, sometimes |
| Potion of Neutralize Poison | 75 | 5 | 1 | Alchemist, sometimes |
| Potion of Resist Heat / Resist Cold | 30 / 30 | 30 / 30 | 30 / 30 | Alchemist, sometimes |
| Potion of Resist Poison | 30 | 20 | 20 | no store |
| Potion of Restore Life Levels | 400 | 40 | 30 | Alchemist, sometimes |
| Staff of Detect Evil | 350 | 20 | 20 | Magic shop, sometimes |
| Staff of Mapping | 600 | 20 | 10 | Magic shop, sometimes |
| Wand of Stone to Mud | 300 | 10 | 10 | Magic shop, sometimes |
| Amulet of Resist Acid | 300 | 10 | 10 | Magic shop, sometimes |
| Amulet of Resist Lightning | 300 | 10 | 10 | no store |
| Ring of Resist Fire and Cold | 250 | 10 | 10 | no store |
| Ring of Free Action | 1500 | 20 | 20 | no store |

- CCW heals 60 and cures poison, stun, amnesia, confusion and cuts besides blindness (`object`); the Alchemist's Cure Light Wounds stops dropping in the dungeon at DL15. Restore Life Levels is for experience drain (section 8); drained stats come back at your next level (`src/player.c adjust_level`), so they are not an emergency (c15 CURE-03).
- "No store" means no `store` list; the Black market (`store`) lists nothing and stocks at random, so it may or may not have them.
- **Unknown scrolls and potions** (volume 1 says try them; at this depth read the list first): Deep Descent (5 below your deepest, section 3), Summon Undead (found from DL15), Aggravate Monster (found from DL5), and the cost-0 potions of Sleep and Salt Water, which paralyse (`object`). Read and drink them on a staircase at full hit points (c15 ITEM-07), UNTESTED here.

## 8. The monsters of 5-20 worth knowing by name (`monster`)
FACT, every unique in range. "Per turn" is the worst melee round (every blow at its maximum) times your turns it gets, as in volume 1:

| Unique | DL | speed | hp | per turn | note |
|---|---|---|---|---|---|
| Bullroarer the Hobbit | 5 | +10 | 60 | 32 | |
| Mughash the Kobold Lord | 7 | +0 | 150 | 30 | kobold escort |
| Lagduf, the Snaga | 8 | +0 | 190 | 38 | wolves, snagas |
| Wormtongue, Agent of Saruman | 8 | +0 | 250 | 10 | casts; steals gold |
| Brodda, the Easterling | 9 | +0 | 210 | 48 | |
| Grishnakh, the Hill Orc | 10 | +0 | 230 | 44 | wolves, orcs |
| Orfax, Son of Boldor | 10 | +10 | 120 | 34 | summons, TELE_TO |
| Golfimbul, the Hill Orc Chief | 12 | +0 | 240 | 44 | orcs, wargs |
| Boldor, King of the Yeeks | 13 | +10 | 180 | 52 | summons |
| Ufthak of Cirith Ungol | 14 | +0 | 320 | 48 | orc escort |
| Ulfast, Son of Ulfang | 16 | +0 | 340 | 60 | |
| Nar, the Dwarf | 17 | +0 | 450 | 60 | casts MIND_BLAST, HOLD no |
| Shagrat, the Orc Captain | 19 | +0 | 400 | 78 | uruk escort |
| Gorbag, the Orc Captain | 19 | +0 | 400 | 78 | uruk escort |
| Old Man Willow | 19 | +0 | 1000 | 52 | never moves; paralyses |
| Bolg, Son of Azog | 20 | +10 | 500 | 144 | fast, tough: the band's worst |

- **Out-speed you** (the +10 ones double your moves; volume 1, section 5). Packs: **wolf** (DL10, +10, 21 hp, bites 1d6: up to 12 per turn; 2d10 companions), warg (DL14, 36 hp), white wolf (DL12). Singles: panther (DL10, 45 hp, up to 32 per turn), tiger (DL12, 66 hp, up to 44), black mamba (DL12, 45 hp, poison, up to 48), sabre-tooth tiger (DL20, 150 hp, up to 80), **blood falcon** (DL20, +30, 6 hp, up to 64 per its turn: kill it first, from range).
- **Drain experience**: grape jelly (DL12, never moves, touch EXP_10), nether worm mass (DL12, breeds), evil eye (DL18, gaze, never moves). **Drain stats**: red jelly, giant red frog, red naga and giant red ant take STR (DL7-9), moaning spirit and quasit take DEX; the purple mushroom patch (DL6, never moves, 1 hp) takes CON three times.
- **Steal**: Wormtongue (gold), the rogue (DL16, an item). **Breed**: giant fruit fly (DL10), giant flea (DL14), hummerhorn (DL18): leave the level.
