# YaesuFT-1000MP

Python CAT control library and interactive CLI for the Yaesu FT-1000MP HF transceiver.

## Features

- Frequency control for VFO-A and VFO-B (100 kHz – 30 MHz)
- Mode selection: LSB, USB, CW, AM, FM, RTTY, PKT
- VFO selection and A→B copy
- Split operation
- Clarifier on/off and offset control
- Memory channel store/recall (channels 1–99)
- PTT control
- Status queries (frequency, mode, clarifier, RIT/XIT, flags)
- Interactive CLI with all commands available

## Requirements

- Python 3.10+
- [pyserial](https://pypi.org/project/pyserial/) ≥ 3.5
- USB-to-serial adapter (FTDI, Prolific, etc.)

### Platform Notes

**Windows:** The adapter appears as a COM port (e.g. `COM3`). Check Device Manager → Ports (COM & LPT) for the port number, or use `--detect` (see CLI Usage below) to auto-detect it. The default port is `COM3` when no override is set.

**Linux:** The adapter typically shows up as `/dev/ttyUSB0`. The default port is `/dev/ttyUSB0` when no override is set. Your user must be in the `dialout` group (`sudo usermod -aG dialout $USER`).

**WSL2:** USB devices must be attached via [usbipd-win](https://github.com/dorssel/usbipd-win) before they appear in the Linux guest. The adapter typically shows up as `/dev/ttyUSB0`. Your user must be in the `dialout` group.

**Multiple cables / Digirig:** If you have more than one USB-to-serial adapter, set the `FT1000MP_PORT` environment variable to select the right one:

```bash
export FT1000MP_PORT=/dev/ttyUSB1   # Linux / WSL2
set FT1000MP_PORT=COM5              # Windows cmd
$env:FT1000MP_PORT = "COM5"         # Windows PowerShell
```

Use the `ports` command inside the CLI (or `python -c "from serial.tools.list_ports import comports; [print(p.device, p.description) for p in comports()]"`) to list available serial ports and identify them by chipset (e.g. "CP2102" vs "CH340").

**Digirig (CP210x):** The CP210x chip asserts RTS high by default, which gates the CAT TX line and prevents write commands from reaching the radio (reads still work). You must deassert RTS:

```bash
python cli.py --rts off                              # CLI flag
export FT1000MP_RTS=false                             # or env var
FT1000MP_RTS=false python3 -m pytest tests/ -v -m live  # tests
```

The `FT1000MP_RTS` and `FT1000MP_DTR` env vars accept `true`/`1` or `false`/`0`.

If using **Hamlib** (`rigctl`/`rigctld`, model 209) with a Digirig, the same fix applies:

```bash
rigctl -m 209 -r /dev/ttyUSB0 --set-conf="rts_state=OFF"
rigctld -m 209 -r /dev/ttyUSB0 --set-conf="rts_state=OFF" -t 4532
```

FTDI-based cables are unaffected — only CP210x (and similar chips that assert RTS high on open) need this override.

## Installation

```bash
pip install -e .            # library + CLI
pip install -e ".[test]"    # include pytest for running tests
```

## Quick Start

```python
from ft1000mp import FT1000MP

# port defaults to COM3 (Windows) or /dev/ttyUSB0 (Linux), or FT1000MP_PORT env var
with FT1000MP() as radio:
    radio.set_frequency_a(14_195_000)    # 14.195 MHz
    radio.set_mode("USB")

    status = radio.get_vfo_status()
    print(f"{status.frequency_hz / 1e6:.6f} MHz  {status.mode_name}")
    print(f"Clarifier: {status.clarifier_offset:+d} Hz")
    print(f"RIT: {status.rit}  XIT: {status.xit}")
```

## CLI Usage

```bash
python cli.py                     # use default port (COM3 or /dev/ttyUSB0)
python cli.py --detect            # auto-detect port by unplugging/replugging cable
python cli.py COM3                # Windows: explicit port
python cli.py /dev/ttyUSB0        # Linux: explicit port
python cli.py --rts off           # Digirig (CP210x) — must deassert RTS
python cli.py COM3 --rts off      # Windows + Digirig
python cli.py /dev/ttyUSB1 --rts off --dtr off
```

| Command | Description |
|---------|-------------|
| `status` | Read current VFO status (frequency, mode, clarifier) |
| `status ab` | Read both VFO-A and VFO-B |
| `flags` | Read radio status flags (split, clarifier, VFO, TX, priority) |
| `freq <MHz>` | Set VFO-A frequency (e.g. `freq 14.250`) |
| `freqb <MHz>` | Set VFO-B frequency |
| `mode <name>` | Set VFO-A mode (LSB USB CW AM FM RTTY PKT) |
| `modeb <name>` | Set VFO-B mode |
| `vfo a\|b` | Select VFO |
| `ab` | Copy VFO-A to VFO-B |
| `split on\|off` | Toggle split operation |
| `clar on\|off` | Toggle clarifier |
| `clar <offset>` | Set clarifier offset in Hz (e.g. `clar 600`, `clar -300`) |
| `ptt on\|off` | Transmitter control |
| `mem <1-99>` | Recall memory channel |
| `vfo2mem` | Store VFO to memory |
| `mem2vfo` | Recall memory to VFO |
| `ports` | List available serial ports |
| `help` | Show command help |
| `quit` | Exit |

## API Reference

### Frequency

| Method | Description |
|--------|-------------|
| `set_frequency_a(freq_hz)` | Set VFO-A frequency in Hz |
| `set_frequency_b(freq_hz)` | Set VFO-B frequency in Hz |

### Mode

| Method | Description |
|--------|-------------|
| `set_mode(name, vfo_b=False)` | Set operating mode by name (e.g. `"USB"`, `"CW"`) |

### VFO

| Method | Description |
|--------|-------------|
| `select_vfo(vfo)` | Select VFO `"A"` or `"B"` |
| `copy_vfo_a_to_b()` | Copy VFO-A settings to VFO-B |

### Split

| Method | Description |
|--------|-------------|
| `set_split(on)` | Enable/disable split operation |

### Clarifier

| Method | Description |
|--------|-------------|
| `set_clarifier(on)` | Enable/disable clarifier |
| `set_clarifier_offset(offset_hz)` | Set clarifier offset (signed, in Hz) |

### Memory

| Method | Description |
|--------|-------------|
| `recall_memory(channel)` | Recall memory channel (1–99) |
| `vfo_to_memory(channel)` | Store current VFO to memory channel |
| `memory_to_vfo(channel)` | Transfer memory channel to VFO |

### PTT

| Method | Description |
|--------|-------------|
| `set_ptt(on)` | Key/unkey transmitter |

### Status

| Method | Returns |
|--------|---------|
| `get_vfo_status()` | `VFOStatus` — frequency, mode, clarifier offset, RIT, XIT |
| `get_both_vfo_status()` | `(VFOStatus, VFOStatus)` — active VFO, then inactive VFO |
| `read_flags()` | `RadioFlags` — split, clarifier, VFO, TX, priority |

## Running Tests

Unit tests (no hardware required):

```bash
pytest tests/ -v -m "not live"
```

Live integration tests (requires an FT-1000MP connected via serial):

```bash
pytest tests/ -v -m live                                # default port
FT1000MP_PORT=/dev/ttyUSB1 pytest tests/ -v -m live     # Linux: different cable
set FT1000MP_PORT=COM5 && pytest tests/ -v -m live       # Windows cmd
$env:FT1000MP_PORT="COM5"; pytest tests/ -v -m live      # Windows PowerShell
```

Live tests save and restore radio state automatically. The radio must **not** be transmitting when tests start.

## Download

Pre-built Windows executables are available on the [Releases](https://github.com/JohnTarbox/YaesuFT-1000MP/releases) page. Download `ft1000mp.exe` and run it directly — no Python installation required.

## Building a Standalone Executable

You can build a single-file `ft1000mp.exe` (Windows) or `ft1000mp` (Linux) that runs without a Python installation.

```bash
pip install -e ".[build]"    # install PyInstaller
python build.py              # produces dist/ft1000mp or dist/ft1000mp.exe
```

The resulting executable is in the `dist/` directory:

```bash
dist\ft1000mp.exe --help               # Windows
dist\ft1000mp.exe COM3 --rts off       # Windows + Digirig
./dist/ft1000mp --help                  # Linux
./dist/ft1000mp /dev/ttyUSB0            # Linux
```

All CLI flags (`--detect`, `--rts`, `--dtr`) and environment variables (`FT1000MP_PORT`, `FT1000MP_RTS`, `FT1000MP_DTR`) work the same as when running from source.

## Technical Notes

- **Frequency encoding:** SET commands use little-endian packed BCD (`freq_hz / 10`). Status responses use big-endian binary with `*16/10` scaling — these are two different encodings.
- **Serial parameters:** 4800 baud, 8 data bits, no parity, 2 stop bits (8N2).
- **Command format:** Every CAT command is exactly 5 bytes: `[P1][P2][P3][P4][OpCode]`.
- **Memory channels:** 1–99 (1-indexed, per Hamlib convention).
- **VFO select:** Works despite Hamlib's `#if 0`. The 32-byte status response returns (active, inactive) order after switching — Hamlib misread this VFO swap as frequency corruption. The `read_flags().vfo_b_selected` flag is unreliable; verify VFO identity by frequency instead.
- **Authoritative reference:** [Hamlib](https://github.com/Hamlib/Hamlib) source — `rigs/yaesu/ft1000mp.h` and `ft1000mp.c`.
