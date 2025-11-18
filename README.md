# pico-multiapp
Raspberry Pi Pico W with incident response and attack-style recon demos; includes a small OLED display and switches to trigger payloads/change between safe and armed.

## Hardware

- Raspberry Pi Pico W
- SSD1306 128x64 OLED (I²C: SDA=GP4, SCL=GP5)
- Momentary push button on GP14 (to GND, pull-up in code)
- SAFE/ARMED slide switch on GP15 (3V3 <-> GP15)
- CircuitPython 10.x

## Apps

### 1. IR Helper

Incident response macro tool. When ARMED, long-pressing the button sends a
bundle of triage commands (whoami, ipconfig, tasklist, etc.) to the focused
terminal. Designed for DFIR labs and repeatable host triage.

### 2. Beacon Trainer

ATT&CK-style recon trainer. Each task corresponds to a technique (e.g.
T1059.001) and runs non-destructive commands to demonstrate how an implant
might behave in a controlled lab environment.

### Controls

- On launcher:
  - Short press: change selected app.
  - Long press: start selected app.
- Inside an app:
  - Short press: change profile/task.
  - Long press while **ARMED**: run current macro as HID.
  - Long press while **SAFE**: exit back to launcher.

## Safety

These scripts are intended **only for lab environments** and are not for malicious uses.
