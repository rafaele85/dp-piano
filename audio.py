"""Sound output. Takes key names, not MIDI numbers.

Uses FluidSynth when pyfluidsynth and a SoundFont are available, otherwise
falls back to the built-in Windows synth. Set the SOUNDFONT environment
variable, or drop a .sf2 file next to this script.

Channel 0 is melody, channel 1 is accompaniment.
"""

import glob
import os

from layout import CHORDS, NOTE_KEYS

MELODY_CH = 0
ACCOMP_CH = 1

DEFAULT_PROGRAM = 0
VELOCITY = 100
ACCOMP_VELOCITY = 55
REVERB_CC = 91
REVERB_LEVEL = 40


def _find_soundfont():
    env = os.environ.get("SOUNDFONT")
    if env and os.path.isfile(env):
        return env
    here = os.path.dirname(os.path.abspath(__file__))
    found = sorted(glob.glob(os.path.join(here, "*.sf2")))
    return found[0] if found else None


class _FluidBackend:
    name = "fluidsynth"

    def __init__(self, sf2):
        import fluidsynth
        self.fs = fluidsynth.Synth()
        self.fs.start(driver="dsound")
        self.sfid = self.fs.sfload(sf2)
        for ch in (MELODY_CH, ACCOMP_CH):
            self.fs.program_select(ch, self.sfid, 0, 0)
            self.fs.cc(ch, REVERB_CC, REVERB_LEVEL)

    def set_program(self, channel, program):
        self.fs.program_select(channel, self.sfid, 0, program)

    def note_on(self, channel, note, velocity):
        self.fs.noteon(channel, note, velocity)

    def note_off(self, channel, note):
        self.fs.noteoff(channel, note)

    def close(self):
        self.fs.delete()


class _PygameBackend:
    name = "pygame.midi"

    def __init__(self):
        import pygame.midi
        self._pm = pygame.midi
        pygame.midi.init()
        self.out = pygame.midi.Output(pygame.midi.get_default_output_id())
        for ch in (MELODY_CH, ACCOMP_CH):
            self.out.write_short(0xB0 | ch, REVERB_CC, REVERB_LEVEL)

    def set_program(self, channel, program):
        self.out.write_short(0xC0 | channel, program)

    def note_on(self, channel, note, velocity):
        self.out.write_short(0x90 | channel, note, velocity)

    def note_off(self, channel, note):
        self.out.write_short(0x80 | channel, note, 0)

    def close(self):
        self.out.close()
        self._pm.quit()


def _make_backend():
    sf2 = _find_soundfont()
    if sf2:
        try:
            backend = _FluidBackend(sf2)
            print(f"audio: fluidsynth ({os.path.basename(sf2)})")
            return backend
        except Exception as exc:
            print(f"audio: fluidsynth unavailable ({exc}), falling back")
    backend = _PygameBackend()
    print("audio: built-in synth")
    return backend


class Audio:
    def __init__(self, program=DEFAULT_PROGRAM):
        self.backend = _make_backend()
        self._programs = {}
        self.set_program(program)
        self._sounding = {}
        self._accomp = []

    # ---- programs ----

    def set_program(self, program, channel=MELODY_CH):
        if self._programs.get(channel) == program:
            return
        self._programs[channel] = program
        try:
            self.backend.set_program(channel, program)
        except Exception:
            pass

    @property
    def program(self):
        return self._programs.get(MELODY_CH)

    # ---- melody ----

    def note_on(self, key, velocity=VELOCITY):
        note = NOTE_KEYS.get(key)
        if note is None or key in self._sounding:
            return
        self._sounding[key] = note
        self.backend.note_on(MELODY_CH, note, velocity)

    def note_off(self, key):
        note = self._sounding.pop(key, None)
        if note is not None:
            self.backend.note_off(MELODY_CH, note)

    # ---- chord pads (melody channel) ----

    def chord_on(self, pad, velocity=VELOCITY):
        entry = CHORDS.get(pad)
        if entry is None or pad in self._sounding:
            return None
        name, notes = entry
        self._sounding[pad] = notes
        for n in notes:
            self.backend.note_on(MELODY_CH, n, velocity)
        return name, notes

    def chord_off(self, pad):
        notes = self._sounding.pop(pad, None)
        if notes:
            for n in notes:
                self.backend.note_off(MELODY_CH, n)

    # ---- accompaniment (its own channel) ----

    def accomp_on(self, notes, velocity=ACCOMP_VELOCITY):
        self.accomp_off()
        self._accomp = list(notes)
        for n in self._accomp:
            self.backend.note_on(ACCOMP_CH, n, velocity)

    def accomp_off(self):
        for n in self._accomp:
            self.backend.note_off(ACCOMP_CH, n)
        self._accomp = []

    # ---- lifecycle ----

    def all_off(self):
        self.accomp_off()
        for key in list(self._sounding):
            if isinstance(self._sounding[key], list):
                self.chord_off(key)
            else:
                self.note_off(key)

    def close(self):
        try:
            self.all_off()
            self.backend.close()
        except Exception:
            pass