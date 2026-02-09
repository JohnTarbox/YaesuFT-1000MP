# Digital Modes Setup Guide: Yaesu FT-1000MP with Digirig Mobile

Complete guide for configuring WSJT-X and Fldigi for digital modes on the Yaesu
FT-1000MP using a Digirig Mobile interface connected to the rear panel PACKET
connector.

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
11. [Audio Level Calibration](#audio-level-calibration)
12. [Testing the Setup](#testing-the-setup)
13. [Operating Tips](#operating-tips)
14. [Troubleshooting](#troubleshooting)

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

| Parameter                 | Display    | Value     | Notes                       |
|---------------------------|------------|-----------|-----------------------------|
| Mode                      | nodE       | PAc-Lo    | Packet Low mode             |
| Display Offset            | dSP-oFSt   | 0.000     |                             |
| RX PLL                    | r-PLL      | 1.500     |                             |
| RX Carrier                | r-cAr      | 453.500   |                             |
| TX PLL                    | t-PLL      | 1.500     |                             |
| TX Carrier                | t-cAr      | 453.500   |                             |
| RTTY Shift                | rttY-SFt   | 0.000     |                             |
| Easy Set                  | EASY-SEt   | oFF       | Must be OFF for manual vals |

> **Alternative (simple method):** Instead of entering values manually, you can
> set Easy Set to **PS31-U** which pre-loads USB-compatible values. Then set
> Easy Set back to **oFF** to lock them in.

> **Note for early-production FT-1000MP (non-Mark-V):** Some early units do not
> allow TX Carrier below 456.300. If this affects you, use the alternative
> values: dSP-oFSt=+2125, r-PLL=+2210, r-cAr=452.790, t-PLL=+2210,
> t-cAr=452.790.

### Menu 6-1: RTTY Polarity

| Parameter      | Value      | Notes                              |
|----------------|------------|------------------------------------|
| RTTY Polarity  | reversed   | Required for correct AFSK decoding |

### Menu 3-0: Frequency Display (Optional)

| Parameter      | Value      | Notes                                   |
|----------------|------------|-----------------------------------------|
| F-diSPly       | cArriEr    | Shows actual carrier (recommended)      |

### Activating USER Mode

After configuring menu 8-6, exit the menu and:

1. Press and **hold** the **PKT** button for approximately 2 seconds.
2. The display should show **PKT** with the **LSB** indicator lit.
3. This is now operating in USB internally despite the LSB indicator.

> Do **not** short-press PKT (that selects standard packet mode, not USER mode).

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
| PTT Method       | **RTS**                            |
| Port             | COM port of CP210x **(same port)** |

> PTT is handled through the DIN-5 PACKET connector (pin 3). The Digirig routes
> the RTS signal from its serial port to the PTT line on the TRRS audio cable.
> If WSJT-X offers a separate PTT port, use the same COM port as CAT.

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
2. Ensure the radio is in **PKT USER** mode (hold PKT button).
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

- WSJT-X, JS8Call, and Fldigi all handle modulation/demodulation in software.
- The radio just needs to be in **PKT USER** mode (which provides USB passthrough).
- Do **not** change the radio's mode while WSJT-X is running.

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

1. **PKT USER mode:** Ensure you held the PKT button (not short-pressed). The
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

---

## Quick Reference Card

```
RADIO SETTINGS
  Menu 8-6:  PAc-Lo / 0 / 1.500 / 453.500 / 1.500 / 453.500 / 0 / oFF
  Menu 6-1:  RTTY polarity = reversed
  Menu 3-0:  F-diSPly = cArriEr  (optional)
  Activate:  Hold PKT button 2 seconds (USER mode)
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
  PTT:        RTS (same port)
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

### Software
- [WSJT-X User Guide](https://wsjt.sourceforge.io/wsjtx-doc/wsjtx-main-2.6.1.html)
- [JS8Call Website](http://js8call.com/)
- [JS8Call Signal ID Wiki (Frequencies & Specs)](https://www.sigidwiki.com/wiki/JS8)
- [JS8Call Overview Presentation (CRHRC)](https://technet.crhrc.org/wp-content/uploads/2025/03/JS8Call-CRHRC-Presentation.pdf)
- [Fldigi Users Manual: Rig Control Configuration](http://www.w1hkj.com/FldigiHelp/rig_config_page.html)
- [Fldigi Beginners' Guide](http://www.w1hkj.com/beginners.html)
- [Fldigi XML Rig Definitions (FT-1000MP)](https://sourceforge.net/projects/fldigi/files/xmls/yaesu/)
- [Hamlib Supported Radios](https://github.com/Hamlib/Hamlib/wiki/Supported-Radios)
