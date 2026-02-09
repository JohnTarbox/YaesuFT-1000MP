"""Comprehensive test suite for FT-1000MP CAT control library.

Unit tests run without hardware. Live integration tests (marked @pytest.mark.live)
require a radio connected via serial. Set FT1000MP_PORT to override
the default serial port.

Run all tests:       pytest tests/ -v
Unit tests only:     pytest tests/ -v -m "not live"
Live tests only:     pytest tests/ -v -m live
"""

import os
import time

import pytest

from ft1000mp.bcd import bytes_to_freq, freq_to_bytes
from ft1000mp.exceptions import (
    InvalidFrequencyError,
    InvalidModeError,
    SerialConnectionError,
)
from ft1000mp.protocol import (
    MODE_BY_NAME,
    MODE_NAMES,
    SUB_MODE_NAMES,
    Mode,
    Opcode,
    StatusFlag,
    VFO,
    cmd_clarifier,
    cmd_clarifier_offset,
    cmd_memory_to_vfo,
    cmd_pacing,
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
from ft1000mp.serial_port import DEFAULT_PORT, SerialPort
from ft1000mp.transceiver import (
    FREQ_MAX_HZ,
    FREQ_MIN_HZ,
    FT1000MP,
    RadioFlags,
    VFOStatus,
    _parse_vfo_block,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SETTLE_TIME = 1.0  # seconds — radio needs settling between commands


def radio_pause():
    """Wait for the radio to settle between commands."""
    time.sleep(SETTLE_TIME)


def encode_freq_for_status(freq_hz: int) -> bytes:
    """Encode a frequency as it would appear in a status response.

    Status responses use big-endian binary with *16/10 scaling.
    """
    raw = freq_hz * 16 // 10
    return raw.to_bytes(4, "big")


# ===================================================================
# UNIT TESTS — no radio needed
# ===================================================================


class TestFreqToBytes:
    """freq_to_bytes: little-endian packed BCD encoding for SET commands."""

    def test_known_value_14mhz(self):
        """14.195.000 Hz → BCD of 1419500 → little-endian."""
        result = freq_to_bytes(14_195_000)
        # 14195000 / 10 = 1419500
        # digits: 0 1 4 1 9 5 0 0
        # BCD pairs (big-endian): 01 41 95 00
        # little-endian: 00 95 41 01
        assert result == bytes([0x00, 0x95, 0x41, 0x01])

    def test_known_value_7mhz(self):
        """7.074.000 Hz."""
        result = freq_to_bytes(7_074_000)
        # 7074000 / 10 = 707400
        # digits: 0 0 7 0 7 4 0 0
        # BCD pairs (big-endian): 00 70 74 00
        # little-endian: 00 74 70 00
        assert result == bytes([0x00, 0x74, 0x70, 0x00])

    def test_10hz_resolution(self):
        """Frequencies differing by <10 Hz encode identically."""
        assert freq_to_bytes(14_195_005) == freq_to_bytes(14_195_000)

    def test_10hz_step(self):
        """10 Hz step changes the last digit."""
        a = freq_to_bytes(14_195_000)
        b = freq_to_bytes(14_195_010)
        assert a != b

    def test_min_frequency(self):
        """100 kHz encodes without error."""
        result = freq_to_bytes(100_000)
        assert len(result) == 4

    def test_max_frequency(self):
        """60 MHz encodes without error."""
        result = freq_to_bytes(60_000_000)
        assert len(result) == 4

    def test_output_always_4_bytes(self):
        freqs = [100_000, 1_800_000, 7_074_000, 14_195_000, 28_500_000, 50_313_000]
        for f in freqs:
            assert len(freq_to_bytes(f)) == 4


class TestBytesToFreq:
    """bytes_to_freq: big-endian binary *10/16 decoding for status responses."""

    def test_known_value_14mhz(self):
        data = encode_freq_for_status(14_195_000)
        result = bytes_to_freq(data)
        assert abs(result - 14_195_000) <= 10

    def test_known_value_7mhz(self):
        data = encode_freq_for_status(7_074_000)
        result = bytes_to_freq(data)
        assert abs(result - 7_074_000) <= 10

    def test_round_trip_multiple_frequencies(self):
        """Encode then decode should be within ±10 Hz."""
        freqs = [
            100_000, 1_800_000, 3_500_000, 7_074_000,
            14_195_000, 21_300_000, 28_500_000, 50_313_000,
        ]
        for f in freqs:
            data = encode_freq_for_status(f)
            decoded = bytes_to_freq(data)
            assert abs(decoded - f) <= 10, f"Failed for {f}: got {decoded}"

    def test_zero_bytes(self):
        assert bytes_to_freq(b"\x00\x00\x00\x00") == 0

    def test_extracts_first_4_bytes(self):
        """Only uses first 4 bytes even if given more."""
        data = encode_freq_for_status(14_195_000) + b"\xff\xff"
        result = bytes_to_freq(data)
        assert abs(result - 14_195_000) <= 10


class TestCommandBuilders:
    """All cmd_* functions produce exactly 5 bytes with correct opcodes."""

    def test_cmd_set_freq_a_length_and_opcode(self):
        cmd = cmd_set_freq_a(14_195_000)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.SET_FREQ_A

    def test_cmd_set_freq_b_length_and_opcode(self):
        cmd = cmd_set_freq_b(14_195_000)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.SET_FREQ_B

    def test_cmd_set_freq_a_payload_matches_bcd(self):
        freq = 14_195_000
        cmd = cmd_set_freq_a(freq)
        assert cmd[:4] == freq_to_bytes(freq)

    def test_cmd_set_freq_b_payload_matches_bcd(self):
        freq = 7_074_000
        cmd = cmd_set_freq_b(freq)
        assert cmd[:4] == freq_to_bytes(freq)

    def test_cmd_set_mode_vfo_a(self):
        cmd = cmd_set_mode(Mode.USB)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.SET_MODE
        assert cmd[3] == 0x01  # USB SET_MODE byte

    def test_cmd_set_mode_vfo_b(self):
        cmd = cmd_set_mode(Mode.CW, vfo_b=True)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.SET_MODE
        assert cmd[3] == 0x02 | 0x80  # CW SET_MODE byte | VFO-B flag

    def test_cmd_set_mode_am(self):
        """AM SET_MODE byte is 0x04 (not 0x03 like the status value)."""
        cmd = cmd_set_mode(Mode.AM)
        assert cmd[3] == 0x04

    def test_cmd_set_mode_fm(self):
        """FM SET_MODE byte is 0x06 (not 0x04 like the status value)."""
        cmd = cmd_set_mode(Mode.FM)
        assert cmd[3] == 0x06

    def test_cmd_set_mode_rtty(self):
        """RTTY SET_MODE byte is 0x08."""
        cmd = cmd_set_mode(Mode.RTTY)
        assert cmd[3] == 0x08

    def test_cmd_set_mode_pkt(self):
        """PKT SET_MODE byte is 0x0A."""
        cmd = cmd_set_mode(Mode.PKT)
        assert cmd[3] == 0x0A

    def test_cmd_select_vfo_a(self):
        cmd = cmd_select_vfo(VFO.A)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.SELECT_VFO
        assert cmd[3] == 0x00

    def test_cmd_select_vfo_b(self):
        cmd = cmd_select_vfo(VFO.B)
        assert cmd[4] == Opcode.SELECT_VFO
        assert cmd[3] == 0x01

    def test_cmd_split_on(self):
        cmd = cmd_split(True)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.SPLIT
        assert cmd[3] == 0x01

    def test_cmd_split_off(self):
        cmd = cmd_split(False)
        assert cmd[4] == Opcode.SPLIT
        assert cmd[3] == 0x00

    def test_cmd_clarifier_on(self):
        cmd = cmd_clarifier(True)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.CLARIFIER
        assert cmd[3] == 0x01

    def test_cmd_clarifier_off(self):
        cmd = cmd_clarifier(False)
        assert cmd[4] == Opcode.CLARIFIER
        assert cmd[3] == 0x00

    def test_cmd_clarifier_offset_positive(self):
        """500 Hz → P1=0x50 (BCD 50 tens), P2=0x00, P3=0x00, P4=0xFF."""
        cmd = cmd_clarifier_offset(500)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.CLARIFIER
        assert cmd[0] == 0x50  # BCD: 50 tens of Hz
        assert cmd[1] == 0x00  # BCD: 0 kHz
        assert cmd[2] == 0x00  # positive direction
        assert cmd[3] == 0xFF  # offset-set marker

    def test_cmd_clarifier_offset_negative(self):
        """-300 Hz → P1=0x30 (BCD 30 tens), P2=0x00, P3=0xFF, P4=0xFF."""
        cmd = cmd_clarifier_offset(-300)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.CLARIFIER
        assert cmd[0] == 0x30  # BCD: 30 tens of Hz
        assert cmd[1] == 0x00  # BCD: 0 kHz
        assert cmd[2] == 0xFF  # negative direction
        assert cmd[3] == 0xFF  # offset-set marker

    def test_cmd_clarifier_offset_zero(self):
        cmd = cmd_clarifier_offset(0)
        assert cmd[0] == 0x00
        assert cmd[1] == 0x00
        assert cmd[2] == 0x00  # positive direction
        assert cmd[3] == 0xFF  # offset-set marker

    def test_cmd_clarifier_offset_1200(self):
        """1200 Hz → P1=0x20 (BCD 20 tens), P2=0x01 (BCD 1 kHz)."""
        cmd = cmd_clarifier_offset(1200)
        assert cmd[0] == 0x20
        assert cmd[1] == 0x01
        assert cmd[2] == 0x00
        assert cmd[3] == 0xFF

    def test_cmd_ptt_on(self):
        """PTT command builder produces correct bytes (never sent to radio)."""
        cmd = cmd_ptt(True)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.PTT
        assert cmd[3] == 0x01

    def test_cmd_ptt_off(self):
        cmd = cmd_ptt(False)
        assert cmd[4] == Opcode.PTT
        assert cmd[3] == 0x00

    def test_cmd_status_update_current(self):
        cmd = cmd_status_update(0x02)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.STATUS_UPDATE
        assert cmd[3] == 0x02

    def test_cmd_status_update_both(self):
        cmd = cmd_status_update(0x03)
        assert cmd[4] == Opcode.STATUS_UPDATE
        assert cmd[3] == 0x03

    def test_cmd_read_flags(self):
        cmd = cmd_read_flags()
        assert len(cmd) == 5
        assert cmd[4] == Opcode.READ_FLAGS
        assert cmd[:4] == b"\x00\x00\x00\x00"

    def test_cmd_recall_memory(self):
        cmd = cmd_recall_memory(42)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.RECALL_MEMORY
        assert cmd[3] == 42  # channel in P4 (byte 3)
        assert cmd[0] == 0   # P1 should be zero

    def test_cmd_recall_memory_channel_98(self):
        cmd = cmd_recall_memory(98)
        assert cmd[3] == 98

    def test_cmd_vfo_to_memory(self):
        cmd = cmd_vfo_to_memory(42)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.VFO_TO_MEMORY
        assert cmd[3] == 42  # channel in P4
        assert cmd[:3] == b"\x00\x00\x00"

    def test_cmd_memory_to_vfo(self):
        cmd = cmd_memory_to_vfo(42)
        assert len(cmd) == 5
        assert cmd[4] == Opcode.MEMORY_TO_VFO
        assert cmd[3] == 42  # channel in P4
        assert cmd[:3] == b"\x00\x00\x00"

    def test_cmd_vfo_a_to_b(self):
        cmd = cmd_vfo_a_to_b()
        assert len(cmd) == 5
        assert cmd[4] == Opcode.COPY_VFO_A_TO_B

    def test_cmd_pacing_default(self):
        cmd = cmd_pacing()
        assert len(cmd) == 5
        assert cmd[4] == Opcode.PACING
        assert cmd[3] == 0x00

    def test_cmd_pacing_nonzero(self):
        cmd = cmd_pacing(5)
        assert cmd[3] == 5


class TestParseVfoBlock:
    """_parse_vfo_block with synthetic 16-byte blocks."""

    def _make_block(
        self,
        freq_hz=14_195_000,
        mode=Mode.USB,
        sub_mode_bit=False,
        user_mode=False,
        clar_offset=0,
        rit=False,
        xit=False,
    ) -> bytes:
        """Build a synthetic 16-byte VFO status block."""
        block = bytearray(16)
        # Byte 0: status flags (unused in VFO block parsing)
        block[0] = 0x00
        # Bytes 1-4: frequency (big-endian binary, *16/10 scaling)
        freq_raw = freq_hz * 16 // 10
        block[1:5] = freq_raw.to_bytes(4, "big")
        # Bytes 5-6: clarifier offset (sign-magnitude, *16/10 scaling)
        if clar_offset >= 0:
            clar_raw = clar_offset * 16 // 10
            block[5] = (clar_raw >> 8) & 0x7F
            block[6] = clar_raw & 0xFF
        else:
            clar_raw = (-clar_offset) * 16 // 10
            block[5] = ((clar_raw >> 8) & 0x7F) | 0x80
            block[6] = clar_raw & 0xFF
        # Byte 7: mode (lower 3 bits); bit 7 = USER sub-mode
        block[7] = (mode & 0x07) | (0x80 if user_mode else 0x00)
        # Byte 8: IF filter / sub-mode (bit 7 = qualifier)
        block[8] = 0x80 if sub_mode_bit else 0x00
        # Byte 9: RIT/XIT
        block[9] = (0x02 if rit else 0) | (0x01 if xit else 0)
        return bytes(block)

    def test_frequency_decode(self):
        status = _parse_vfo_block(self._make_block(freq_hz=14_195_000))
        assert abs(status.frequency_hz - 14_195_000) <= 10

    def test_frequency_7mhz(self):
        status = _parse_vfo_block(self._make_block(freq_hz=7_074_000))
        assert abs(status.frequency_hz - 7_074_000) <= 10

    def test_mode_lsb(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.LSB))
        assert status.mode == Mode.LSB
        assert status.mode_name == "LSB"

    def test_mode_usb(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.USB))
        assert status.mode == Mode.USB
        assert status.mode_name == "USB"

    def test_mode_cw_normal(self):
        """CW with sub_mode_bit=True → 'CW'."""
        status = _parse_vfo_block(self._make_block(mode=Mode.CW, sub_mode_bit=True))
        assert status.mode == Mode.CW
        assert status.mode_name == "CW"

    def test_mode_cw_reverse(self):
        """CW with sub_mode_bit=False → 'CW-R'."""
        status = _parse_vfo_block(self._make_block(mode=Mode.CW, sub_mode_bit=False))
        assert status.mode_name == "CW-R"

    def test_mode_am(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.AM, sub_mode_bit=False))
        assert status.mode_name == "AM"

    def test_mode_sam(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.AM, sub_mode_bit=True))
        assert status.mode_name == "SAM"

    def test_mode_fm(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.FM))
        assert status.mode == Mode.FM
        assert status.mode_name == "FM"

    def test_mode_rtty(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.RTTY, sub_mode_bit=False))
        assert status.mode_name == "RTTY"

    def test_mode_rtty_reverse(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.RTTY, sub_mode_bit=True))
        assert status.mode_name == "RTTY-R"

    def test_mode_pkt_lsb(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.PKT, sub_mode_bit=False))
        assert status.mode_name == "PKT-L"

    def test_mode_pkt_fm(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.PKT, sub_mode_bit=True))
        assert status.mode_name == "PKT-FM"

    def test_mode_pkt_user(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.PKT, user_mode=True))
        assert status.mode_name == "PKT-USER"
        assert status.user_mode is True

    def test_mode_pkt_user_flag_false_normally(self):
        status = _parse_vfo_block(self._make_block(mode=Mode.PKT, sub_mode_bit=False))
        assert status.user_mode is False

    def test_mode_usb_user_mode_flag(self):
        """USER bit only meaningful for PKT, but should still be parsed."""
        status = _parse_vfo_block(self._make_block(mode=Mode.USB, user_mode=True))
        assert status.user_mode is True
        assert status.mode_name == "USB-USER"

    def test_clarifier_zero(self):
        status = _parse_vfo_block(self._make_block(clar_offset=0))
        assert status.clarifier_offset == 0

    def test_clarifier_positive(self):
        status = _parse_vfo_block(self._make_block(clar_offset=500))
        assert abs(status.clarifier_offset - 500) <= 10

    def test_rit_flag(self):
        status = _parse_vfo_block(self._make_block(rit=True, xit=False))
        assert status.rit is True
        assert status.xit is False

    def test_xit_flag(self):
        status = _parse_vfo_block(self._make_block(rit=False, xit=True))
        assert status.rit is False
        assert status.xit is True

    def test_both_rit_xit(self):
        status = _parse_vfo_block(self._make_block(rit=True, xit=True))
        assert status.rit is True
        assert status.xit is True

    def test_neither_rit_xit(self):
        status = _parse_vfo_block(self._make_block(rit=False, xit=False))
        assert status.rit is False
        assert status.xit is False


