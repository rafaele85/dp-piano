"""Song data. Each module here defines one song; no loader code.

    SLOT     str, the number key that selects it
    NAME     str
    NOTES    list of (key, beats) or (key, beats, lyric)
    PROGRAM  int, GM program for the melody
    CHORDS   list of (chord_notes, start_beat)   -- optional
    ACCOMP   int, GM program for the backing     -- optional

Subfolders text/ and midi/ hold data files, not modules.
"""