# code.py  -- Pico launcher for two apps

import time
import board
import busio
import digitalio
import usb_hid
import adafruit_ssd1306

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS

import ir_helper
import beacon_trainer

# ---------- Shared hardware setup ----------

# I2C + OLED
i2c = busio.I2C(board.GP5, board.GP4)  # SCL, SDA
OLED_WIDTH = 128
OLED_HEIGHT = 64
oled = adafruit_ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)

# SAFE/ARMED slide switch on GP15 (3V3 <-> GP15)
armed_pin = digitalio.DigitalInOut(board.GP15)
armed_pin.direction = digitalio.Direction.INPUT
armed_pin.pull = digitalio.Pull.DOWN  # True when ARMED

# Button on GP14 -> GND, pull-up
button_pin = digitalio.DigitalInOut(board.GP14)
button_pin.direction = digitalio.Direction.INPUT
button_pin.pull = digitalio.Pull.UP  # not pressed=True, pressed=False

# HID keyboard
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)

# Timing thresholds (seconds)
MIN_PRESS = 0.08     # ignore ultra-short glitches
LONG_PRESS = 0.55    # >= long → long press, between min & long → short


def is_armed():
    return armed_pin.value


def button_pressed():
    # convert to True when physically pressed
    return not button_pin.value


def launcher_menu():
    """Simple menu that lets you pick which app to run."""
    apps = ["IR Helper", "Beacon Trainer"]
    selected = 0

    last_state = False
    press_start = 0.0

    while True:
        now = time.monotonic()
        pressed = button_pressed()

        # Edge: just pressed
        if pressed and not last_state:
            press_start = now

        # Edge: just released
        if not pressed and last_state:
            duration = now - press_start

            if duration < MIN_PRESS:
                # ignore tiny bounces
                pass
            elif duration < LONG_PRESS:
                # Short press: cycle app
                selected = (selected + 1) % len(apps)
            else:
                # Long press: start selected app
                return selected

        last_state = pressed

        # Draw menu screen
        oled.fill(0)
        oled.text("Pico Multi-App", 0, 0, 1)
        oled.text("Mode: " + ("ARMED" if is_armed() else "SAFE"), 0, 12, 1)

        for i, name in enumerate(apps):
            prefix = ">" if i == selected else " "
            oled.text(prefix + name, 0, 28 + 10 * i, 1)

        oled.text("Short: select", 0, 50, 1)
        oled.text("Long: start", 0, 58, 1)

        oled.show()
        time.sleep(0.03)  # slightly faster for smoother feel


while True:
    choice = launcher_menu()

    if choice == 0:
        ir_helper.run(oled, button_pin, armed_pin, keyboard, layout)
    else:
        beacon_trainer.run(oled, button_pin, armed_pin, keyboard, layout)

    # When the chosen app returns, show launcher again
