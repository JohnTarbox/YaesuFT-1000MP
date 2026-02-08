#!/usr/bin/env python3
"""Interactive CLI for the Yaesu FT-1000MP CAT control."""

import sys

from ft1000mp import FT1000MP, FT1000MPError
from ft1000mp.protocol import MODE_BY_NAME


def print_help():
    print(
        """
FT-1000MP CAT Control Commands:
  status            Read current VFO status (frequency, mode, clarifier)
  status ab         Read both VFO-A and VFO-B
  flags             Read radio status flags
  freq <MHz>        Set VFO-A frequency (e.g. freq 14.250)
  freqb <MHz>       Set VFO-B frequency
  mode <name>       Set VFO-A mode (LSB USB CW AM FM RTTY PKT)
  modeb <name>      Set VFO-B mode
  vfo a|b           Select VFO
  ab                Copy VFO-A to VFO-B
  split on|off      Toggle split operation
  clar on|off       Toggle clarifier
  clar <offset_hz>  Set clarifier offset (e.g. clar 600 or clar -300)
  ptt on|off        Transmitter control
  mem <1-99>        Recall memory channel
  vfo2mem <1-99>    Store VFO to memory channel
  mem2vfo <1-99>    Recall memory channel to VFO
  help              Show this help
  quit              Exit
"""
    )


def format_freq(hz: int) -> str:
    """Format frequency in Hz as a readable MHz string."""
    mhz = hz / 1_000_000
    return f"{mhz:.6f} MHz ({hz:,} Hz)"


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"

    print(f"FT-1000MP CAT Control — connecting on {port}")
    try:
        radio = FT1000MP(port=port)
        radio.open()
    except FT1000MPError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("Connected. Type 'help' for commands, 'quit' to exit.\n")

    try:
        while True:
            try:
                line = input("ft1000mp> ").strip()
            except EOFError:
                break

            if not line:
                continue

            parts = line.split()
            cmd = parts[0].lower()
            args = parts[1:]

            try:
                if cmd == "quit" or cmd == "exit":
                    break

                elif cmd == "help":
                    print_help()

                elif cmd == "status":
                    if args and args[0].lower() == "ab":
                        vfo_a, vfo_b = radio.get_both_vfo_status()
                        for label, st in [("VFO-A", vfo_a), ("VFO-B", vfo_b)]:
                            print(f"  {label}:")
                            print(f"    Frequency : {format_freq(st.frequency_hz)}")
                            print(f"    Mode      : {st.mode_name}")
                            print(f"    Clarifier : {st.clarifier_offset:+d} Hz")
                            print(f"    RIT       : {'ON' if st.rit else 'OFF'}")
                            print(f"    XIT       : {'ON' if st.xit else 'OFF'}")
                    else:
                        status = radio.get_vfo_status()
                        print(f"  Current VFO:")
                        print(f"    Frequency : {format_freq(status.frequency_hz)}")
                        print(f"    Mode      : {status.mode_name}")
                        print(f"    Clarifier : {status.clarifier_offset:+d} Hz")
                        print(f"    RIT       : {'ON' if status.rit else 'OFF'}")
                        print(f"    XIT       : {'ON' if status.xit else 'OFF'}")

                elif cmd == "flags":
                    flags = radio.read_flags()
                    print(f"  Split       : {'ON' if flags.split else 'OFF'}")
                    print(f"  Clarifier   : {'ON' if flags.clarifier else 'OFF'}")
                    print(f"  VFO         : {'B' if flags.vfo_b_selected else 'A'}")
                    print(f"  TX          : {'ON' if flags.transmitting else 'OFF'}")
                    print(f"  Priority    : {'ON' if flags.priority else 'OFF'}")
                    print(f"  Raw flags   : 0x{flags.raw:02X}")

                elif cmd == "freq":
                    if not args:
                        status = radio.get_vfo_status()
                        print(f"  VFO: {format_freq(status.frequency_hz)}")
                    else:
                        freq_mhz = float(args[0])
                        freq_hz = int(freq_mhz * 1_000_000)
                        radio.set_frequency_a(freq_hz)
                        print(f"  VFO-A set to {format_freq(freq_hz)}")

                elif cmd == "freqb":
                    if not args:
                        status = radio.get_vfo_status()
                        print(f"  VFO: {format_freq(status.frequency_hz)}")
                    else:
                        freq_mhz = float(args[0])
                        freq_hz = int(freq_mhz * 1_000_000)
                        radio.set_frequency_b(freq_hz)
                        print(f"  VFO-B set to {format_freq(freq_hz)}")

                elif cmd == "mode":
                    if not args:
                        print(
                            f"  Available: {', '.join(sorted(MODE_BY_NAME.keys()))}"
                        )
                    else:
                        radio.set_mode(args[0])
                        print(f"  Mode set to {args[0].upper()}")

                elif cmd == "modeb":
                    if not args:
                        print(
                            f"  Available: {', '.join(sorted(MODE_BY_NAME.keys()))}"
                        )
                    else:
                        radio.set_mode(args[0], vfo_b=True)
                        print(f"  VFO-B mode set to {args[0].upper()}")

                elif cmd == "vfo":
                    if not args:
                        print("  Usage: vfo a|b")
                    else:
                        radio.select_vfo(args[0])
                        print(f"  Selected VFO-{args[0].upper()}")

                elif cmd == "ab":
                    radio.copy_vfo_a_to_b()
                    print("  Copied VFO-A to VFO-B")

                elif cmd == "split":
                    if not args:
                        print("  Usage: split on|off")
                    else:
                        on = args[0].lower() == "on"
                        radio.set_split(on)
                        print(f"  Split {'ON' if on else 'OFF'}")

                elif cmd == "clar":
                    if not args:
                        print("  Usage: clar on|off | clar <offset_hz>")
                    elif args[0].lower() in ("on", "off"):
                        on = args[0].lower() == "on"
                        radio.set_clarifier(on)
                        print(f"  Clarifier {'ON' if on else 'OFF'}")
                    else:
                        offset = int(args[0])
                        radio.set_clarifier_offset(offset)
                        print(f"  Clarifier offset set to {offset:+d} Hz")

                elif cmd == "ptt":
                    if not args:
                        print("  Usage: ptt on|off")
                    else:
                        on = args[0].lower() == "on"
                        radio.set_ptt(on)
                        print(f"  PTT {'ON' if on else 'OFF'}")

                elif cmd == "mem":
                    if not args:
                        print("  Usage: mem <1-99>")
                    else:
                        channel = int(args[0])
                        radio.recall_memory(channel)
                        print(f"  Recalled memory channel {channel}")

                elif cmd == "vfo2mem":
                    if not args:
                        print("  Usage: vfo2mem <1-99>")
                    else:
                        channel = int(args[0])
                        radio.vfo_to_memory(channel)
                        print(f"  VFO stored to memory channel {channel}")

                elif cmd == "mem2vfo":
                    if not args:
                        print("  Usage: mem2vfo <1-99>")
                    else:
                        channel = int(args[0])
                        radio.memory_to_vfo(channel)
                        print(f"  Memory channel {channel} recalled to VFO")

                else:
                    print(f"  Unknown command: {cmd}. Type 'help' for commands.")

            except FT1000MPError as e:
                print(f"  Error: {e}")
            except ValueError as e:
                print(f"  Invalid value: {e}")

    except KeyboardInterrupt:
        print()
    finally:
        radio.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()
