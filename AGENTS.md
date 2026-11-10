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

## Starting

```sh
bash scripts/setup.sh          # pinned clone and tool check; safe to rerun
uv venv .venv && uv pip install -e '.[test]' --python .venv/bin/python
.venv/bin/python -m pytest -q
```

The owner's WSL has no system `pip`, so use the virtual environment for every
command. Builds and runs take `/tmp/angband-validation.lock` with `flock`, as
the owner's other Angband work does.
