"""The pinned sources, and where they are cloned.

Nothing in this repository reads a moving branch. A run records the pin it
played, so a replay can be checked against the same tree.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINS = ROOT / 'pins.json'
VENDOR = ROOT / 'vendor'


def load(path=PINS):
    """The pins, as written."""
    document = json.loads(Path(path).read_text())
    if document.get('schema') != 'borg-runner/pins@1':
        raise ValueError(f'{path} is not a borg-runner/pins@1 document')
    return document['pins']


def pin(name, path=PINS):
    pins = load(path)
    if name not in pins:
        raise KeyError(f'no pin called {name!r}; there are {sorted(pins)}')
    return pins[name]


def clone(name, vendor=VENDOR):
    """Where `setup.sh` puts the pinned clone of `name`."""
    return Path(vendor) / name


def commit(name, path=PINS):
    return pin(name, path)['commit']
