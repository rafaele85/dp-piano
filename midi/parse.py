"""Read melody, tempo and instrument from a MIDI file.

Pure parsing — knows nothing about the keyboard layout.
"""

MIN_TRACK_NOTES = 8
MAX_BEATS = 4.0
GRID = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]


def snap(beats):
    return min(GRID, key=lambda g: abs(g - beats))


def track_pitches(track):
    return [m.note for m in track
            if m.type == "note_on" and m.velocity > 0
            and getattr(m, "channel", 0) != 9]


def pick_melody_track(mid):
    """Highest-register track with enough notes.

    Ranked by average pitch, not note count: accompaniment usually has
    more notes than the melody.
    """
    best, best_score = None, None
    for track in mid.tracks:
        pitches = track_pitches(track)
        if len(pitches) < MIN_TRACK_NOTES:
            continue
        avg = sum(pitches) / len(pitches)
        if best_score is None or avg > best_score:
            best, best_score = track, avg
    return best


def track_program(track):
    for msg in track:
        if msg.type == "program_change":
            return msg.program
    return None


def file_tempo(mid):
    """Microseconds per beat from the first set_tempo, or None."""
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                return msg.tempo
    return None


def onsets(track):
    """[(pitch, start_tick)] — one note per onset, highest pitch wins."""
    events = []
    t = 0
    for msg in track:
        t += msg.time
        if msg.type == "note_on" and msg.velocity > 0 \
                and getattr(msg, "channel", 0) != 9:
            events.append((msg.note, t))

    events.sort(key=lambda e: (e[1], -e[0]))
    reduced = []
    last = None
    for pitch, start in events:
        if start == last:
            continue
        reduced.append((pitch, start))
        last = start
    return reduced


def durations(note_onsets, ticks_per_beat, tail_ticks=None):
    """Beat value per note, onset to onset, so rests are included."""
    if tail_ticks is None:
        tail_ticks = ticks_per_beat
    out = []
    for i, (_pitch, start) in enumerate(note_onsets):
        if i + 1 < len(note_onsets):
            span = note_onsets[i + 1][1] - start
        else:
            span = tail_ticks
        beats = span / ticks_per_beat if ticks_per_beat else 1.0
        out.append(min(snap(beats), MAX_BEATS))
    return out


def parse(path):
    """Returns a dict, or None if nothing usable was found."""
    import mido

    mid = mido.MidiFile(path)
    track = pick_melody_track(mid)
    if track is None:
        return None

    note_onsets = onsets(track)
    if not note_onsets:
        return None

    ticks_per_beat = mid.ticks_per_beat or 480
    tempo = file_tempo(mid)

    return {
        "pitches": [p for p, _s in note_onsets],
        "beats": durations(note_onsets, ticks_per_beat),
        "program": track_program(track),
        "seconds_per_beat": (tempo / 1_000_000.0) if tempo else None,
    }