class TestValidation:
    """Frequency bounds, mode validation, channel range."""

    def test_freq_too_low(self):
        with pytest.raises(InvalidFrequencyError):
            FT1000MP._validate_freq(99_999)

    def test_freq_too_high(self):
        with pytest.raises(InvalidFrequencyError):
            FT1000MP._validate_freq(30_000_001)

    def test_freq_at_min(self):
        FT1000MP._validate_freq(FREQ_MIN_HZ)  # should not raise

    def test_freq_at_max(self):
        FT1000MP._validate_freq(FREQ_MAX_HZ)  # should not raise

    def test_freq_mid_range(self):
        FT1000MP._validate_freq(14_195_000)  # should not raise

    def test_valid_mode_names(self):
        for name in ["LSB", "USB", "CW", "AM", "FM", "RTTY", "PKT"]:
            result = FT1000MP._validate_mode(name)
            assert result == MODE_BY_NAME[name]

    def test_mode_case_insensitive(self):
        assert FT1000MP._validate_mode("usb") == Mode.USB
        assert FT1000MP._validate_mode("Cw") == Mode.CW

    def test_invalid_mode(self):
        with pytest.raises(InvalidModeError):
            FT1000MP._validate_mode("SSB")

    def test_invalid_mode_empty(self):
        with pytest.raises(InvalidModeError):
            FT1000MP._validate_mode("")

    def test_channel_range_in_recall(self):
        """recall_memory raises ValueError for out-of-range channels."""
        radio = FT1000MP.__new__(FT1000MP)
        with pytest.raises(ValueError):
            radio.recall_memory(0)
        with pytest.raises(ValueError):
            radio.recall_memory(100)


