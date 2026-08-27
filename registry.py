"""Discovers songs from all three sources and owns the SONGS table.

Entries are (name, notes, program, chords, accomp, seconds_per_beat).
seconds_per_beat is None unless the source specified a tempo.
"""

import importlib
import os
import pkgutil

import songs
from config import DEFAULT_ACCOMP, DEFAULT_PROGRAM

SONGS = {}

SONGS_DIR = os.path.dirname(os.path.abspath(songs.__file__))


def _claim(slot, entry, source):
    if slot in SONGS:
        print(f"registry: slot {slot} taken, skipping {entry[0]} ({source})")
        return False
    SONGS[slot] = entry
    return True


def _load_modules():
    for info in pkgutil.iter_modules(songs.__path__):
        if info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"songs.{info.name}")
        except Exception as exc:
            print(f"registry: songs/{info.name}.py: {exc}")
            continue
        slot = getattr(mod, "SLOT", None)
        if not slot:
            continue
        _claim(slot, (
            mod.NAME,
            mod.NOTES,
            getattr(mod, "PROGRAM", DEFAULT_PROGRAM),
            getattr(mod, "CHORDS", []),
            getattr(mod, "ACCOMP", DEFAULT_ACCOMP),
            None,
        ), info.name)


def _load_text():
    try:
        import textloader
    except Exception as exc:
        print(f"registry: text loader unavailable ({exc})")
        return
    for slot, name, notes, program, accomp in textloader.load_dir(
            os.path.join(SONGS_DIR, "text")):
        _claim(slot, (name, notes, program, [], accomp, None), "text")


def _load_midi():
    try:
        from layout import NOTE_TO_KEY
        from midi.loader import load_dir
    except Exception as exc:
        print(f"registry: MIDI loader unavailable ({exc})")
        return
    for slot, name, notes, program, spb in load_dir(
            os.path.join(SONGS_DIR, "midi"), NOTE_TO_KEY, set(SONGS)):
        _claim(slot, (name, notes, program, [], program, spb), "midi")


def reload_songs():
    SONGS.clear()
    _load_modules()
    _load_text()
    _load_midi()
    return SONGS


reload_songs()

if not SONGS:
    print("registry: no songs found")
else:
    print("songs: " + " | ".join(
        f"{slot}={SONGS[slot][0]}" for slot in sorted(SONGS)))