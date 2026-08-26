"""Lesson state machine: demo playback, then wait-mode practice."""

import threading
import time

from scoring import Scorer
from songs import BEAT, DEMO_BEAT, REPEATS, SONGS

FLASH_ON = 0.12
FLASH_OFF = 0.10
FLASH_TIMES = 3
ERROR_FLASH = 0.3


def note_of(entry):
    return entry[0]


def beats_of(entry):
    return entry[1]


def lyric_of(entry):
    return entry[2] if len(entry) > 2 else ""


class Lesson:
    """Holds practice state. Never touches the LEDs directly."""

    def __init__(self, audio, log=print):
        self.audio = audio
        self.log = log
        self.scorer = Scorer(BEAT)

        self.song = []
        self.song_slot = next(iter(SONGS))
        self.step = 0

        self.practising = False
        self.demoing = False
        self.flashing = False

        self.hold_until = 0.0
        self.hold_span = 0.0
        self.error_until = 0.0

        self._demo_key = None
        self._demo_next = None
        self._token = 0

    # ---- selection ----

    def select_song(self, slot):
        if slot in SONGS:
            self.song_slot = slot
            self.log(f"selected: {SONGS[slot][0]}  (space to start)")

    def set_level(self, slot):
        name = self.scorer.set_level(slot)
        if name:
            self.log(f"level: {name}")

    # ---- renderer interface ----

    @property
    def active(self):
        return self.practising or self.demoing

    @property
    def score(self):
        return self.scorer.score

    def target_key(self):
        if self.demoing:
            return self._demo_key
        if self.practising and self.step < len(self.song):
            return note_of(self.song[self.step])
        return None

    def next_key(self):
        cur = self.target_key()
        if self.demoing:
            nxt = self._demo_next
        elif self.practising and self.step + 1 < len(self.song):
            nxt = note_of(self.song[self.step + 1])
        else:
            nxt = None
        return nxt if nxt and nxt != cur else None

    def bar_fraction(self, now):
        if not self.practising or self.hold_until <= now or not self.hold_span:
            return 0.0
        return (self.hold_until - now) / self.hold_span

    def in_error(self, now):
        return now < self.error_until

    # ---- run control ----

    def start(self):
        name, base, program = SONGS[self.song_slot]
        self.audio.set_program(program)
        self.song = list(base) * REPEATS
        self.step = 0
        self.hold_until = 0.0
        self.scorer.reset()
        self.practising = False
        self._token += 1
        self.demoing = True
        self.log(f"\n{name} — demo, then {REPEATS} rounds "
                 f"({len(self.song)} notes).")
        threading.Thread(target=self._demo_run,
                         args=(self._token, list(base)), daemon=True).start()

    def stop(self):
        self._token += 1
        self.demoing = False
        self.flashing = False
        self._demo_key = self._demo_next = None
        if self.practising:
            self._report()
        self.practising = False
        self.hold_until = 0.0
        self.scorer.grade_pending()
        self.log("Stopped.")

    def shutdown(self):
        self._token += 1
        self.demoing = False
        self.practising = False
        self.flashing = False

    # ---- demo ----

    def _demo_run(self, token, tune):
        for i, entry in enumerate(tune):
            if token != self._token:
                break
            self._demo_key = note_of(entry)
            self._demo_next = (note_of(tune[i + 1])
                               if i + 1 < len(tune) else None)
            syl = lyric_of(entry)
            if syl:
                print(syl, end=" ", flush=True)
            span = beats_of(entry) * DEMO_BEAT
            self.audio.note_on(self._demo_key)
            time.sleep(span * 0.9)
            self.audio.note_off(self._demo_key)
            time.sleep(span * 0.1)
        self._demo_key = self._demo_next = None
        print()

        if token == self._token:
            self._flash(token)
        if token == self._token:
            self.demoing = False
            self.practising = True
            self.log(f"Your turn — {len(self.song)} notes. "
                     f"Level: {self.scorer.level_name}")

    def _flash(self, token):
        for _ in range(FLASH_TIMES):
            if token != self._token:
                break
            self.flashing = True
            time.sleep(FLASH_ON)
            self.flashing = False
            time.sleep(FLASH_OFF)
        self.flashing = False

    # ---- player input ----

    def on_press(self, key):
        if not self.practising or self.step >= len(self.song):
            return
        now = time.perf_counter()
        entry = self.song[self.step]

        if key != note_of(entry):
            self.error_until = now + ERROR_FLASH
            self.scorer.on_wrong()
            self.log(f"  x wrong: {key}, want {note_of(entry)}")
            return

        label = self.scorer.grade_pending(now)
        if label:
            self.log(f"  - {label}")

        self.hold_span = self.scorer.on_correct(key, beats_of(entry), now)
        self.hold_until = now + self.hold_span

        self.step += 1
        self.log(f"{self.step}/{len(self.song)}  {lyric_of(entry)}"
                 f"   [{self.scorer.score:.0f}]")

        if self.step >= len(self.song):
            self.scorer.grade_pending(now)
            self.practising = False
            self.hold_until = 0.0
            self.log(f"Done — grade {self.scorer.grade}")
            self._report()

    def on_release(self, key):
        if not self.practising:
            return
        label = self.scorer.on_release(key)
        if label:
            self.log(f"  - {label}")

    # ---- reporting ----

    def _report(self):
        for line in self.scorer.report_lines():
            self.log(line)