class TestEnumsAndConstants:
    """Verify enums and constants match the FT-1000MP protocol spec."""

    def test_mode_values(self):
        assert Mode.LSB == 0
        assert Mode.USB == 1
        assert Mode.CW == 2
        assert Mode.AM == 3
        assert Mode.FM == 4
        assert Mode.RTTY == 5
        assert Mode.PKT == 6

    def test_vfo_values(self):
        assert VFO.A == 0
        assert VFO.B == 1

    def test_opcode_values(self):
        assert Opcode.SPLIT == 0x01
        assert Opcode.RECALL_MEMORY == 0x02
        assert Opcode.VFO_TO_MEMORY == 0x03
        assert Opcode.SELECT_VFO == 0x05
        assert Opcode.MEMORY_TO_VFO == 0x06
        assert Opcode.CLARIFIER == 0x09
        assert Opcode.SET_FREQ_A == 0x0A
        assert Opcode.SET_MODE == 0x0C
        assert Opcode.PACING == 0x0E
        assert Opcode.PTT == 0x0F
        assert Opcode.STATUS_UPDATE == 0x10
        assert Opcode.COPY_VFO_A_TO_B == 0x85
        assert Opcode.SET_FREQ_B == 0x8A
        assert Opcode.READ_FLAGS == 0xFA

    def test_status_flag_values(self):
        assert StatusFlag.SPLIT == 0x01
        assert StatusFlag.CLARIFIER == 0x04
        assert StatusFlag.VFO_B == 0x10
        assert StatusFlag.TRANSMITTING == 0x20
        assert StatusFlag.PRIORITY == 0x80

    def test_mode_names_complete(self):
        for m in Mode:
            assert m in MODE_NAMES

    def test_mode_by_name_inverse(self):
        for val, name in MODE_NAMES.items():
            assert MODE_BY_NAME[name] == val

    def test_sub_mode_names_keys(self):
        expected_keys = {
            (Mode.CW, False), (Mode.CW, True),
            (Mode.AM, False), (Mode.AM, True),
            (Mode.RTTY, False), (Mode.RTTY, True),
            (Mode.PKT, False), (Mode.PKT, True),
        }
        assert set(SUB_MODE_NAMES.keys()) == expected_keys


