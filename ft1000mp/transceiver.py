"""High-level FT-1000MP transceiver control.

Composes the SerialPort transport with the protocol command builders
to provide a clean Python API for controlling the radio.

Status-update response layout (16 bytes per VFO, from Hamlib):
  Byte  0     : displayed-status flags
  Bytes 1-4   : frequency  (big-endian binary, *10/16 scaling)
  Bytes 5-6   : clarifier offset (sign-magnitude, *10/16 scaling)
  Byte  7     : mode (bits 0-2)
  Byte  8     : IF-filter / extended-mode (bit 7 = sub-mode qualifier)
  Byte  9     : MEM/RIT/XIT status
  Bytes 10-15 : additional data
"""

from dataclasses import dataclass
from .bcd import bytes_to_freq
from .exceptions import InvalidFrequencyError, InvalidModeError
from .protocol import (
    MODE_BY_NAME,
    MODE_NAMES,
    SUB_MODE_NAMES,
    Mode,
    StatusFlag,
    VFO,
    cmd_clarifier,
    cmd_clarifier_offset,
    cmd_memory_to_vfo,
    cmd_ptt,
    cmd_read_flags,
    cmd_recall_memory,
    cmd_select_vfo,
    cmd_set_freq_a,
    cmd_set_freq_b,
    cmd_set_mode,
    cmd_split,
    cmd_status_update,
    cmd_vfo_a_to_b,
    cmd_vfo_to_memory,
)
from .serial_port import SerialPort

# Frequency limits for the FT-1000MP
FREQ_MIN_HZ = 100_000       # 100 kHz
FREQ_MAX_HZ = 30_000_000    # 30 MHz — original FT-1000MP and Mark V


@dataclass
class VFOStatus:
    """Parsed VFO status from a 16-byte status update response."""
    frequency_hz: int
    mode: int
    mode_name: str
    clarifier_offset: int
    rit: bool
    xit: bool


@dataclass
class RadioFlags:
    """Parsed status flags from a 5-byte flag response."""
    split: bool
    clarifier: bool
    vfo_b_selected: bool
    transmitting: bool
    priority: bool
    raw: int


def _parse_vfo_block(data: bytes) -> VFOStatus:
    """Parse a single 16-byte VFO status block."""
    # Frequency: bytes 1-4, big-endian binary, *10/16 scaling
    freq_hz = bytes_to_freq(data[1:5])

    # Clarifier offset: bytes 5-6, sign-magnitude, *10/16 scaling
    clar_raw = (data[5] << 8) | data[6]
    if data[5] & 0x80:
        clar_raw = -(((~clar_raw + 1) & 0x7FFF))
    clar_hz = clar_raw * 10 // 16

    # Mode: byte 7, lower 3 bits
    mode_val = data[7] & 0x07

    # Sub-mode qualifier: byte 8 bit 7
    sub_mode_bit = bool(data[8] & 0x80)
    mode_name = SUB_MODE_NAMES.get(
        (mode_val, sub_mode_bit),
        MODE_NAMES.get(mode_val, f"UNKNOWN(0x{mode_val:02X})"),
    )

    # RIT/XIT: byte 9
    xit = bool(data[9] & 0x01)
    rit = bool(data[9] & 0x02)

    return VFOStatus(
        frequency_hz=freq_hz,
        mode=mode_val,
        mode_name=mode_name,
        clarifier_offset=clar_hz,
        rit=rit,
        xit=xit,
    )


