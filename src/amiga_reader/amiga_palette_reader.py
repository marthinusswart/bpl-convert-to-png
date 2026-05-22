import struct
import os
from pathlib import Path


class AmigaPaletteReader:
    """Reads and analyzes Amiga .pal (palette) files"""

    def __init__(self, filepath, bits=12):
        """Args:
        filepath: Path to the .pal file.
        bits:     Color depth of each palette entry — 12 (default, -RawPalette)
                  or 24 (-RawPalette24).
        """
        self.filepath = Path(filepath)
        self.bits = bits
        self.colors = []
        self.num_colors = 0
        self._read_palette()

    def _read_palette(self):
        """Read the palette file.

        12-bit (-RawPalette):   2 bytes/color, big-endian 0x0RGB
        24-bit (-RawPalette24): 4 bytes/color, big-endian 0x00RRGGBB
        """
        with open(self.filepath, "rb") as f:
            data = f.read()

        file_size = len(data)

        if self.bits == 24:
            if file_size % 4 != 0:
                raise ValueError(
                    f"{self.filepath}: file size {file_size} is not a multiple of 4; "
                    "not a valid 24-bit palette."
                )
            self.num_colors = file_size // 4
            for i in range(self.num_colors):
                offset = i * 4
                # 24-bit: 0x00 RR GG BB (big-endian)
                _, r, g, b = struct.unpack_from("BBBB", data, offset)
                self.colors.append((r, g, b))
        else:  # 12-bit (default)
            if file_size % 2 != 0:
                raise ValueError(
                    f"{self.filepath}: file size {file_size} is not a multiple of 2; "
                    "not a valid 12-bit palette."
                )
            self.num_colors = file_size // 2
            for i in range(self.num_colors):
                offset = i * 2
                # 12-bit Amiga RGB: 0x0RGB (big-endian word)
                word = struct.unpack(">H", data[offset : offset + 2])[0]
                r = ((word >> 8) & 0x0F) * 17  # Scale 4-bit to 8-bit
                g = ((word >> 4) & 0x0F) * 17
                b = (word & 0x0F) * 17
                self.colors.append((r, g, b))

    def get_summary(self):
        """Get summary information about the palette"""
        return {
            "num_colors": self.num_colors,
            "file_size": os.path.getsize(self.filepath),
            "colors": self.colors,
            "bits": self.bits,
        }
