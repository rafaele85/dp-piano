"""Sound output. Takes key names, not MIDI numbers.

Uses FluidSynth when pyfluidsynth and a SoundFont are available, otherwise
falls back to the built-in Windows synth. Set the SOUNDFONT environment
variable, or drop a .sf2 file next to this script.
"""

import glob
import os

from layout import CHORDS, NOTE_KEYS

DEFAULT_PROGRAM = 0
VELOCITY = 100
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
        self.fs.program_select(0, self.sfid, 0, 0)
        self.fs.cc(0, REVERB_CC, REVERB_LEVEL)

    def set_program(self, program):
        self.fs.program_select(0, self.sfid, 0, program)

    def note_on(self, note, velocity):
        self.fs.noteon(0, note, velocity)

    def note_off(self, note):
        self.fs.noteoff(0, note)

    def close(self):
        self.fs.delete()


class _PygameBackend:
    name = "pygame.midi"

    def __init__(self):
        import pygame.midi
        self._pm = pygame.midi
        pygame.midi.init()
        self.out = pygame.midi.Output(pygame.midi.get_default_output_id())
        self.out.write_short(0xB0, REVERB_CC, REVERB_LEVEL)

    def set_program(self, program):
        self.out.set_instrument(program)

    def note_on(self, note, velocity):
        self.out.note_on(note, velocity)

    def note_off(self, note):
        self.out.note_off(note, 0)

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
        self.program = None
        self.set_program(program)
        self._sounding = {}

    def set_program(self, program):
        if program == self.program:
            return
        self.program = program
        try:
            self.backend.set_program(program)
        except Exception:
            pass

    def note_on(self, key, velocity=VELOCITY):
        note = NOTE_KEYS.get(key)
        if note is None or key in self._sounding:
            return
        self._sounding[key] = note
        self.backend.note_on(note, velocity)

    def note_off(self, key):
        note = self._sounding.pop(key, None)
        if note is not None:
            self.backend.note_off(note)

    def chord_on(self, pad, velocity=VELOCITY):
        entry = CHORDS.get(pad)
        if entry is None or pad in self._sounding:
            return None
        name, notes = entry
        self._sounding[pad] = notes
        for n in notes:
            self.backend.note_on(n, velocity)
        return name, notes

    def chord_off(self, pad):
        notes = self._sounding.pop(pad, None)
        if notes:
            for n in notes:
                self.backend.note_off(n)

    def all_off(self):
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