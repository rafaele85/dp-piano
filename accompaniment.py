"""Backing chords that follow the player's tempo.

Reads beat position from the Lesson and sounds the chord under it. Freezes
when the player stops advancing, so it backs you rather than pushing you.
"""

import threading
import time

TICK = 0.02
STALL_BEATS = 2.5     # silence after this much idle time, in user beats
LEAD = 0.35           # how far past the last press the beat may drift


class Accompaniment:
    def __init__(self, lesson, audio):
        self.lesson = lesson
        self.audio = audio
        self.enabled = True
        self._running = False
        self._thread = None
        self._current = None

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self._silence()
        return self.enabled

    def _silence(self):
        if self._current is not None:
            self.audio.accomp_off()
            self._current = None

    def _effective_beat(self, now):
        """Beat position, drifting slightly past the last press."""
        last = self.lesson.last_advance
        if not last:
            return None
        idle = now - last
        beat_len = self.lesson.user_beat or 0.5
        if idle > STALL_BEATS * beat_len:
            return None
        drift = min(idle / beat_len, LEAD) if beat_len else 0.0
        return self.lesson.beat_pos + drift

    def _loop(self):
        while self._running:
            if not self.enabled or not self.lesson.active:
                self._silence()
                time.sleep(TICK)
                continue

            now = time.perf_counter()
            beat = self._effective_beat(now)
            if beat is None:
                self._silence()
                time.sleep(TICK)
                continue

            notes = self.lesson.chord_at(beat)
            if notes and notes != self._current:
                self.audio.accomp_on(notes)
                self._current = notes

            time.sleep(TICK)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        self._silence()