class TestErrorHandling:
    """Error handling without a radio connection."""

    def test_serial_not_opened(self):
        sp = SerialPort(port="/dev/null")
        with pytest.raises(SerialConnectionError):
            sp.send_command(b"\x00" * 5, response_length=5)

    def test_invalid_frequency_on_set_a(self):
        radio = FT1000MP.__new__(FT1000MP)
        with pytest.raises(InvalidFrequencyError):
            radio.set_frequency_a(0)

    def test_invalid_frequency_on_set_b(self):
        radio = FT1000MP.__new__(FT1000MP)
        with pytest.raises(InvalidFrequencyError):
            radio.set_frequency_b(999_999_999)

    def test_invalid_mode_on_set_mode(self):
        radio = FT1000MP.__new__(FT1000MP)
        with pytest.raises(InvalidModeError):
            radio.set_mode("INVALID")


# ===================================================================
# LIVE INTEGRATION TESTS — require radio on serial port
# ===================================================================


def _env_bool(name: str) -> "bool | None":
    """Read an env var as a bool: '0'/'false' → False, '1'/'true' → True, unset → None."""
    val = os.environ.get(name)
    if val is None:
        return None
    return val.lower() in ("1", "true")


@pytest.fixture(scope="session")
def radio():
    """Session-scoped fixture: open port once for all live tests."""
    r = FT1000MP(
        port=DEFAULT_PORT,
        rts=_env_bool("FT1000MP_RTS"),
        dtr=_env_bool("FT1000MP_DTR"),
    )
    r.open()
    radio_pause()
    yield r
    r.close()


