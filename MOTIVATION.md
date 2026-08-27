# Why this exists

It started as a question: can I turn individual keys on my keyboard on and off from code?

The Dark Project KD87a has per-key RGB. The vendor software can set colours, so something on the wire must carry that. But the KD87a isn't in OpenRGB's device list, and there's no public documentation for it.

## Finding the door

The first guess was wrong. A driver on GitHub identified the board as `0416:C345` — Winbond silicon — and OpenRGB has a controller contributed for the RedSquare Keyrox whose author noted it used "the same controller" as the KD87a. So: same chip, presumably same protocol. I tried the Keyrox frame format against feature reports and got nothing. Silence, no errors, no light.

The answer was in the device enumeration all along. Listing the KD87a's HID collections showed one with usage page `0xFF1B` and usage `0x91` — which is *exactly* what OpenRGB's `WinbondGamingKeyboardController` registers, just for a different product ID (`0416:B23C`, a Pulsar PCMK TKL). Same vendor, same vendor-defined collection, different PID.

That mattered for two reasons. It explained the failure — that driver uses HID **output** reports, not feature reports, so scanning feature reports was never going to find anything. And it meant the protocol was already written down; it just wasn't associated with this keyboard.

Sixty-four byte output reports, report ID `0x01`. Eight messages carry a full frame of RGB triplets. Channel values cap at `0xC1`, not `0xFF`. Ten milliseconds between writes or the firmware drops them.

The whole board lit up red on the first try.

## Where the difficulty actually was

Not in the protocol. Once the frame format was known, lighting a specific key was arithmetic.

The hard part was concurrency. Frames are absolute — every LED you don't set goes dark — so all state has to live in one buffer, and any code that writes to the hardware is fighting every other writer. The bugs that ate the most time were all variations on the same theme: a key stuck red after release, a target that never turned green, colours that were correct in memory and wrong on the board.

Three attempts before it was right. Locking the buffer wasn't enough, because two threads could snapshot correct frames and then write them out of order. Locking the whole flush wasn't enough either, because painting inside a Windows keyboard hook blocks the hook, and Windows silently drops hooks that take too long. The fix was structural rather than defensive: one render thread owns all output, key handlers only mutate state and return immediately.

That's the lesson worth keeping. The stale-colour bugs weren't solved by adding synchronization — they were solved by removing the second writer.

## What got built on top

Once keys could be lit, the rest followed almost by momentum. Chord pads, then individual notes, then a hard-coded melody, then wait-mode where playback pauses until you play the right key. Then scoring, then skill levels, then backing chords that follow your tempo instead of a metronome. Then loading songs from MIDI files, which meant guessing which track holds the melody and squeezing a two-octave tune into eighteen keys.

Some of those turned out to be genuinely interesting problems in their own right. Grading felt punitive until the score became a rolling window over recent notes rather than a running total — a cumulative counter can only ratchet down, and a player who's improving needs to see it. Tempo had to be inferred from the player rather than imposed, or every self-paced note reads as "too short."

## What it isn't

It's not a way to learn piano. Flat keys, no velocity sensing, and both hands within six inches of each other. It trains note reading, chord spelling, and interval geometry — real things, but not touch, dynamics, or hand span. A $40 MIDI controller would do the musical job better, and the lesson code here would drive it unchanged.

The keyboard piano was never really the point.

## The point

The protocol notes in the README are the part that might be useful to someone else. As far as I can tell, nothing public records that the KD87a speaks the Winbond gaming keyboard protocol at `0416:C345`. OpenRGB knows the protocol; it just doesn't know this board uses it. Adding the VID/PID to that detector would probably be a one-line change.

Everything above the HID layer is a toy. The two hundred lines below it are a small piece of documentation that didn't exist before.