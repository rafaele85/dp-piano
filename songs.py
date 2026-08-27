BEAT = 0.55
REPEATS = 2
DEMO_BEAT = 0.5

# ---- chord voicings, an octave below middle C ----
C = [48, 52, 55]
F = [41, 45, 48]
G = [43, 47, 50]
Am = [45, 48, 52]
Em = [40, 43, 47]
Dm = [38, 41, 45]

# Himno de la Alegría (Miguel Ríos, 1970) — AABA
# "Es-cu" is elided onto the first note, so it lands as "'cucha hermano"
# a=C s=D d=E f=F g=G
ODE_TO_JOY = [
    # A1
    ("d", 1, "Escu"), ("d", 1, "cha"), ("f", 1, "her"), ("g", 1, "ma"),
    ("g", 1, "no"), ("f", 1, "la"), ("d", 1, "can"), ("s", 1, "ción"),
    ("a", 1, "de"), ("a", 1, "la"), ("s", 1, "a"), ("d", 1, "le"),
    ("d", 1.5, "grí"), ("s", 0.5, "i"), ("s", 2, "a"),
    # A2
    ("d", 1, "el"), ("d", 1, "can"), ("f", 1, "to"), ("g", 1, "a"),
    ("g", 1, "le"), ("f", 1, "gre"), ("d", 1, "del"), ("s", 1, "que"),
    ("a", 1, "es"), ("a", 1, "pe"), ("s", 1, "ra un"), ("d", 1, "nue"),
    ("s", 1.5, "vo"), ("a", 0.5, "dí"), ("a", 2, "a"),
    # B
    ("s", 1, "ven"), ("s", 1, "can"), ("d", 1, "ta"), ("a", 1, "sue"),
    ("s", 1, "ña"), ("d", 0.5, "can"), ("f", 0.5, "tan"), ("d", 1, "do"),
    ("a", 1, "vi"),
    ("s", 1, "ve"), ("d", 0.5, "so"), ("f", 0.5, "ñan"), ("d", 1, "do"),
    ("s", 1, "el"),
    ("a", 1, "nue"), ("s", 1, "vo"), ("g", 2, "sol"),
    # A2 again
    ("d", 1, "en"), ("d", 1, "que"), ("f", 1, "los"), ("g", 1, "hom"),
    ("g", 1, "bres"), ("f", 1, "vol"), ("d", 1, "ve"), ("s", 1, "rán"),
    ("a", 1, "a"), ("a", 1, "ser"), ("s", 1, "her"), ("d", 1, "ma"),
    ("s", 1.5, "nos"), ("a", 0.5, ""), ("a", 2, ""),
]

# One chord per two beats, aligned to the melody above.
ODE_CHORDS = [
    # A1 (beats 0-15)
    (C, 0), (C, 2), (G, 4), (C, 6),
    (F, 8), (C, 10), (G, 12), (C, 14),
    # A2 (16-31)
    (C, 16), (C, 18), (G, 20), (C, 22),
    (F, 24), (C, 26), (G, 28), (C, 30),
    # B (32-49)
    (Am, 32), (C, 34), (Dm, 36), (G, 38),
    (C, 40), (Am, 42), (Dm, 44), (G, 46),
    (C, 48),
    # A2 again (50-65)
    (C, 50), (C, 52), (G, 54), (C, 56),
    (F, 58), (C, 60), (G, 62), (C, 64),
]

TWINKLE = [
    ("a", 1, "Twin"), ("a", 1, "kle"), ("g", 1, "twin"), ("g", 1, "kle"),
    ("h", 1, "lit"), ("h", 1, "tle"), ("g", 2, "star"),
    ("f", 1, "how"), ("f", 1, "I"), ("d", 1, "won"), ("d", 1, "der"),
    ("s", 1, "what"), ("s", 1, "you"), ("a", 2, "are"),
]

TWINKLE_CHORDS = [
    (C, 0), (F, 2), (C, 4), (G, 6),
    (C, 8), (G, 10), (C, 12), (G, 14),
]

# name, melody, melody program, chord track, accompaniment program
SONGS = {
    "1": ("Himno de la Alegría", ODE_TO_JOY, 48, ODE_CHORDS, 52),
    "3": ("Twinkle Twinkle", TWINKLE, 10, TWINKLE_CHORDS, 89),
}