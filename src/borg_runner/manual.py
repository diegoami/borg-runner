"""The manual a decisions model is given, and its hash.

A decisions model reads nothing: it is handed a state and options with
descriptions. So the manual is the question, and the question is a file -
versioned here, hashed into every run record, and therefore measurable. Two
runs are comparable only if they used the same one (D14).
"""
import hashlib
import re
from pathlib import Path

from . import pins

MANUALS = pins.ROOT / 'manuals'
DEFAULT = 'jev-1'


def path(name=DEFAULT):
    return MANUALS / f'{name}.md'


def load(name=DEFAULT):
    """The instructions and the per-key descriptions this manual adds."""
    text = path(name).read_text()
    sections = {}
    current = None
    for line in text.splitlines():
        heading = re.match(r'^##\s+(\w[\w -]*)', line)
        if heading:
            current = heading.group(1).strip().lower()
            sections[current] = []
        elif current:
            sections[current].append(line)

    instructions = '\n'.join(sections.get('instructions', [])).strip()
    keys, key = {}, None
    for line in sections.get('commands', []):
        if line.startswith('>') and ' = ' not in line:
            continue                                  # a blockquote note
        found = re.match(r'^(\S) = (.*)$', line)
        if found:
            key, description = found.group(1), found.group(2).strip()
            keys[key] = description
        elif key and line.strip() and line.startswith(' '):
            keys[key] += ' ' + line.strip()
    def pairs(section, pattern):
        out, at = {}, None
        for line in sections.get(section, []):
            found = re.match(pattern, line)
            if found:
                at = found.group(1)
                out[at] = found.group(2).strip()
            elif at and line.strip() and line.startswith(' '):
                out[at] += ' ' + line.strip()
        return out

    return {'name': name, 'instructions': instructions, 'keys': keys,
            'goals': pairs('goals', r'^(\w+) = (.*)$'),
            'strategy': pairs('strategy', r'^([A-Z]+-[0-9]+) = (.*)$'),
            'state_contract': pairs('state', r'^(\w+) = (.*)$'),
            'sha256': hashlib.sha256(text.encode()).hexdigest()}
