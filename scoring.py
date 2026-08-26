"""Rolling-window scoring for practice sessions.

The score is 'how well am I playing recently', not a lifetime total, so a
bad patch fades out after WINDOW notes regardless of how bad it was.
"""

import time
from collections import deque

WINDOW = 16

LEVELS = {
    "7": dict(
        name="novice",
        grade_duration=False,
        grade_gap=False,
        short=0.0,
        long=99.0,
        gap=None,
        partial_credit=0.0,
    ),
    "8": dict(
        name="normal",
        grade_duration=True,
        grade_gap=True,
        short=0.45,
        long=2.20,
        gap=1.4,
        partial_credit=0.5,
    ),
    "9": dict(
        name="strict",
        grade_duration=True,
        grade_gap=True,
        short=0.70,
        long=1.40,
        gap=0.7,
        partial_credit=0.3,
    ),
}

DEFAULT_LEVEL = "7"


class Scorer:
    def __init__(self, default_beat, level_slot=DEFAULT_LEVEL):
        self.default_beat = default_beat
        self.level = LEVELS[level_slot]
        self.user_beat = default_beat
        self._recent = deque(maxlen=WINDOW)
        self.reset()

    # ---- configuration ----

    def set_level(self, slot):
        if slot in LEVELS:
            self.level = LEVELS[slot]
            return self.level["name"]
        return None

    @property
    def level_name(self):
        return self.level["name"]

    # ---- lifecycle ----

    def reset(self):
        self._recent.clear()
        self.user_beat = self.default_beat
        self.n_correct = 0
        self.n_wrong = 0
        self.n_short = 0
        self.n_long = 0
        self.n_gap = 0
        self._pending = None      # (key, press_time, beats)
        self._last_onset = 0.0
        self._last_beats = 0.0
        self._last_release = 0.0
        self.run_start = 0.0

    # ---- scoring ----

    @property
    def score(self):
        if not self._recent:
            return 100.0
        return 100.0 * sum(self._recent) / len(self._recent)

    def _record(self, value):
        self._recent.append(value)

    def on_wrong(self):
        self.n_wrong += 1
        self._record(0.0)

    def on_correct(self, key, beats, now=None):
        """Register an accepted press. Returns the expected hold in seconds."""
        now = now or time.perf_counter()

        self.grade_pending(now)
        self.n_correct += 1
        self._record(1.0)

        if self.level["grade_gap"] and self._last_release:
            gap = now - self._last_release
            if gap > self.level["gap"] * self.user_beat:
                self.n_gap += 1
                self._record(self.level["partial_credit"])

        if self._last_onset and self._last_beats:
            interval = (now - self._last_onset) / self._last_beats
            if 0.12 < interval < 2.5:
                self.user_beat = 0.75 * self.user_beat + 0.25 * interval

        if not self.run_start:
            self.run_start = now

        self._pending = (key, now, beats)
        self._last_onset = now
        self._last_beats = beats
        return beats * self.user_beat

    def grade_pending(self, now=None):
        """Grade the note awaiting release. Returns a label or None."""
        if self._pending is None:
            return None
        now = now or time.perf_counter()
        _key, press, beats = self._pending
        self._pending = None

        if not self.level["grade_duration"]:
            return None

        expected = beats * self.user_beat
        if expected <= 0:
            return None

        ratio = (now - press) / expected
        if ratio < self.level["short"]:
            self.n_short += 1
            self._record(self.level["partial_credit"])
            return f"short ({ratio:.2f}x)"
        if ratio > self.level["long"]:
            self.n_long += 1
            self._record(self.level["partial_credit"])
            return f"long ({ratio:.2f}x)"
        return None

    def pending_key(self):
        return self._pending[0] if self._pending else None

    def on_release(self, key, now=None):
        """Returns a duration label if this release completed a graded note."""
        now = now or time.perf_counter()
        label = None
        if self.pending_key() == key:
            label = self.grade_pending(now)
        self._last_release = now
        return label

    # ---- reporting ----

    def graded_any(self):
        return bool(self.n_correct or self.n_wrong)

    def report_lines(self):
        if not self.graded_any():
            return []
        lines = [
            f"--- recent {self.score:.0f}/100  ({self.level_name}) ---",
            f"correct {self.n_correct} | wrong key {self.n_wrong} | "
            f"short {self.n_short} | long {self.n_long} | gaps {self.n_gap}",
            f"your tempo: {self.user_beat:.2f}s per beat",
        ]
        if self.run_start:
            elapsed = time.perf_counter() - self.run_start
            lines.append(f"elapsed {elapsed:.1f}s")
        return lines