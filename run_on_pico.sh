#!/bin/bash
# Run a file on the Pico instead of on this computer.
#
#   ./run_on_pico.sh test_matrix.py     bring-up test, run this first
#   ./run_on_pico.sh sign.py            the Paradox Transistor Lab sign
#   ./run_on_pico.sh --install sign.py  save it as main.py so it starts on power-up
#
# The VS Code Run button (and `python3 sign.py`) uses the Mac's Python, which
# has no `machine` module - that one lives in the Pico's firmware, so running
# these files locally always ends in ModuleNotFoundError. This sends the file to
# the board over USB serial and shows its output here. Ctrl-C stops it.

set -u
cd "$(dirname "$0")"
INSTALL=0
if [ "${1:-}" = "--install" ]; then INSTALL=1; shift; fi
FILE="${1:-sign.py}"
[ -f "$FILE" ] || { echo "No such file: $FILE"; exit 2; }

have_serial() { ls /dev/cu.usbmodem* >/dev/null 2>&1; }
in_bootsel()  { system_profiler SPUSBDataType 2>/dev/null | grep -qi "RP2 Boot"; }
on_usb()      { system_profiler SPUSBDataType 2>/dev/null | grep -q "0x2e8a"; }

if ! have_serial; then
  if in_bootsel; then
    # This bench board's BOOTSEL button is stuck, so it lands in the bootloader
    # at every reset and needs a software boot before it will run MicroPython.
    if [ -x "$HOME/pico-oled/start.sh" ]; then
      echo "Board is in BOOTSEL. Booting MicroPython ..."
      "$HOME/pico-oled/start.sh" || { echo "Boot failed. Unplug, replug, retry."; exit 1; }
    else
      echo "Board is in the BOOTSEL bootloader. Flash MicroPython, or unplug and replug it."
      exit 1
    fi
  elif on_usb; then
    echo "An RP2040 is on USB but is not running MicroPython. Unplug and replug it."
    exit 1
  else
    echo "No Pico on USB (no device with vendor ID 0x2e8a)."
    echo "Try another cable - charge-only USB cables have no data lines - and plug"
    echo "straight into the Mac rather than through a hub."
    exit 1
  fi
fi

# Waits for the port and leaves the REPL at a clean >>> prompt; see pico_port.py
# for why both steps matter on this board.
prepare() { python3 pico_port.py; }

PORT=$(prepare) || exit 1

# `resume` tells mpremote not to soft-reset on connect. The soft reset re-creates
# the board's USB device, which kills the port mpremote is holding and surfaces as
# "OSError: [Errno 6] Device not configured". Using an explicit port rather than
# `connect auto` avoids a second flaky path.
mp() { python3 -m mpremote connect "$PORT" resume "$@"; }

# The scripts import these on the board, so they must be on its filesystem.
LIBS="config.py matrix.py font.py"
echo "Copying $LIBS to the board ..."
for f in $LIBS; do
  mp cp "$f" : >/dev/null || exit 1
  PORT=$(prepare) || exit 1
done

if [ "$INSTALL" = 1 ]; then
  mp cp "$FILE" :main.py >/dev/null || exit 1
  echo "Installed $FILE as main.py: it runs whenever the board powers up."
  echo "(Not on a board with a stuck BOOTSEL button - that one boots into the"
  echo " bootloader instead and needs ~/pico-oled/start.sh.)"
  exit 0
fi

echo "Running $FILE on $PORT  (Ctrl-C to stop)"
exec python3 -m mpremote connect "$PORT" resume run "$FILE"