@pytest.fixture(scope="session", autouse=False)
def saved_state(radio):
    """Capture VFO-A/B state before live tests and restore after."""
    radio_pause()
    flags = radio.read_flags()
    radio_pause()
    vfo_a, vfo_b = radio.get_both_vfo_status()
    radio_pause()

    state = {
        "vfo_a_freq": vfo_a.frequency_hz,
        "vfo_b_freq": vfo_b.frequency_hz,
        "vfo_a_mode": vfo_a.mode_name,
        "vfo_b_mode": vfo_b.mode_name,
        "split": flags.split,
        "clarifier": flags.clarifier,
        "vfo_b_selected": flags.vfo_b_selected,
    }

    yield state

    # --- Restore state ---
    # Select VFO-A first so freq/mode sets target the right VFO
    radio.select_vfo("A")
    radio_pause()
    radio.set_frequency_a(state["vfo_a_freq"])
    radio_pause()
    # Restore VFO-A mode — use base mode name (strip sub-mode qualifiers)
    mode_a = state["vfo_a_mode"]
    if mode_a in MODE_BY_NAME:
        radio.set_mode(mode_a)
    elif mode_a in ("CW-R", "CW"):
        radio.set_mode("CW")
    elif mode_a == "SAM":
        radio.set_mode("AM")
    elif mode_a in ("RTTY-R",):
        radio.set_mode("RTTY")
    elif mode_a in ("PKT-L", "PKT-FM"):
        radio.set_mode("PKT")
    radio_pause()
    radio.set_frequency_b(state["vfo_b_freq"])
    radio_pause()
    # Restore VFO-B mode
    mode_b = state["vfo_b_mode"]
    if mode_b in MODE_BY_NAME:
        radio.set_mode(mode_b, vfo_b=True)
    elif mode_b in ("CW-R", "CW"):
        radio.set_mode("CW", vfo_b=True)
    elif mode_b == "SAM":
        radio.set_mode("AM", vfo_b=True)
    elif mode_b in ("RTTY-R",):
        radio.set_mode("RTTY", vfo_b=True)
    elif mode_b in ("PKT-L", "PKT-FM"):
        radio.set_mode("PKT", vfo_b=True)
    radio_pause()
    radio.set_split(state["split"])
    radio_pause()
    radio.set_clarifier(state["clarifier"])
    radio_pause()
    # NOTE: We intentionally do NOT restore VFO-B selection here.
    # select_vfo() is broken on the FT-1000MP (Hamlib disables it with #if 0)
    # because it corrupts frequency data. Radio is left on VFO-A.


