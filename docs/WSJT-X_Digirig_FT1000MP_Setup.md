# Digital Modes Setup Guide: Yaesu FT-1000MP with Digirig Mobile

Complete guide for configuring WSJT-X, Fldigi, JS8Call, Winlink (VARA HF),
VarAC, GridTracker, JTAlert, flrig, and Hamlib rigctld for digital modes on
the Yaesu FT-1000MP using a Digirig Mobile interface connected to the rear
panel PACKET connector.

---

## Table of Contents

1. [Overview](#overview)
2. [Hardware Connections](#hardware-connections)
3. [Driver Installation](#driver-installation)
4. [Radio Menu Configuration](#radio-menu-configuration)
5. [WSJT-X Radio Settings](#wsjt-x-radio-settings)
6. [WSJT-X Audio Settings](#wsjt-x-audio-settings)
7. [Fldigi Rig Control Settings](#fldigi-rig-control-settings)
8. [Fldigi Audio Settings](#fldigi-audio-settings)
9. [JS8Call Radio Settings](#js8call-radio-settings)
10. [JS8Call Audio Settings](#js8call-audio-settings)
11. [Winlink Overview](#winlink-overview)
12. [Winlink Express + VARA HF Setup (Windows)](#winlink-express--vara-hf-setup-windows)
13. [Pat Winlink Setup (Linux)](#pat-winlink-setup-linux)
14. [VarAC Setup](#varac-setup)
15. [flrig Rig Control Middleware](#flrig-rig-control-middleware)
16. [Hamlib rigctld Rig Control Daemon](#hamlib-rigctld-rig-control-daemon)
17. [GridTracker Setup](#gridtracker-setup)
18. [JTAlert Setup](#jtalert-setup)
19. [Audio Level Calibration](#audio-level-calibration)
20. [Testing the Setup](#testing-the-setup)
21. [Operating Tips](#operating-tips)
22. [Backing Up Radio Settings (Clone Mode)](#backing-up-radio-settings-clone-mode)
23. [Troubleshooting](#troubleshooting)

---

## Overview

The Digirig Mobile provides both CAT control (via CP210x USB-to-serial) and audio
I/O (via CM108 USB sound card) through a single USB-C cable to your computer.
Two cables run from the Digirig to the FT-1000MP rear panel:

- **DIN-5 cable** to the PACKET jack (audio + PTT)
- **DB-9 cable** to the CAT port (serial control)

> **Important:** The rear PACKET connector is only active when the radio is in
> **PKT** or **PKT USER** mode. Standard USB/LSB modes do not route audio
> through this connector.

---

## Hardware Connections

### Rear Panel Cabling

```
 Digirig Mobile                    FT-1000MP Rear Panel
 +--------------+                  +--------------------+
 | 3.5mm TRRS   |----DIN-5------->| PACKET jack        |
 | (audio/PTT)  |                  | (5-pin DIN)        |
 |              |                  |                    |
 | 3.5mm TRS    |----DB-9-------->| CAT port           |
 | (serial/CAT) |                  | (D-sub 9)          |
 |              |                  |                    |
 | USB-C        |----to computer   |                    |
 +--------------+                  +--------------------+
```

### PACKET Jack Pinout (DIN-5)

| Pin | Signal    | Digirig TRRS Mapping | Description                      |
|-----|-----------|----------------------|----------------------------------|
| 1   | DATA IN   | Ring 1 (RIG_AFIN)    | Audio from computer to radio     |
| 2   | GND       | Sleeve (GND)         | Ground                           |
| 3   | PTT       | Ring 2 (PTT)         | Push-to-talk (active low)        |
| 4   | DATA OUT  | Tip (RIG_AFOUT)      | Audio from radio to computer     |
| 5   | BUSY      | Not connected        | Squelch signal (unused)          |

### Notes

- The DATA OUT level is fixed at approximately 100 mV into 600 ohms, set
  internally by trimmer VR3010 on the AF board. The front panel AF volume knob
  does **not** affect this output.
- The DB-9 CAT cable uses a straight-through RS-232 pinout.

---

## Driver Installation

### Windows

1. Connect the Digirig to your computer via USB-C.
2. Open **Device Manager**.
3. Under **Ports (COM & LPT)**, look for
   **Silicon Labs CP210x USB to UART Bridge (COMx)** -- note the COM port number.
4. Under **Sound, video and game controllers**, look for
   **USB Audio Device** or **USB PnP Sound Device**.
5. If the CP210x shows an exclamation mark, download and install the driver from
   [Silicon Labs CP210x VCP Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers).

**Tip:** In Windows Sound Settings, rename the Digirig playback and recording
devices to "Digirig" so they are easy to identify in WSJT-X.

### Linux

The CP210x and CM108 drivers are built into the Linux kernel. The serial port
will appear as `/dev/ttyUSB0` (or similar) and the audio device will be listed
by `aplay -l` and `arecord -l`.

Your user must be in the `dialout` group:
```bash
sudo usermod -aG dialout $USER
# Log out and back in for the change to take effect
```

### WSL2 (Windows Subsystem for Linux)

USB devices must be attached to WSL2 using `usbipd`:
```powershell
# In Windows PowerShell (Admin):
usbipd list                           # Find the Digirig bus ID (e.g. 1-3)
usbipd bind --busid 1-3               # Bind the device (first time only)
usbipd attach --wsl --busid 1-3       # Attach to WSL2
```
The serial port will appear as `/dev/ttyUSB0` in WSL2.

---

## Radio Menu Configuration

Access the menu system by holding **FAST** while pressing **ENTER**.
Use the main tuning dial to navigate between menu groups, and the **SUB** dial
to change values. Press **ENTER** to save.

### Menu 8-6: PKT USER Mode (Critical)

This configures the USER sub-mode within PKT mode. The settings below make the
radio operate in USB internally while showing PKT/LSB on the display. This is
necessary because the FT-1000MP only routes rear PACKET connector audio in PKT
mode.

#### Complete Parameter Reference

| # | Parameter      | Display    | Valid Range              |
|---|----------------|------------|--------------------------|
| 1 | Mode           | nodE       | LSB, USB, CW, RTTY, PKT |
| 2 | Display Offset | dSP-oFSt   | ±5.000 kHz               |
| 3 | RX PLL         | r-PLL      | ±5.000 kHz               |
| 4 | RX Carrier     | r-cAr      | 450.000–460.000 kHz      |
| 5 | TX PLL         | t-PLL      | ±5.000 kHz               |
| 6 | TX Carrier     | t-cAr      | 450.000–460.000 kHz      |
| 7 | RTTY Shift     | rttY-SFt   | ±5.000 kHz               |
| 8 | Easy Set       | EASY-SEt   | oFF, SStu-L, SStu-u, FAcS-L, FAcS-u |

#### Standard Values (most FT-1000MP and all Mark V units)

| Parameter      | Display    | Value     | Notes                       |
|----------------|------------|-----------|-----------------------------|
| Mode           | nodE       | PAc-Lo    | Packet Low mode             |
| Display Offset | dSP-oFSt   | 0.000     |                             |
| RX PLL         | r-PLL      | 1.750     |                             |
| RX Carrier     | r-cAr      | 453.250   |                             |
| TX PLL         | t-PLL      | 1.750     |                             |
| TX Carrier     | t-cAr      | 453.250   |                             |
| RTTY Shift     | rttY-SFt   | 0.000     |                             |
| Easy Set       | EASY-SEt   | oFF       | Must be OFF for manual vals |

These values match those loaded by the **SStu-u** (SSTV Upper/USB) Easy Set
preset. The PLL offset of 1.750 and carrier of 453.250 transform the PAc-Lo
(LSB-based) internal mode into USB-equivalent operation.

#### Easy Set Method (Recommended)

Instead of entering values manually, use the SStu-u preset:

1. Scroll to parameter 8 (Easy Set / `EASY-SEt`)
2. Set it to **SStu-u** and press **ENTER**
3. Set it back to **oFF** and press **ENTER** to lock the values in

#### Early-Production Values (non-Mark-V units that cannot set t-cAr below 456.300)

| Parameter      | Display    | Value     | Notes                          |
|----------------|------------|-----------|--------------------------------|
| Mode           | nodE       | PAc-Lo    | Packet Low mode                |
| Display Offset | dSP-oFSt   | +2.125    |                                |
| RX PLL         | r-PLL      | +2.210    | Set PLL values before carriers |
| RX Carrier     | r-cAr      | 452.790   |                                |
| TX PLL         | t-PLL      | +2.210    | Set PLL values before carriers |
| TX Carrier     | t-cAr      | 452.790   |                                |
| RTTY Shift     | rttY-SFt   | 0.000     |                                |
| Easy Set       | EASY-SEt   | oFF       | Must be OFF for manual vals    |

> Set PLL values (+2.210) *before* carrier values. The modified PLL offset
> shifts the acceptable carrier range, allowing 452.790 on early units.

### Menu 6-1: RTTY Polarity

| Parameter      | Value      | Notes                              |
|----------------|------------|------------------------------------|
| RTTY Polarity  | reversed   | Required for correct AFSK decoding |

### Menu 3-0: Frequency Display (Optional)

| Parameter      | Value      | Notes                                   |
|----------------|------------|-----------------------------------------|
| F-diSPly       | cArriEr    | Shows actual carrier (recommended)      |

### Activating USER Mode

After configuring menu 8-6, exit the menu and press the dedicated **USER**
button on the front panel. The display should show **PKT** with the **LSB**
indicator lit. The radio is now operating in USB internally (per your Menu 8-6
settings) despite the LSB indicator.

> The **USER** button directly activates PKT USER mode. The **PKT** button
> cycles through the standard PKT sub-modes (PKT-L, PKT-FM) and does **not**
> enter USER mode.

---

## WSJT-X Radio Settings

Open WSJT-X and go to **File > Settings** (or **F2**), then the **Radio** tab.

### Rig Selection

| Setting          | Value                              |
|------------------|------------------------------------|
| Rig              | **Yaesu FT-1000MP**                |

> For the Mark V or Mark V Field, select **Yaesu FT-1000MP** (the same entry
> works for all FT-1000MP variants in Hamlib).

### CAT Control

| Setting          | Value                              |
|------------------|------------------------------------|
| Serial Port      | COM port of CP210x (e.g. COM3)     |
| Baud Rate        | **4800**                           |
| Data Bits        | **Eight**                          |
| Stop Bits        | **Two**                            |
| Handshake        | **None**                           |
| Force Control Lines | RTS: **Off**, DTR: **Off**      |

> **Critical:** The Digirig uses a CP210x chip that asserts RTS high by default.
> This gates the CAT TX line on the FT-1000MP, causing write commands to be
> silently ignored while reads still work. You **must** force RTS off.

### PTT Method

| Setting          | Value                              |
|------------------|------------------------------------|
| PTT Method       | **CAT**                            |

> PTT via CAT sends a software command to key the transmitter. This is the
> simplest method and does not require a separate PTT port.
>
> **Alternative:** Set PTT Method to **RTS** (same COM port as CAT). The
> Digirig routes the RTS signal from its serial port to the PTT line on the
> TRRS audio cable via the DIN-5 PACKET connector (pin 3).

### Mode

| Setting          | Value                              |
|------------------|------------------------------------|
| Mode             | **None**                           |

> **Critical:** Do not set this to USB or Data/Pkt. Setting Mode to USB causes
> WSJT-X to send a SET_MODE command that kicks the radio out of PKT USER mode.
> Setting it to Data/Pkt switches the radio to RTTY on transmit. Leave it on
> **None** and control the mode from the radio's front panel.

### Transmit Audio Source

| Setting              | Value                              |
|----------------------|------------------------------------|
| Transmit Audio Source | **Rear/Data**                     |

> The Digirig is connected to the rear PACKET connector. Selecting Rear/Data
> ensures TX audio is routed through the PACKET port, not the front mic.

### Split Operation

| Setting          | Value                              |
|------------------|------------------------------------|
| Split Operation  | **Fake It**                        |

> "Fake It" has WSJT-X shift the VFO frequency for transmit, keeping TX audio
> in the 1500-2000 Hz range for a cleaner signal. This is simpler and more
> reliable than "Rig" split with the FT-1000MP.

### Linux Serial Port

On Linux, use the device path instead of COM port:

| Setting          | Value                              |
|------------------|------------------------------------|
| Serial Port      | **/dev/ttyUSB0**                   |

---

## WSJT-X Audio Settings

Go to **File > Settings > Audio** tab.

### Soundcard Selection

| Setting            | Value                                          |
|--------------------|------------------------------------------------|
| Input (Receive)    | **USB Audio Device** (or "Digirig" if renamed) |
| Output (Transmit)  | **USB Audio Device** (or "Digirig" if renamed) |

On Linux, the device may appear as something like `plughw:CARD=Device,DEV=0`
or you can select the ALSA device name.

---

## Fldigi Rig Control Settings

Fldigi offers two methods for CAT control of the FT-1000MP: **Hamlib** (built-in
library supporting many rigs) and **RigCAT** (XML-based definitions). Hamlib is
recommended as it requires no additional files.

Open **Configure > Rig Control** (or use the configuration wizard on first launch).

### Method 1: Hamlib (Recommended)

Select the **Hamlib** tab and check **Use Hamlib**.

| Setting            | Value                                        |
|--------------------|----------------------------------------------|
| Rig                | **Yaesu FT-1000MP**                          |
| Device             | COM port (e.g. COM3) or `/dev/ttyUSB0`       |
| Baud rate          | **4800**                                     |
| Stop bits          | **2**                                        |
| Sideband           | (leave default)                              |
| PTT via Hamlib command | **Unchecked** (use hardware PTT instead)  |

> **Variant selection:** Hamlib lists multiple FT-1000MP models. Choose the one
> matching your radio:
>
> | Radio                    | Hamlib Model                    |
> |--------------------------|---------------------------------|
> | FT-1000MP (original)     | **Yaesu FT-1000MP**             |
> | Mark V FT-1000MP         | **Yaesu MARK-V FT-1000MP**     |
> | Mark V Field FT-1000MP   | **Yaesu MARK-V Field FT-1000MP** |

After entering settings, click **Initialize**. The button text should change
from red to black, indicating successful connection. The frequency display in
Fldigi's toolbar should now track the radio.

> If initialization fails, try checking **RTS/CTS** off (and toggling the
> **RTS** and **DTR** checkboxes), then re-initialize.

### Method 2: RigCAT (Alternative)

If Hamlib does not work reliably, use the RigCAT method with an XML rig
definition file:

1. Download `FT-1000MP.xml` from the
   [Fldigi XML archive](https://sourceforge.net/projects/fldigi/files/xmls/yaesu/).
2. Save it to a known location on your computer.
3. In Fldigi, go to **Configure > Rig Control > RigCAT** tab.
4. Check **Use RigCAT**.
5. Browse to the downloaded XML file.
6. Set the serial port, baud rate (**4800**), and stop bits (**2**).
7. Click **Initialize**.

### Hardware PTT Configuration

Select the **Hardware PTT** tab:

| Setting                | Value                                       |
|------------------------|---------------------------------------------|
| Use serial port PTT    | **Checked**                                 |
| Device                 | COM port of CP210x (same as CAT port)       |
| Use RTS                | **Checked**                                 |
| RTS = +V               | **Checked** (PTT active when RTS asserted)  |
| Use DTR                | **Unchecked**                               |

> **Important:** Disable any **hardware flow control** or **handshake** options
> in the serial port settings. The Digirig uses RTS for PTT, not for flow
> control. Any setting that mentions RTS/CTS handshake must be turned off.

> **CP210x RTS note:** The same RTS issue from the WSJT-X section applies here.
> The CP210x asserts RTS high by default. In Fldigi's Hamlib tab, ensure RTS is
> not checked as a flow control option. It should only be used as a PTT signal
> via the Hardware PTT tab. If CAT reads work but writes fail, this is the
> likely cause.

---

## Fldigi Audio Settings

Go to **Configure > Soundcard > Devices** tab.

### Soundcard Selection

| Setting            | Value                                          |
|--------------------|------------------------------------------------|
| Capture (Input)    | **USB Audio Device** (or "Digirig" if renamed) |
| Playback (Output)  | **USB Audio Device** (or "Digirig" if renamed) |

On Linux, select the appropriate ALSA device from the **Port Audio** or
**PulseAudio** dropdown.

### Audio Level Monitoring

- Fldigi has a built-in waterfall and signal level indicator.
- The diamond-shaped indicator on the bottom left shows input level.
- A properly adjusted level shows a dark blue waterfall background with signals
  visible as yellow/red traces.
- If the waterfall background is bright or washed out, the input level is too
  high.

### Transmit Audio

- Fldigi's built-in attenuator can be adjusted from the main window.
- The output level slider on the right side of the main window controls
  transmit audio amplitude.
- Start with the slider at about **50%** and adjust as described in
  [Audio Level Calibration](#audio-level-calibration).

### Supported Modes

Fldigi supports many digital modes through the PACKET connector, including:

| Mode     | Typical Use            | Bandwidth  |
|----------|------------------------|------------|
| PSK31    | Keyboard chat (QSO)    | 31 Hz      |
| PSK63    | Faster keyboard chat   | 63 Hz      |
| RTTY     | Classic teletype       | 170 Hz     |
| Olivia   | Weak signal chat       | 250-2000 Hz|
| MT63     | Keyboard (net use)     | 500-2000 Hz|
| JS8Call* | Keyboard (via JS8Call) | 50 Hz      |
| CW       | Software CW decode     | ~100 Hz    |
| THOR     | Weak signal keyboard   | varies     |
| MFSK     | Image and text         | varies     |

*JS8Call uses its own application but similar radio/audio setup.

---

## JS8Call Radio Settings

JS8Call is a keyboard-to-keyboard messaging mode built on the FT8 engine. It
enables longer free-text messages, store-and-forward messaging, and automatic
relay through other stations. The radio and audio configuration is very similar
to WSJT-X since JS8Call shares the same underlying Hamlib integration.

Open **File > Settings** (or press **F2**), then select the **Radio** tab.

### CAT Control

| Setting          | Value                              |
|------------------|------------------------------------|
| Rig              | **Yaesu FT-1000MP**                |
| Serial Port      | COM port of CP210x (e.g. COM3)     |
| Baud Rate        | **4800**                           |
| Data Bits        | **Default** (8)                    |
| Stop Bits        | **2**                              |
| Handshake        | **None**                           |

> **Note:** JS8Call uses Hamlib for CAT control, the same library as WSJT-X.
> The rig selection dropdown contains the same entries. Select the appropriate
> FT-1000MP variant for your radio:
>
> | Radio                    | Selection                         |
> |--------------------------|-----------------------------------|
> | FT-1000MP (original)     | **Yaesu FT-1000MP**               |
> | Mark V FT-1000MP         | **Yaesu MARK-V FT-1000MP**       |
> | Mark V Field FT-1000MP   | **Yaesu MARK-V Field FT-1000MP** |

### PTT Method

| Setting          | Value                              |
|------------------|------------------------------------|
| PTT Method       | **RTS**                            |
| Port             | COM port of CP210x (same as CAT)   |
| Transmit Delay   | **0.2** seconds                    |

> The Digirig routes the RTS signal to the DIN-5 PTT line. This is the same
> PTT mechanism as WSJT-X.

### Split Operation

| Setting          | Value                              |
|------------------|------------------------------------|
| Split Operation  | **Fake It**                        |

> "Fake It" works well with the FT-1000MP. JS8Call will shift the VFO
> frequency as needed during transmit to keep the audio tone in the optimal
> range.

### Linux Serial Port

On Linux, use the device path instead of COM port:

| Setting          | Value                              |
|------------------|------------------------------------|
| Serial Port      | **/dev/ttyUSB0**                   |

### CP210x RTS Note

The same CP210x RTS issue applies to JS8Call. If CAT reads work but writes
(frequency changes, mode changes) are silently ignored, ensure that RTS is not
being asserted high by the serial driver. JS8Call may not have an explicit
"Force RTS Off" option like WSJT-X. If you encounter this problem:

1. Check if JS8Call has RTS/DTR control options in the radio settings.
2. Alternatively, use a small utility to set the serial port RTS state before
   launching JS8Call.
3. On Linux, `stty -F /dev/ttyUSB0 -crtscts` can disable hardware flow control.

---

## JS8Call Audio Settings

In **File > Settings**, select the **Audio** tab.

### Soundcard Selection

| Setting            | Value                                          |
|--------------------|------------------------------------------------|
| Input (Capture)    | **USB Audio Device** (or "Digirig" if renamed) |
| Output (Playback)  | **USB Audio Device** (or "Digirig" if renamed) |

On Linux, select the appropriate ALSA or PulseAudio device.

> **Important:** Set the **Notification Soundcard** to your computer's built-in
> speakers or headphones -- not the Digirig. This prevents notification sounds
> from being transmitted over the air.

### JS8Call Speed Modes

JS8Call supports four transmission speeds. All use USB mode through the PACKET
connector:

| Speed   | Bandwidth | TX Period | Effective Speed | Best For                        |
|---------|-----------|-----------|-----------------|----------------------------------|
| Slow    | 25 Hz     | 30 sec    | ~8 WPM          | Weak signals, difficult paths    |
| Normal  | 50 Hz     | 15 sec    | ~16 WPM         | Default; balanced range/speed    |
| Fast    | 80 Hz     | 10 sec    | ~24 WPM         | Good signal conditions           |
| Turbo   | 160 Hz    | 6 sec     | ~40 WPM         | Strong signals, local nets       |

> **Tip:** Start QSOs in **Normal** mode. Switch to Slow for weak/marginal
> signals or Fast/Turbo when conditions allow. You can enable multi-speed
> decoding via the **Mode** menu to decode all speeds simultaneously.

### JS8Call Frequencies

Default calling frequencies (dial frequency, USB):

| Band | Frequency  |
|------|------------|
| 160m | 1.842 MHz  |
| 80m  | 3.578 MHz  |
| 40m  | 7.078 MHz  |
| 30m  | 10.130 MHz |
| 20m  | 14.078 MHz |
| 17m  | 18.104 MHz |
| 15m  | 21.078 MHz |
| 12m  | 24.922 MHz |
| 10m  | 28.078 MHz |

Most activity is on **40m** (evening/night) and **20m** (daytime).

### Time Synchronization

Like FT8, JS8Call requires accurate system time (within ~2 seconds). See the
[time synchronization instructions](#step-5-verify-time-synchronization) in the
Testing section. JS8Call also has a built-in **Timing** tab (enable via
**View > Show Waterfall Controls**) that lets you fine-tune clock drift.

---

## Winlink Overview

Winlink is a global radio email system that allows sending and receiving email
over HF and VHF radio. It works by connecting to RMS (Radio Message Server)
gateway stations that relay your messages to/from the internet.

The system requires three components:

1. **Winlink client** -- Winlink Express (Windows) or Pat (Linux/macOS)
2. **Digital modem** -- VARA HF (recommended), ARDOP, or Packet
3. **Radio + interface** -- FT-1000MP + Digirig (what we're setting up)

> **Important:** Winlink/VARA HF operates in **USB mode**, not PKT mode.
> Unlike WSJT-X, Fldigi, and JS8Call which use the PACKET connector in PKT USER
> mode, VARA HF sends audio through the same PACKET connector but the radio
> should be in **PKT USER** mode (which is internally USB). The same menu 8-6
> configuration used for the other applications works here too.

> **Windows vs Linux:** VARA HF is Windows-only software. On Linux, you can
> run it under Wine, or use ARDOP (open-source alternative) with the Pat
> Winlink client. VARA HF provides significantly better performance than ARDOP.

---

## Winlink Express + VARA HF Setup (Windows)

### Step 1: Install Software

1. Download and install [Winlink Express](https://downloads.winlink.org/User%20Programs/).
2. Download and install [VARA HF](https://rosmodem.wordpress.com/) (free
   trial version available; paid version removes speed limit).
3. On first launch of Winlink Express, create your account with your callsign,
   password, grid square, and recovery email.

### Step 2: Configure VARA HF Modem

Launch VARA HF (it can also be launched automatically by Winlink Express).

#### VARA HF Soundcard Settings

Go to **Settings > SoundCard**:

| Setting         | Value                                          |
|-----------------|------------------------------------------------|
| Device Input    | **Microphone (USB Audio Device)** (Digirig)    |
| Device Output   | **Speakers (USB Audio Device)** (Digirig)      |

> If you renamed the Digirig audio devices, select the renamed entries.

#### VARA HF PTT Settings

Go to **Settings > PTT**:

| Setting         | Value                                          |
|-----------------|------------------------------------------------|
| PTT             | **COM**                                        |
| Port            | COM port of CP210x (e.g. COM3)                 |
| PTT Pin         | **RTS**                                        |

> The Digirig uses RTS to trigger PTT. When VARA asserts RTS, the Digirig
> closes the PTT circuit via the DIN-5 pin 3 on the PACKET connector.

#### VARA HF Network Settings

Go to **Settings > VARA Setup**:

| Setting              | Value       |
|----------------------|-------------|
| VARA HF Command Port | **8300**    |
| VARA HF Data Port    | **8301**    |

These are the defaults. Winlink Express connects to VARA via these TCP ports.

### Step 3: Configure Winlink Express Radio Setup

1. In Winlink Express, select **VARA HF Winlink** from the session dropdown
   (upper right).
2. Click **Open Session**.
3. Go to **Settings > Radio Setup** (or click the gear icon).

#### Radio Setup Dialog

| Setting              | Value                                       |
|----------------------|---------------------------------------------|
| Radio Model          | **Yaesu FT-1000MP Mk V**                   |
| Radio Control Port   | COM port of CP210x (e.g. COM3)              |
| Baud Rate            | **4800**                                    |
| Enable RTS           | **Unchecked** (for CAT -- see note below)   |
| Enable DTR           | **Unchecked**                               |
| PTT Port             | *(leave blank -- VARA handles PTT)*         |

> **Radio model selection:** Winlink Express lists the FT-1000MP as
> **"Yaesu FT-1000MP Mk V"** in the radio model dropdown. This selection
> works for the original FT-1000MP, Mark V, and Mark V Field variants.

> **RTS for CAT vs PTT:** In Winlink Express's Radio Setup, the "Enable RTS"
> checkbox controls the serial port RTS line for CAT communication, **not**
> PTT. Since the CP210x asserts RTS high by default (which blocks CAT writes),
> leave this **unchecked**. PTT is handled separately by VARA HF through its
> own COM port RTS configuration.

#### VARA TNC Setup

Go to **Settings > VARA TNC Setup**:

| Setting              | Value                              |
|----------------------|------------------------------------|
| TNC Host             | **localhost** (or 127.0.0.1)       |
| Virtual Command Port | **8300**                           |
| Modem Path           | **C:\VARA\VARA.exe** (adjust path) |

### Step 4: Connect to an RMS Gateway

1. In the VARA HF Winlink session window, click **Channel Selection**.
2. A list of available RMS gateway stations appears, showing callsign,
   frequency, distance, and last update time.
3. Sort by distance to find nearby stations.
4. Double-click a station to select it.
5. The radio should automatically tune to the gateway's frequency via CAT
   control. Verify the dial frequency matches.
6. Click **Start** to initiate the connection.
7. VARA will handle the handshake, and Winlink will transfer any pending
   messages.

### Winlink Operating Frequencies

Winlink RMS gateways operate across the HF bands. Common frequency ranges:

| Band | Frequency Range   | Notes                          |
|------|-------------------|--------------------------------|
| 80m  | 3.580-3.600 MHz   | Night, regional               |
| 40m  | 7.083-7.100 MHz   | Evening, medium range          |
| 30m  | 10.130-10.148 MHz  | 24-hour, good propagation      |
| 20m  | 14.095-14.112 MHz  | Daytime, long range            |
| 17m  | 18.100-18.110 MHz  | Daytime, long range            |

> Exact frequencies are determined by the RMS gateway station. Use the
> Channel Selection tool to find active gateways and their frequencies.

---

## Pat Winlink Setup (Linux)

Pat is an open-source, cross-platform Winlink client that runs natively on
Linux. It supports VARA (via Wine), ARDOP, AX.25, and Telnet.

### Install Pat

Download from [getpat.io](https://getpat.io/) or install via Go:

```bash
# Debian/Ubuntu (download .deb from GitHub releases):
sudo dpkg -i pat_*_linux_amd64.deb

# Or install from source:
go install github.com/la5nta/pat@latest
```

### Configure Pat

Pat stores its configuration in `~/.config/pat/config.json`. On first run,
it creates a default config. Edit it with your callsign and settings:

```bash
pat configure    # Opens config in your editor
```

Key configuration fields:

```json
{
  "mycall": "YOUR_CALLSIGN",
  "secure_login_password": "your_winlink_password",
  "locator": "FN42ab",
  "hamlib_rigs": {
    "ft1000mp": {
      "address": "/dev/ttyUSB0",
      "network": "serial",
      "rig_model": 1024
    }
  }
}
```

> **Hamlib rig model numbers:**
>
> | Radio                    | Model Number |
> |--------------------------|--------------|
> | FT-1000MP (original)     | **1024**     |
> | Mark V FT-1000MP         | **1004**     |
> | Mark V Field FT-1000MP   | **1025**     |

### ARDOP Setup (Open-Source HF Modem)

ARDOP is the open-source alternative to VARA HF. While slower, it runs
natively on Linux without Wine.

1. Install ARDOP:
   ```bash
   # Download from GitHub releases:
   # https://github.com/pflarue/ardop
   ```

2. Configure Pat for ARDOP in `config.json`:
   ```json
   {
     "ardop": {
       "addr": "localhost:8515",
       "arq_bandwidth": {
         "Forced": false,
         "Max": 2000
       },
       "rig": "ft1000mp",
       "ptt_ctrl": true
     }
   }
   ```

3. Start ARDOP with the Digirig audio device:
   ```bash
   ardopcf 8515 plughw:CARD=Device,DEV=0 plughw:CARD=Device,DEV=0
   ```

4. Start Pat and connect:
   ```bash
   pat http                    # Start web UI at http://localhost:8080
   pat connect ardop://RMS_CALLSIGN?freq=14095000
   ```

### VARA HF via Wine (Higher Performance)

VARA HF can run under Wine on Linux with good results:

1. Install Wine and VARA HF following the guide at
   [Winlink and VARA on Linux](https://winlink.org/content/winlink_express_and_vara_linux_mac_updated_instructions).
2. Configure Pat to use VARA instead of ARDOP:
   ```json
   {
     "vara": {
       "host": "localhost",
       "cmdPort": 8300,
       "dataPort": 8301,
       "rig": "ft1000mp",
       "ptt_ctrl": true
     }
   }
   ```

3. Start VARA under Wine, then connect via Pat:
   ```bash
   pat connect varahf://RMS_CALLSIGN?freq=14095000
   ```

### Pat Web Interface

Pat provides a browser-based UI for composing and reading messages:

```bash
pat http    # Opens web UI at http://localhost:8080
```

From the web interface you can compose messages, view your inbox, and
initiate connections to RMS gateways.

---

## VarAC Setup

VarAC is a real-time HF chat application for keyboard-to-keyboard QSOs,
built on the VARA HF modem. Unlike FT8 or JS8Call which use timed
transmission slots, VarAC operates more like an instant messenger --
you type a message and it transmits immediately. It supports CQ calling,
direct connect, store-and-forward messaging, and file transfers.

VarAC uses the same VARA HF modem as Winlink, so if you have already
configured VARA HF (see [Winlink Express + VARA HF Setup](#winlink-express--vara-hf-setup-windows)),
much of the setup is already done.

> **Windows only:** VarAC is a Windows application. On Linux, it can be
> run under Wine.

### Step 1: Install VarAC

1. Download VarAC from [varac-hamradio.com](https://www.varac-hamradio.com/download).
2. Extract to a dedicated folder (e.g. `C:\VarAC`) -- do **not** run from
   the zip file.
3. Ensure [VARA HF](https://rosmodem.wordpress.com/) is already installed.
4. Launch VarAC and enter your callsign.

### Step 2: Configure VARA HF Modem

If you have not already configured VARA HF for Winlink, set it up now.
The VARA HF configuration is shared between VarAC and Winlink Express.

Go to VARA HF **Settings > SoundCard**:

| Setting         | Value                                          |
|-----------------|------------------------------------------------|
| Device Input    | **Microphone (USB Audio Device)** (Digirig)    |
| Device Output   | **Speakers (USB Audio Device)** (Digirig)      |

Go to VARA HF **Settings > PTT**:

| Setting         | Value                                          |
|-----------------|------------------------------------------------|
| PTT             | **COM**                                        |
| Port            | COM port of CP210x (e.g. COM3)                 |
| PTT Pin         | **RTS**                                        |

### Step 3: Configure VarAC RIG Control

Go to **Settings > RIG control & VARA Configuration**.

VarAC offers several RIG control methods. For the FT-1000MP with Digirig,
use the **CAT** method with a custom command file:

#### PTT Configuration (Upper Left)

| Setting          | Value                              |
|------------------|------------------------------------|
| PTT Method       | **CAT**                            |
| COM Port         | COM port of CP210x (e.g. COM3)     |
| Baud Rate        | **4800**                           |
| Data Bits        | **8**                              |
| Stop Bits        | **2**                              |
| Parity           | **None**                           |

> **Critical:** The FT-1000MP requires **2 stop bits**. If you leave this
> at the default of 1, PTT and CAT commands will not work.

#### CAT Command File for FT-1000MP

VarAC uses a CAT command file to send radio-specific hex commands. Create
or edit the file to include FT-1000MP commands:

| Parameter    | Value              | Notes                              |
|--------------|--------------------|------------------------------------|
| CmdType      | **HEX**            | FT-1000MP uses hex commands        |
| PTTOn        | **000000010F**     | PTT on (opcode 0x0F, param 0x01)  |
| PTTOff       | **000000000F**     | PTT off (opcode 0x0F, param 0x00) |

> **Mode commands:** The FT-1000MP should already be in PKT USER mode
> (set manually on the radio). Comment out any Mode commands in the CAT
> file with a semicolon (`;`) to prevent VarAC from attempting to change
> the radio's mode, which may not work correctly via CAT for this radio.

#### Frequency Control

| Setting          | Value                              |
|------------------|------------------------------------|
| Frequency Control | **CAT** (same port)               |

> If CAT frequency control is unreliable, you can set it to **None** and
> tune the radio manually. VarAC will still function for chat, but you
> will need to change bands by hand.

#### VARA HF Modem Path

| Setting              | Value                              |
|----------------------|------------------------------------|
| VARAHF main file path | **C:\VARA\VARA.exe** (adjust)     |
| VARAHF main port     | **8300** (default)                 |

Click **Save and Exit** after configuring.

### Step 4: Test the Connection

1. Use the **TEST** buttons in the RIG control settings to verify PTT and
   frequency control work correctly.
2. PTT test: the radio should key up when you click TEST.
3. Frequency test: the radio should change frequency when you click TEST.

### VarAC Calling Frequencies

VarAC uses dedicated calling frequencies separate from FT8/JS8Call. When
you call CQ, VarAC encodes a "slot" frequency where the actual QSO will
take place, so the calling frequency stays clear.

| Band | Calling Frequency | Notes                          |
|------|-------------------|--------------------------------|
| 160m | 1.995 MHz         |                                |
| 80m  | 3.595 MHz         | Evening/night                  |
| 60m  | 5.355 MHz         | Channel restrictions may apply |
| 40m  | 7.105 MHz         | Primary evening/night          |
| 30m  | 10.133 MHz        | 24-hour                        |
| 20m  | 14.105 MHz        | Primary daytime                |
| 17m  | 18.107 MHz        | Daytime                        |
| 15m  | 21.105 MHz        | Daytime                        |
| 12m  | 24.927 MHz        | Daytime                        |
| 10m  | 28.105 MHz        | Daytime/sporadic E             |

Most activity is on **20m** (daytime) and **40m** (evening/night).

> Additional calling frequencies can be added by editing the
> `VarAC_frequencies.conf` file in the VarAC installation directory.

### VarAC Operating Tips

- **Bandwidth:** All VarAC QSOs use 500 Hz bandwidth by default. Always
  use 500 Hz on calling frequencies and slots.
- **Power:** 25-50W is typical. VarAC is a 100% duty cycle mode during
  transmit.
- **QSY:** After calling CQ and connecting with a station, VarAC
  automatically QSYs both stations to a slot frequency for the QSO.
  Right-click QSY buttons to listen on the destination before moving.
- **File transfers:** Keep files small (5-10 KB max in high speed,
  1-2 KB in low speed). Do not send large files over HF.
- **Sniffer:** Before calling CQ, use the sniffer feature to verify
  your chosen slot is clear of other traffic.

---

## flrig Rig Control Middleware

[flrig](http://www.w1hkj.com/flrig-help/) is a rig control application that
acts as a middleware server between your radio and multiple digital mode
applications. Instead of each application opening the serial port directly,
flrig holds the serial connection and serves rig data to clients via XMLRPC.

### Why Use flrig?

- **Serial port sharing:** Only one application can open a COM port at a time.
  Without flrig, you must close WSJT-X before opening Fldigi or JS8Call. With
  flrig, all applications connect to flrig's XMLRPC server simultaneously.
- **Single point of control:** Frequency, mode, and PTT are managed in one
  place. All connected clients see the same rig state.
- **No start order dependency:** Client applications can start and stop in any
  order without affecting the serial connection to the radio.
- **Consistent behavior:** flrig handles the CAT protocol details, so all
  client applications get the same reliable rig control.

### Installing flrig

- **Windows:** Download the installer from
  [w1hkj.com/files/flrig](http://www.w1hkj.com/files/flrig/).
- **Linux:** Install from your distribution's package manager:
  ```bash
  # Debian/Ubuntu
  sudo apt install flrig

  # Fedora
  sudo dnf install flrig
  ```
  Or build from source at
  [sourceforge.net/projects/fldigi/files/flrig](https://sourceforge.net/projects/fldigi/files/flrig/).

### Configuring flrig for the FT-1000MP

1. Launch flrig.
2. Open **Config > Setup > Transceiver**.
3. Select **Yaesu FT-1000MP** from the transceiver dropdown.
   - If you have a Mark V or Mark V Field, select **Yaesu FT-1000MP-A** instead.
4. Set the serial port:
   - **Windows:** COMx (Digirig CP210x port)
   - **Linux:** `/dev/ttyUSB0`
5. Set serial parameters:
   - **Baud rate:** 4800
   - **Stop bits:** 2
6. Configure PTT:
   - **PTT via CAT** is the simplest option (flrig sends CAT PTT commands).
   - Alternatively, select **RTS** if you prefer hardware PTT via the
     CP210x RTS pin. If using RTS for PTT, ensure the **RTS for CAT** option
     is **unchecked** (since the CP210x RTS must be held low for CAT to work).
7. Click **Init** (or **Initialize**).
   - The Init button turns from **red to black/green** on successful connection.
   - The flrig main window should now display the radio's current frequency
     and mode.

> **Important (Digirig CP210x):** If using PTT via CAT, flrig handles RTS
> internally. If you experience CAT communication problems, check that flrig
> is not asserting RTS high. In the Config > Setup dialog, ensure **RTS/CTS
> flow control** is disabled and **RTS** is not checked unless you specifically
> need it for PTT.

### flrig XMLRPC Server

flrig runs an XMLRPC server on **localhost:12345** by default. This is the
interface that client applications connect to. The server starts automatically
when flrig launches -- no additional configuration is needed.

To verify the server is running, you can test from a browser or command line:
```
http://localhost:12345
```

### Connecting WSJT-X to flrig

1. Open WSJT-X **Settings > Radio**.
2. Set **Rig** to **FLRig FLRig** (not the direct Yaesu FT-1000MP entry).
3. Leave all serial port settings at their defaults -- WSJT-X communicates
   with flrig over XMLRPC, not directly via serial.
4. Set **PTT Method** to **CAT** (flrig relays PTT to the radio).
5. Click **Test CAT** -- it should turn green immediately if flrig is running.
6. Click **Test PTT** -- the radio should key up.

> **Note:** When using flrig, WSJT-X does not need to know the COM port, baud
> rate, or stop bits. All serial communication is handled by flrig.

### Connecting Fldigi to flrig

1. Open Fldigi **Configure > Rig Control**.
2. Go to the **flrig** tab.
3. Check **Use flrig** to enable the connection.
4. Fldigi connects to flrig on localhost:12345 automatically.
5. Close the configuration dialog.
6. The flrig icon or status in Fldigi's toolbar should indicate a successful
   connection. Frequency changes in Fldigi will appear on the radio.

> **Note:** When using flrig, disable Hamlib and RigCAT in Fldigi to avoid
> conflicts. Only one rig control method should be active at a time.

### Connecting JS8Call to flrig

1. Open JS8Call **File > Settings > Radio**.
2. Set **Rig** to **FLRig FLRig**.
3. Leave serial settings at defaults.
4. Set **PTT Method** to **CAT**.
5. Click **Test CAT** -- should turn green.

JS8Call uses the same flrig XMLRPC interface as WSJT-X.

### Connecting VarAC to flrig

VarAC does not have native flrig support. When using VarAC, you have two
options:

1. **Close flrig** and let VarAC control the radio directly via CAT commands
   (see the [VarAC Setup](#varac-setup) section).
2. **Use OmniRig** (Windows) as an intermediary if you need shared access.

### Running Multiple Applications Simultaneously

With flrig running and connected to the radio:

1. Start flrig **first** and verify the Init button is green/black.
2. Start any combination of WSJT-X, Fldigi, and JS8Call.
3. All applications will show the current frequency and can control the radio.
4. PTT from any application will key up the radio.
5. Applications can be started and stopped in any order.

> **Caution:** While multiple applications can connect simultaneously, only
> **one application should transmit at a time**. Running WSJT-X and Fldigi
> simultaneously is fine for monitoring, but ensure only one has TX enabled.

---

## Hamlib rigctld Rig Control Daemon

[rigctld](https://hamlib.sourceforge.net/html/rigctld.1.html) is a TCP network
daemon from the **Hamlib** project that connects to your radio's serial port
and exposes rig control over a TCP socket. Like flrig, it solves the serial
port sharing problem, but rigctld is a command-line daemon with no GUI --
ideal for headless systems, Raspberry Pi setups, and Linux servers.

### Why Use rigctld?

- **Serial port sharing:** rigctld holds the serial connection and multiplexes
  access to multiple client applications simultaneously over TCP.
- **No GUI required:** Runs as a lightweight daemon, perfect for headless or
  remote operation (e.g., Raspberry Pi controlling the radio).
- **Standardized interface:** Applications connect using Hamlib's text protocol
  on TCP port 4532 -- they do not need to know the radio's native CAT protocol.
- **Remote access:** rigctld can listen on all network interfaces, allowing
  applications on other computers to control the radio.
- **Systemd integration:** Can run as a Linux service that starts automatically
  at boot.

### rigctld vs. flrig

| Feature | rigctld | flrig |
|---------|---------|-------|
| Interface | Command-line daemon (headless) | GUI application with rig display |
| Protocol | Hamlib text protocol over TCP (port 4532) | XML-RPC over HTTP (port 12345) |
| Resource usage | Minimal (no GUI) | Higher (GUI, web server) |
| Ease of setup | Command-line configuration | GUI configuration |
| Headless/remote | Ideal (designed for it) | Possible but less natural |
| Best for | Linux, Raspberry Pi, headless, remote | Windows desktop, users who want a GUI |

Both support the FT-1000MP. Choose based on whether you want a GUI or a daemon.

### Installing rigctld

rigctld is part of the Hamlib package.

- **Windows:** Download Hamlib from
  [github.com/Hamlib/Hamlib/releases](https://github.com/Hamlib/Hamlib/releases).
  Extract the archive; `rigctld.exe` and `rigctl.exe` are in the `bin` folder.
- **Linux:**
  ```bash
  # Debian/Ubuntu
  sudo apt install libhamlib-utils

  # Fedora
  sudo dnf install hamlib
  ```

Verify installation:
```bash
rigctld --version
```

### Hamlib Model Numbers

| Radio | Model ID |
|-------|----------|
| FT-1000MP | 1024 |
| MARK-V FT-1000MP | 1004 |
| MARK-V Field FT-1000MP | 1025 |

Confirm with:
```bash
rigctld -l | grep -i 1000mp
```

### Starting rigctld for the FT-1000MP

**Basic startup (Linux):**
```bash
rigctld -m 1024 -r /dev/ttyUSB0 -s 4800 -C stop_bits=2
```

**With Digirig (CP210x) -- RTS must be forced off:**
```bash
rigctld -m 1024 -r /dev/ttyUSB0 -s 4800 -C stop_bits=2,rts_state=OFF
```

**Windows:**
```cmd
rigctld -m 1024 -r COM3 -s 4800 -C stop_bits=2,rts_state=OFF
```

**With debug output (useful for troubleshooting):**
```bash
rigctld -m 1024 -r /dev/ttyUSB0 -s 4800 -C stop_bits=2,rts_state=OFF -vvvv
```

### rigctld Command-Line Options

| Option | Purpose | FT-1000MP Value |
|--------|---------|-----------------|
| `-m` | Hamlib model number | `1024` (or `1004` / `1025`) |
| `-r` | Serial port device | `/dev/ttyUSB0` or `COMx` |
| `-s` | Baud rate | `4800` |
| `-t` | TCP listening port | `4532` (default) |
| `-T` | Listening IP address | `127.0.0.1` (localhost) or `0.0.0.0` (all interfaces) |
| `-C` | Backend configuration | `stop_bits=2,rts_state=OFF` |
| `-v` | Increase verbosity (stackable) | `-vvvv` for maximum debug |

> **Critical (Digirig CP210x):** Always include `rts_state=OFF` in the `-C`
> options. The CP210x asserts RTS high by default, which blocks CAT writes.
> FTDI-based cables do not need this.

### Connecting WSJT-X to rigctld

1. Start rigctld as described above.
2. In WSJT-X, go to **Settings > Radio**.
3. Set **Rig** to **Hamlib NET rigctl**.
4. Set **Network Server** to `127.0.0.1:4532`.
5. Set **PTT Method** to **CAT**.
6. Set **Split Operation** to **Fake It**.
7. Click **Test CAT** -- should turn green.

> WSJT-X does not need to know the COM port, baud rate, or stop bits when
> using rigctld. All serial communication is handled by the daemon.

### Connecting Fldigi to rigctld

1. Start rigctld as described above.
2. In Fldigi, go to **Configure > Rig Control > Hamlib** tab.
3. Set **Rig** to **Hamlib NET rigctl** (may appear as "NET rigctl (Beta)").
4. Set **Device** to `127.0.0.1:4532`.
5. Adjust polling settings if needed:
   - **Retries:** 5
   - **Write delay:** 50 ms (increase if multiple apps share rigctld)
6. Click **Initialize** -- should turn green.

> Disable RigCAT and hardware PTT tabs when using rigctld. Only one rig
> control method should be active.

### Connecting JS8Call to rigctld

1. Start rigctld as described above.
2. In JS8Call, go to **File > Settings > Radio**.
3. Set **Rig** to **Hamlib NET rigctl**.
4. Set **Network Server** to `127.0.0.1:4532`.
5. Set **PTT Method** to **CAT**.
6. Click **Test CAT** -- should turn green.

### Testing with the rigctl Command-Line Client

`rigctl` is the interactive companion to `rigctld`. Use it to test the
connection or query the radio from the command line.

**Connect to a running rigctld instance:**
```bash
rigctl -m 2 -r 127.0.0.1:4532
```

Model `-m 2` is the special "NET rigctl" model that connects over TCP.

**One-shot commands (no interactive mode):**
```bash
# Get current frequency
rigctl -m 2 -r localhost:4532 f

# Set frequency to 14.074 MHz (FT8)
rigctl -m 2 -r localhost:4532 F 14074000

# Set mode to USB
rigctl -m 2 -r localhost:4532 M USB 0

# Key up PTT
rigctl -m 2 -r localhost:4532 T 1

# Release PTT
rigctl -m 2 -r localhost:4532 T 0
```

**Interactive mode commands:**

| Command | Shortcut | Description |
|---------|----------|-------------|
| `get_freq` | `f` | Get current frequency |
| `set_freq` | `F` | Set frequency (Hz) |
| `get_mode` | `m` | Get current mode |
| `set_mode` | `M` | Set mode and passband |
| `get_ptt` | `t` | Get PTT state |
| `set_ptt` | `T` | Set PTT (0=RX, 1=TX) |
| `get_rit` | `j` | Get RIT offset |
| `set_rit` | `J` | Set RIT offset (Hz) |
| `get_vfo` | `v` | Get active VFO |
| `set_vfo` | `V` | Set active VFO |
| `quit` | `q` | Exit rigctl |

**Direct serial test (bypassing rigctld):**
```bash
rigctl -m 1024 -r /dev/ttyUSB0 -s 4800 -C stop_bits=2,rts_state=OFF
```

This talks directly to the radio without the daemon. Useful for verifying
serial communication before starting rigctld.

### Running rigctld as a Linux Service (systemd)

Create `/etc/systemd/system/rigctld.service`:

```ini
[Unit]
Description=Hamlib rigctld rig control daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/rigctld -m 1024 -r /dev/ttyUSB0 -s 4800 -t 4532 -C stop_bits=2,rts_state=OFF
Restart=on-failure
RestartSec=60
User=rigctld
Group=dialout

[Install]
WantedBy=multi-user.target
```

Set it up:
```bash
# Create a dedicated user
sudo useradd -r -s /usr/sbin/nologin rigctld
sudo usermod -aG dialout rigctld

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable rigctld
sudo systemctl start rigctld

# Check status
systemctl status rigctld
```

### Stable Device Names with udev (Linux)

If you have multiple USB-serial devices, `/dev/ttyUSB0` may change between
reboots. Create a udev rule for a stable symlink.

Create `/etc/udev/rules.d/99-hamradio.rules`:
```
# Digirig CP210x -> /dev/digirig
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="digirig"
```

Reload rules:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Then use `-r /dev/digirig` in your rigctld command.

### Running rigctld on Windows at Startup

Create a batch file (e.g., `C:\hamradio\start_rigctld.bat`):
```bat
@echo off
START /MIN "rigctld" "C:\hamlib\bin\rigctld.exe" -m 1024 -r COM3 -s 4800 -t 4532 -C stop_bits=2,rts_state=OFF
```

To autostart, place a shortcut to the batch file in:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

Or use **Task Scheduler** to create a task triggered "At log on" that runs
the batch file.

---

## GridTracker Setup

[GridTracker](https://gridtracker.org/) is an open-source companion application
that displays decoded digital mode activity on an interactive world map in real
time. It plots callsigns by grid square, tracks award progress (DXCC, WAS, grid
squares, CQ/ITU zones), provides alerts for wanted contacts, and can forward
logged QSOs to services like LoTW, QRZ, eQSL, and ClubLog.

> **Key point:** GridTracker does **not** control your radio. It receives
> decoded data from WSJT-X (or JTDX) over a UDP network connection. Your
> FT-1000MP CAT configuration is entirely handled by WSJT-X -- GridTracker
> is radio-agnostic.

```
FT-1000MP <--serial CAT--> WSJT-X <--UDP (port 2237)--> GridTracker
```

### Installing GridTracker

The current version is **GridTracker 2** (a complete rewrite of the original).
GridTracker 1 is end-of-life and no longer supported.

- **Windows:** Download the installer from
  [gridtracker.org/downloads](https://gridtracker.org/downloads/).
  Run `GridTracker-Installer.exe` and follow the wizard.
- **macOS:** Download `GridTracker.app`, drag to Applications. First launch:
  right-click > Open to bypass Gatekeeper.
- **Linux:**
  ```bash
  # Debian/Ubuntu
  sudo dpkg -i GridTracker2-*.deb

  # Fedora
  sudo dnf install GridTracker2-*.rpm
  ```

GridTracker 2 has a built-in auto-updater that checks for new versions.

### Configuring WSJT-X for GridTracker

Three settings in WSJT-X are **required** for GridTracker to work correctly.
Missing any of them causes lost logs or broken map behavior.

1. Open WSJT-X **File > Settings > Reporting**.
2. Check **"Prompt me to log QSO"**.
3. Check **"Clear DX call and grid after logging"**.
4. Check **"Accept UDP requests"**.
5. Set **UDP Server** to `127.0.0.1` port `2237`.
6. Recommended: enable **"PSK Reporter Spotting"** for PSK Reporter integration.

Also verify in the **General** tab:
- Your **callsign** is entered.
- Your **grid square** is set to 6 characters (e.g., `FN42ab`, not just `FN42`).

### Configuring GridTracker

1. Launch GridTracker.
2. Open **Settings > General**.
3. Verify the IP address is `127.0.0.1` and port is `2237` (must match WSJT-X).
4. GridTracker should immediately begin displaying decoded stations on the map
   when WSJT-X is running and decoding.

### Callsign Lookups

Configure in **Settings > Lookups**:

| Service | Notes |
|---------|-------|
| **CALLOOK** | US callsigns only, free, no account needed (default) |
| **QRZ.com** | Requires QRZ account; XML subscription for full API access |
| **HamQTH.com** | Free; requires HamQTH account credentials |
| **QRZCQ.com** | Alternative lookup service |

### Logging Integration

GridTracker can forward logged QSOs to external services. Configure in
**Settings > Logging**:

- **LoTW** -- via TQSL; queues failed uploads and retries automatically
- **QRZ.com** -- requires API key
- **eQSL**
- **ClubLog**
- **HRDLog.net**
- **ACLog** (N3FJP)
- **Log4OM**
- **N1MM Logger+**
- **DXKeeper** (DXLab Suite)
- **Cloudlog / Wavelog**

You can also import existing ADIF log files to populate the map with
worked/confirmed status for award tracking.

### Alerts

Configure in **Settings > Alerts** to receive audio/visual notifications for:

- **Wanted grids** -- grids you have not worked or confirmed
- **Wanted DXCC entities** -- new countries
- **Wanted US states** -- for WAS tracking
- **Wanted CQ zones / ITU zones**
- **Specific callsigns** -- buddy list, your own call, etc.

Alerts can be filtered by band/mode, CQ-only stations, minimum signal
strength, and whether the station includes a grid in their transmission.

### PSK Reporter Integration

GridTracker can display where your signal has been received via
[PSK Reporter](https://pskreporter.info/):

1. Enable **"PSK Reporter Spotting"** in WSJT-X (Settings > Reporting).
2. In GridTracker, use the **PSK Spot** button on the Control Panel.
3. A map of reception reports from the past 24 hours is displayed with
   path lines from your QTH to each receiving station.

### Running with Multiple Companion Applications

If you need GridTracker **and** another application (like JTAlert or N1MM)
to both receive WSJT-X data, use UDP multicast:

1. In WSJT-X: set UDP server IP to a multicast address like `224.0.0.1`,
   keep port `2237`.
2. In GridTracker: enable **Multicast** in Settings and set the same IP/port.
3. In the other application: set the same multicast IP/port.
4. All applications receive the same UDP data simultaneously.

Alternatively, GridTracker can forward UDP data to a second port (default
`2238`) via its forwarding settings.

### JS8Call and Fldigi Compatibility

- **JS8Call:** GridTracker previously supported JS8Call via a WSJT-X-compatible
  UDP interface. JS8Call has since removed that interface, so live decode
  integration is currently unavailable. If JS8Call re-enables it, GridTracker
  will support it automatically.
- **Fldigi:** GridTracker does not have native Fldigi integration. You can
  import Fldigi's ADIF log file manually for map display, but real-time decode
  plotting is not supported.

### GridTracker with flrig or rigctld

GridTracker does not interact with flrig or rigctld. Whether WSJT-X controls
the radio directly, through flrig, or through rigctld is transparent to
GridTracker -- it only sees the UDP data stream from WSJT-X.

---

## JTAlert Setup

[JTAlert](https://hamapps.com/) is a free Windows companion application for
WSJT-X and JTDX that provides real-time audio and visual alerts based on
decoded callsigns. It tracks award progress (DXCC, WAS, WPX, grids, CQ/ITU
zones), detects duplicate contacts ("Worked B4"), and bridges QSO logging
to external logbook software and online services.

> **Key point:** JTAlert does **not** control your radio. Like GridTracker, it
> receives decoded data from WSJT-X over UDP and is completely radio-agnostic.
> Your FT-1000MP CAT setup is handled entirely by WSJT-X.

```
FT-1000MP <--serial CAT--> WSJT-X <--UDP (port 2237)--> JTAlert
                                                          |
                                                          +--> Logbook (ACLog, DXKeeper, etc.)
                                                          +--> Online (LoTW, QRZ, eQSL, ClubLog)
```

> **Platform:** JTAlert is **Windows only** (Windows 10/11). There is no Linux
> or macOS version. Linux users should consider
> [GridTracker](#gridtracker-setup) as an alternative.

### Installing JTAlert

**Prerequisites:**
- **.NET 8 Desktop Runtime** -- download from Microsoft (match your Windows
  architecture: 64-bit or 32-bit).

**Installation (three downloads from [hamapps.com](https://hamapps.com/)):**
1. **JTAlert application** -- main installer.
2. **Callsign Database** -- LoTW and eQSL user databases for flagging
   confirmed stations.
3. **Voiced Alert Sounds** (optional) -- spoken callsign/country alerts
   available in 21 languages.

### Configuring WSJT-X for JTAlert

JTAlert reads WSJT-X's configuration file on startup to auto-detect the UDP
settings. In WSJT-X, go to **File > Settings > Reporting**:

1. Check **"Accept UDP requests"** -- **required** for JTAlert to trigger
   logging in WSJT-X.
2. Check **"Prompt me to log QSO"**.
3. Check **"Clear DX call and grid after logging"**.
4. Set **UDP Server** to `127.0.0.1` port `2237` (defaults).
   - If also running GridTracker, use multicast `224.0.0.1` instead
     (see [Running with GridTracker](#running-jtalert-with-gridtracker) below).

> Without "Accept UDP requests" checked, JTAlert cannot trigger the WSJT-X
> log dialog or control the DX call field.

### Configuring JTAlert

1. Launch JTAlert (after WSJT-X is running).
2. Open **Settings** (F2 key or Settings menu).
3. Set your **callsign** and **grid square**.
4. JTAlert auto-detects the WSJT-X UDP connection -- no manual port
   configuration is typically needed.

### Alert Configuration

Each alert type can be independently configured with custom colors and sounds.
Open **Settings > Alerts** to enable:

- **Your Callsign Decoded** -- someone is calling you
- **CQ Stations** -- stations calling CQ
- **Wanted DXCC** (by band/mode) -- countries you need
- **Wanted US States** (by band/mode) -- for WAS tracking
- **Wanted Grids** (by band/mode) -- grid squares you need
- **Wanted CQ Zones** (by band/mode) -- for WAZ tracking
- **Wanted Continents** (by band/mode)
- **Wanted Prefixes** (by band/mode) -- specific prefixes you are chasing
- **Wanted Callsigns** -- specific stations you define

Alerts can be restricted to stations that are **LoTW users** or **eQSL users**,
so you only chase contacts likely to confirm.

### Logging Integration

JTAlert can automatically forward logged QSOs to external logbook software.
Configure in **Settings > Logging**:

| Logbook | Integration |
|---------|-------------|
| **DXKeeper** (DXLab Suite) | Native TCP API |
| **ACLog** (N3FJP) | Auto-detected API |
| **Log4OM V2** | UDP integration |
| **HRD Logbook** | Native API |
| **Standard ADIF file** | File-based export |

> **Important:** Do not enable both JTAlert's logging and WSJT-X's direct QSO
> forwarding to the same logbook -- this creates duplicate entries. Use one
> path or the other.

### Online QSO Uploads

JTAlert can automatically upload logged QSOs to:

- **QRZ.com** logbook (requires API key)
- **eQSL.cc**
- **ClubLog**
- **HRDLog.net**

### Callsign Lookups

Configure in **Settings > Lookups**:

- **QRZ.com** -- requires paid XML subscription
- **HamQTH.com** -- free alternative

Lookup data (name, QTH, grid) can be automatically populated into logged QSOs.

### B4 (Worked Before) Database

JTAlert maintains an internal database of all logged QSOs to flag duplicate
contacts:

- Decoded stations that have been worked before are highlighted as "Worked B4"
  in the decode list.
- B4 matching can be configured by **band**, **mode**, or **band+mode**.
- For new installations, import your existing log via ADIF to seed the database.
- After the initial import, JTAlert updates the B4 database automatically with
  each new QSO.
- Audio alerts can be suppressed for "Worked B4" stations to reduce alert
  fatigue.

### Rebuild Alert Database (Scan Log)

After initial setup or after importing QSOs, rebuild the alert database to
sync JTAlert's award tracking with your actual log:

1. Open **Settings** (F2).
2. Navigate to **Rebuild Alert Database**.
3. Enable rebuilds for each award you are pursuing (DXCC, WAS, grids, etc.).
4. Select confirmation options (e.g., "confirmed via LoTW" for DXCC credit).
5. Click **Rebuild All (enabled)**.
6. Click **OK (Apply)** when prompted.

After a rebuild, alerts will only fire for entities you still **need**, not
ones you have already worked or confirmed.

### LoTW Integration

- **LoTW user flagging:** JTAlert maintains a database of known LoTW users and
  flags decoded callsigns that are LoTW members. This lets you prioritize
  contacts with stations that will confirm.
- **Restrict alerts to LoTW users:** Configure wanted-entity alerts to only
  fire for stations that are LoTW users.
- **QSL status:** JTAlert can automatically set the LoTW sent status to
  "Requested" in your logbook when logging a QSO.

### Running JTAlert with GridTracker

To run both JTAlert and GridTracker simultaneously, use **UDP multicast** so
WSJT-X can send data to multiple listeners:

1. In WSJT-X: set UDP server IP to `224.0.0.1`, keep port `2237`.
2. JTAlert auto-detects the multicast address from WSJT-X's config.
3. In GridTracker: enable **Multicast** and set IP to `224.0.0.1`, port `2237`.
4. Both applications receive the same UDP data simultaneously.

### JTDX Support

JTAlert has full JTDX support, identical to WSJT-X. All alerting and logging
features work the same way. JTDX supports FT8 and JT65 but not FT4.

### JS8Call Support

JTAlert has **limited** JS8Call support. It can handle JS8Call's log QSO
requests (forwarding logged contacts to your logbook), but full decode-level
alerting (wanted DXCC, states, etc.) is not available for JS8Call decodes.

---

## Audio Level Calibration

Proper audio levels are critical for digital modes. Incorrect levels cause
failed decodes (too low) or distorted/spurious signals (too high).

### Receive Levels (Radio to Computer)

1. Tune to an active FT8 frequency (e.g. 14.074 MHz).
2. In WSJT-X, watch the level indicator at the bottom left of the waterfall.
3. Adjust the **recording device level** in your OS sound settings:
   - **Start at 20%** and increase gradually.
   - The level bar should show signals but stay **below the red zone**.
   - Aim for a noise floor around 30-40 dB on the WSJT-X display.
4. The radio's front panel AF knob does **not** affect DATA OUT level --
   adjustments are made on the computer side only.

### Transmit Levels (Computer to Radio)

1. Set the WSJT-X **Pwr** slider to approximately **25-50%** initially.
2. Set the OS **playback device level** to approximately **80%**.
3. Set the radio's **MIC GAIN** knob to approximately **10 o'clock**
   (same position as normal SSB operation).
4. Key up a test transmission (use the **Tune** button in WSJT-X):
   - Watch the radio's **ALC meter**.
   - Adjust the Pwr slider so that output power reaches your target wattage
     **with little to no ALC deflection**.
   - Any ALC action means the audio input is too hot and will cause splatter.
5. Also check the radio's power output meter -- for FT8, 25-50W is typical.

> **Key principle:** Minimize ALC activity. The ALC should barely move or not
> move at all. Reduce the WSJT-X Pwr slider or OS playback level until ALC
> deflection disappears.

---

## Testing the Setup

### Step 1: Test CAT Control

1. In WSJT-X **Settings > Radio**, click **Test CAT**.
2. The button should turn **green**.
3. If it turns red, see [Troubleshooting](#troubleshooting).
4. Try changing the frequency in WSJT-X -- the radio's display should follow.

### Step 2: Test PTT

1. Click **Test PTT** in the Radio settings.
2. The radio should switch to transmit (TX indicator lights up).
3. Click **Test PTT** again to return to receive.
4. If the radio does not key up, verify PTT method and COM port settings.

### Step 3: Test Audio Receive

1. Close settings and tune to an active FT8 frequency:
   - **20m:** 14.074 MHz
   - **40m:** 7.074 MHz
   - **17m:** 18.100 MHz
2. Ensure the radio is in **PKT USER** mode (press the **USER** button).
3. You should see signals on the WSJT-X waterfall display.
4. After a decode cycle (15 seconds for FT8), decoded stations should appear.

### Step 4: Test Audio Transmit

1. Click **Tune** in WSJT-X to transmit a steady carrier.
2. Verify the radio shows TX and the power meter shows output.
3. Adjust levels as described in [Audio Level Calibration](#audio-level-calibration).
4. Click **Tune** again to stop.

### Step 5: Verify Time Synchronization

FT8 requires accurate system time (within ~1 second).

- **Windows:** Enable "Set time automatically" in Settings, or use
  [Meinberg NTP](https://www.meinberg.de/english/sw/ntp.htm) or
  [Dimension 4](http://www.thinkman.com/dimension4/).
- **Linux:** Ensure `systemd-timesyncd` or `ntpd` is running:
  ```bash
  timedatectl status    # Check NTP sync status
  ```

---

## Operating Tips

### Frequency Selection

Common FT8 frequencies (dial frequency, USB):

| Band | Frequency  |
|------|------------|
| 160m | 1.840 MHz  |
| 80m  | 3.573 MHz  |
| 40m  | 7.074 MHz  |
| 30m  | 10.136 MHz |
| 20m  | 14.074 MHz |
| 17m  | 18.100 MHz |
| 15m  | 21.074 MHz |
| 12m  | 24.915 MHz |
| 10m  | 28.074 MHz |

### Power

FT8 and JS8Call are very efficient. Typical power levels:

- **25-50W** for general operation
- **5-10W** for QRP
- Avoid running full power (100W+) unless necessary -- it increases QRM for
  others and stresses the radio's duty cycle

### Duty Cycle

FT8, JS8Call, and PSK modes are 100% duty cycle during transmit. The FT-1000MP
handles this well, but avoid extended continuous transmit sessions. The radio
will get warm during prolonged operation.

### Mode Selection

- WSJT-X, JS8Call, Fldigi, VARA, and VarAC all handle modulation/demodulation in software.
- The radio just needs to be in **PKT USER** mode (which provides USB passthrough).
- Do **not** change the radio's mode while digital software is running.

---

## Backing Up Radio Settings (Clone Mode)

After configuring all the menu settings for digital modes, it's a good idea to
back up your radio's configuration so you can restore it if needed.

### What Clone Mode Does

The FT-1000MP supports **clone mode**, which transfers the entire radio
configuration (all menu settings, memory channels, and operating parameters)
over the CAT serial port. This allows you to:

- **Back up** your radio's configuration to a file on your computer
- **Restore** a saved configuration back to the radio
- **Maintain multiple profiles** (e.g., contest settings vs. digital mode
  settings) and swap between them
- **Transfer settings** between two identical FT-1000MP radios

### Important Limitations

- Clone mode is a **bulk transfer** of the entire configuration -- you cannot
  read or write individual menu items via CAT commands.
- Clone mode must be **initiated from the radio's front panel** -- it cannot be
  started remotely via CAT.
- The FT-1000MP CAT protocol has **no opcode for reading or writing individual
  menu settings or EEPROM addresses**. This is a limitation of the radio's
  firmware, unlike some newer Yaesu radios (FT-817/857/897) that have
  undocumented EEPROM read commands.
- During normal CAT operation, you can read the radio's current frequency,
  mode, VFO status, and meter readings, but not menu configuration.

### Hidden Menu Access

The FT-1000MP has a hidden service menu (items 9-0 through 9-8) accessible by
holding **FAST** and **LOCK** simultaneously while powering on. This menu
includes Collins filter adjustments, IF gain settings, and CPU self-check. Use
with caution -- incorrect values can degrade radio performance.

### Software for Clone Management

[SuperControl](https://www.supercontrol.de/cat/us/featuresft1000mp.php)
(commercial, Windows) is the primary software for managing FT-1000MP clone
files. It can:

- Read clone data from the radio
- Edit settings on the computer
- Write clone data back to the radio
- Archive multiple configuration profiles

### Reset Procedures

If you need to restore factory defaults without a clone backup:

| Reset Level | Key Combination at Power-On   | Effect                              |
|-------------|-------------------------------|--------------------------------------|
| Level 1     | Hold **SUB (CE)** + **ENT**   | Resets memories to defaults (menus preserved) |
| Level 3     | Hold **29/0**                 | Full factory reset (all settings)    |

> **Caution:** Level 3 reset erases all menu settings, memory channels, and
> custom configurations. You will need to re-enter all menu settings from
> the [Radio Menu Configuration](#radio-menu-configuration) section.

---

## Troubleshooting

### CAT Control Fails (Test CAT turns red)

1. **Verify COM port:** Check Device Manager (Windows) or `ls /dev/ttyUSB*`
   (Linux) to confirm the correct port.
2. **Check baud rate:** Must be **4800** with **2 stop bits**.
3. **Force RTS off:** The CP210x in the Digirig asserts RTS high by default,
   which blocks CAT writes. Ensure RTS is forced off in WSJT-X settings.
4. **Cable check:** Ensure the DB-9 cable is firmly seated in the CAT port.
5. **No other software:** Only one program can use a COM port at a time. Close
   any other CAT/logging software.
6. **Radio memory corruption:** In rare cases, CAT queries return wrong values.
   A Level 3 reset may be needed (hold **29/0** key during power-up to restore
   factory defaults, then re-enter menu settings).

### No Audio on Waterfall

1. **PKT USER mode:** Ensure you pressed the **USER** button (not PKT). The
   PACKET jack is silent in USB/LSB/CW modes.
2. **Correct audio device:** Verify WSJT-X input is set to the Digirig's USB
   audio device, not your computer's built-in microphone.
3. **Recording level:** Check OS recording device level is not at 0%.
4. **Windows privacy:** On Windows 11, ensure apps have permission to access
   the microphone (Settings > Privacy > Microphone).
5. **Cable:** Verify the DIN-5 cable is plugged into the **PACKET** jack (not
   the nearby RTTY FSK jack).

### Radio Does Not Transmit (PTT Fails)

1. **PTT method:** Should be **RTS** on the CP210x COM port.
2. **DIN-5 cable:** Check that pin 3 (PTT) is properly wired to the TRRS Ring 2.
3. **MOX/inhibit:** Ensure the radio is not in a locked or inhibit state.

### Distorted or Splattery Transmit Signal

1. **ALC:** Reduce WSJT-X Pwr slider until ALC meter shows no deflection.
2. **MIC GAIN:** Try reducing below 10 o'clock.
3. **OS playback level:** Reduce from 80% if needed.
4. **EDSP:** If Menu 4-4 (TX EDSP) is enabled, try setting it to **off** for
   digital modes to avoid unwanted audio processing.

### Frequency Jumps Back After Changing

This is a known issue on some FT-1000MP units with corrupted internal memory.
Perform a Level 3 reset (hold **29/0** during power-up), then re-enter your
menu settings.

### JTAlert Not Receiving Decodes or Not Logging

1. **Accept UDP requests:** In WSJT-X Settings > Reporting, "Accept UDP
   requests" must be checked. This is the most common cause of JTAlert not
   working.
2. **WSJT-X running first:** WSJT-X should be running before JTAlert is
   launched. JTAlert reads WSJT-X's config file on startup.
3. **UDP port match:** JTAlert reads the port from WSJT-X's config. If you
   changed the default port (2237), restart JTAlert so it picks up the change.
4. **Firewall:** Ensure both WSJT-X and JTAlert are allowed through the
   Windows firewall for UDP traffic.
5. **.NET runtime:** JTAlert requires .NET 8 Desktop Runtime. If JTAlert
   crashes or fails to start, verify the runtime is installed.
6. **Duplicate logging:** If QSOs are being logged twice, you have both
   JTAlert and WSJT-X sending to the same logbook. Disable one path.
7. **Multicast (when also using GridTracker):** Switch WSJT-X UDP server from
   `127.0.0.1` to `224.0.0.1` and restart both JTAlert and GridTracker.

### GridTracker Shows No Stations on Map

1. **WSJT-X UDP settings:** Go to WSJT-X Settings > Reporting and verify all
   three checkboxes are enabled: "Prompt me to log QSO", "Clear DX call and
   grid after logging", and "Accept UDP requests".
2. **Port match:** WSJT-X UDP port (default `2237`) must match GridTracker's
   listening port in Settings > General.
3. **IP match:** Both must use `127.0.0.1` (or the same multicast address if
   using multicast).
4. **WSJT-X decoding:** Verify WSJT-X itself is decoding stations (check the
   decode list). If WSJT-X shows no decodes, the issue is with the radio/audio
   setup, not GridTracker.
5. **Firewall:** On Windows, ensure GridTracker has network access through the
   firewall. Some third-party firewalls (BitDefender, etc.) may block UDP.
6. **Restart both:** After changing any network settings, restart both WSJT-X
   and GridTracker.

### Fldigi Hamlib Initialize Fails (Button Stays Red)

1. **Turn radio on first:** The radio must be powered on and in PKT USER mode
   before clicking Initialize. Fldigi must detect the CAT connection.
2. **Toggle RTS/DTR:** Try checking or unchecking the RTS and DTR checkboxes
   in the Hamlib tab, then re-initialize.
3. **Try RigCAT:** If Hamlib is unreliable, switch to the RigCAT method using
   the FT-1000MP.xml definition file (see [Method 2: RigCAT](#method-2-rigcat-alternative)).
4. **Command interval:** In the Hamlib advanced settings, try increasing the
   **retries**, **retry interval**, and **command interval** values for more
   consistent communication.
5. **DB-9 cable polarity:** There are two types of FT-1000MP RS-232 cables
   on the market -- one with crossed RXD/TXD and one without. Both use
   female/female connectors, making them hard to distinguish. If CAT fails
   with one cable, try the other type.

### Decoding Works but No QSOs Complete

1. **Time sync:** FT8 requires time accuracy within ~1 second. Check NTP.
2. **TX frequency:** Make sure you are not transmitting on the same frequency
   as your receive. Split mode ("Fake It") helps with this.
3. **Power:** Ensure you are actually transmitting RF (check power meter, not
   just TX indicator).

### VARA HF Won't Connect to RMS Gateway

1. **Frequency mismatch:** Verify the radio's dial frequency matches the
   gateway frequency shown in Winlink's Channel Selection.
2. **PTT not working:** Check VARA's PTT settings (Settings > PTT): must be
   COM port with RTS pin. Verify the correct COM port is selected.
3. **Audio routing:** Confirm VARA's soundcard settings point to the Digirig
   USB audio device, not the computer's built-in audio.
4. **Gateway offline:** RMS gateways go offline. Try a different gateway.
   Sort by distance and pick one that was recently updated.
5. **VARA version:** Ensure you have a current version of VARA HF installed.
   Older versions may have compatibility issues.

### Winlink Express Radio Control Not Working

1. **COM port conflict:** VARA HF and Winlink Express may both try to access
   the same COM port. VARA handles PTT via its own COM connection. If there
   is a conflict, ensure only one application is accessing the CAT port.
2. **Radio model:** Select **"Yaesu FT-1000MP Mk V"** in the radio setup
   dropdown. If your exact model is not listed, this entry works for all
   FT-1000MP variants.
3. **Baud rate:** Must be **4800** to match the radio's fixed CAT speed.

### flrig Init Button Stays Red

1. **Serial port:** Verify the correct COM port is selected in Config > Setup.
   Only one application can hold the serial port -- close any other CAT software
   (WSJT-X, Fldigi, etc.) before initializing flrig.
2. **Transceiver selection:** Ensure you selected **Yaesu FT-1000MP** (or
   **FT-1000MP-A** for Mark V). The wrong rig selection will send incorrect
   CAT commands.
3. **Baud rate and stop bits:** Must be **4800 baud, 2 stop bits**.
4. **RTS issue (Digirig):** If RTS/CTS flow control is enabled or RTS is
   asserted, CAT writes may be blocked. Disable flow control and uncheck RTS
   (unless using RTS for PTT).
5. **Radio power:** The radio must be powered on before clicking Init.
6. **Try re-init:** Click Init again after making changes. flrig does not
   auto-retry.

### rigctld Fails to Start or No Communication

1. **Serial port in use:** Close any other application using the COM port
   (WSJT-X, Fldigi, flrig, etc.) before starting rigctld.
2. **Wrong model number:** Use `-m 1024` for the standard FT-1000MP, `-m 1004`
   for the Mark V, or `-m 1025` for the Mark V Field.
3. **Stop bits:** Must include `-C stop_bits=2` on the command line.
4. **RTS (Digirig):** Must include `rts_state=OFF` in the `-C` options.
5. **Permissions (Linux):** The user running rigctld must be in the `dialout`
   group: `sudo usermod -aG dialout $USER` (log out and back in).
6. **Radio power:** The radio must be on before starting rigctld.
7. **Debug output:** Add `-vvvv` to see detailed communication. Look for
   "IO error" or "timeout" messages.

### WSJT-X/JS8Call Cannot Connect to rigctld

1. **rigctld running:** Verify rigctld is running (`ps aux | grep rigctld` on
   Linux, or check Task Manager on Windows).
2. **Rig selection:** Must be **Hamlib NET rigctl** in the radio settings.
3. **Network server:** Must be `127.0.0.1:4532` (or whatever port you used
   with `-t`).
4. **Firewall:** On Windows, ensure the firewall allows connections on port
   4532.
5. **Port conflict:** Another service may be using port 4532. Try a different
   port with `-t 4533` and update the client accordingly.

### WSJT-X/JS8Call Cannot Connect to flrig

1. **flrig running:** Ensure flrig is running and the Init button is
   green/black (connected to radio).
2. **Rig selection:** Must be **FLRig FLRig** in the radio settings, not the
   direct Yaesu entry.
3. **XMLRPC port:** flrig defaults to port 12345. If you changed it in flrig,
   the client applications may not find it.
4. **Firewall:** On Windows, ensure the firewall is not blocking localhost
   connections on port 12345.
5. **Multiple flrig instances:** Only one instance of flrig should be running.

### VarAC PTT or CAT Not Working

1. **Stop bits:** The FT-1000MP requires **2 stop bits**. VarAC defaults
   to 1. Change this in Settings > RIG control & VARA Configuration.
2. **CmdType:** Must be **HEX** for the FT-1000MP (not TEXT).
3. **PTT commands:** Use `000000010F` (on) and `000000000F` (off).
4. **Mode commands:** Comment out any Mode commands in the CAT command
   file with `;` -- the radio should be in PKT USER mode manually.
5. **COM port conflict:** If VARA HF is also using the same COM port for
   PTT, there may be a conflict. Ensure VarAC and VARA are not both
   trying to open the same serial port simultaneously.

---

## Quick Reference Card

```
RADIO SETTINGS
  Menu 8-6:  PAc-Lo / 0 / 1.750 / 453.250 / 1.750 / 453.250 / 0 / oFF
  Menu 6-1:  RTTY polarity = reversed
  Menu 3-0:  F-diSPly = cArriEr  (optional)
  Activate:  Press USER button (USER mode)
  MIC GAIN:  10 o'clock

WSJT-X RADIO TAB
  Rig:        Yaesu FT-1000MP
  Serial:     COMx / /dev/ttyUSB0
  Baud:       4800
  Data Bits:  Eight
  Stop Bits:  Two
  Handshake:  None
  RTS:        Off (forced)
  DTR:        Off (forced)
  PTT:        CAT
  Mode:       None
  TX Audio:   Rear/Data
  Split:      Fake It

WSJT-X AUDIO TAB
  Input:      USB Audio Device (Digirig)
  Output:     USB Audio Device (Digirig)

FLDIGI RIG CONTROL (Hamlib tab)
  Rig:        Yaesu FT-1000MP
  Device:     COMx / /dev/ttyUSB0
  Baud:       4800
  Stop bits:  2

FLDIGI HARDWARE PTT
  Use serial port PTT:  Checked
  Device:               COMx (same as CAT)
  Use RTS:              Checked
  RTS = +V:             Checked

FLDIGI AUDIO (Soundcard > Devices)
  Capture:    USB Audio Device (Digirig)
  Playback:   USB Audio Device (Digirig)

JS8CALL RADIO TAB
  Rig:        Yaesu FT-1000MP
  Serial:     COMx / /dev/ttyUSB0
  Baud:       4800
  Data Bits:  Default (8)
  Stop Bits:  2
  Handshake:  None
  PTT:        RTS (same port)
  TX Delay:   0.2s
  Split:      Fake It

JS8CALL AUDIO TAB
  Input:      USB Audio Device (Digirig)
  Output:     USB Audio Device (Digirig)
  Notify:     Built-in speakers (NOT Digirig)

VARA HF (Settings > SoundCard)
  Device Input:   Microphone (USB Audio Device) [Digirig]
  Device Output:  Speakers (USB Audio Device) [Digirig]

VARA HF (Settings > PTT)
  PTT:        COM
  Port:       COMx (Digirig CP210x)
  PTT Pin:    RTS

WINLINK EXPRESS (Radio Setup)
  Radio Model:       Yaesu FT-1000MP Mk V
  Radio Control Port: COMx (Digirig CP210x)
  Baud Rate:         4800
  Enable RTS:        Unchecked
  Enable DTR:        Unchecked

PAT WINLINK (Linux)
  Hamlib rig model:  1024 (FT-1000MP)
  Serial address:    /dev/ttyUSB0

FLRIG (Config > Setup > Transceiver)
  Rig:        Yaesu FT-1000MP (or FT-1000MP-A for Mark V)
  Serial:     COMx / /dev/ttyUSB0
  Baud:       4800
  Stop Bits:  2
  PTT:        CAT (or RTS)
  XMLRPC:     localhost:12345 (automatic)

WSJT-X VIA FLRIG
  Rig:        FLRig FLRig
  PTT:        CAT
  (no serial port config needed)

FLDIGI VIA FLRIG
  Configure > Rig Control > flrig tab
  Use flrig:  Checked
  (disable Hamlib and RigCAT)

JS8CALL VIA FLRIG
  Rig:        FLRig FLRig
  PTT:        CAT
  (no serial port config needed)

RIGCTLD (command line)
  Start:      rigctld -m 1024 -r /dev/ttyUSB0 -s 4800 -C stop_bits=2,rts_state=OFF
  Windows:    rigctld -m 1024 -r COM3 -s 4800 -C stop_bits=2,rts_state=OFF
  TCP port:   4532 (default)
  Mark V:     Use -m 1004 instead of -m 1024

WSJT-X VIA RIGCTLD
  Rig:        Hamlib NET rigctl
  Network:    127.0.0.1:4532
  PTT:        CAT
  (no serial port config needed)

FLDIGI VIA RIGCTLD
  Rig:        Hamlib NET rigctl
  Device:     127.0.0.1:4532
  (disable RigCAT and hardware PTT)

JS8CALL VIA RIGCTLD
  Rig:        Hamlib NET rigctl
  Network:    127.0.0.1:4532
  PTT:        CAT
  (no serial port config needed)

GRIDTRACKER (Settings > General)
  IP:         127.0.0.1
  Port:       2237 (must match WSJT-X UDP port)
  WSJT-X:     Settings > Reporting > Accept UDP requests
              UDP Server = 127.0.0.1 port 2237
              Prompt me to log QSO = Checked
              Clear DX call and grid = Checked

JTALERT (Windows only)
  Prereq:     .NET 8 Desktop Runtime
  WSJT-X:     Settings > Reporting > Accept UDP requests
              UDP Server = 127.0.0.1 port 2237
  Multicast:  Use 224.0.0.1 if also running GridTracker
  Auto-reads WSJT-X config on startup (no manual port config)

VARAC (Settings > RIG control & VARA Configuration)
  PTT Method:     CAT
  COM Port:       COMx (Digirig CP210x)
  Baud:           4800
  Data Bits:      8
  Stop Bits:      2 (critical!)
  Parity:         None
  CmdType:        HEX
  PTTOn:          000000010F
  PTTOff:         000000000F
  Freq Control:   CAT (same port)
  VARA path:      C:\VARA\VARA.exe
  VARA port:      8300

AUDIO LEVELS (all applications)
  OS Recording:   Start at 20%, adjust to stay below red
  OS Playback:    ~80%
  WSJT-X Pwr:     25-50%, adjust for zero ALC
  JS8Call Pwr:     25-50%, adjust for zero ALC
  Fldigi TX:      ~50%, adjust for zero ALC
  MIC GAIN:       ~10 o'clock
```

---

## References

### Digirig
- [Digirig Forum: Getting Started with FT-1000MP](https://forum.digirig.net/t/getting-started-with-yaesu-ft-1000mp/5723)
- [Digirig Forum: Cables for FT-1000/FT-2000](https://forum.digirig.net/t/cables-for-yaesu-ft-1000-yaesu-ft-2000/502)
- [Digirig: Setting Audio Levels for Digital Modes](https://digirig.net/setting-audio-levels-for-digital-modes/)
- [Digirig: Getting Started with Digirig Mobile](https://digirig.net/getting-started-with-digirig-mobile/)
- [Digirig: Understanding Rig Control Options](https://digirig.net/understanding-rig-control-options/)

### Radio
- [S53RM: FT-1000MP PACKET Connector Setup for WSJT](https://lea.hamradio.si/~s53rm/FT-1000MP%20WSJT.htm)
- [TigerTronics: FT-1000MP Setup](https://tigertronics.com/ft1000mp.htm)
- [MicroHam: FT-1000MP Transceiver Settings](https://www.microham.com/contents/en-us/d151.html)
- [N1EU: FT-1000MP Setup Page](https://www.qsl.net/n1eu/Yaesu/MPsetup.htm)
- [FT-1000MP Operating Manual (PDF)](http://www.foxtango.org/ft-library/FT-Library/nineties/FT-1000MP%20Operating%20Manual.pdf)

### Software & Utilities
- [SuperControl: FT-1000MP Clone & CAT Software](https://www.supercontrol.de/cat/us/featuresft1000mp.php)
- [WSJT-X User Guide](https://wsjt.sourceforge.io/wsjtx-doc/wsjtx-main-2.6.1.html)
- [JS8Call Website](http://js8call.com/)
- [JS8Call Signal ID Wiki (Frequencies & Specs)](https://www.sigidwiki.com/wiki/JS8)
- [JS8Call Overview Presentation (CRHRC)](https://technet.crhrc.org/wp-content/uploads/2025/03/JS8Call-CRHRC-Presentation.pdf)
- [Fldigi Users Manual: Rig Control Configuration](http://www.w1hkj.com/FldigiHelp/rig_config_page.html)
- [Fldigi Beginners' Guide](http://www.w1hkj.com/beginners.html)
- [Fldigi XML Rig Definitions (FT-1000MP)](https://sourceforge.net/projects/fldigi/files/xmls/yaesu/)
- [Hamlib Supported Radios](https://github.com/Hamlib/Hamlib/wiki/Supported-Radios)

### flrig
- [flrig Website & Downloads](http://www.w1hkj.com/files/flrig/)
- [flrig Help / User Guide](http://www.w1hkj.com/flrig-help/)
- [flrig with WSJT-X Integration](http://www.w1hkj.com/flrig-help/flrig_with_wsjt-x.html)
- [flrig Source Code (SourceForge)](https://sourceforge.net/projects/fldigi/files/flrig/)

### GridTracker
- [GridTracker Website & Downloads](https://gridtracker.org/)
- [GridTracker Documentation](https://docs.gridtracker.org/)
- [Getting Started with GridTracker](https://docs.gridtracker.org/latest/Getting-Started.html)
- [Configuring WSJT-X for GridTracker (Appendix B)](https://docs.gridtracker.org/latest/Appendices/Appendix-B-Configuring-WSJT-X-and-JTDX-for-GridTracker.html)
- [GridTracker Source Code (GitLab)](https://gitlab.com/gridtracker.org/gridtracker2)

### JTAlert
- [JTAlert Website & Download](https://hamapps.com/)
- [JTAlert Voiced Alert Sound Files](https://hamapps.com/Sounds/)
- [HamApps Support Group](https://hamapps.groups.io/g/Support/)
- [W6AER: Using JTAlert with WSJT-X](https://w6aer.com/using_jtalert_with_wsjt-x/)
- [K0PIR: WSJT-X JTAlert Setup Guide](https://k0pir.us/wsjt-x-jt-alert/)
- [DXLab Suite: Getting Started with JTAlert](https://www.dxlabsuite.com/dxlabwiki/GettingStartedwithK1JTModesWithJTAlert)

### Hamlib / rigctld
- [Hamlib Project (GitHub)](https://github.com/Hamlib/Hamlib)
- [Hamlib Releases & Downloads](https://github.com/Hamlib/Hamlib/releases)
- [rigctld Man Page](https://hamlib.sourceforge.net/html/rigctld.1.html)
- [rigctl Man Page](https://hamlib.sourceforge.net/html/rigctl.1.html)
- [Hamlib Supported Radios Wiki](https://github.com/Hamlib/Hamlib/wiki/Supported-Radios)
- [Hamlib FAQ](https://github.com/Hamlib/Hamlib/wiki/FAQ)
- [DrGerg: Hamlib, Log4OM2, Fldigi, JS8Call & WSJT-X Together](https://www.drgerg.com/hamlib-et-al.html)

### VarAC
- [VarAC Website & Download](https://www.varac-hamradio.com/)
- [VarAC Quick Start Guide](https://www.varac-hamradio.com/forum/manuals-troubleshooting/varac-quick-start-guide)
- [VarAC CAT Command File & Customization Guide](https://www.varac-hamradio.com/forum/manuals-troubleshooting/rig-control-cat-command-file-cat-customization-guide)
- [VarAC with FT-1000MP Mark V (Forum)](https://www.varac-hamradio.com/forum/varac-hf-discussion-forum/varac-and-yaesu-ft-1000mp-mark-v-no-ptt-or-cat)
- [VarAC Installation and Configuration (K0PIR)](https://k0pir.us/varac-installation-and-configuration-with-vara-hf/)

### Winlink
- [Winlink Express Download](https://downloads.winlink.org/User%20Programs/)
- [Winlink Quick Start Guide](https://winlink.org/content/quick_start_amateur_radio_and_shares_stations)
- [VARA HF Modem](https://rosmodem.wordpress.com/)
- [Winlink and VARA on Linux/Mac](https://winlink.org/content/winlink_express_and_vara_linux_mac_updated_instructions)
- [Pat Winlink Client](https://getpat.io/)
- [ARDOP Open-Source Modem](https://github.com/pflarue/ardop)
- [N1CLC: Winlink Email Using VARA HF](https://www.n1clc.com/2022/06/winlink-email-using-vara-hf.html)
- [DELCO ARES: Winlink with VARA and Digirig Troubleshooting](https://www.delcoares.org/training/delco-ares-training/other-skills/using-winlink/winlink-with-vara-fm-and-digirig-troubleshooting-guide)
