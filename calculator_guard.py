import ctypes
import time
from ctypes import wintypes


if not hasattr(ctypes, "windll"):
    raise SystemExit("calculator_guard.py requires Windows")


user32 = ctypes.WinDLL("user32", use_last_error=True)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.GetForegroundWindow.restype = wintypes.HWND
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL

WINDOW_TITLE = "calculator"
WM_CLOSE = 0x0010
SW_RESTORE = 9
POLL_INTERVAL_SECONDS = 1.0


def get_calculator_windows():
    windows = []

    def collect_window(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True

        title_length = user32.GetWindowTextLengthW(hwnd)
        if title_length == 0:
            return True

        title = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, title, len(title))
        if title.value.strip().casefold() == WINDOW_TITLE:
            windows.append(hwnd)
        return True

    if not user32.EnumWindows(WNDENUMPROC(collect_window), 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return windows


def focus_window(hwnd):
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)

    current_thread = kernel32.GetCurrentThreadId()
    foreground = user32.GetForegroundWindow()
    foreground_thread = user32.GetWindowThreadProcessId(foreground, None)
    attached = (
        foreground_thread != 0
        and foreground_thread != current_thread
        and user32.AttachThreadInput(current_thread, foreground_thread, True)
    )
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(current_thread, foreground_thread, False)


def monitor_calculator():
    previous_windows = set()

    while True:
        try:
            windows = get_calculator_windows()
            current_windows = set(windows)

            if not current_windows:
                previous_windows.clear()
            else:
                existing_windows = previous_windows & current_windows
                new_windows = current_windows - previous_windows

                if existing_windows and new_windows:
                    foreground = user32.GetForegroundWindow()
                    primary = (
                        foreground
                        if foreground in existing_windows
                        else next(hwnd for hwnd in windows if hwnd in existing_windows)
                    )

                    for hwnd in new_windows:
                        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

                    focus_window(primary)

                previous_windows = current_windows
        except Exception:
            # A transient window/API error should not stop the monitor.
            pass

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        monitor_calculator()
    except KeyboardInterrupt:
        pass