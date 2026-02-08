"""Serial transport layer for the FT-1000MP CAT protocol.

Handles opening the serial port, writing commands byte-by-byte with
inter-byte delays, reading responses, and retry logic.
"""

import time
from typing import Optional

import serial

from .exceptions import CommandTimeoutError, SerialConnectionError

# Default serial parameters for the FT-1000MP
DEFAULT_PORT = "/dev/ttyUSB0"    # USB serial adapter via usbipd
DEFAULT_BAUDRATE = 4800
DEFAULT_TIMEOUT = 0.4            # 400ms read timeout
DEFAULT_RETRIES = 6
INTER_BYTE_DELAY = 0.005         # 5ms between bytes
POST_COMMAND_DELAY = 0.005       # 5ms after full command


class SerialPort:
    """Low-level serial transport for FT-1000MP CAT commands."""

    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.retries = retries
        self._ser: Optional[serial.Serial] = None

    # -- context manager ---------------------------------------------------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # -- open / close ------------------------------------------------------

    def open(self):
        if self._ser and self._ser.is_open:
            return
        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,
                timeout=self.timeout,
            )
        except serial.SerialException as exc:
            raise SerialConnectionError(
                f"Cannot open {self.port}: {exc}"
            ) from exc

    def close(self):
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._ser = None

    @property
    def is_open(self) -> bool:
        return self._ser is not None and self._ser.is_open

    # -- send / receive ----------------------------------------------------

    def send_command(
        self, cmd: bytes, response_length: int = 0
    ) -> Optional[bytes]:
        """Send a 5-byte CAT command and optionally read a response.

        Args:
            cmd: Exactly 5 bytes to send.
            response_length: Number of bytes to read back (0 = no response).

        Returns:
            Response bytes, or None if response_length is 0.

        Raises:
            CommandTimeoutError: If the radio does not respond after retries.
            SerialConnectionError: If the serial port is not open.
        """
        if not self.is_open:
            raise SerialConnectionError("Serial port is not open")

        for attempt in range(1, self.retries + 1):
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()

            # Write byte-by-byte with inter-byte delay
            for b in cmd:
                self._ser.write(bytes([b]))
                time.sleep(INTER_BYTE_DELAY)
            time.sleep(POST_COMMAND_DELAY)

            if response_length == 0:
                return None

            data = self._ser.read(response_length)
            if len(data) == response_length:
                return data

            # Retry — wait a bit longer before next attempt
            time.sleep(self.timeout)

        raise CommandTimeoutError(
            f"No response after {self.retries} attempts "
            f"(cmd=0x{cmd[-1]:02X}, expected {response_length} bytes)"
        )
