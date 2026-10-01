import ctypes
import random
import threading
import winsound
import tkinter as tk
from collections import deque
from ctypes import wintypes
from pathlib import Path
from queue import Queue

from PIL import Image, ImageTk
from pynput import keyboard


ASSET_DIR = Path(__file__).resolve().parent
IMAGE_PATH = ASSET_DIR / "evil_pulles.png"
SOUND_PATH = ASSET_DIR / "PULLES_sound.wav"
IMAGE_HEIGHT = int(1080 * 0.7)
COPILOT_VK_CODES = {0xC4, 0xB7}

open_popups = deque()
popup_queue = Queue()
root = tk.Tk()
root.withdraw()
listener_ref = []
copilot_key_down = False


def play_loud_sound():
    winsound.PlaySound(
        str(SOUND_PATH),
        winsound.SND_FILENAME | winsound.SND_ASYNC,
    )


def get_work_area():
    work_area = wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(
        0x0030,
        0,
        ctypes.byref(work_area),
        0,
    )
    return work_area.left, work_area.top, work_area.right, work_area.bottom


def show_popup():
    while open_popups and len(open_popups) >= 5:
        oldest_popup = open_popups.popleft()
        if oldest_popup.winfo_exists():
            oldest_popup.destroy()

    popup = tk.Toplevel(root)
    open_popups.append(popup)
    popup.title("PULLES IS WATCHING YOU!")
    threading.Thread(target=play_loud_sound, daemon=True).start()
    popup.resizable(False, False)

    with Image.open(IMAGE_PATH) as source_image:
        resized_image = source_image.resize(
            (IMAGE_HEIGHT, IMAGE_HEIGHT),
            Image.Resampling.LANCZOS,
        )
    image = ImageTk.PhotoImage(resized_image)
    image_label = tk.Label(popup, image=image)
    image_label.image = image
    image_label.pack()

    text_label = tk.Label(
        popup,
        text="PULLES IS WATCHING YOU!",
        font=("Aptos Display", 24, "bold"),
    )
    text_label.pack(pady=(12, 12))

    popup.update_idletasks()
    popup_width = image.width()
    popup_height = popup.winfo_reqheight()
    work_left, work_top, work_right, work_bottom = get_work_area()
    x = random.randint(work_left, max(work_left, work_right - popup_width))
    y = random.randint(work_top, max(work_top, work_bottom - popup_height))
    popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")

    closing = False

    def close_popup():
        nonlocal closing
        if closing:
            return
        closing = True

        if popup in open_popups:
            open_popups.remove(popup)
        if popup.winfo_exists():
            popup.destroy()

    popup.protocol("WM_DELETE_WINDOW", close_popup)
    popup.after(2000, close_popup)


def process_popup_queue():
    while not popup_queue.empty():
        popup_queue.get()
        show_popup()
    root.after(50, process_popup_queue)


def filter_copilot_key(message, event):
    global copilot_key_down

    if event.vkCode not in COPILOT_VK_CODES:
        return

    if message in (0x0100, 0x0104):  # WM_KEYDOWN / WM_SYSKEYDOWN
        if not copilot_key_down:
            copilot_key_down = True
            popup_queue.put(True)
        listener_ref[0].suppress_event()
    elif message in (0x0101, 0x0105):  # WM_KEYUP / WM_SYSKEYUP
        copilot_key_down = False
        listener_ref[0].suppress_event()


root.after(50, process_popup_queue)
listener = keyboard.Listener(win32_event_filter=filter_copilot_key)
listener_ref.append(listener)
listener.daemon = True
listener.start()
root.mainloop()
