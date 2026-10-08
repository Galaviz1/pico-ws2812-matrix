"""Find the Pico's serial port and leave its REPL at a clean prompt.

Called by run_on_pico.sh before every mpremote command. Two board-specific
reasons this is needed:

  * mpremote normally soft-resets the board (Ctrl-D) when it connects. On the
    RP2040 that tears down and re-creates the USB CDC device, so the port mpremote
    just opened disappears under it and pyserial raises
    "OSError: [Errno 6] Device not configured". run_on_pico.sh therefore uses
    `mpremote resume`, which skips the soft reset - but resume attaches to
    whatever state the REPL was left in.

  * So the REPL has to be put in a known state first: Ctrl-C to stop anything
    still running, Ctrl-B to leave raw REPL, then drain the banner. Skipping this
    makes mpremote fail with "could not exec command (response: b'R\\x01')".

Prints the port path on success; exits non-zero with a message on failure.
"""

import glob
import sys
import time

import serial


def find_port(timeout=10.0):
    deadline = time.monotonic() + timeout
    while True:
        ports = sorted(glob.glob("/dev/cu.usbmodem*"))
        if ports:
            return ports[0]
        if time.monotonic() >= deadline:
            return None
        time.sleep(0.25)


def clean_repl(port, attempts=3):
    last = None
    for _ in range(attempts):
        try:
            with serial.Serial(port, 115200, timeout=0.5) as s:
                s.write(b"\x03\x03")      # interrupt a running script
                time.sleep(0.3)
                s.write(b"\x02")          # leave raw REPL if we are in it
                time.sleep(0.3)
                s.reset_input_buffer()    # drop the banner
                s.write(b"\r\n")
                time.sleep(0.3)
                if b">>>" in s.read(200):
                    return True
        except OSError as e:
            # The port can vanish briefly while the board re-enumerates.
            last = e
            time.sleep(1.0)
    if last:
        print("could not talk to %s: %s" % (port, last), file=sys.stderr)
    return False


if __name__ == "__main__":
    p = find_port()
    if not p:
        print("no /dev/cu.usbmodem* port appeared", file=sys.stderr)
        sys.exit(1)
    if not clean_repl(p):
        print("port %s did not reach a REPL prompt" % p, file=sys.stderr)
        sys.exit(1)
    print(p)
