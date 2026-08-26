"""Renders lesson state to the keyboard LEDs. Single writer thread."""

import threading
import time

from board import COUNTS, Board
from layout import (BAR, BAR_ERROR, BAR_HOLD, BLACK, CHORDS, HEALTH, NEXT,
                    TARGET, WHITE, health_color, idle_color)

FLASH_COLOR = (255, 255, 255)
TICK = 0.02

ALL_KEYS = list(WHITE) + list(BLACK) + list(CHORDS)


class Renderer:
    def __init__(self, lesson):
        self.lesson = lesson
        self.board = Board()
        self._running = False
        self._thread = None

    # ---- frame composition ----

    def _desired(self):
        now = time.perf_counter()
        colors = {k: idle_color(k) for k in ALL_KEYS}

        if self.lesson.flashing:
            for k in ALL_KEYS + BAR + [HEALTH]:
                colors[k] = FLASH_COLOR
            return colors

        nxt = self.lesson.next_key()
        if nxt:
            colors[nxt] = NEXT
        target = self.lesson.target_key()
        if target:
            colors[target] = TARGET

        if self.lesson.in_error(now):
            bar_lit, bar_color = len(BAR), BAR_ERROR
        else:
            frac = self.lesson.bar_fraction(now)
            bar_lit, bar_color = int(round(frac * len(BAR))), BAR_HOLD
        for i, k in enumerate(BAR):
            colors[k] = bar_color if i < bar_lit else (0, 0, 0)

        colors[HEALTH] = (health_color(self.lesson.score)
                          if self.lesson.active else (0, 0, 0))
        return colors

    # ---- thread ----

    def _loop(self):
        last = [[None] * c for c in COUNTS]
        while self._running:
            for key, rgb in self._desired().items():
                self.board.set(key, rgb)
            changed = []
            for msg in range(8):
                if self.board.buf[msg] != last[msg]:
                    changed.append(msg)
                    last[msg] = list(self.board.buf[msg])
            if changed:
                self.board.write(changed)
            time.sleep(TICK)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)

    def close(self):
        self.stop()
        try:
            self.board.close()
        except Exception:
            pass