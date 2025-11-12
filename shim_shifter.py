# shim_shifter.py
# Wrap the professor's 74HC595 Shifter (LSB-first) so your code can stay MSB-first.

from shifter import Shifter as ProfShifter  # <-- professor's shifter.py

def _rev8(b: int) -> int:
    b &= 0xFF
    b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
    b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
    b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
    return b

class Shifter(ProfShifter):
    def shiftByte(self, b: int):
        # Your code composes an MSB-first byte; flip it for the LSB-first driver.
        super().shiftByte(_rev8(b))
