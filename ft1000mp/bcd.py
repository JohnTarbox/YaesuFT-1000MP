"""Frequency encode/decode helpers for Yaesu FT-1000MP.

The FT-1000MP uses ASYMMETRIC encoding:

  SET direction (host → radio):
    Little-endian packed BCD of freq_hz / 10.
    (Hamlib's ``to_bcd`` function.)

  GET direction (status response):
    Big-endian binary integer with *10/16 scaling.
    freq_hz = raw_u32 * 10 // 16
"""


# -- SET direction: little-endian packed BCD --------------------------------

def freq_to_bytes(freq_hz: int) -> bytes:
    """Encode a frequency in Hz for a SET command (little-endian packed BCD).

    Matches Hamlib's ``to_bcd(buf, freq/10, 8)``.

    Args:
        freq_hz: Frequency in Hertz (10 Hz resolution).

    Returns:
        4 bytes, little-endian packed BCD.
    """
    val = freq_hz // 10
    result = bytearray(4)
    for i in range(4):
        low = val % 10
        val //= 10
        high = val % 10
        val //= 10
        result[i] = (high << 4) | low
    return bytes(result)


# -- GET direction: binary *10/16 scaling -----------------------------------

def bytes_to_freq(data: bytes) -> int:
    """Decode 4 bytes from a status response into a frequency in Hz.

    Args:
        data: 4 bytes, big-endian binary.

    Returns:
        Frequency in Hertz.
    """
    raw = int.from_bytes(data[:4], "big")
    return raw * 10 // 16


# -- Legacy big-endian BCD (unused, kept for reference) ---------------------

def freq_to_bcd_bytes(freq_hz: int) -> bytes:
    scaled = freq_hz // 10
    digits = f"{scaled:08d}"
    result = []
    for i in range(0, 8, 2):
        high = int(digits[i])
        low = int(digits[i + 1])
        result.append((high << 4) | low)
    return bytes(result)


def bcd_bytes_to_freq(data: bytes) -> int:
    digits = []
    for b in data[:4]:
        digits.append((b >> 4) & 0x0F)
        digits.append(b & 0x0F)
    scaled = 0
    for d in digits:
        scaled = scaled * 10 + d
    return scaled * 10
