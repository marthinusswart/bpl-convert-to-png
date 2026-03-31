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

    def decode_pixels(self, sprite_width=None, sprite_height=None):
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

        If the data was exported as a sequence of sprites (e.g. from a spritesheet),
        providing sprite_width and sprite_height will decode each tile sequentially 
        and stitch them together into the final image dimensions.

        Returns a 2D list of pixel indices [y][x] and optionally mask data.
        """
        if self.width == 0 or self.height == 0:
            return None, None

        sw = sprite_width if sprite_width else self.width
        sh = sprite_height if sprite_height else self.height

        if self.width % sw != 0 or self.height % sh != 0:
            raise ValueError(
                f"Overall image dimensions ({self.width}x{self.height}) must be "
                f"multiples of sprite dimensions ({sw}x{sh})."
            )

        # KingCon enforces Amiga width alignment to 16-bit words per scanline
        sw_bytes = ((sw + 15) // 16) * 2

        tiles_x = self.width // sw
        tiles_y = self.height // sh

        pixels = [[0 for _ in range(self.width)] for _ in range(self.height)]
        mask = (
            [[255 for _ in range(self.width)] for _ in range(self.height)]
            if self.has_mask
            else None
        )

        data = self.data
        depth = self.depth

        # Calculate the size of a single sprite/tile chunk in the BPL file
        if self.interleaved:
            if self.has_mask:
                bytes_per_chunk = sh * depth * 2 * sw_bytes
            else:
                bytes_per_chunk = sh * depth * sw_bytes
        else:
            if self.has_mask:
                bytes_per_chunk = sh * sw_bytes * (depth + 1)
            else:
                bytes_per_chunk = sh * sw_bytes * depth

        sprite_idx = 0
        for ty in range(tiles_y):
            for tx in range(tiles_x):
                base_offset = sprite_idx * bytes_per_chunk
                sprite_idx += 1

                for y in range(sh):
                    dest_y = ty * sh + y
                    for x_byte in range(sw_bytes):
                        # --- read one byte from each color plane ---
                        color_plane_bytes = []
                        for j in range(depth):
                            if self.interleaved:
                                if self.has_mask:
                                    # Layout: [p0][mask][p1][mask]... per scanline
                                    off = (
                                        base_offset
                                        + y * depth * 2 * sw_bytes
                                        + j * 2 * sw_bytes
                                        + x_byte
                                    )
                                else:
                                    # Layout: [p0][p1]...[pN-1] per scanline
                                    off = (
                                        base_offset
                                        + y * depth * sw_bytes
                                        + j * sw_bytes
                                        + x_byte
                                    )
                            else:
                                # Non-interleaved: whole plane j is contiguous
                                off = (
                                    base_offset
                                    + j * (sw_bytes * sh)
                                    + y * sw_bytes
                                    + x_byte
                                )

                            color_plane_bytes.append(data[off] if off < len(data) else 0)

                        # --- read mask byte (one per color plane when interleaved) ---
                        mask_byte = None
                        if self.has_mask:
                            if self.interleaved:
                                # Mask slot immediately follows plane 0
                                off = (
                                    base_offset
                                    + y * depth * 2 * sw_bytes
                                    + 1 * sw_bytes  # slot index 1 = mask after plane 0
                                    + x_byte
                                )
                            else:
                                # Non-interleaved: mask is the last plane
                                off = (
                                    base_offset
                                    + depth * (sw_bytes * sh)
                                    + y * sw_bytes
                                    + x_byte
                                )
                            mask_byte = data[off] if off < len(data) else 0

                        # --- decode 8 pixels from this byte column ---
                        for bit in range(8):
                            x = x_byte * 8 + bit
                            if x >= sw:
                                break
                            
                            dest_x = tx * sw + x
                            bit_flag = 0x80 >> bit  # MSB-first (Amiga bit ordering)

                            pixel_index = 0
                            for j in range(depth):
                                if color_plane_bytes[j] & bit_flag:
                                    pixel_index |= 1 << j
                            pixels[dest_y][dest_x] = pixel_index

                            if mask is not None and mask_byte is not None:
                                mask[dest_y][dest_x] = 255 if (mask_byte & bit_flag) else 0

        return pixels, mask
