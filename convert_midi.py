import mido

path = "songs/midi/cant.mid"
mid = mido.MidiFile(path)

print("ticks_per_beat:", mid.ticks_per_beat)
print("tracks:", len(mid.tracks))

for i, track in enumerate(mid.tracks):
    notes = [m.note for m in track
             if m.type == "note_on" and m.velocity > 0]
    channels = {getattr(m, "channel", None) for m in track
                if m.type == "note_on"}
    print(f"[{i}] {track.name!r}  notes={len(notes)}  channels={channels}"
          f"  range={min(notes) if notes else '-'}..{max(notes) if notes else '-'}")