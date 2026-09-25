import math
import random
import threading
import ctypes
import winsound
from ctypes import wintypes
from pynput import keyboard

import psutil
import time
import tkinter as tk
from collections import deque
from queue import Queue
from PIL import Image, ImageTk



IMAGE_PATH = r"C:\Users\robin\Documents\Remap\evil_pulles.png"
SOUND_PATH = r"C:\Users\robin\Documents\Remap\PULLES_sound.wav"
IMAGE_HEIGHT = int(1080 * 0.7)

seen = set()
open_popups = deque()
root = tk.Tk()
root.withdraw()

popup_queue = Queue()
txt = ""


def process_popup_queue():
    while not popup_queue.empty():
        event = popup_queue.get()
        if event is True:
            show_popup()
    root.after(50, process_popup_queue)


def on_press(key):
    global txt
    try:
        txt += '{}'.format(key.char)
        print(txt)
        if len(txt) > 25:
            txt = txt[1:]

        lower_txt = txt.lower()
        match lower_txt:
            case _ if "sam" in lower_txt or "pulles" in lower_txt:
                popup_queue.put(True)
                print("PULLES IS WATCHING YOU!")
                txt = ""
            case _ if "jayden" in lower_txt:
                popup_queue.put(True)
                print("JAYDEN IS WATCHING YOU!")
                txt = ""
    except AttributeError:
        print('special key {} pressed'.format(
            key))

def on_release(key):
    if key == keyboard.Key.esc:
        # Stop listener
        return False

def play_loud_sound():
    winsound.PlaySound(
        SOUND_PATH,
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
    x = random.randint(
        work_left,
        max(work_left, work_right - popup_width),
    )
    y = random.randint(
        work_top,
        max(work_top, work_bottom - popup_height),
    )
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

root.after(50, process_popup_queue)
listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener.daemon = True
listener.start()
root.mainloop()

