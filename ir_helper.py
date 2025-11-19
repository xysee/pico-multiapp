# ir_helper.py  -- Incident Responder Helper v2 (robust button logic)
# - Loads profiles from ir_profiles.json (falls back to built-ins)
# - Auto-opens a terminal for each profile OS (Windows/Linux)
# - Logs each run to ir_log.txt
# - Button:
#     tap           -> next profile
#     hold (ARMED)  -> run profile
#     very long SAFE-> exit to menu

import time
import json
from adafruit_hid.keycode import Keycode

MIN_PRESS = 0.05      # ignore ultra-short bounces
RUN_HOLD = 0.7        # hold >= this (ARMED) -> run
EXIT_HOLD = 2.0       # hold >= this (SAFE)  -> exit


DEFAULT_PROFILES = [
    {
        "name": "WIN_BASE_IR",
        "description": "User, IP, processes",
        "os": "windows",
        "commands": [
            "echo === WINDOWS BASELINE IR ===",
            "whoami /all",
            "hostname",
            "ipconfig /all",
            "tasklist /v",
        ],
    },
    {
        "name": "WIN_PERSIST",
        "description": "services & startup",
        "os": "windows",
        "commands": [
            "echo === WINDOWS PERSISTENCE ENUM ===",
            "sc.exe query type= service state= all",
            "Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location",
    "schtasks.exe /query /fo LIST /v",
        ],
    },
    {
        "name": "LINUX_BASE_IR",
        "description": "id, ip, ps aux",
        "os": "linux",
        "commands": [
            "echo '=== LINUX BASELINE IR ==='",
            "id",
            "hostnamectl",
            "ip a",
            "ps aux",
        ],
    },
]


def _load_profiles():
    try:
        with open("ir_profiles.json", "r") as f:
            data = json.load(f)
        profiles = data.get("profiles", [])
        if not profiles:
            raise ValueError("empty profiles")
        return profiles
    except Exception:
        return DEFAULT_PROFILES


def _log_run(profile):
    try:
        t = time.localtime()
        ts = (
            f"{t.tm_year:04}-{t.tm_mon:02}-{t.tm_mday:02} "
            f"{t.tm_hour:02}:{t.tm_min:02}:{t.tm_sec:02}"
        )
        with open("ir_log.txt", "a") as log:
            log.write(
                f"{ts} | {profile.get('name','?')} | "
                f"{profile.get('os','?')}\n"
            )
    except OSError:
        pass


def run(oled, button_pin, armed_pin, keyboard, layout):
    profiles = _load_profiles()

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

    def open_terminal_for_profile(profile):
        os_name = profile.get("os", "windows").lower()

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
        prof = profiles[current_profile]

        oled.text("IR Helper", 0, 0, 1)
        oled.text("Mode: " + mode, 0, 12, 1)
        oled.text("Prof: " + prof.get("name", "?"), 0, 24, 1)

        desc = prof.get("description", "")
        if len(desc) > 21:
            desc = desc[:21]
        oled.text("Desc: " + desc, 0, 36, 1)

        os_name = prof.get("os", "?").upper()
        oled.text("OS: " + os_name, 0, 44, 1)

        if status:
            msg = status
        else:
            msg = "Tap=Next  Hold=Run"
        if len(msg) > 21:
            msg = msg[:21]
        oled.text(msg, 0, 54, 1)

        oled.show()

    def run_profile(idx):
        prof = profiles[idx]
        show_screen("Opening term...")
        open_terminal_for_profile(prof)
        show_screen("Running " + prof.get("name", "?"))

        for cmd in prof.get("commands", []):
            type_line(cmd)

        _log_run(prof)
        show_screen("Profile sent")
        time.sleep(1.5)

    current_profile = 0
    last_state = False
    press_start = 0.0
    run_triggered = False  # did we already run while this press was held?

    while True:
        now = time.monotonic()
        pressed = button_pressed()

        # When button first goes down
        if pressed and not last_state:
            press_start = now
            run_triggered = False

        # While button is held, check for "run" hold
        if pressed and not run_triggered:
            held = now - press_start
            if held >= RUN_HOLD and is_armed():
                run_profile(current_profile)
                run_triggered = True  # don't run again until next press

        # When button is released
        if not pressed and last_state:
            duration = now - press_start

            if duration >= MIN_PRESS:
                if run_triggered:
                    # Already ran while held – nothing else to do on release
                    pass
                else:
                    # No run yet; treat as tap or exit depending on duration & SAFE
                    if not is_armed() and duration >= EXIT_HOLD:
                        show_screen("Exiting to menu")
                        time.sleep(1.0)
                        return
                    else:
                        current_profile = (current_profile + 1) % len(profiles)
                        show_screen("Profile changed")
                        time.sleep(0.25)

        last_state = pressed
        show_screen()
        time.sleep(0.03)

