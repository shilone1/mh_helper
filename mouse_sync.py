import signal
import threading

from pynput import keyboard, mouse

import broadcast_mouse as bm


def _sigint_handler(sig, frame):
    bm.stop_event.set()


def main() -> None:
    signal.signal(signal.SIGINT, _sigint_handler)

    print("[START] mouse_sync (NORMAL + FAST mode)")
    for i in range(len(bm.window_capture_areas_)):
        print("  ", bm.area_str(i))
    print("[KEYS] SPACE toggle | F6 FAST_MODE | F7 test | ESC quit")

    worker_thread = threading.Thread(target=bm.worker_loop, daemon=True)
    worker_thread.start()

    mouse_listener = mouse.Listener(on_click=bm.on_click)
    keyboard_listener = keyboard.Listener(on_press=bm.on_key_press)

    mouse_listener.start()
    keyboard_listener.start()
    keyboard_listener.join()

    bm.stop_event.set()
    mouse_listener.stop()
    worker_thread.join(timeout=2.0)
    print("[END] exited")


if __name__ == "__main__":
    main()
