"""Opcodes, enums, and 5-byte command builders for the FT-1000MP CAT protocol.

Every CAT command is exactly 5 bytes: [P1][P2][P3][P4][OpCode].

Frequency encoding uses big-endian binary with *16/10 scaling (NOT packed BCD).
"""

from enum import IntEnum

from .bcd import freq_to_bytes


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class Opcode(IntEnum):
    SPLIT = 0x01
    RECALL_MEMORY = 0x02
    VFO_TO_MEMORY = 0x03
    SELECT_VFO = 0x05
    MEMORY_TO_VFO = 0x06
    CLARIFIER = 0x09
    SET_FREQ_A = 0x0A
    SET_MODE = 0x0C
    PACING = 0x0E
    PTT = 0x0F
    STATUS_UPDATE = 0x10
    COPY_VFO_A_TO_B = 0x85
    SET_FREQ_B = 0x8A
    READ_FLAGS = 0xFA


class Mode(IntEnum):
    """Operating-mode values as they appear on the wire (byte 7, bits 0-2)."""
    LSB = 0x00
    USB = 0x01
    CW = 0x02
    AM = 0x03
    FM = 0x04
    RTTY = 0x05
    PKT = 0x06


class VFO(IntEnum):
    A = 0x00
    B = 0x01


# ---------------------------------------------------------------------------
# Status-flag bitmask constants (byte 0 of status response, or byte 0 of
# the 5-byte flag response from opcode 0xFA)
# ---------------------------------------------------------------------------

class StatusFlag:
    SPLIT = 0x01
    CLARIFIER = 0x04
    VFO_B = 0x10
    TRANSMITTING = 0x20
    PRIORITY = 0x80


# ---------------------------------------------------------------------------
# Mode lookup tables
# ---------------------------------------------------------------------------

MODE_NAMES: dict[int, str] = {
    Mode.LSB: "LSB",
    Mode.USB: "USB",
    Mode.CW: "CW",
    Mode.AM: "AM",
    Mode.FM: "FM",
    Mode.RTTY: "RTTY",
    Mode.PKT: "PKT",
}

MODE_BY_NAME: dict[str, int] = {v: k for k, v in MODE_NAMES.items()}

# SET_MODE command byte values (differ from status-response mode values).
# From Hamlib ncmd[] array in ft1000mp.c.
SET_MODE_VALUES: dict[int, int] = {
    Mode.LSB:  0x00,
    Mode.USB:  0x01,
    Mode.CW:   0x02,
    Mode.AM:   0x04,
    Mode.FM:   0x06,
    Mode.RTTY: 0x08,
    Mode.PKT:  0x0A,
}

# Sub-mode display names (qualified by IF-filter byte 8 bit 7)
SUB_MODE_NAMES: dict[tuple[int, bool], str] = {
    (Mode.CW, False): "CW-R",
    (Mode.CW, True): "CW",
    (Mode.AM, False): "AM",
    (Mode.AM, True): "SAM",
    (Mode.RTTY, False): "RTTY",
    (Mode.RTTY, True): "RTTY-R",
    (Mode.PKT, False): "PKT-L",
    (Mode.PKT, True): "PKT-FM",
}


# ---------------------------------------------------------------------------
# Command builders — each returns exactly 5 bytes
# ---------------------------------------------------------------------------

def _cmd(p1: int = 0, p2: int = 0, p3: int = 0, p4: int = 0,
         opcode: int = 0) -> bytes:
    return bytes([p1, p2, p3, p4, opcode])


def cmd_set_freq_a(freq_hz: int) -> bytes:
    raw = freq_to_bytes(freq_hz)
    return bytes([*raw, Opcode.SET_FREQ_A])


def cmd_set_freq_b(freq_hz: int) -> bytes:
    raw = freq_to_bytes(freq_hz)
    return bytes([*raw, Opcode.SET_FREQ_B])


