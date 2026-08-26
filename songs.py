BEAT = 0.55
REPEATS = 2
DEMO_BEAT = 0.5

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

TWINKLE = [
    ("a", 1, "Twin"), ("a", 1, "kle"), ("g", 1, "twin"), ("g", 1, "kle"),
    ("h", 1, "lit"), ("h", 1, "tle"), ("g", 2, "star"),
    ("f", 1, "how"), ("f", 1, "I"), ("d", 1, "won"), ("d", 1, "der"),
    ("s", 1, "what"), ("s", 1, "you"), ("a", 2, "are"),
]

# (name, notes, GM program)
SONGS = {
    "1": ("Himno de la Alegría", ODE_TO_JOY, 48),   # string ensemble
    "3": ("Twinkle Twinkle", TWINKLE, 10),          # music box
}