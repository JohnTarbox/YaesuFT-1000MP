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
    """Set operating mode. Add 0x80 to the mode byte to target VFO-B."""
    mode_byte = mode | 0x80 if vfo_b else mode
    return _cmd(p4=mode_byte, opcode=Opcode.SET_MODE)


def cmd_select_vfo(vfo: int) -> bytes:
    return _cmd(p4=vfo, opcode=Opcode.SELECT_VFO)


def cmd_split(on: bool) -> bytes:
    return _cmd(p4=0x01 if on else 0x00, opcode=Opcode.SPLIT)


def cmd_clarifier(on: bool) -> bytes:
    """Turn clarifier on or off."""
    return _cmd(p4=0x01 if on else 0x00, opcode=Opcode.CLARIFIER)


def cmd_clarifier_offset(offset_hz: int) -> bytes:
    """Set clarifier offset. Offset is a signed value in Hz.

    The offset is encoded as a 2-byte signed big-endian value in P1-P2,
    with P3 indicating direction (0x00 = positive, 0xFF = negative).
    """
    if offset_hz >= 0:
        p3 = 0x00
        val = offset_hz & 0xFFFF
    else:
        p3 = 0xFF
        val = (-offset_hz) & 0xFFFF
    p1 = (val >> 8) & 0xFF
    p2 = val & 0xFF
    return bytes([p1, p2, p3, 0x00, Opcode.CLARIFIER])


def cmd_ptt(on: bool) -> bytes:
    return _cmd(p4=0x01 if on else 0x00, opcode=Opcode.PTT)


def cmd_status_update(target: int = 0x02) -> bytes:
    """Request status update. target: 0x02=current, 0x03=VFO-A+B (32 bytes)."""
    return _cmd(p4=target, opcode=Opcode.STATUS_UPDATE)


def cmd_read_flags() -> bytes:
    return _cmd(opcode=Opcode.READ_FLAGS)


def cmd_recall_memory(channel: int) -> bytes:
    return _cmd(p1=channel, opcode=Opcode.RECALL_MEMORY)


def cmd_vfo_to_memory() -> bytes:
    return _cmd(opcode=Opcode.VFO_TO_MEMORY)


def cmd_memory_to_vfo() -> bytes:
    return _cmd(opcode=Opcode.MEMORY_TO_VFO)


def cmd_vfo_a_to_b() -> bytes:
    return _cmd(opcode=Opcode.COPY_VFO_A_TO_B)


def cmd_pacing(interval: int = 0) -> bytes:
    return _cmd(p4=interval, opcode=Opcode.PACING)