def cmd_set_mode(mode: int, vfo_b: bool = False) -> bytes:
    """Set operating mode.

    The SET_MODE command uses different byte values than the status-response
    mode encoding. Add 0x80 to the SET byte to target VFO-B.
    """
    set_byte = SET_MODE_VALUES[mode]
    if vfo_b:
        set_byte |= 0x80
    return _cmd(p4=set_byte, opcode=Opcode.SET_MODE)


def cmd_select_vfo(vfo: int) -> bytes:
    """Select VFO A or B.

    WARNING: Hamlib disables this command (``#if 0``) noting that switching
    VFOs this way "changes the frequencies in the response".  Use
    cmd_set_freq_a / cmd_set_freq_b and cmd_set_mode with vfo_b=True to
    control VFO-A/B independently instead.
    """
    return _cmd(p4=vfo, opcode=Opcode.SELECT_VFO)


def cmd_split(on: bool) -> bytes:
    return _cmd(p4=0x01 if on else 0x00, opcode=Opcode.SPLIT)


def cmd_clarifier(on: bool) -> bytes:
    """Turn clarifier on or off."""
    return _cmd(p4=0x01 if on else 0x00, opcode=Opcode.CLARIFIER)


def cmd_clarifier_offset(offset_hz: int) -> bytes:
    """Set clarifier offset. Offset is a signed value in Hz.

    Encoding follows Hamlib ft1000mp.c:
      P1 = BCD of (abs(offset) % 1000) / 10   (tens-of-Hz component)
      P2 = BCD of abs(offset) / 1000           (kHz component)
      P3 = direction: 0x00 = positive, 0xFF = negative
      P4 = 0xFF  (distinguishes offset-set from clarifier on/off)
    """
    if offset_hz < 0:
        direction = 0xFF
        offset_hz = -offset_hz
    else:
        direction = 0x00
    tens = (offset_hz % 1000) // 10  # 10-Hz digit pairs
    khz = offset_hz // 1000
    p1 = ((tens // 10) << 4) | (tens % 10)  # BCD
    p2 = ((khz // 10) << 4) | (khz % 10)    # BCD
    return bytes([p1, p2, direction, 0xFF, Opcode.CLARIFIER])


def cmd_ptt(on: bool) -> bytes:
    return _cmd(p4=0x01 if on else 0x00, opcode=Opcode.PTT)


def cmd_status_update(target: int = 0x02) -> bytes:
    """Request status update. target: 0x02=current, 0x03=VFO-A+B (32 bytes)."""
    return _cmd(p4=target, opcode=Opcode.STATUS_UPDATE)


def cmd_read_flags() -> bytes:
    return _cmd(opcode=Opcode.READ_FLAGS)


def cmd_recall_memory(channel: int) -> bytes:
    """Recall memory channel. Channel goes in P4 (byte 3) per Hamlib."""
    return _cmd(p4=channel, opcode=Opcode.RECALL_MEMORY)


def cmd_vfo_to_memory(channel: int) -> bytes:
    """Store current VFO to a memory channel.

    Channel goes in P4 (byte 3), matching the Hamlib FT-990/FT-1000D
    vfo_op(RIG_OP_FROM_VFO) implementation.  Call cmd_recall_memory(channel)
    first to select the target channel on the radio.
    """
    return _cmd(p4=channel, opcode=Opcode.VFO_TO_MEMORY)


def cmd_memory_to_vfo(channel: int) -> bytes:
    """Transfer a memory channel to VFO.

    Channel goes in P4 (byte 3), matching the Hamlib FT-990/FT-1000D
    vfo_op(RIG_OP_TO_VFO) implementation.  Call cmd_recall_memory(channel)
    first to select the source channel on the radio.
    """
    return _cmd(p4=channel, opcode=Opcode.MEMORY_TO_VFO)


def cmd_vfo_a_to_b() -> bytes:
    return _cmd(opcode=Opcode.COPY_VFO_A_TO_B)


def cmd_pacing(interval: int = 0) -> bytes:
    return _cmd(p4=interval, opcode=Opcode.PACING)
