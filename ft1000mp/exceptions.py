"""Custom exception hierarchy for FT-1000MP CAT control."""


class FT1000MPError(Exception):
    """Base exception for all FT-1000MP errors."""


class SerialConnectionError(FT1000MPError):
    """Failed to open or communicate over the serial port."""


class CommandTimeoutError(FT1000MPError):
    """Radio did not respond within the expected time."""


class InvalidFrequencyError(FT1000MPError):
    """Frequency is outside the valid range (100 kHz - 60 MHz)."""


class InvalidModeError(FT1000MPError):
    """Unrecognized operating mode."""