# --- Helper to map sub-mode display names back to base modes ---
_SUB_MODE_TO_BASE = {
    "CW-R": "CW", "CW": "CW",
    "SAM": "AM", "AM": "AM",
    "RTTY": "RTTY", "RTTY-R": "RTTY",
    "PKT-L": "PKT", "PKT-FM": "PKT",
    "LSB": "LSB", "USB": "USB", "FM": "FM",
}


@pytest.mark.live
class TestLiveConnection:
    """Basic connectivity checks."""

    def test_read_flags(self, radio, saved_state):
        flags = radio.read_flags()
        assert isinstance(flags, RadioFlags)

    def test_get_vfo_status(self, radio, saved_state):
        radio_pause()
        status = radio.get_vfo_status()
        assert isinstance(status, VFOStatus)
        assert FREQ_MIN_HZ <= status.frequency_hz <= FREQ_MAX_HZ

    def test_get_both_vfo_status(self, radio, saved_state):
        radio_pause()
        a, b = radio.get_both_vfo_status()
        assert isinstance(a, VFOStatus)
        assert isinstance(b, VFOStatus)
        assert FREQ_MIN_HZ <= a.frequency_hz <= FREQ_MAX_HZ
        assert FREQ_MIN_HZ <= b.frequency_hz <= FREQ_MAX_HZ

    def test_not_transmitting(self, radio, saved_state):
        """Safety: radio must not be transmitting during tests."""
        radio_pause()
        flags = radio.read_flags()
        assert flags.transmitting is False


