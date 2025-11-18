# beacon_trainer.py  -- Option D: Beacon Trainer / pseudo-C2

import time
from adafruit_hid.keycode import Keycode

MIN_PRESS = 0.08
LONG_PRESS = 0.55

TASKS = [
    {
        "name": "T1059.001",
        "description": "PS recon demo",
        "lines": [
            "echo === PowerShell Recon Demo ===",
            "whoami",
            "Get-NetTCPConnection",
        ],
    },
    {
        "name": "T1082",
        "description": "Sysinfo demo",
        "lines": [
            "echo === System Info Demo ===",
            "systeminfo",
        ],
    },
    {
        "name": "T1016",
        "description": "Network config",
        "lines": [
            "echo === Network Config Demo ===",
            "ipconfig /all",
        ],
    },
]


def run(oled, button_pin, armed_pin, keyboard, layout):
    """Main loop for the Beacon Trainer app."""

    def is_armed():
        return armed_pin.value

    def button_pressed():
        return not button_pin.value

    def clear():
        oled.fill(0)

    def type_line(line: str):
        layout.write(line)
        keyboard.send(Keycode.ENTER)
        time.sleep(0.05)

    def show_screen(status=None):
        clear()
        mode = "ARMED" if is_armed() else "SAFE"
        task = TASKS[current_task]

        oled.text("Beacon Trainer", 0, 0, 1)
        oled.text("Mode: " + mode, 0, 12, 1)
        oled.text("Task: " + task["name"], 0, 24, 1)

        desc = task["description"]
        if len(desc) > 21:
            desc = desc[:21]
        oled.text("Desc: " + desc, 0, 36, 1)

        if status:
            msg = status
        else:
            msg = "Short=Next  Long=Run"
        if len(msg) > 21:
            msg = msg[:21]
        oled.text(msg, 0, 50, 1)

        oled.show()

    def run_task(idx):
        task = TASKS[idx]
        show_screen("Running " + task["name"])
        for line in task["lines"]:
            type_line(line)
        show_screen("Task sent")
        time.sleep(1.5)

    current_task = 0
    last_state = False
    press_start = 0.0

    while True:
        now = time.monotonic()
        pressed = button_pressed()

        if pressed and not last_state:
            press_start = now

        if not pressed and last_state:
            duration = now - press_start

            if duration < MIN_PRESS:
                pass
            elif duration < LONG_PRESS:
                current_task = (current_task + 1) % len(TASKS)
                show_screen("Task changed")
                time.sleep(0.3)
            else:
                if is_armed():
                    run_task(current_task)
                else:
                    show_screen("Exiting to menu")
                    time.sleep(1.0)
                    return

        last_state = pressed
        show_screen()
        time.sleep(0.03)
