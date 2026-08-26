import threading
import time

import hid

VID, PID = 0x0416, 0xC345
PATH = 0
LEN = 64
MAXV = 0xC1
COUNTS = [18] * 7 + [6]

POS = {
    "f1": (0, 2),  "f2": (0, 3),  "f3": (0, 4),  "f4": (0, 5),
    "f5": (0, 7),  "f6": (0, 8),  "f7": (0, 9),  "f8": (0, 10),
    "f9": (0, 11), "f10": (0, 12), "f11": (0, 13), "f12": (0, 14),
    "q": (2, 9),  "w": (2, 10), "e": (2, 11), "r": (2, 12), "t": (2, 13),
    "y": (2, 14), "u": (2, 15), "i": (2, 16), "o": (2, 17), "p": (3, 0),
    "a": (3, 14), "s": (3, 15), "d": (3, 16), "f": (3, 17),
    "g": (4, 0),  "h": (4, 1),  "j": (4, 2),  "k": (4, 3),  "l": (4, 4),
    ";": (4, 5),  "'": (4, 6),
    "z": (5, 0),  "x": (5, 1),  "c": (5, 2),  "v": (5, 3),  "b": (5, 4),
    "n": (5, 5),  "m": (5, 6),
}

BAR_MSGS = [0]
KEY_MSGS = [2, 3, 4, 5]


class Board:
    def __init__(self):
        info = hid.enumerate(VID, PID)[PATH]
        self.dev = hid.device()
        self.dev.open_path(info["path"])
        self.buf = [[(0, 0, 0)] * c for c in COUNTS]
        self.io = threading.Lock()
        self._custom_mode()

    def _custom_mode(self):
        mode = bytearray(LEN)
        mode[0], mode[1], mode[5] = 1, 7, 0x0E
        mode[6], mode[7], mode[8] = 10, 3, 0
        with self.io:
            self.dev.write(bytes(mode))
            time.sleep(0.01)

    def set(self, key, rgb):
        """Update the buffer only. Call write() to push."""
        if key not in POS:
            return
        msg, slot = POS[key]
        self.buf[msg][slot] = rgb

    def _frame(self, i):
        m = bytearray(LEN)
        m[0], m[1], m[4], m[5] = 1, 9, i, COUNTS[i] * 3
        for slot, (r, g, b) in enumerate(self.buf[i]):
            off = 6 + slot * 3
            m[off] = r * MAXV // 255
            m[off + 1] = g * MAXV // 255
            m[off + 2] = b * MAXV // 255
        return bytes(m)

    def write(self, msgs):
        """Unconditionally send the given messages."""
        frames = [self._frame(i) for i in msgs]
        with self.io:
            for f in frames:
                self.dev.write(f)
                time.sleep(0.01)

    def blank(self):
        self.buf = [[(0, 0, 0)] * c for c in COUNTS]
        self.write(range(8))

    def close(self):
        self.blank()
        with self.io:
            self.dev.close()