@pytest.mark.live
class TestLiveFrequency:
    """Set and verify frequencies across HF bands."""

    BAND_FREQUENCIES = [
        1_810_000,    # 160m
        3_573_000,    # 80m FT8
        7_074_000,    # 40m FT8
        14_195_000,   # 20m SSB
        21_300_000,   # 15m
        28_500_000,   # 10m
    ]

    @pytest.mark.parametrize("freq_hz", BAND_FREQUENCIES)
    def test_set_frequency_a(self, radio, saved_state, freq_hz):
        radio.select_vfo("A")
        radio_pause()
        radio.set_frequency_a(freq_hz)
        radio_pause()
        status = radio.get_vfo_status()
        assert abs(status.frequency_hz - freq_hz) <= 10, (
            f"Set {freq_hz}, got {status.frequency_hz}"
        )

    def test_set_frequency_b(self, radio, saved_state):
        radio.set_frequency_b(21_300_000)
        radio_pause()
        _, vfo_b = radio.get_both_vfo_status()
        assert abs(vfo_b.frequency_hz - 21_300_000) <= 10

    def test_set_frequency_b_second(self, radio, saved_state):
        radio.set_frequency_b(3_573_000)
        radio_pause()
        _, vfo_b = radio.get_both_vfo_status()
        assert abs(vfo_b.frequency_hz - 3_573_000) <= 10

    def test_boundary_min(self, radio, saved_state):
        radio.select_vfo("A")
        radio_pause()
        radio.set_frequency_a(FREQ_MIN_HZ)
        radio_pause()
        status = radio.get_vfo_status()
        assert abs(status.frequency_hz - FREQ_MIN_HZ) <= 10

    def test_boundary_max(self, radio, saved_state):
        """30 MHz — top of HF general coverage on the original FT-1000MP."""
        radio.select_vfo("A")
        radio_pause()
        radio.set_frequency_a(30_000_000)
        radio_pause()
        status = radio.get_vfo_status()
        assert abs(status.frequency_hz - 30_000_000) <= 10


@pytest.mark.live
class TestLiveMode:
    """Set and verify operating modes."""

    @pytest.mark.parametrize("mode_name", ["USB", "LSB", "CW", "AM", "FM"])
    def test_set_mode_vfo_a(self, radio, saved_state, mode_name):
        radio.select_vfo("A")
        radio_pause()
        radio.set_frequency_a(14_195_000)
        radio_pause()
        radio.set_mode(mode_name)
        radio_pause()
        radio_pause()  # extra settle for mode change
        status = radio.get_vfo_status()
        assert status.mode == MODE_BY_NAME[mode_name], (
            f"Set {mode_name}, got mode={status.mode} ({status.mode_name})"
        )

    def test_set_mode_vfo_b_cw(self, radio, saved_state):
        radio.set_mode("CW", vfo_b=True)
        radio_pause()
        _, vfo_b = radio.get_both_vfo_status()
        assert vfo_b.mode == Mode.CW


@pytest.mark.live
class TestLiveVFO:
    """VFO selection and copy."""

    def test_select_vfo_a(self, radio, saved_state):
        radio.select_vfo("A")
        radio_pause()
        flags = radio.read_flags()
        assert flags.vfo_b_selected is False

    def test_select_vfo_b(self, radio, saved_state):
        """Verify VFO-B select switches the active VFO.

        The VFO select command (0x05) works despite Hamlib's ``#if 0``.
        We verify by frequency rather than ``read_flags().vfo_b_selected``
        which is unreliable (like the clarifier flag).  The 32-byte
        response also swaps to (active, inactive) order after switching.
        """
        freq_a = 14_195_000   # 14.195 MHz
        freq_b = 7_074_000    #  7.074 MHz
        radio.select_vfo("A")
        radio_pause()
        radio.set_frequency_a(freq_a)
        radio_pause()
        radio.set_frequency_b(freq_b)
        radio_pause()

        # Send VFO-B select command
        radio.select_vfo("B")
        radio_pause()
        radio_pause()  # extra settle time

        # Verify operating frequency switched to VFO-B's
        after_current = radio.get_vfo_status(0x02)
        radio_pause()
        after_both = radio.get_both_vfo_status()

        assert abs(after_current.frequency_hz - freq_b) < 100, (
            f"VFO-B select did not switch operating frequency. "
            f"Expected ~{freq_b:,} Hz, got {after_current.frequency_hz:,} Hz"
        )
        # 32-byte response returns (active, inactive) — blocks swap after VFO switch
        assert abs(after_both[0].frequency_hz - freq_b) < 100, (
            f"Expected active block to hold VFO-B freq ~{freq_b:,} Hz, "
            f"got {after_both[0].frequency_hz:,} Hz"
        )
        assert abs(after_both[1].frequency_hz - freq_a) < 100, (
            f"Expected inactive block to hold VFO-A freq ~{freq_a:,} Hz, "
            f"got {after_both[1].frequency_hz:,} Hz"
        )

        # Restore VFO-A selection
        radio.select_vfo("A")
        radio_pause()


