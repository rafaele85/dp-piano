"""Fit MIDI pitches onto the playable key range."""

from config import HIGH_NOTE, LOW_NOTE


def best_transpose(pitches):
    """Semitone shift keeping the most notes inside the range."""
    best_shift, best_kept = 0, -1
    for shift in range(-24, 25):
        kept = sum(1 for p in pitches if LOW_NOTE <= p + shift <= HIGH_NOTE)
        if kept > best_kept:
            best_shift, best_kept = shift, kept
    return best_shift, best_kept


def clamp(pitch, notes_to_keys):
    """Nearest playable mapped pitch: octave shift first, then neighbours."""
    if pitch in notes_to_keys:
        return notes_to_keys[pitch]
    candidate = pitch
    while candidate < LOW_NOTE:
        candidate += 12
    while candidate > HIGH_NOTE:
        candidate -= 12
    if candidate in notes_to_keys:
        return notes_to_keys[candidate]
    for offset in range(1, 13):
        for probe in (candidate - offset, candidate + offset):
            if LOW_NOTE <= probe <= HIGH_NOTE and probe in notes_to_keys:
                return notes_to_keys[probe]
    return None


def to_keys(pitches, beats, notes_to_keys):
    """Returns (notes, shift, kept, clamped)."""
    shift, kept = best_transpose(pitches)
    notes = []
    clamped = 0
    for pitch, dur in zip(pitches, beats):
        shifted = pitch + shift
        key = notes_to_keys.get(shifted)
        if key is None:
            key = clamp(shifted, notes_to_keys)
            if key is not None:
                clamped += 1
        if key is None:
            continue
        notes.append((key, dur))
    return notes, shift, kept, clamped