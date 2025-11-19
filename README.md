# Pico W IR Helper & Beacon Trainer

Raspberry Pi Pico W project that turns the board into a **blue-team friendly HID tool**:

- **IR Helper** – incident response macro tool for repeatable host triage
- **Beacon Trainer** – ATT&CK-style recon / “beacon” simulator for DFIR labs

The device uses a small OLED display, a push button, and a SAFE/ARMED slide switch to
select apps and trigger payloads. All payloads are **non-destructive** and intended
for controlled lab environments.

---

## Hardware

- **Microcontroller:** Raspberry Pi Pico W  
- **Display:** SSD1306 128×64 OLED  
  - I²C: `SDA = GP4`, `SCL = GP5`
- **Input:**
  - Momentary push button on **GP14** → GND (pull-up in code)
  - SAFE/ARMED slide switch on **GP15** (3V3 ↔ GP15, ARMED = high)
- **Firmware:** CircuitPython 10.x

---

## Apps

### 1. IR Helper

Incident response macro tool. Profiles are defined in **`ir_profiles.json`** and each
profile is a small triage “playbook”.

**Features:**

- Profiles have: `name`, `description`, `os`, `commands[]`
- `os` controls how the terminal is opened:
  - `windows` → sends `Win + R` → `powershell` → ENTER
  - `linux`   → sends `Ctrl + Alt + T`
- Each command is typed via HID and followed by ENTER
- Runs are logged to **`ir_log.txt`** on the Pico (timestamp + profile name + OS)

Typical profile examples:

- `WIN_BASE_IR`: baseline (whoami, hostname, ipconfig, tasklist, etc.)
- `WIN_PERSIST`: services, startup items, scheduled tasks
- `LINUX_BASE_IR`: id, hostnamectl, ip a, ps aux

You can edit or add profiles by modifying `ir_profiles.json` on CIRCUITPY.

---

### 2. Beacon Trainer

ATT&CK-style recon trainer. Tasks are defined in **`bt_tasks.json`** and/or
served over Wi-Fi from a JSON endpoint. Each task simulates a (non-malicious)
“beacon” that an implant might execute in a lab.

**Task fields:**

- `name` – often an ATT&CK technique ID (e.g. `T1059.001`)
- `phase` – Execution, Discovery, etc.
- `description` – short human description
- `os` – currently `windows` (used to auto-open terminal)
- `lines[]` – list of commands to execute
- `marker` – unique string used for log/detection training

**Behavior:**

- On run (ARMED):
  1. Auto-opens a terminal (like IR Helper, based on `os`)
  2. Types each command in `lines[]`
  3. Types `echo BT_MARKER <marker>` so you can hunt for it in logs
  4. Appends a log entry to **`bt_log.txt`** with timestamp, task name, phase, source

**Task loading order:**

1. If Wi-Fi credentials and `BT_SERVER_URL` are set in `settings.toml`, it tries to
   fetch tasks from that HTTP URL (e.g. a JSON file served by your laptop).
2. If the server fetch fails, it falls back to local **`bt_tasks.json`** on CIRCUITPY.
3. If that also fails, it uses a small built-in default task set.

This lets you demo a **“C2 config over Wi-Fi”** story without any malicious code.

---

## Controls

### Launcher (main menu)

- **Short press (tap):** change selected app (IR Helper / Beacon Trainer)
- **Long press:** start the selected app
- OLED shows:
  - Current mode: `SAFE` / `ARMED`
  - Highlighted app with `>` cursor

### Inside an app (IR Helper or Beacon Trainer)

- **Short press (tap):** cycle to the next profile / task  
- **Hold while ARMED (~0.7s+):**  
  - Auto-open appropriate terminal  
  - Run the current profile / task as HID keystrokes  
- **Very long hold while SAFE (~2s+):** exit back to the launcher  
- Short/medium holds in SAFE will not send commands (SAFE = no HID execution)

This gives you a clear physical safety model:

- Switch to **SAFE** when moving between hosts or plugging in
- Flip to **ARMED** only when you’re ready to demonstrate a payload

---

## Configuration

### Files on `CIRCUITPY` (root)

- `code.py` – launcher and app wiring
- `ir_helper.py` – IR Helper implementation
- `beacon_trainer.py` – Beacon Trainer implementation
- `ir_profiles.json` – incident response profiles (editable)
- `bt_tasks.json` – beacon tasks (editable, also used as local fallback)
- `settings.toml` – **not in repo**; holds Wi-Fi + server settings (see below)
- `ir_log.txt`, `bt_log.txt` – generated at runtime (logs)

### `settings.toml` (example)

On the CIRCUITPY drive, create `settings.toml`:

```toml
CIRCUITPY_WIFI_SSID="YourSSID"
CIRCUITPY_WIFI_PASSWORD="YourWifiPassword"
BT_SERVER_URL="http://<your-laptop-ip>:8000/bt_tasks.json"
