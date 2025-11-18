# ir_helper.py  -- Option A: Incident Responder Helper

import time
from adafruit_hid.keycode import Keycode

MIN_PRESS = 0.08
LONG_PRESS = 0.55

PROFILES = [
    {
        "name": "WIN_BASE_IR",
        "description": "whoami, ipconfig, tasklist",
        "commands": [
            "echo === WINDOWS BASELINE IR ===",
            "whoami",
            "ipconfig /all",
            "tasklist /v",
        ],
    },
    {
        "name": "WIN_NET",
        "description": "netstat, arp, routes",
        "commands": [
            "echo === WINDOWS NETWORK SNAPSHOT ===",
            "netstat -ano",
            "arp -a",
            "route print",
        ],
    },
    {
        "name": "LINUX_BASE_IR",
        "description": "id, ip a, ps aux",
        "commands": [
            "echo '=== LINUX BASELINE IR ==='",
            "id",
            "ip a",
            "ps aux",
        ],
    },
]


def run(oled, button_pin, armed_pin, keyboard, layout):
    """Main loop for the IR helper app."""

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
        prof = PROFILES[current_profile]

        oled.text("IR Helper", 0, 0, 1)
        oled.text("Mode: " + mode, 0, 12, 1)
        oled.text("Prof: " + prof["name"], 0, 24, 1)

        desc = prof["description"]
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

    def run_profile(idx):
        prof = PROFILES[idx]
        show_screen("Running " + prof["name"])
        for cmd in prof["commands"]:
            type_line(cmd)
        show_screen("Profile sent")
        time.sleep(1.5)

    current_profile = 0
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
                current_profile = (current_profile + 1) % len(PROFILES)
                show_screen("Profile changed")
                time.sleep(0.3)
            else:
                if is_armed():
                    run_profile(current_profile)
                else:
                    show_screen("Exiting to menu")
                    time.sleep(1.0)
                    return

        last_state = pressed
        show_screen()
        time.sleep(0.03)
