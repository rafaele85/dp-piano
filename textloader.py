"""Read songs from plain text files so non-programmers can write them.

    name: My Song
    slot: 7
    program: 0

    d d f g | g f d s
    a a s d | d- s. s--

Settings first, blank line, then notes. Bar lines and line breaks are
ignored. Length marks: none = 1 beat, '-' = 2, '--' = 4, '.' = half,
'-.' = 1.5. A '-' on its own is a rest, added to the previous note.
"""

import os
import re

from config import DEFAULT_ACCOMP, DEFAULT_PROGRAM

LENGTHS = {
    "": 1.0,
    "-": 2.0,
    "--": 4.0,
    ".": 0.5,
    "-.": 1.5,
    "..": 0.25,
}

NOTE_RE = re.compile(r"^([a-z;'\-])([\-.]*)$")


def _parse_note(token):
    m = NOTE_RE.match(token)
    if not m:
        raise ValueError(f"cannot read note: {token!r}")
    key, marks = m.groups()
    if marks not in LENGTHS:
        raise ValueError(f"cannot read length: {token!r}")
    return key, LENGTHS[marks]


def parse(text):
    """Returns (settings dict, notes list)."""
    settings = {}
    note_lines = []
    in_notes = False

    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            if settings:
                in_notes = True
            continue
        if not in_notes and ":" in line:
            key, value = line.split(":", 1)
            settings[key.strip().lower()] = value.strip()
        else:
            in_notes = True
            note_lines.append(line)

    notes = []
    for line in note_lines:
        for token in line.replace("|", " ").split():
            key, beats = _parse_note(token)
            if key == "-":
                if notes:
                    prev = notes[-1]
                    notes[-1] = (prev[0], prev[1] + beats)
                continue
            notes.append((key, beats))

    return settings, notes


def load_dir(directory):
    """Yields (slot, name, notes, program, accomp)."""
    if not os.path.isdir(directory):
        return
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(directory, fname)
        with open(path, encoding="utf-8") as fh:
            try:
                settings, notes = parse(fh.read())
            except ValueError as exc:
                print(f"text: {fname}: {exc}")
                continue
        if not notes:
            continue
        slot = settings.get("slot")
        if not slot:
            print(f"text: {fname}: no slot, skipping")
            continue
        yield (
            slot,
            settings.get("name", os.path.splitext(fname)[0]),
            notes,
            int(settings.get("program", DEFAULT_PROGRAM)),
            int(settings.get("accomp", DEFAULT_ACCOMP)),
        )