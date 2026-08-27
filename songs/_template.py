"""Copy to songs/<name>.py and fill in.

Key map:
    white   a=C  s=D  d=E  f=F  g=G  h=A  j=B  k=C  l=D  ;=E  '=F
    black   w=C# e=D#      t=F# y=G# u=A#      o=C# p=D#

Beats are relative: 1 = quarter, 0.5 = eighth, 2 = half, 1.5 = dotted.
Chord start_beat is the cumulative beat where that chord takes over;
the track loops over one pass of NOTES, so the last chord holds to the end.
"""

from . import C, Am, Dm, Em, F, G   # noqa: F401

SLOT = "4"
NAME = "Untitled"
PROGRAM = 56      # 56 = trumpet, 65 = alto sax, 0 = piano, 11 = vibraphone
ACCOMP = 32       # 32 = acoustic bass, 48 = strings, 16 = organ

NOTES = [
    ("a", 1),
    ("s", 1),
    ("d", 2),
]

CHORDS = [
    (C, 0),
]