class FT1000MP:
    """High-level interface to the Yaesu FT-1000MP transceiver."""

    def __init__(self, port: str = "/dev/ttyUSB0"):
        self._serial = SerialPort(port=port)

    # -- context manager ---------------------------------------------------

    def __enter__(self):
        self._serial.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._serial.close()

    def open(self):
        self._serial.open()

    def close(self):
        self._serial.close()

    # -- validation helpers ------------------------------------------------

    @staticmethod
    def _validate_freq(freq_hz: int):
        if not (FREQ_MIN_HZ <= freq_hz <= FREQ_MAX_HZ):
            raise InvalidFrequencyError(
                f"Frequency {freq_hz} Hz is outside "
                f"{FREQ_MIN_HZ}-{FREQ_MAX_HZ} Hz range"
            )

    @staticmethod
    def _validate_mode(mode_name: str) -> int:
        key = mode_name.upper()
        if key not in MODE_BY_NAME:
            raise InvalidModeError(
                f"Unknown mode '{mode_name}'. "
                f"Valid modes: {', '.join(sorted(MODE_BY_NAME.keys()))}"
            )
        return MODE_BY_NAME[key]

    # -- frequency ---------------------------------------------------------

    def set_frequency_a(self, freq_hz: int):
        """Set VFO-A frequency in Hz."""
        self._validate_freq(freq_hz)
        self._serial.send_command(cmd_set_freq_a(freq_hz))

    def set_frequency_b(self, freq_hz: int):
        """Set VFO-B frequency in Hz."""
        self._validate_freq(freq_hz)
        self._serial.send_command(cmd_set_freq_b(freq_hz))

    # -- mode --------------------------------------------------------------

    def set_mode(self, mode_name: str, vfo_b: bool = False):
        """Set operating mode by name (e.g. 'USB', 'CW', 'LSB')."""
        mode_val = self._validate_mode(mode_name)
        self._serial.send_command(cmd_set_mode(mode_val, vfo_b=vfo_b))

    # -- VFO ---------------------------------------------------------------

    def select_vfo(self, vfo: str):
        """Select VFO A or B. Accepts 'a'/'A' or 'b'/'B'.

        Note: the 32-byte status response (target 0x03) returns
        (active_vfo, inactive_vfo) after switching, not always (A, B).
        The ``read_flags().vfo_b_selected`` flag is unreliable.
        """
        vfo_val = VFO.A if vfo.upper() == "A" else VFO.B
        self._serial.send_command(cmd_select_vfo(vfo_val))

    def copy_vfo_a_to_b(self):
        """Copy VFO-A settings to VFO-B."""
        self._serial.send_command(cmd_vfo_a_to_b())

    # -- split -------------------------------------------------------------

    def set_split(self, on: bool):
        self._serial.send_command(cmd_split(on))

    # -- clarifier ---------------------------------------------------------

    def set_clarifier(self, on: bool):
        self._serial.send_command(cmd_clarifier(on))

    def set_clarifier_offset(self, offset_hz: int):
        self._serial.send_command(cmd_clarifier_offset(offset_hz))

    # -- PTT ---------------------------------------------------------------

    def set_ptt(self, on: bool):
        self._serial.send_command(cmd_ptt(on))

    # -- memory ------------------------------------------------------------

    def recall_memory(self, channel: int):
        """Select a memory channel (1-99).

        This switches the radio into memory mode and sets the channel pointer.
        """
        if not (1 <= channel <= 99):
            raise ValueError(f"Channel must be 1-99, got {channel}")
        self._serial.send_command(cmd_recall_memory(channel))

    def vfo_to_memory(self, channel: int):
        """Store current VFO to a memory channel (1-99).

        Call recall_memory(channel) first to select the target channel,
        then this command to write the VFO data into it.
        """
        if not (1 <= channel <= 99):
            raise ValueError(f"Channel must be 1-99, got {channel}")
        self._serial.send_command(cmd_vfo_to_memory(channel))

    def memory_to_vfo(self, channel: int):
        """Transfer a memory channel to VFO (1-99).

        Call recall_memory(channel) first to select the source channel,
        then this command to copy its contents into the active VFO.
        """
        if not (1 <= channel <= 99):
            raise ValueError(f"Channel must be 1-99, got {channel}")
        self._serial.send_command(cmd_memory_to_vfo(channel))

    # -- status queries ----------------------------------------------------

    def get_vfo_status(self, target: int = 0x02) -> VFOStatus:
        """Read current VFO status (16-byte response).

        target: 0x02 = current operating data (default).
        """
        data = self._serial.send_command(cmd_status_update(target), 16)
        return _parse_vfo_block(data)

    def get_both_vfo_status(self) -> tuple[VFOStatus, VFOStatus]:
        """Read both VFO statuses (32-byte response).

        Returns (active_vfo_status, inactive_vfo_status).  The radio
        always puts the currently selected VFO first, so after
        ``select_vfo('B')`` the first element holds VFO-B's data.
        """
        data = self._serial.send_command(cmd_status_update(0x03), 32)
        return _parse_vfo_block(data[0:16]), _parse_vfo_block(data[16:32])

    def read_flags(self) -> RadioFlags:
        """Read the 5-byte status flags.

        NOTE: The ``clarifier`` field from this response is unreliable.
        The 5-byte flags response (opcode 0xFA) does not consistently
        report clarifier state.  To check whether the clarifier (RIT) is
        enabled, use ``get_vfo_status().rit`` instead.
        """
        data = self._serial.send_command(cmd_read_flags(), 5)
        flags = data[0]
        return RadioFlags(
            split=bool(flags & StatusFlag.SPLIT),
            clarifier=bool(flags & StatusFlag.CLARIFIER),
            vfo_b_selected=bool(flags & StatusFlag.VFO_B),
            transmitting=bool(flags & StatusFlag.TRANSMITTING),
            priority=bool(flags & StatusFlag.PRIORITY),
            raw=flags,
        )
