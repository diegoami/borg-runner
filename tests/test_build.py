"""The build, and the claim that no Borg is in it.

The slow test builds the game; the fast ones check the patch is the shape the
build expects, because a pinned tree that moves under it must fail loudly
rather than quietly produce a different game.
"""
import pytest

from borg_runner import build, pins


def test_the_build_is_keyed_by_the_commit_and_the_patch():
    """A changed patch must give a new build, not a stale binary."""
    key = build.key()
    assert key.startswith(pins.commit('angband')[:12])
    assert len(build.patch_sha256()) == 64


def test_the_borg_is_off_and_our_frontend_is_on():
    """D1: ALLOW_BORG is what defines inkey_hack, so the Borg's hook is gone."""
    assert '-DSUPPORT_BORG=OFF' in build.CMAKE_ARGS
    definitions = [new for _, _, new in build.EDITS if 'USE_AGENT' in new]
    assert definitions, 'nothing defines USE_AGENT, so the frontend compiles away'


def test_every_edit_names_a_file_that_exists_at_the_pin():
    """The three upstream files we touch, and nothing else."""
    touched = {name for name, _, _ in build.EDITS}
    assert touched == {'src/main.h', 'src/main.c', 'CMakeLists.txt'}
    clone = pins.clone('angband')
    if not clone.exists():
        pytest.skip('run scripts/setup.sh first')
    for name in touched:
        assert (clone / name).exists(), name


def test_each_edit_matches_exactly_once_in_the_pinned_tree():
    """The loud failure: if the tree moved, say so before building."""
    clone = pins.clone('angband')
    if not clone.exists():
        pytest.skip('run scripts/setup.sh first')
    for name, old, _ in build.EDITS:
        text = (clone / name).read_text()
        assert text.count(old) == 1, f'{name}: {text.count(old)} matches, expected 1'


def test_the_frontend_asks_for_nothing_it_should_not():
    """The frontend must hold no tactics. A grep is a blunt instrument and
    exactly the right one: these words have no business in it."""
    source = (build.PATCH / 'src' / 'main-agent.c').read_text()
    for forbidden in ('hit_point', 'danger', 'monster', 'inventory', 'spell'):
        assert forbidden not in source.lower(), f'{forbidden} suggests an opinion'


def test_the_frontend_lets_the_game_end_a_key_string():
    """T11: the game's own flush drops the rest of the buffer, and `-k` keeps
    it so a recording made before the rule still replays byte for byte."""
    source = (build.PATCH / 'src' / 'main-agent.c').read_text()
    flush = source[source.index('case TERM_XTRA_FLUSH'):]
    assert 'agent_keep_buffer' in flush
    assert 'agent_at = agent_held = 0' in flush
    assert '"-k"' in source or "'-k'" in source


@pytest.mark.slow
def test_the_built_binary_contains_no_borg_at_all():
    """D1's gate. Needs a compiler, cmake and libx11-dev."""
    import subprocess
    out = build.prepare(log=lambda *a: None)
    assert build.binary(out).exists()
    symbols = subprocess.run(['nm', str(build.binary(out))],
                             capture_output=True, text=True).stdout.lower()
    assert 'borg' not in symbols
    assert 'inkey_hack' not in symbols


def test_the_configure_flags_are_part_of_the_build_key():
    """A changed flag changes the binary, so it must change the key.

    Pinning the build id had no effect at first because the key did not cover
    the flags, so prepare() handed back the cached binary.
    """
    first = build.patch_sha256()
    original = list(build.CMAKE_ARGS)
    try:
        build.CMAKE_ARGS.append('-DSOMETHING_ELSE=ON')
        assert build.patch_sha256() != first
    finally:
        build.CMAKE_ARGS[:] = original
    assert build.patch_sha256() == first


KEY_WITH_X11 = build.key()


def test_x11_can_be_left_out_for_a_machine_without_it(monkeypatch):
    """Playing and replaying use our own frontend; X11 is only for takeover.

    A build without it replays a recorded run byte for byte - checked on
    sonnet-1, 125 asks, no differences, 2026-11-10 - so a cloud container with
    no libx11-dev can still play and still reproduce what the owner's machine
    recorded.
    """
    assert '-DSUPPORT_X11_FRONTEND=ON' in build.cmake_args()
    monkeypatch.setenv(build.NO_X11, '1')
    without = build.cmake_args()
    assert '-DSUPPORT_X11_FRONTEND=OFF' in without
    assert '-DSUPPORT_X11_FRONTEND=ON' not in without
    # The flags are part of the build key, so the two builds do not share a
    # directory and neither reuses the other's cache.
    assert build.key() != KEY_WITH_X11


def test_the_build_id_is_pinned_to_the_game_and_not_to_this_repository():
    """Left alone, cmake stamps our own git describe into the splash screen,
    so every commit here changed screen 1 of every recording."""
    pinned = [a for a in build.CMAKE_ARGS if a.startswith('-DANGBAND_BUILD_ID=')]
    assert pinned, 'the build id must be pinned'
    assert pins.commit('angband')[:7] in pinned[0]
