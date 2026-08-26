WHITE = {"a": 60, "s": 62, "d": 64, "f": 65, "g": 67, "h": 69, "j": 71,
         "k": 72, "l": 74, ";": 76, "'": 77}
BLACK = {"w": 61, "e": 63, "t": 66, "y": 68, "u": 70, "o": 73, "p": 75}
NOTE_KEYS = {**WHITE, **BLACK}

NOTE_TO_KEY = {}
for _k, _n in list(WHITE.items()) + list(BLACK.items()):
    NOTE_TO_KEY.setdefault(_n, _k)

CHORDS = {
    "z": ("C",    [60, 64, 67]),
    "x": ("Dm",   [62, 65, 69]),
    "c": ("Em",   [64, 67, 71]),
    "v": ("F",    [65, 69, 72]),
    "b": ("G",    [67, 71, 74]),
    "n": ("Am",   [69, 72, 76]),
    "m": ("Bdim", [71, 74, 77]),
}

BAR = ["f1", "f2", "f3", "f4", "f5", "f6",
       "f7", "f8", "f9", "f10", "f11"]
HEALTH = "f12"

REST_WHITE = (120, 120, 120)
REST_BLACK = (25, 20, 90)
PAD = (200, 90, 0)
TARGET = (0, 255, 0)
NEXT = (0, 80, 255)
BAR_HOLD = (0, 255, 0)
BAR_ERROR = (255, 0, 0)


def idle_color(key):
    if key in WHITE:
        return REST_WHITE
    if key in BLACK:
        return REST_BLACK
    if key in CHORDS:
        return PAD
    return (0, 0, 0)


def health_color(score):
    """0 = red, 50 = amber, 100 = green."""
    s = max(0.0, min(100.0, score)) / 100.0
    if s < 0.5:
        t = s / 0.5
        return (255, int(160 * t), 0)
    t = (s - 0.5) / 0.5
    return (int(255 * (1 - t)), int(160 + 95 * t), 0) 