# Agent entry

This file is for any session that works on this repository. Read it, then
[docs/DESIGN.md](docs/DESIGN.md), which holds every decision and what it rules
out, then [PLAN.md](PLAN.md).

**There are two different jobs here, and they must not be confused.**

## If you are here to build the frontend

Normal work: take the first `todo` task of the milestone in progress, branch,
test, open a PR, merge it when it is green. The frontend holds **no tactics,
no thresholds and no opinion about how to play** — that is the whole discipline of
this repository. If you find yourself writing "if hit points are below", stop:
that belongs to the model, in the prompt.

## If you are here to play

**Use [PLAYGAME.txt](PLAYGAME.txt)** for a new game, or
[CONTINUEGAME.txt](CONTINUEGAME.txt) to carry a stopped one on. They are the
prompt, kept in one place so every run is played under the same rules; what
follows is the longer explanation behind them.

Whoever starts you passes `AGENT=<family>` — which agent you are, as a model
family. That names [agents/&lt;family&gt;/](agents/), the directory your own
earlier sessions wrote for this one: `COMMON.md` and a page per class. You
read it before your first keypress and write back to it before you stop, and
`borg_runner playbook --family <family> --class <class>` says which pages
exist. It is the only place your experience changes how your own model plays.

You are the player, not the maintainer. Read the brief
(`docs/BRIEF.md`) and your own agent directory, and nothing else from this
repository — not the plan, not other runs' reports. Your judgement at a position has to be independent of
anyone else's, or the run is worth nothing (D9).

Read the manuals, press keys, keep your own memory of the world, and write the
report at the end. You may not change a setting, a source file or an option.

## Cloud sessions, and any machine that is not the owner's

Nothing here needs a model key, a provider or a budget (D8): the session
itself is the player. What it does need is the pinned clones and a compiler.

```sh
bash scripts/setup.sh                      # clones at the pins; checks the tools
export BORG_RUNNER_NO_X11=1                # if there is no libx11-dev
uv venv .venv && uv pip install -e '.[test]' --python .venv/bin/python
.venv/bin/python -m pytest -q              # 346 fast tests, no build
.venv/bin/python -m borg_runner build      # the game, once, a few minutes
```

- **Network**: github.com, for the two pinned repositories, and the Python
  package index. No model API is called from this repository.
- **Packages**: `git`, `cmake`, `make`, a C compiler, Python 3.10+. Nothing
  else is imported at run time — `pyproject.toml` has no dependencies and the
  tests only add pytest. `scripts/setup.sh --` names anything missing, and
  `BORG_RUNNER_INSTALL=1 bash scripts/setup.sh` installs `libx11-dev` where
  apt and sudo are available.
- **No display is needed.** Playing and replaying use our own `-magent`
  frontend, which is files in a directory. X11 is compiled in for `takeover`
  alone — replaying to a turn and handing the savefile to a person in a real
  terminal — so a container without the X11 headers sets
  `BORG_RUNNER_NO_X11=1` and loses that one command and nothing else.
  **Checked, 2026-11-10:** a build with the X11 frontend off replayed
  `sonnet-1` byte for byte, 125 asks, no differences. The flags are part of
  the build key, so the two builds keep separate directories.
- **Writable**: `build/` and `runs/`, both git-ignored. A run is a directory
  and a process; two runs never share either (D15).
- **To publish a run** the session needs push rights: `archive`, `overview`
  and a commit of `records/`, `knowledge/`, `agents/` and the three dashboard
  files. The site is GitHub Pages from `main`.

What does **not** work away from the owner's machine: `takeover` without X11,
and nothing else. The slow tests build and play the game, so they need the
compiler and a few minutes: `.venv/bin/python -m pytest -q -m slow`.

## Starting

```sh
bash scripts/setup.sh          # pinned clone and tool check; safe to rerun
uv venv .venv && uv pip install -e '.[test]' --python .venv/bin/python
.venv/bin/python -m pytest -q
```

The owner's WSL has no system `pip`, so use the virtual environment for every
command. Builds and runs take `/tmp/angband-validation.lock` with `flock`, as
the owner's other Angband work does.
