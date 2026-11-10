"""Build the pinned game with our frontend, reproducibly.

The pinned tree is copied, our frontend is added, and the build is keyed by
the commit and the hash of the patch - so the same inputs give the same
directory, and a changed patch gives a new one rather than a stale binary.

Three upstream files are edited, and all three only to register the frontend:
`src/main.h` and `src/main.c` to declare and list it, and `CMakeLists.txt` to
compile it. The game's own logic is untouched (D1, D2).
"""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from . import pins

PATCH = pins.ROOT / 'patch'
BUILDS = pins.ROOT / 'build'
FRONTEND = 'src/main-agent.c'

# The build id is pinned on purpose. Left alone, CMake runs `git describe` in
# the source directory - which is a copy inside *this* repository - so the
# game's splash screen carried borg-runner's own commit and a -dirty flag, and
# every commit here changed screen 1 of every recording. A replay then
# differed on the first ask and on nothing else. Found 2026-11-09 by replaying
# three runs under a new build.
CMAKE_ARGS = ['-DSUPPORT_BORG=OFF', '-DSUPPORT_TEST_FRONTEND=OFF',
              '-DSUPPORT_X11_FRONTEND=ON', '-DCMAKE_BUILD_TYPE=Release',
              f'-DANGBAND_BUILD_ID=borg-runner-{pins.commit("angband")[:7]}']

# Playing and replaying use our own `-magent` frontend, which is files and no
# display. X11 is compiled in for one thing only: `takeover`, which hands a
# replayed savefile to a person in a real terminal (D7, D11). A machine with
# no `libx11-dev` - a cloud container, usually - can build everything else,
# so `BORG_RUNNER_NO_X11=1` drops that frontend. The flags are part of the
# build key, so such a build lives in its own directory and does not disturb
# the local one; the screens are the same either way, because the splash is
# pinned by ANGBAND_BUILD_ID and no frontend but ours is ever started.
NO_X11 = 'BORG_RUNNER_NO_X11'


def cmake_args():
    if not os.environ.get(NO_X11):
        return list(CMAKE_ARGS)
    return [argument if argument != '-DSUPPORT_X11_FRONTEND=ON'
            else '-DSUPPORT_X11_FRONTEND=OFF' for argument in CMAKE_ARGS]

# Each edit is (file, what must be there exactly once, what replaces it).
EDITS = (
    ('src/main.h',
     'extern errr init_test(int argc, char **argv);',
     'extern errr init_test(int argc, char **argv);\n'
     'extern errr init_agent(int argc, char **argv);'),
    ('src/main.h',
     'extern const char help_test[];',
     'extern const char help_test[];\nextern const char help_agent[];'),
    ('src/main.c',
     '#ifdef USE_TEST\n\t{ "test", help_test, init_test, false, true },\n'
     '#endif /* !USE_TEST */',
     '#ifdef USE_TEST\n\t{ "test", help_test, init_test, false, true },\n'
     '#endif /* !USE_TEST */\n'
     '#ifdef USE_AGENT\n\t{ "agent", help_agent, init_agent, false, true },\n'
     '#endif /* !USE_AGENT */'),
    ('CMakeLists.txt',
     '        $<$<BOOL:${SUPPORT_TEST_FRONTEND}>:src/main-test.c>',
     '        $<$<BOOL:${SUPPORT_TEST_FRONTEND}>:src/main-test.c>\n'
     '        src/main-agent.c'),
    ('CMakeLists.txt',
     'target_compile_definitions(OurExecutable PRIVATE "${ANGBAND_BUILD_ID_OPTION}")',
     'target_compile_definitions(OurExecutable PRIVATE -D USE_AGENT)\n'
     'target_compile_definitions(OurExecutable PRIVATE "${ANGBAND_BUILD_ID_OPTION}")'),
)


def patch_sha256(patch=PATCH):
    """Every file of the patch, by name, so a changed patch is a new build."""
    digest = hashlib.sha256()
    for path in sorted(Path(patch).rglob('*')):
        if path.is_file():
            digest.update(str(path.relative_to(patch)).encode())
            digest.update(path.read_bytes())
    for _, old, new in EDITS:
        digest.update(old.encode())
        digest.update(new.encode())
    # The configure flags belong in the key too: changing one of them changes
    # the binary, and leaving them out meant a changed flag quietly reused the
    # cached build. Found when pinning the build id did not take effect.
    for argument in cmake_args():
        digest.update(argument.encode())
    return digest.hexdigest()


def key(patch=PATCH):
    """The build's identity: the game's commit and the patch."""
    return f'{pins.commit("angband")[:12]}-{patch_sha256(patch)[:12]}'


def binary(out):
    return Path(out) / 'build' / 'game' / 'angband'


def apply_patch(source, patch=PATCH, log=print):
    """Copy our files in and make the three registration edits."""
    source, patch = Path(source), Path(patch)
    for path in sorted(patch.rglob('*')):
        if path.is_file():
            target = source / path.relative_to(patch)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            log(f'patch: added {path.relative_to(patch)}')
    for name, old, new in EDITS:
        path = source / name
        text = path.read_text()
        if new in text:
            continue
        if text.count(old) != 1:
            raise ValueError(
                f'{name}: expected exactly one place to edit, found '
                f'{text.count(old)}. The pinned tree moved under the patch.')
        path.write_text(text.replace(old, new))
        log(f'patch: edited {name}')


def prepare(out=None, force=False, log=print):
    """The built tree, from cache when the inputs have not changed."""
    out = Path(out) if out else BUILDS / key()
    if binary(out).exists() and not force:
        log(f'build: cached {out}')
        return out
    if out.exists() and force:
        shutil.rmtree(out)

    source = out / 'source'
    if not source.exists():
        shutil.copytree(pins.clone('angband'), source,
                        ignore=shutil.ignore_patterns('.git'))
    apply_patch(source, log=log)

    for name, command in (
            ('configure', ['cmake', '-S', str(source), '-B', str(out / 'build'),
                           *cmake_args()]),
            ('build', ['cmake', '--build', str(out / 'build'),
                       '--target', 'OurExecutable', '-j', '4'])):
        log(f'build: {name}')
        done = subprocess.run(command, capture_output=True, text=True)
        if done.returncode != 0:
            raise RuntimeError(f'{name} failed:\n{done.stdout[-3000:]}\n{done.stderr[-3000:]}')

    # cmake leaves only the writable directories under game/lib; the game's
    # read-only data lives in the source tree. Copying it in makes the built
    # tree self-contained, which the takeover terminal needs as much as play.
    data = out / 'build' / 'game' / 'lib'
    for name in ('gamedata', 'help', 'screens', 'customize', 'fonts', 'icons',
                 'sounds', 'tiles'):
        here, there = source / 'lib' / name, data / name
        if here.is_dir() and not there.exists():
            shutil.copytree(here, there)
            log(f'build: lib/{name}')
    for name in ('save', 'panic', 'scores'):
        (data / name).mkdir(parents=True, exist_ok=True)

    identity = {
        'schema': 'borg-runner/build@1',
        'game': pins.pin('angband')['repository'],
        'commit': pins.commit('angband'),
        'patch_sha256': patch_sha256(),
        'cmake_args': cmake_args(),
        'binary_sha256': hashlib.sha256(binary(out).read_bytes()).hexdigest(),
    }
    (out / 'build-identity.json').write_text(
        json.dumps(identity, indent=2, sort_keys=True) + '\n')
    log(f'build: {binary(out)}')
    return out
