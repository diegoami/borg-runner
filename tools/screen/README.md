# tools/screen — the shared screen tools

A run may write code: the screen is all it has, and parsing 80×24 of text by
eye costs attention that the dungeon wants. One of the first runs here wrote a
143-line breadth-first search, and the next life of the same character wrote
it again. **This directory is so that the third one does not.**

Every tool reads a screen dump and prints. None of them presses a key, and
none of them decides anything.

```sh
python3 tools/screen/explore.py m-screen.txt          # press M first: one ask, the level
python3 tools/screen/look.py  runs/mine/ask/screen-42.txt --map
python3 tools/screen/aim.py   runs/mine/ask/screen-42.txt --to '>'
python3 tools/screen/map.py   runs/mine/ask/screen-42.txt --shops
python3 tools/screen/diff.py  runs/mine/ask/screen-41.txt runs/mine/ask/screen-42.txt
```

| tool | what it is for |
|---|---|
| [screen.py](screen.py) | the reader the others use: panels, sidebar, status line, `@`, glyph coordinates, and whether a menu is covering the map |
| [look.py](look.py) | everything the screen has drawn, nearest first, with the offset from `@` in the game's own form (`3 S, 2 E`) |
| [aim.py](aim.py) | a place on the screen → the keys that make **the game** walk there (`*`, cursor digits, `g`) |
| [map.py](map.py) | the panel with coordinate rulers, and a local route over tiles that are drawn walkable |
| [diff.py](diff.py) | what changed between two screens — and whether anything did, which is how you catch a key that did nothing |
| [explore.py](explore.py) | where the level is still dark, and the keys to send the game at it. Give it an `M` screen — one ask, the whole remembered level — or a run's recent screens |

They take a raw dump (`runs/<run>/ask/screen-<n>.txt`) or the output of
`answer`/`wait` pasted into a file; `screen.py` strips the `=== ASK` header
and the notebook that follows.

## Two rules

**Check the game first.** The game does more than it looks. Its own walk
covers 17 to 44 tiles in one ask and pathfinds through ground you have never
seen; `lxg` explores and `l>g` walks to a known staircase. A tool that
reimplements that measures your code instead of the game, and costs you the
chance to find out what the game already had. `aim.py` exists to *use* the
game's pathfinder, not to replace it — and `map.py`, which does route, says in
its own header when not to use it.

**A shared tool runs in a bare checkout.** No `import borg_runner`: a player
runs these as plain scripts. `python -m borg_runner tools --check` holds that,
along with every tool parsing and saying where it came from.

## Writing one, and keeping it

While you play, your own tools go in `runs/<your run>/tools/` — they are
archived with the run, because a run played with a pathfinder it wrote is
measuring its code as well as itself, and a reader a month later cannot tell
the two apart unless the code is there.

When one turns out to be worth keeping, adopt it:

```sh
python -m borg_runner tools                                   # what exists already
python -m borg_runner tools --adopt runs/mine/tools/x.py --from mine
python -m borg_runner tools --check
```

Adoption copies it here with a header naming the run it came from and the
date. **Your own copy is left exactly as you played it**: the record keeps
what you ran, and the library keeps the version that may be corrected since.

If you improve a tool that is already here, say so in its header — what was
wrong and which run found it. `map.py` is the example: it arrived with its
direction table transposed, so every route it printed walked the wrong way,
and that is now fixed once for everybody rather than rediscovered per run.
