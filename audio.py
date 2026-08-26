"""Sound output. Takes key names, not MIDI numbers."""

import pygame.midi

from layout import CHORDS, NOTE_KEYS

DEFAULT_PROGRAM = 0     # acoustic grand
VELOCITY = 100
REVERB_CC = 91
REVERB_LEVEL = 40


class Audio:
    def __init__(self, program=DEFAULT_PROGRAM):
        pygame.midi.init()
        self.out = pygame.midi.Output(pygame.midi.get_default_output_id())
        self.program = None
        self.set_program(program)
        self.out.write_short(0xB0, REVERB_CC, REVERB_LEVEL)
        self._sounding = {}

    # ---- configuration ----

    def set_program(self, program):
        """GM program number, 0-127."""
        if program == self.program:
            return
        self.program = program
        self.out.set_instrument(program)

    # ---- single notes ----

    def note_on(self, key, velocity=VELOCITY):
        note = NOTE_KEYS.get(key)
        if note is None or key in self._sounding:
            return
        self._sounding[key] = note
        self.out.note_on(note, velocity)

    def note_off(self, key):
        note = self._sounding.pop(key, None)
        if note is not None:
            self.out.note_off(note, 0)

    # ---- chords ----

    def chord_on(self, pad, velocity=VELOCITY):
        entry = CHORDS.get(pad)
        if entry is None or pad in self._sounding:
            return None
        name, notes = entry
        self._sounding[pad] = notes
        for n in notes:
            self.out.note_on(n, velocity)
        return name, notes

    def chord_off(self, pad):
        notes = self._sounding.pop(pad, None)
        if notes:
            for n in notes:
                self.out.note_off(n, 0)

    # ---- lifecycle ----

    def all_off(self):
        for key in list(self._sounding):
            value = self._sounding[key]
            if isinstance(value, list):
                self.chord_off(key)
            else:
                self.note_off(key)

    def close(self):
        try:
            self.all_off()
            self.out.close()
            pygame.midi.quit()
        except Exception:
            pass