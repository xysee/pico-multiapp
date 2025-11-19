# beacon_trainer.py  -- Beacon Trainer v2 (robust button logic + auto-open)
# - Connects to Wi-Fi once at startup (if configured)
# - Loads tasks from BT_SERVER_URL, then bt_tasks.json, then defaults
# - Auto-opens terminal based on task["os"]
# - Button:
#     tap           -> next task
#     hold (ARMED)  -> run task
#     very long SAFE-> exit to menu

import time
import json
import os

import wifi
import adafruit_connection_manager
import adafruit_requests
from adafruit_hid.keycode import Keycode

MIN_PRESS = 0.05
RUN_HOLD = 0.7
EXIT_HOLD = 2.0

DEFAULT_TASKS = [
    {
        "name": "T1059.001",
        "phase": "Execution",
        "description": "PS recon demo",
        "os": "windows",
        "marker": "BT_PS_RECON",
        "lines": [
            "whoami",
            "Get-NetTCPConnection"
        ],
    }
]


def _log_run(task, source):
    try:
        t = time.localtime()
        ts = (
            f"{t.tm_year:04}-{t.tm_mon:02}-{t.tm_mday:02} "
            f"{t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02}"
        )
        with open("bt_log.txt", "a") as log:
            log.write(
                f"{ts} | {task.get('name','?')} | "
                f"{task.get('phase','?')} | {source}\n"
            )
    except OSError:
        pass


def _load_tasks_from_local_file():
    with open("bt_tasks.json", "r") as f:
        data = json.load(f)
    tasks = data.get("tasks", [])
    if not tasks:
        raise ValueError("bt_tasks.json has no 'tasks'")
    return tasks


def _load_tasks_from_server_simple(session, url):
    r = session.get(url)
    try:
        if r.status_code != 200:
            raise RuntimeError("HTTP status " + str(r.status_code))
        data = r.json()
        tasks = data.get("tasks", [])
        if not tasks:
            raise ValueError("server JSON has no 'tasks'")
        return tasks
    finally:
        try:
            r.close()
        except Exception:
            pass


def _ensure_wifi_once(oled):
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    pw = os.getenv("CIRCUITPY_WIFI_PASSWORD")

    if not ssid or not pw:
        print("Wi-Fi credentials not set; skipping server load.")
        return

    try:
        if wifi.radio.ipv4_address is None:
            oled.fill(0)
            oled.text("Beacon Trainer", 0, 0, 1)
            oled.text("Connecting Wi-Fi", 0, 12, 1)
            oled.show()
            wifi.radio.connect(ssid, pw)
            oled.text("Wi-Fi OK", 0, 24, 1)
            oled.show()
            time.sleep(0.7)
        else:
            print("Wi-Fi already connected:", wifi.radio.ipv4_address)
    except Exception as e:
        print("Wi-Fi connect failed:", repr(e))


def _load_tasks(oled):
    ssid = os.getenv("CIRCUITPY_WIFI_SSID")
    pw = os.getenv("CIRCUITPY_WIFI_PASSWORD")
    url = os.getenv("BT_SERVER_URL")

    session = None
    if ssid and pw and url:
        pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
        ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
        session = adafruit_requests.Session(pool, ssl_context)

    # Try server first
    if session and url:
        oled.fill(0)
        oled.text("Beacon Trainer", 0, 0, 1)
        oled.text("Loading tasks...", 0, 12, 1)
        oled.text("Trying server...", 0, 24, 1)
        oled.show()

        try:
            tasks = _load_tasks_from_server_simple(session, url)
            oled.text("OK: server", 0, 36, 1)
            oled.show()
            time.sleep(1.0)
            return tasks, "server"
        except Exception as e:
            print("Server load failed:", repr(e))

    # Then local file
    oled.fill(0)
    oled.text("Beacon Trainer", 0, 0, 1)
    oled.text("Loading tasks...", 0, 12, 1)
    oled.text("Trying local...", 0, 24, 1)
    oled.show()

    try:
        tasks = _load_tasks_from_local_file()
        oled.text("OK: local", 0, 36, 1)
        oled.show()
        time.sleep(1.0)
        return tasks, "local"
    except Exception as e:
        print("Local file load failed:", repr(e))

    # Fallback to defaults
    oled.fill(0)
    oled.text("Beacon Trainer", 0, 0, 1)
    oled.text("Using defaults", 0, 12, 1)
    oled.show()
    time.sleep(1.0)
    return DEFAULT_TASKS, "built-in"


def run(oled, button_pin, armed_pin, keyboard, layout):
    _ensure_wifi_once(oled)
    tasks, source = _load_tasks(oled)

    def is_armed():
        return armed_pin.value

    def button_pressed():
        return not button_pin.value

    def clear():
        oled.fill(0)

    def type_line(line: str):
        layout.write(line)
        keyboard.send(Keycode.ENTER)
        time.sleep(0.06)

    def open_terminal_for_task(task):
        os_name = task.get("os", "windows").lower()
        if os_name == "windows":
            keyboard.send(Keycode.GUI, Keycode.R)
            time.sleep(0.7)
            layout.write("powershell")
            keyboard.send(Keycode.ENTER)
            time.sleep(1.5)
        elif os_name == "linux":
            keyboard.send(Keycode.CONTROL, Keycode.ALT, Keycode.T)
            time.sleep(1.5)

    def show_screen(status=None):
        clear()
        mode = "ARMED" if is_armed() else "SAFE"
        task = tasks[current_task]

        oled.text("Beacon Trainer", 0, 0, 1)
        oled.text("Mode: " + mode, 0, 12, 1)
        oled.text("Task: " + task.get("name", "?"), 0, 24, 1)

        phase = task.get("phase", "?")
        desc = task.get("description", "")
        if len(desc) > 18:
            desc = desc[:18]
        oled.text("Phase: " + phase, 0, 36, 1)
        oled.text("Desc: " + desc, 0, 46, 1)

        if status:
            msg = status
        else:
            msg = "Tap=Next  Hold=Run"
        if len(msg) > 21:
            msg = msg[:21]
        oled.text(msg, 0, 56, 1)

        oled.show()

    def run_task(idx):
        task = tasks[idx]
        show_screen("Opening term...")
        open_terminal_for_task(task)
        show_screen("Running " + task.get("name", "?"))

        for line in task.get("lines", []):
            type_line(line)

        marker = task.get("marker")
        if marker:
            type_line(f"echo BT_MARKER {marker}")

        _log_run(task, source)

        m = marker if marker else "BT_MARKER"
        show_screen("Marker: " + m)
        time.sleep(2.0)

    current_task = 0
    last_state = False
    press_start = 0.0
    run_triggered = False

    while True:
        now = time.monotonic()
        pressed = button_pressed()

        # Button just pressed
        if pressed and not last_state:
            press_start = now
            run_triggered = False

        # While held, check for run
        if pressed and not run_triggered:
            held = now - press_start
            if held >= RUN_HOLD and is_armed():
                run_task(current_task)
                run_triggered = True

        # Button just released
        if not pressed and last_state:
            duration = now - press_start

            if duration >= MIN_PRESS:
                if run_triggered:
                    # Already ran while held
                    pass
                else:
                    # No run yet: tap or exit
                    if not is_armed() and duration >= EXIT_HOLD:
                        show_screen("Exiting to menu")
                        time.sleep(1.0)
                        return
                    else:
                        current_task = (current_task + 1) % len(tasks)
                        show_screen("Task changed")
                        time.sleep(0.25)

        last_state = pressed
        show_screen()
        time.sleep(0.03)

