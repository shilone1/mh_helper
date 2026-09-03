import time
import random
import ctypes
import threading
import queue
import traceback
from ctypes import wintypes

from pynput import mouse, keyboard

# =========================
# Window capture areas (screen coords): (x, y, w, h)
# =========================
window_capture_areas_ = [
    (0, 0, 638, 505),        # 0
    (638, 0, 638, 505),      # 1
    (1280, 0, 638, 505),     # 2
    (1274, 517, 638, 505),   # 3
    (632, 517, 638, 505),    # 4
]

# =========================
# Normal mode tunables
# =========================
base_delay_s = 0.018
delay_jitter_s = 0.006
gauss_sigma_px = 5.0
restore_cursor = True

START_BROADCAST_DELAY_S = 0.02

# smooth move (fast but still smooth)
click_pause_before_s = (0.0, 0.006)
click_pause_after_s  = (0.0, 0.004)

error_probability = 0.15
error_range_px = (-10, 10)
miss_click_probability = 0.10

# =========================
# FAST mode tunables (near-same-time)
# =========================
FAST_MODE = False

FAST_base_delay_s = 0.0
FAST_delay_jitter_s = 0.0
FAST_gauss_sigma_px = 0.0
FAST_restore_cursor = True
FAST_START_BROADCAST_DELAY_S = 0.0

FAST_click_pause_before_s = (0.0, 0.0)
FAST_click_pause_after_s  = (0.0, 0.0)

FAST_error_probability = 0.0
FAST_miss_click_probability = 0.0
FAST_use_smooth_move = False   # IMPORTANT: teleport for max speed

# =========================
# KEYBINDS
# =========================
TOGGLE_KEY = keyboard.Key.space
QUIT_KEY   = keyboard.Key.esc
TEST_KEY   = keyboard.Key.f7
FAST_KEY   = keyboard.Key.f6

# =========================
# Win32 API
# =========================
user32 = ctypes.windll.user32

INPUT_MOUSE = 0
MOUSEEVENTF_LEFTDOWN  = 0x0002
MOUSEEVENTF_LEFTUP    = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP   = 0x0010

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("mi", MOUSEINPUT)]

def _send_input(flags: int):
    inp = INPUT(
        type=INPUT_MOUSE,
        mi=MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=flags, time=0, dwExtraInfo=None),
    )
    sent = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    if sent != 1:
        raise ctypes.WinError()

def click_left():
    _send_input(MOUSEEVENTF_LEFTDOWN)
    _send_input(MOUSEEVENTF_LEFTUP)

def click_right():
    _send_input(MOUSEEVENTF_RIGHTDOWN)
    _send_input(MOUSEEVENTF_RIGHTUP)

def set_cursor_pos(x: int, y: int):
    x, y = int(x), int(y)
    if user32.SetCursorPos(x, y):
        return True

    # SetCursorPos can fail transiently without setting a useful Win32 error.
    # Retry once and let the next movement step continue if it still fails.
    time.sleep(0)
    return bool(user32.SetCursorPos(x, y))

def get_cursor_pos():
    pt = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(pt)):
        raise ctypes.WinError()
    return pt.x, pt.y

def screen_w():
    return user32.GetSystemMetrics(0)

def screen_h():
    return user32.GetSystemMetrics(1)

# =========================
# Geometry
# =========================
def point_in_area(area, x, y):
    ax, ay, aw, ah = area
    return (ax <= x < ax + aw) and (ay <= y < ay + ah)

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def find_master_index(x, y):
    for i, area in enumerate(window_capture_areas_):
        if point_in_area(area, x, y):
            return i
    return None

def area_str(i):
    x, y, w, h = window_capture_areas_[i]
    return f"idx={i} (x={x},y={y},w={w},h={h})"

# =========================
# Human-ish behavior helpers
# =========================
stop_event = threading.Event()

def add_human_error(x, y, p, rng):
    if p > 0 and random.random() < p:
        x += random.randint(*rng)
        y += random.randint(*rng)
    return x, y

def move_cursor_smoothly(target_x, target_y):
    """Fast smooth; used in NORMAL mode."""
    if stop_event.is_set():
        return

    start_x, start_y = get_cursor_pos()

    duration = random.uniform(0.006, 0.020)
    dt = 0.001
    steps = max(1, int(duration / dt))
    steps = min(steps, 22)

    dx = (target_x - start_x) / steps
    dy = (target_y - start_y) / steps

    for i in range(steps):
        if stop_event.is_set():
            return
        cx = start_x + dx * (i + 1) + random.gauss(0, 0.2)
        cy = start_y + dy * (i + 1) + random.gauss(0, 0.2)
        set_cursor_pos(int(cx), int(cy))
        time.sleep(dt)

# =========================
# Core engine
# =========================
enabled = True
evt_q = queue.Queue(maxsize=50)

injecting = threading.Event()
inject_lock = threading.Lock()

def _get_mode_params():
    """Return the active params depending on FAST_MODE."""
    if FAST_MODE:
        return dict(
            base_delay_s=FAST_base_delay_s,
            delay_jitter_s=FAST_delay_jitter_s,
            gauss_sigma_px=FAST_gauss_sigma_px,
            restore_cursor=FAST_restore_cursor,
            start_delay_s=FAST_START_BROADCAST_DELAY_S,
            click_before=FAST_click_pause_before_s,
            click_after=FAST_click_pause_after_s,
            err_p=FAST_error_probability,
            err_rng=error_range_px,
            miss_click_p=FAST_miss_click_probability,
            use_smooth=FAST_use_smooth_move,
        )
    else:
        return dict(
            base_delay_s=base_delay_s,
            delay_jitter_s=delay_jitter_s,
            gauss_sigma_px=gauss_sigma_px,
            restore_cursor=restore_cursor,
            start_delay_s=START_BROADCAST_DELAY_S,
            click_before=click_pause_before_s,
            click_after=click_pause_after_s,
            err_p=error_probability,
            err_rng=error_range_px,
            miss_click_p=miss_click_probability,
            use_smooth=True,
        )

