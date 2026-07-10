from pynput import mouse, keyboard
import threading
import pyperclip  # For clipboard operations

# Install pyperclip if not already installed
# pip install pyperclip

# Global variables
show_coordinates = False
last_mouse_position = (0, 0)
stop_flag = threading.Event()  # To signal listeners to stop

# Function to handle mouse movement
def on_move(x, y):
    global last_mouse_position, show_coordinates
    last_mouse_position = (x, y)
    if show_coordinates:
        print(f"Mouse moved to: ({x}, {y})", end="\r")  # Overwrite line to avoid clutter

# Function to handle keyboard events
def on_press(key):
    global show_coordinates, last_mouse_position

    # Exit if the stop flag is set
    if stop_flag.is_set():
        return False

    # Toggle showing coordinates when `Ctrl` is pressed
    if key == keyboard.Key.ctrl_l:  # Left Ctrl
        show_coordinates = True

    # Copy the current mouse position to clipboard when `Ctrl + S` is pressed
    if hasattr(key, 'char') and key.char == 's':
        pyperclip.copy(f"{last_mouse_position}")
        print(f"\nCopied to clipboard: {last_mouse_position}")

def on_release(key):
    global show_coordinates

    # Stop showing coordinates when `Ctrl` is released
    if key == keyboard.Key.ctrl_l:  # Left Ctrl
        show_coordinates = False

    # Exit the program with `Esc`
    if key == keyboard.Key.esc:
        stop_flag.set()
        return False  # Stop listener

# Start listeners
def start_listeners():
    try:
        with mouse.Listener(on_move=on_move) as mouse_listener, keyboard.Listener(on_press=on_press, on_release=on_release) as keyboard_listener:
            mouse_listener.join()
            keyboard_listener.join()
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting...")
        stop_flag.set()

# Run the program
if __name__ == "__main__":
    print("Press 'Ctrl' to show coordinates, 'Ctrl+S' to copy, and 'Esc' to exit.")
    print("Press 'Ctrl+C' in the terminal to kill the program.")
    start_listeners()