@pytest.mark.live
class TestLiveSplit:
    """Split on/off toggle."""

    def test_split_on(self, radio, saved_state):
        radio.set_split(True)
        radio_pause()
        flags = radio.read_flags()
        assert flags.split is True

    def test_split_off(self, radio, saved_state):
        radio.set_split(False)
        radio_pause()
        flags = radio.read_flags()
        assert flags.split is False


@pytest.mark.live
class TestLiveClarifier:
    """Clarifier on/off and offset."""

    def test_clarifier_off(self, radio, saved_state):
        radio.set_clarifier(False)
        radio_pause()
        flags = radio.read_flags()
        assert flags.clarifier is False

    def test_clarifier_on(self, radio, saved_state):
        radio.set_clarifier(True)
        radio_pause()
        radio_pause()  # extra settle for clarifier toggle
        # The 5-byte flags response (read_flags) does NOT report clarifier
        # state reliably. The clarifier enable is reflected in the 16-byte
        # status update byte 9 bit 1 (the RIT flag), because on the
        # FT-1000MP "clarifier" = RIT.
        status = radio.get_vfo_status()
        assert status.rit is True
        # clean up
        radio.set_clarifier(False)
        radio_pause()

    def test_clarifier_offset_positive(self, radio, saved_state):
        radio.set_clarifier(True)
        radio_pause()
        radio_pause()  # extra settle for clarifier toggle
        radio.set_clarifier_offset(500)
        radio_pause()
        radio_pause()  # extra settle for offset change
        status = radio.get_vfo_status()
        assert abs(status.clarifier_offset - 500) <= 20
        # clean up
        radio.set_clarifier_offset(0)
        radio_pause()
        radio.set_clarifier(False)
        radio_pause()

    def test_clarifier_offset_zero(self, radio, saved_state):
        radio.set_clarifier(True)
        radio_pause()
        radio.set_clarifier_offset(0)
        radio_pause()
        status = radio.get_vfo_status()
        assert abs(status.clarifier_offset) <= 10
        # clean up
        radio.set_clarifier(False)
        radio_pause()


@pytest.mark.live
class TestLiveCopyAtoB:
    """Copy VFO-A to VFO-B."""

    def test_copy_a_to_b(self, radio, saved_state):
        # Set A to a known freq/mode
        radio.select_vfo("A")
        radio_pause()
        radio.set_frequency_a(14_225_000)
        radio_pause()
        radio.set_mode("USB")
        radio_pause()

        # Copy A → B
        radio.copy_vfo_a_to_b()
        radio_pause()

        # Verify both match
        vfo_a, vfo_b = radio.get_both_vfo_status()
        assert abs(vfo_a.frequency_hz - vfo_b.frequency_hz) <= 10
        assert vfo_a.mode == vfo_b.mode


@pytest.mark.live
class TestLiveMemory:
    """Memory store and recall using channel 98."""

    def test_store_and_recall(self, radio, saved_state):
        test_freq = 7_234_000  # distinctive freq to distinguish from stale data

        # Set VFO-A to known state
        radio.select_vfo("A")
        radio_pause()
        radio.set_frequency_a(test_freq)
        radio_pause()
        radio.set_mode("LSB")
        radio_pause()

        # Verify VFO is set correctly before store
        status = radio.get_vfo_status()
        radio_pause()
        assert abs(status.frequency_hz - test_freq) <= 10, (
            f"Pre-store check: expected ~{test_freq}, got {status.frequency_hz}"
        )

        # Store to channel 98: skip recall_memory to avoid clobbering VFO,
        # send vfo_to_memory directly with channel in P4
        radio.vfo_to_memory(98)
        radio_pause()

        # Change VFO to something different
        radio.set_frequency_a(14_195_000)
        radio_pause()
        radio.set_mode("USB")
        radio_pause()

        # Recall channel 98 then transfer memory→VFO for readback
        radio.recall_memory(98)
        radio_pause()
        radio.memory_to_vfo(98)
        radio_pause()

        # Read back and verify the recalled freq/mode
        status = radio.get_vfo_status()
        assert abs(status.frequency_hz - test_freq) <= 10, (
            f"Expected ~{test_freq}, got {status.frequency_hz}"
        )
        assert status.mode == Mode.LSB, (
            f"Expected LSB, got {status.mode_name}"
        )


@pytest.mark.live
class TestLiveSafety:
    """Safety checks run at the end of the live test session."""

    def test_never_transmitting(self, radio, saved_state):
        """Verify the radio is not transmitting."""
        radio_pause()
        flags = radio.read_flags()
        assert flags.transmitting is False, "Radio is transmitting — ABORT!"