def _inject_at_screen(sx, sy, kind: str, params, bounds=None):
    with inject_lock:
        injecting.set()
        try:
            if params["use_smooth"]:
                move_cursor_smoothly(sx, sy)
                if params["click_before"][1] > 0:
                    time.sleep(random.uniform(*params["click_before"]))
            else:
                # FAST teleport
                set_cursor_pos(sx, sy)

            tx, ty = add_human_error(sx, sy, params["err_p"], params["err_rng"])
            if bounds is None:
                x_min, y_min, x_max, y_max = 0, 0, screen_w() - 1, screen_h() - 1
            else:
                ax, ay, aw, ah = bounds
                x_min, y_min, x_max, y_max = ax, ay, ax + aw - 1, ay + ah - 1
            tx = clamp(tx, x_min, x_max)
            ty = clamp(ty, y_min, y_max)
            set_cursor_pos(int(tx), int(ty))

            if kind == "left":
                click_left()
            elif kind == "right":
                click_right()
            else:
                raise ValueError(f"Unknown click kind: {kind}")

            if params["use_smooth"] and params["click_after"][1] > 0:
                time.sleep(random.uniform(*params["click_after"]))

        finally:
            injecting.clear()

def broadcast_click(sx, sy, kind: str):
    params = _get_mode_params()

    master_idx = find_master_index(sx, sy)
    if master_idx is None:
        return

    ox, oy = get_cursor_pos()

    mx0, my0, _, _ = window_capture_areas_[master_idx]
    rel_x = sx - mx0
    rel_y = sy - my0

    try:
        child_number = 0
        for i, area in enumerate(window_capture_areas_):
            if i == master_idx:
                continue
            if stop_event.is_set():
                break

            if random.random() < params["miss_click_p"]:
                continue

            ax, ay, aw, ah = area
            tx = ax + rel_x
            ty = ay + rel_y

            if params["gauss_sigma_px"] > 0:
                tx += random.gauss(0.0, params["gauss_sigma_px"])
                ty += random.gauss(0.0, params["gauss_sigma_px"])

            tx = clamp(tx, ax, ax + aw - 1)
            ty = clamp(ty, ay, ay + ah - 1)

            delay = child_number * params["base_delay_s"]
            child_number += 1
            if params["delay_jitter_s"] > 0:
                delay = max(0.0, delay + random.uniform(
                    -params["delay_jitter_s"], params["delay_jitter_s"]
                ))

            if delay > 0 and stop_event.wait(delay):
                break

            _inject_at_screen(int(tx), int(ty), kind, params, bounds=area)
    finally:
        if params["restore_cursor"] and not stop_event.is_set():
            if params["use_smooth"]:
                move_cursor_smoothly(ox, oy)
            else:
                set_cursor_pos(ox, oy)

def click_master_and_children(sx, sy, kind: str):
    """Inject one click in the source window, then copy it to every child."""
    master_idx = find_master_index(sx, sy)
    if master_idx is None:
        raise ValueError(f"Click position ({sx}, {sy}) is outside all configured windows")

    params = _get_mode_params()
    _inject_at_screen(
        sx,
        sy,
        kind,
        params,
        bounds=window_capture_areas_[master_idx],
    )
    broadcast_click(sx, sy, kind)

def worker_loop():
    while not stop_event.is_set():
        try:
            try:
                kind, sx, sy = evt_q.get(timeout=0.1)
            except queue.Empty:
                continue

            if enabled and not stop_event.is_set():
                params = _get_mode_params()
                if params["start_delay_s"] > 0 and stop_event.wait(params["start_delay_s"]):
                    break
                broadcast_click(sx, sy, kind)

        except Exception:
            traceback.print_exc()

# =========================
# Listeners
# =========================
def on_click(x, y, button, pressed):
    if stop_event.is_set():
        return

    sx, sy = int(x), int(y)
    if injecting.is_set():
        return

    if not enabled:
        return

    if find_master_index(sx, sy) is None:
        return

    if pressed:
        return

    # release
    try:
        if button == mouse.Button.left:
            evt_q.put_nowait(("left", sx, sy))

        elif button == mouse.Button.right:
            evt_q.put_nowait(("right", sx, sy))

    except queue.Full:
        pass

def on_key_press(key):
    global enabled, FAST_MODE
    if stop_event.is_set():
        return False
    try:
        if key == TOGGLE_KEY:
            enabled = not enabled
            print(f"[TOGGLE] enabled={enabled}")

        elif key == FAST_KEY:
            FAST_MODE = not FAST_MODE
            print(f"[MODE] FAST_MODE={FAST_MODE}")

        elif key == TEST_KEY:
            ax, ay, aw, ah = window_capture_areas_[0]
            cx = ax + aw // 2
            cy = ay + ah // 2
            try:
                evt_q.put_nowait(("left", cx, cy))
                print(f"[TEST] enqueue left at win0 center ({cx},{cy})")
            except queue.Full:
                pass

        elif key == QUIT_KEY:
            stop_event.set()
            return False
    except Exception:
        traceback.print_exc()

