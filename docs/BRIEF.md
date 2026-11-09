# If you are here to play

You are the player. Read this, read the manuals, and play. Do not read
PLAN.md, another run's report, or anything under `runs/` — your judgement at a
position has to be your own, or the run is worth nothing (D9).

## What you see, and what you send

One round trip is: the screen as the game drew it, and a string of keys back.
Nothing is parsed for you and nothing is remembered for you.

```sh
.venv/bin/python -m borg_runner play --seed 7 --name my-run    # starts and waits
.venv/bin/python -m borg_runner answer 1 ' ' --run runs/my-run \
    --reason "past the splash" \
    --memory "Human Warrior, seed 7. 0 gold. Plan: shops, then down."
```

`answer` sends the keys **and prints the next screen**, so after the first one
it is one call per decision.

- **`--reason`** is one line, recorded with the keys. It is what the report
  shows beside what actually happened.
- **`--memory`** is yours. Send it when it changes; the newest one is printed
  back to you with every screen. Nothing here maintains it, corrects it or
  checks it against the game — see below.
- **`--note`** appends to your **notebook**, which is printed back with every
  screen from then on. See "Write tricks down" below; this is the most
  valuable thing you produce.

## Your character is drawn, not chosen

**At the race menu press `*`, and at the class menu press `*`.** The game's
own birth screen offers it — "`*` for a random menu item" — so the draw is the
game's, not ours and not yours. You do not pick your race or your class.

This is a rule because the alternative quietly ruins the knowledge. A model
left to choose will pick the class it reasons best about, every run; the notes
then read as general when they are really one class's notes, and nobody
notices until a different class dies of them. One earlier run chose Warrior,
another chose Mage for a spell it had read about, and their notes disagree
about what the early game is like.

So read your class's playbook **after** the draw, not before, and when an
inherited note turns out to be about somebody else's class, say so.

The record keeps the race and class the game drew, from the game's own state,
so a run that chose instead of drawing is visible afterwards.

## Keys

Every byte you send is a key. Four escapes exist for keys you cannot type:

| You write | The game gets |
|---|---|
| `\n` | Enter (`KC_ENTER`; a prompt saying "Press Return" will **not** take a carriage return) |
| `\e` | Escape |
| `\t` | Tab |
| `\\` | a literal backslash |

**Send several keys at once.** `2222` is four steps south in one round trip.
This is the whole economy of the thing: use the game's own multi-turn commands
rather than one step at a time.

| Keys | What the game does for you |
|---|---|
| `.` then a direction | Run — follows the corridor until *it* decides to stop |
| `R` `&` `\n` | Rest until healed or disturbed. One ask, often hundreds of turns |
| `v` then an item then a target | Throw, resolved in one |

A game turn is about ten game "turns" per step at normal speed, so turn
numbers move in tens.

## The cursor line

The ask header says `cursor at x,y`. That is where the game put the cursor,
and in a menu **it is the highlight** — a person sees reverse video, you see
this. Angband's birth menus move the highlight when you press a letter and
select on `\n`, so `b` then `\n` picks the second item. Watch the cursor move
if you are unsure whether a key selected or only pointed.

## Your memory is yours, and it can be wrong

Press `i` once and remember your inventory. Press `e` for equipment and `b`
for a spell book. After that, assume what you carry is still there unless you
used it, dropped it, or something burnt or stole it — and when you are not
sure, **spend a keypress and look** rather than guessing.

Nothing here will correct you. That is deliberate: a player who believes they
still have a Phase Door and does not is making a real mistake, and if the
frontend quietly fixed it the mistake could never be seen. Your memory is
recorded as you wrote it, so the report can show what you believed beside what
was true.

## Write tricks down

`runs/<your run>/notebook.md` is yours. It is printed back to you with every
screen, and **nothing here ever writes to it or corrects it** except your own
`--note`. You may edit the file to prune it; only the last 60 lines are shown,
so a notebook that grows without bound crowds out the screen.

Write down what the game taught you that the manual did not say, in the form
of something you can act on next time. Two real examples from earlier runs,
both of which cost dozens of wasted keys before anyone noticed:

```
- `>` only works while standing on a down staircase; the bottom status line
  says "Down staircase" when you are (ask 23: pressed > off the stairs and
  the message line said "There is no down staircase here")
- after taking stairs down you arrive on an *up* staircase, so `<` there
  undoes the descent you just made (ask 31: went 0 -> 1 -> 0 -> 1)
```

**Every note carries the evidence that taught it** — the ask, and what the
screen said. A note without evidence is a superstition, and it will be
believed by whoever inherits this notebook.

The notebook is the point of the run. The character will probably die; the
notes are what survives, and a later run may be given them to start from.

## What to read

**Read these before your first key, and make your first note say which files
you actually opened.** Nothing else records it, so without that note nobody
can tell whether a run was played by a reader or a guesser — and the whole
question here is what a reader does differently.

The game's own manual, at the pin:

```sh
sed -n 1,200p vendor/angband/docs/guide.rst
grep -n "Throw\|Run\|Rest" vendor/angband/docs/command.rst
```

A strategy manual written for this game, at its pin (read it through git; the
chapters are large, so read the ones you need):

```sh
cd vendor/strategy-manual
git cat-file -p HEAD:docs/c-manual/README.md                     # the chapter list
git cat-file -p HEAD:docs/c-manual/15-notes-for-the-borg.md      # numeric rules
git cat-file -p HEAD:docs/c-manual/14-class-playbooks.md         # find your class
git cat-file -p HEAD:docs/c-manual/appendices/A1-monsters-by-depth.md   # grep it
```

Chapter 15 says of itself that its rules are "a starting policy to be
measured, not truths". Treat them that way: following one and being hurt by it
is a **result**, and the most valuable thing you can report.

The minimum before you spend any gold: the commands you intend to use, and
your class's section of chapter 14. The appendices are lookup tables — grep
them when you meet something, do not read them through.

## Rules

- Change no setting, no source file and no option. You are playing the game as
  it is.
- Write only inside your run directory and the scratchpad.
- Anything you assert about the game names where you read it, or the turn and
  the message that showed it.
- You may not call anything a defect. If you think a player could do better,
  say what would settle it.

## When you stop

Write `runs/<your run>/REPORT.md`:

1. **What happened** — depth, level, how it ended, asks, turns. If you died:
   what killed you and the last three decisions before it.
2. **The decisions you would take back**, with the turn and what you would do
   instead.
3. **Where the manual was wrong or not enough.**
4. **What you could not see or could not do** — the moment, and what you
   wanted. The screen is all you get; say when that was not enough.
5. **Leads**, each as the statement, the evidence (turn, screen, line) and
   **how to test it** — and `takeover --at-turn N` is how a person checks one
   by hand.

A broken run honestly reported is a result. A tidy story is not.
