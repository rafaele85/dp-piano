"""Scan a directory of .mid files and yield song entries."""

import os
import re

from config import DEFAULT_PROGRAM

from . import mapping, parse

FREE_SLOTS = ["4", "5", "6"]
DEBUG = False

SLOT_RE = re.compile(r"^([0-9])\s*[-_. ]\s*(.+)$")


def load_file(path, notes_to_keys):
    """Returns (name, slot_hint, notes, program, seconds_per_beat) or None."""
    base = os.path.splitext(os.path.basename(path))[0]
    slot_hint = None
    m = SLOT_RE.match(base)
    if m:
        slot_hint, base = m.group(1), m.group(2).strip()

    parsed = parse.parse(path)
    if not parsed:
        print(f"midi: {base}: no usable melody track")
        return None

    notes, shift, kept, clamped = mapping.to_keys(
        parsed["pitches"], parsed["beats"], notes_to_keys)
    if not notes:
        print(f"midi: {base}: nothing playable after mapping")
        return None

    pitches = parsed["pitches"]
    print(f"midi: {base}: {len(notes)} notes, range "
          f"{min(pitches)}..{max(pitches)}, transpose {shift:+d}, "
          f"{kept}/{len(pitches)} in range, {clamped} clamped")

    program = parsed["program"]
    if program is None:
        program = DEFAULT_PROGRAM

    if DEBUG:
        print(f"midi: {base}: program={program} "
              f"spb={parsed['seconds_per_beat']}")
        print(f"midi: {base}: first 24 -> {notes[:24]}")

    return base, slot_hint, notes, program, parsed["seconds_per_beat"]


def load_dir(directory, notes_to_keys, taken):
    """Yields (slot, name, notes, program, seconds_per_beat)."""
    if not os.path.isdir(directory):
        return
    free = [s for s in FREE_SLOTS if s not in taken]
    for fname in sorted(os.listdir(directory)):
        if not fname.lower().endswith((".mid", ".midi")):
            continue
        try:
            result = load_file(os.path.join(directory, fname), notes_to_keys)
        except Exception as exc:
            print(f"midi: {fname}: {exc}")
            continue
        if not result:
            continue
        name, slot_hint, notes, program, spb = result
        slot = slot_hint if slot_hint and slot_hint not in taken else None
        if slot is None:
            if not free:
                print(f"midi: no free slot for {name}")
                continue
            slot = free.pop(0)
        taken.add(slot)
        yield slot, name, notes, program, spb