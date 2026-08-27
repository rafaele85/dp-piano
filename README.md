# KD87a Piano Trainer

Turns a Dark Project KD87a keyboard into a piano trainer. Per-key RGB lighting shows which key to play next; the program waits until you play it, grades your accuracy, and plays backing chords that follow your tempo.

## Hardware protocol

The KD87a's lighting is undocumented. What follows was reverse-engineered against this board; OpenRGB's `WinbondGamingKeyboardController` implements the same protocol for a different PID (`0416:B23C`, Pulsar PCMK TKL), and this repo may be the only public record that the KD87a speaks it too.

| Property | Value |
|---|---|
| VID:PID | `0416:C345` |
| Interface | MI\_02, usage page `0xFF1B`, usage `0x91` |
| Transport | HID **output** reports (`hid_write`), not feature reports |
| Report length | 64 bytes, report ID `0x01` |
| Channel ceiling | `0xC1` (193), not `0xFF` |

### Set custom (per-key) mode

```
byte 0: 0x01   report ID
byte 1: 0x07   command: set key LED mode
byte 5: 0x0E
byte 6: 0x0A   mode 10 = custom
byte 7: brightness (0-3)
byte 8: speed
```

### Set LED colours

Eight messages carry the full frame. RGB triplets start at offset 6.

```
byte 0: 0x01   report ID
byte 1: 0x09   command: set LED data
byte 4: message index, 0-7
byte 5: data length: 0x36 for messages 0-6, 0x12 for message 7
byte 6+: RGB triplets (18 per message, 6 in message 7)
```

Frames are **absolute** — every LED not set in a message goes dark. Allow ~10 ms between writes; the firmware drops writes sent faster.

### Key positions

Addressed as `(message, slot)`:

```
msg 0:  0=Esc, 2-5=F1-F4, 7-14=F5-F12, 15=PrtSc, 16=ScrLk, 17=Pause
msg 1:  4=Backtick, 5-14=1-0, 15=Minus, 16=Equals
msg 2:  0=Backspace, 1-3=Ins/Home/PgUp, 8=Tab, 9-17=Q..O
msg 3:  0=P, 1=[, 2=], 12=CapsLock, 14-17=A,S,D,F
msg 4:  0-6=G,H,J,K,L,Semicolon,Quote  8=Enter, 16=LShift
msg 5:  0-9=Z,X,C,V,B,N,M,Comma,Period,Slash  12=RShift, 14=Up
msg 6:  2=LCtrl, 3=Win, 4=Alt, 8=Space, 15=RCtrl, 17=Left
```

Slots beyond a message's declared length are silently ignored — no error.

## Piano layout

```
    W  E     T  Y  U     O  P          black keys
  A  S  D  F  G  H  J  K  L  ;  '      white keys
  C  D  E  F  G  A  B  C  D  E  F      notes (middle C = A)

  Z  X  C  V  B  N  M                  chord pads: C Dm Em F G Bdim
```

`R` and `I` are unmapped — that's where a piano has no black key.

## Controls

| Key | Action |
|---|---|
| `Space` | Start lesson (demo, then practice) |
| `2` | Stop and report |
| `1` / `3` | Select song |
| `7` / `8` / `9` | Novice / normal / strict |
| `0` | Toggle backing chords |
| `Esc` | Quit |

## Colours

Green is the note to play now, blue the one after, dim white and dark blue are the resting piano. F1–F11 show remaining hold time (all red = wrong key). F12 is a health light, red through amber to green, tracking accuracy over the last 16 notes.

## Modules

```
board.py           HID transport, 132-slot colour buffer
layout.py          key -> (message, slot), key -> MIDI note, colours
songs.py           melodies, lyrics, chord tracks, instruments
scoring.py         rolling-window grading, tempo estimation
lesson.py          demo + practice state machine
audio.py           FluidSynth with pygame.midi fallback
accompaniment.py   backing chords that follow the player
render.py          single writer thread, LED output
piano.py           wiring
```

Only `render.py` writes to the LEDs. Key hooks mutate state and return immediately — Windows drops low-level hooks that block, and a full repaint takes ~40 ms.

## Setup

```
pip install -r requirements.txt
python piano.py
```

Optional: drop a General MIDI SoundFont (`.sf2`) next to `piano.py` for much better sound, or set `SOUNDFONT` to its path. Falls back to the Windows synth automatically.

`keyboard` needs elevated privileges for global hooks on Windows — run your terminal or IDE as administrator.

## Scoring

The score is a rolling window over the last 16 notes, not a lifetime total, so a bad patch fades rather than sticking. Novice grades key accuracy only; normal and strict add note duration and gaps between notes, judged against your own tempo rather than a fixed metronome.

## Limitations

Flat keys with no velocity sensing. This trains note reading, chord spelling, and interval geometry — not touch, dynamics, or hand span. A used 49-key MIDI controller works with the same lesson code if you want the physical side.