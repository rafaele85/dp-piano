"""Keyboard piano trainer for the Dark Project KD87a.

SPACE  start lesson        1 / 3  pick song
2      stop                7/8/9  skill level
0      toggle backing      ESC    quit
"""

import atexit

import keyboard

from accompaniment import Accompaniment
from audio import Audio
from layout import CHORDS, NOTE_KEYS
from lesson import Lesson
from render import Renderer
from scoring import LEVELS
from songs import SONGS


def main():
    audio = Audio()
    lesson = Lesson(audio)
    renderer = Renderer(lesson)
    backing = Accompaniment(lesson, audio)

    def shutdown():
        lesson.shutdown()
        backing.stop()
        renderer.close()
        audio.close()

    atexit.register(shutdown)

    def on_note_press(key):
        audio.note_on(key)
        lesson.on_press(key)

    def on_note_release(key):
        audio.note_off(key)
        lesson.on_release(key)

    def on_pad_press(pad):
        played = audio.chord_on(pad)
        if played:
            name, notes = played
            print(name, notes)

    def toggle_backing():
        print(f"backing: {'on' if backing.toggle() else 'off'}")

    for key in NOTE_KEYS:
        keyboard.on_press_key(key, lambda e, k=key: on_note_press(k))
        keyboard.on_release_key(key, lambda e, k=key: on_note_release(k))

    for pad in CHORDS:
        keyboard.on_press_key(pad, lambda e, p=pad: on_pad_press(p))
        keyboard.on_release_key(pad, lambda e, p=pad: audio.chord_off(p))

    for slot in SONGS:
        keyboard.on_press_key(slot, lambda e, s=slot: lesson.select_song(s))

    for slot in LEVELS:
        keyboard.on_press_key(slot, lambda e, s=slot: lesson.set_level(s))

    keyboard.on_press_key("space", lambda e: lesson.start())
    keyboard.on_press_key("2", lambda e: lesson.stop())
    keyboard.on_press_key("0", lambda e: toggle_backing())

    renderer.start()
    backing.start()

    print("ASDFGHJKL;' white | WETYUOP black | ZXCVBNM chords")
    print("SPACE = start | 2 = stop | 1/3 = song | 7/8/9 = level | 0 = backing")
    print(f"level: {lesson.scorer.level_name}")

    try:
        keyboard.wait("esc")
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()
        shutdown()


if __name__ == "__main__":
    main()