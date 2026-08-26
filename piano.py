import atexit
import threading
import time
from collections import deque

import keyboard
import pygame.midi

from board import COUNTS, Board
from layout import (BAR, BAR_ERROR, BAR_HOLD, BLACK, CHORDS, HEALTH, NEXT,
                    NOTE_KEYS, TARGET, WHITE, health_color, idle_color)
from songs import BEAT, DEMO_BEAT, REPEATS, SONGS

FLASH_COLOR = (255, 255, 255)
FLASH_ON, FLASH_OFF, FLASH_TIMES = 0.12, 0.10, 3
WINDOW = 16

LEVELS = {
    "7": dict(name="novice", grade_duration=False, grade_gap=False,
              short=0.0, long=99.0, gap=None, dur_credit=0.0),
    "8": dict(name="normal", grade_duration=True, grade_gap=True,
              short=0.45, long=2.20, gap=1.4, dur_credit=0.5),
    "9": dict(name="strict", grade_duration=True, grade_gap=True,
              short=0.70, long=1.40, gap=0.7, dur_credit=0.3),
}
level = LEVELS["7"]
current_slot = "1"

pygame.midi.init()
out = pygame.midi.Output(pygame.midi.get_default_output_id())
out.set_instrument(0)

board = Board()

held_pads = {}
held_notes = set()

song = []
lesson_on = False
step = 0
hold_until = hold_span = 0.0
error_until = 0.0

graded_key = None
graded_press = 0.0
graded_beats = 0.0
last_release = 0.0
last_onset = 0.0
last_beats = 0.0
user_beat = BEAT

recent = deque(maxlen=WINDOW)
n_wrong = n_short = n_long = n_gap = n_clean = 0
run_start = 0.0

demo_on = False
demo_key = demo_next = None
demo_token = 0
flash_on = False
running = True


def note_of(e):
    return e[0]


def beats_of(e):
    return e[1]


def lyric_of(e):
    return e[2] if len(e) > 2 else ""


def score_now():
    if not recent:
        return 100.0
    return 100.0 * sum(recent) / len(recent)


def record(value):
    recent.append(value)


def desired():
    now = time.perf_counter()
    m = {}
    for k in list(WHITE) + list(BLACK) + list(CHORDS):
        m[k] = idle_color(k)

    if flash_on:
        for k in list(WHITE) + list(BLACK) + list(CHORDS) + BAR + [HEALTH]:
            m[k] = FLASH_COLOR
        return m

    if demo_on:
        if demo_next and demo_next != demo_key:
            m[demo_next] = NEXT
        if demo_key:
            m[demo_key] = TARGET
    elif lesson_on and step < len(song):
        cur = note_of(song[step])
        m[cur] = TARGET
        if step + 1 < len(song):
            nxt = note_of(song[step + 1])
            if nxt != cur:
                m[nxt] = NEXT

    if now < error_until:
        bar_n, bar_c = len(BAR), BAR_ERROR
    elif lesson_on and hold_until > now:
        frac = (hold_until - now) / hold_span if hold_span else 0
        bar_n, bar_c = int(round(frac * len(BAR))), BAR_HOLD
    else:
        bar_n, bar_c = 0, (0, 0, 0)
    for i, k in enumerate(BAR):
        m[k] = bar_c if i < bar_n else (0, 0, 0)

    m[HEALTH] = health_color(score_now()) if (lesson_on or demo_on) else (0, 0, 0)
    return m


def renderer():
    last = [[None] * c for c in COUNTS]
    while running:
        for k, rgb in desired().items():
            board.set(k, rgb)
        changed = []
        for msg in range(8):
            if board.buf[msg] != last[msg]:
                changed.append(msg)
                last[msg] = list(board.buf[msg])
        if changed:
            board.write(changed)
        time.sleep(0.02)


def set_level(slot):
    global level
    if slot in LEVELS:
        level = LEVELS[slot]
        print(f"level: {level['name']}")


def select_song(slot):
    global current_slot
    if slot in SONGS:
        current_slot = slot
        print(f"selected: {SONGS[slot][0]}  (space to start)")


def do_flash(token):
    global flash_on
    for _ in range(FLASH_TIMES):
        if token != demo_token:
            break
        flash_on = True
        time.sleep(FLASH_ON)
        flash_on = False
        time.sleep(FLASH_OFF)
    flash_on = False


def demo_run(token, tune):
    global demo_on, demo_key, demo_next, lesson_on, run_start
    for i, e in enumerate(tune):
        if token != demo_token:
            break
        demo_key = note_of(e)
        demo_next = note_of(tune[i + 1]) if i + 1 < len(tune) else None
        syl = lyric_of(e)
        if syl:
            print(syl, end=" ", flush=True)
        n = NOTE_KEYS[demo_key]
        out.note_on(n, 100)
        time.sleep(beats_of(e) * DEMO_BEAT * 0.9)
        out.note_off(n, 0)
        time.sleep(beats_of(e) * DEMO_BEAT * 0.1)
    demo_key = demo_next = None
    print()
    if token == demo_token:
        do_flash(token)
    if token == demo_token:
        demo_on = False
        lesson_on = True
        run_start = 0.0
        print(f"Your turn — {len(song)} notes. Level: {level['name']}")


def lesson_start():
    global lesson_on, step, hold_until, song, demo_on, demo_token
    global n_wrong, n_short, n_long, n_gap, n_clean
    global graded_key, user_beat, last_onset, last_release, run_start
    name, base = SONGS[current_slot]
    song = list(base) * REPEATS
    step = 0
    hold_until = 0.0
    graded_key = None
    user_beat = BEAT
    last_onset = last_release = run_start = 0.0
    recent.clear()
    n_wrong = n_short = n_long = n_gap = n_clean = 0
    lesson_on = False
    demo_token += 1
    demo_on = True
    print(f"\n{name} — demo, then {REPEATS} rounds ({len(song)} notes).")
    threading.Thread(target=demo_run, args=(demo_token, list(base)),
                     daemon=True).start()


