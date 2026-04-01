from pathlib import Path


class AmigaBitplaneReader:
    """Reads and analyzes Amiga .bpl (bitplane) files.

    The BPL is always index-based (no embedded palette).
    Structure must be supplied explicitly via constructor arguments.
    """

    def __init__(
        self,
        filepath,
        width,
        height,
        bits=5,
        has_mask=False,
        interleaved=True,
    ):
        """Args:
        filepath:    Path to the .bpl file.
        width:       Image width in pixels (must be a multiple of 16).
        height:      Image height in pixels.
        bits:        Number of color bitplanes (default 5 → 32 colors).
        has_mask:    Whether a mask plane is present (default False).
        interleaved: Whether the layout is interleaved (default True).
        """
        self.filepath = Path(filepath)
        self.file_size = 0
        self.width = width
        self.height = height
        self.depth = bits
        self.has_mask = has_mask
        self.interleaved = interleaved
        self.data = None

        # Compute plane slots per scanline from the supplied parameters
        if has_mask and interleaved:
            self.total_planes = bits * 2  # [p0][mask][p1][mask]...
        elif has_mask:
            self.total_planes = bits + 1  # color planes + 1 mask plane at end
        else:
            self.total_planes = bits

        with open(self.filepath, "rb") as f:
            self.data = f.read()
        self.file_size = len(self.data)
        
        # Validate file size against requested dimensions
        width_bytes = ((self.width + 15) // 16) * 2
        expected_size = width_bytes * self.height * self.total_planes
        if self.file_size > 0 and self.file_size < expected_size:
            raise ValueError(
                f"File is too small! The .bpl file is only {self.file_size} bytes, "
                f"but a {self.width}x{self.height} image with {self.total_planes} total planes "
                f"requires at least {expected_size} bytes.\n\n"
                f"Hint: If you generated this with KingCon using '-W=16 -H=16', KingCon treated those "
                f"as crop dimensions and ONLY exported a single 16x16 tile!"
            )

    def get_summary(self):
        """Get summary information about the bitplane"""
        max_colors = 2**self.depth if self.depth > 0 else 0

        return {
            "file_size": self.file_size,
            "width": self.width,
            "height": self.height,
            "depth": self.depth,
            "max_colors": max_colors,
            "has_mask": self.has_mask,
            "interleaved": self.interleaved,
            "bytes_per_line": ((self.width + 15) // 16) * 2 if self.width > 0 else 0,
            "total_planes": self.total_planes,
        }

    def decode_pixels(self):
        """Decode bitplane data to pixel indices.

        Supports all three KingCon layouts (from kingcon.md):

        Non-interleaved (no mask / with mask appended as last plane):
            Scanline y, plane j, byte x_byte:
                offset = j * (widthBytes * height) + y * widthBytes + x_byte

        Interleaved, no mask:
            Scanline y, plane j, byte x_byte:
                offset = y * (widthBytes * depth) + j * widthBytes + x_byte

        Interleaved, with mask (mask duplicated after each color plane):
            Layout per scanline: [p0][mask][p1][mask]...[pN-1][mask]
            Scanline y, color plane j, byte x_byte:
                offset = y * (widthBytes * depth * 2) + j * 2 * widthBytes + x_byte
            Mask byte for color plane j, byte x_byte:
                offset = y * (widthBytes * depth * 2) + (j * 2 + 1) * widthBytes + x_byte

        Returns a 2D list of pixel indices [y][x] and optionally mask data.
        """
        if self.width == 0 or self.height == 0:
            return None, None

        width_bytes = ((self.width + 15) // 16) * 2

        pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]
        mask = (
            [[255 for _ in range(self.width)] for _ in range(self.height)]
            if self.has_mask
            else None
        )

        data = self.data
        depth = self.depth

        for y in range(self.height):
            for x_byte in range(width_bytes):
                color_plane_bytes = [0] * depth
                mask_byte = 0

                if self.has_mask:
                    if self.interleaved:
                        for j in range(depth):
                            off = (y * depth * 2 * width_bytes) + (j * 2 * width_bytes) + x_byte
                            color_plane_bytes[j] = data[off] if off < len(data) else 0
                        mask_off = (y * depth * 2 * width_bytes) + (1 * width_bytes) + x_byte
                        mask_byte = data[mask_off] if mask_off < len(data) else 0
                    else:
                        for j in range(depth):
                            off = (j * width_bytes * self.height) + (y * width_bytes) + x_byte
                            color_plane_bytes[j] = data[off] if off < len(data) else 0
                        mask_off = (depth * width_bytes * self.height) + (y * width_bytes) + x_byte
                        mask_byte = data[mask_off] if mask_off < len(data) else 0
                else:
                    if self.interleaved:
                        for j in range(depth):
                            off = (y * depth * width_bytes) + (j * width_bytes) + x_byte
                            color_plane_bytes[j] = data[off] if off < len(data) else 0
                    else:
                        for j in range(depth):
                            off = (j * width_bytes * self.height) + (y * width_bytes) + x_byte
                            color_plane_bytes[j] = data[off] if off < len(data) else 0

                for bit in range(8):
                    x = x_byte * 8 + bit
                    if x >= self.width:
                        break

                    bit_flag = 0x80 >> bit

                    pixel_index = 0
                    for j in range(depth):
                        if color_plane_bytes[j] & bit_flag:
                            pixel_index |= 1 << j
                    pixels[y][x] = pixel_index

                    if mask is not None:
                        mask[y][x] = 255 if (mask_byte & bit_flag) else 0

        return pixels, mask