def report():
    if not (n_clean + n_wrong + n_short + n_long):
        return
    elapsed = time.perf_counter() - run_start if run_start else 0
    print(f"\n--- recent {score_now():.0f}/100  ({level['name']}) ---")
    print(f"correct {n_clean} | wrong key {n_wrong} | "
          f"short {n_short} | long {n_long} | gaps {n_gap}")
    print(f"your tempo: {user_beat:.2f}s per beat")
    if elapsed:
        print(f"elapsed {elapsed:.1f}s")


def lesson_stop():
    global lesson_on, hold_until, demo_on, demo_token, demo_key, demo_next
    global flash_on, graded_key
    demo_token += 1
    demo_on = False
    demo_key = demo_next = None
    flash_on = False
    if lesson_on:
        report()
    lesson_on = False
    hold_until = 0.0
    graded_key = None
    print("Stopped.")


def grade_pending(now):
    global graded_key, n_short, n_long
    if graded_key is None:
        return
    if not level["grade_duration"]:
        graded_key = None
        return
    expected = graded_beats * user_beat
    if expected <= 0:
        graded_key = None
        return
    ratio = (now - graded_press) / expected
    if ratio < level["short"]:
        n_short += 1
        record(level["dur_credit"])
        print(f"  - short ({ratio:.2f}x)")
    elif ratio > level["long"]:
        n_long += 1
        record(level["dur_credit"])
        print(f"  - long ({ratio:.2f}x)")
    graded_key = None


def lesson_input(key):
    global step, lesson_on, hold_until, hold_span, error_until
    global graded_key, graded_press, graded_beats
    global n_wrong, n_gap, n_clean, run_start, user_beat, last_onset, last_beats
    if not lesson_on or step >= len(song):
        return
    now = time.perf_counter()

    if key != note_of(song[step]):
        error_until = now + 0.3
        n_wrong += 1
        record(0.0)
        print(f"  x wrong: {key}, want {note_of(song[step])}")
        return

    grade_pending(now)
    n_clean += 1
    record(1.0)

    if level["grade_gap"] and last_release:
        gap = now - last_release
        if gap > level["gap"] * user_beat:
            n_gap += 1
            record(level["dur_credit"])
            print(f"  - gap ({gap:.2f}s)")

    if last_onset and last_beats:
        interval = (now - last_onset) / last_beats
        if 0.12 < interval < 2.5:
            user_beat = 0.75 * user_beat + 0.25 * interval

    if not run_start:
        run_start = now

    entry = song[step]
    hold_span = beats_of(entry) * user_beat
    hold_until = now + hold_span
    graded_key, graded_press, graded_beats = key, now, beats_of(entry)
    last_onset, last_beats = now, beats_of(entry)

    syl = lyric_of(entry)
    step += 1
    print(f"{step}/{len(song)}  {syl}   [{score_now():.0f}]")
    if step >= len(song):
        grade_pending(now)
        lesson_on = False
        hold_until = 0.0
        print("Done.")
        report()


def pad_press(pad):
    if pad in held_pads:
        return
    name, notes = CHORDS[pad]
    print(name, notes)
    for n in notes:
        out.note_on(n, 100)
    held_pads[pad] = notes


def pad_release(pad):
    notes = held_pads.pop(pad, None)
    if notes is None:
        return
    for n in notes:
        out.note_off(n, 0)


def note_press(key):
    if key in held_notes:
        return
    held_notes.add(key)
    out.note_on(NOTE_KEYS[key], 100)
    if not demo_on:
        lesson_input(key)


def note_release(key):
    global last_release
    if key not in held_notes:
        return
    held_notes.discard(key)
    out.note_off(NOTE_KEYS[key], 0)
    if demo_on or not lesson_on:
        return
    now = time.perf_counter()
    if key == graded_key:
        grade_pending(now)
    last_release = now


def cleanup():
    global running, demo_token
    running = False
    demo_token += 1
    time.sleep(0.1)
    for pad in list(held_pads):
        pad_release(pad)
    for key in list(held_notes):
        note_release(key)
    try:
        board.close()
    except Exception:
        pass
    try:
        out.close()
        pygame.midi.quit()
    except Exception:
        pass


atexit.register(cleanup)

threading.Thread(target=renderer, daemon=True).start()

for _pad in CHORDS:
    keyboard.on_press_key(_pad, lambda e, p=_pad: pad_press(p))
    keyboard.on_release_key(_pad, lambda e, p=_pad: pad_release(p))

for _key in NOTE_KEYS:
    keyboard.on_press_key(_key, lambda e, k=_key: note_press(k))
    keyboard.on_release_key(_key, lambda e, k=_key: note_release(k))

for _slot in SONGS:
    keyboard.on_press_key(_slot, lambda e, s=_slot: select_song(s))
for _lv in LEVELS:
    keyboard.on_press_key(_lv, lambda e, s=_lv: set_level(s))

keyboard.on_press_key("space", lambda e: lesson_start())
keyboard.on_press_key("2", lambda e: lesson_stop())

print("ASDFGHJKL;' white | WETYUOP black | ZXCVBNM chords")
print("SPACE = start | 2 = stop | 1/3 = pick song | 7/8/9 = level")
try:
    keyboard.wait("esc")
except KeyboardInterrupt:
    pass
finally:
    keyboard.unhook_all()
    cleanup()